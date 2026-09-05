"""Safety controller: state machine, decision logic, and fail-safe shutdown."""

from dataclasses import dataclass, field

from .config import (
    WARNING_PRESSURE,
    EMERGENCY_PRESSURE,
    VALVE_CLOSE_TIMEOUT_TICKS,
)
from .states import State
from .sensor import PressureSensor
from .valve import Valve
from .logging import EventLog, EventType


@dataclass
class SafetySystem:
    """Digital safety controller for the cylinder-filling process.

    Implements the design-baseline state machine and safety requirements:
    continuous pressure monitoring, 120 bar warning, ≥125 bar emergency
    shutdown, sensor/valve/controller fault handling, E-stop, power failure,
    no automatic restart, and intentional key-style reset.

    This is a logic simulation only. It must not be connected to real
    high-pressure gas equipment.
    """

    state: State = State.POWER_OFF
    sensor: PressureSensor = field(default_factory=PressureSensor)
    valve: Valve = field(default_factory=Valve)
    e_stop: bool = False
    power_available: bool = True
    external_fault: bool = False
    watchdog_expired: bool = False
    max_pressure: float = 0.0
    log: EventLog = field(default_factory=EventLog)

    # ------------------------------------------------------------------
    # Compatibility shim for older call sites that used .events
    # ------------------------------------------------------------------
    @property
    def events(self) -> list[str]:
        return self.log.messages()

    def _record(
        self,
        event_type: EventType,
        message: str,
        *,
        pressure: float | None = None,
        **extra,
    ) -> None:
        self.log.append(
            event_type,
            message,
            state=self.state.value,
            pressure=pressure,
            **extra,
        )

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def power_on(self) -> None:
        if not self.power_available:
            self.lock("Power unavailable")
            return

        self.state = State.SELF_CHECK
        self._record(EventType.POWER_ON, "System powered on")
        self.self_check()

    def self_check(self) -> None:
        """Verify safety preconditions before entering READY."""
        if not self.power_available:
            self.lock("Power unavailable")
        elif self.e_stop:
            self.lock("Emergency stop active")
        elif self.external_fault:
            self.lock("External/controller fault")
        elif self.watchdog_expired:
            self.lock("Watchdog failure")
        elif not self.sensor.healthy():
            self.lock("Pressure sensor fault")
        elif (self.sensor.read() or 0.0) >= WARNING_PRESSURE:
            # Prevent reset while process pressure is still elevated
            self.lock("Pressure still at or above warning threshold")
        else:
            if not self.valve.physically_closed:
                self.valve.close()
            if not self.valve.physically_closed:
                self.lock("Valve failed to close during self-check")
                return
            self.state = State.READY
            self._record(EventType.SELF_CHECK, "Self-check passed - READY")

    def start(self) -> None:
        """Operator start request — only accepted from READY."""
        if self.state != State.READY:
            self._record(EventType.INFO, "Start rejected - system not READY")
            return

        if self.e_stop or not self.power_available:
            self.lock("Start interlock failed")
            return

        if self.external_fault or self.watchdog_expired:
            self.lock("Controller/watchdog interlock failed")
            return

        if not self.sensor.healthy():
            self.lock("Pressure sensor fault")
            return

        self.valve.command(True)
        self.state = State.FILLING
        self._record(EventType.START, "Filling started")

    def reset(self) -> None:
        """Authorized reset from LOCK. Returns only to SELF_CHECK → READY."""
        if self.state != State.LOCK:
            self._record(EventType.INFO, "Reset ignored - system not LOCKED")
            return

        self._record(EventType.RESET, "Reset requested")
        self.self_check()

    # ------------------------------------------------------------------
    # Cyclic update (called each discrete simulation tick)
    # ------------------------------------------------------------------
    def update(self) -> None:
        if not self.power_available:
            self.power_failure()
            return

        if self.e_stop:
            self.emergency_stop()
            return

        if self.external_fault:
            self.lock("Controller failure")
            return

        if self.watchdog_expired:
            self.watchdog_failure()
            return

        if self.state not in (State.FILLING, State.WARNING):
            return

        # Continuous command/feedback monitoring while filling
        if not self.valve.matches_command:
            self.lock("Valve fault - command/feedback mismatch")
            return

        pressure = self.sensor.read()

        if pressure is None or not self.sensor.healthy():
            self.lock("Pressure sensor fault")
            return

        self.max_pressure = max(self.max_pressure, pressure)

        if pressure >= EMERGENCY_PRESSURE:
            self.emergency_shutdown(pressure)
        elif pressure >= WARNING_PRESSURE:
            if self.state != State.WARNING:
                self.state = State.WARNING
                self._record(
                    EventType.WARNING,
                    f"Warning threshold reached: {pressure:.1f} bar",
                    pressure=pressure,
                )
        else:
            self.state = State.FILLING

    # ------------------------------------------------------------------
    # Safe shutdown path (bounded valve-close verification)
    # ------------------------------------------------------------------
    def _verify_valve_closed(self, reason: str) -> bool:
        """Issue CLOSE and confirm feedback within the configured timeout.

        Returns True only when CLOSED is verified. Otherwise the system
        remains LOCKED and records that the safe state could not be verified.
        """
        self.valve.close()

        for tick in range(1, VALVE_CLOSE_TIMEOUT_TICKS + 1):
            if self.valve.physically_closed:
                self._record(
                    EventType.INFO,
                    f"Valve CLOSED confirmation received at tick "
                    f"{tick}/{VALVE_CLOSE_TIMEOUT_TICKS}",
                )
                self.state = State.LOCK
                self._record(EventType.LOCK, reason)
                self._record(EventType.LOCK, "System LOCKED - SAFE STATE VERIFIED")
                return True

        self.state = State.LOCK
        self._record(
            EventType.CRITICAL,
            f"CRITICAL FAULT: Valve CLOSED confirmation timeout "
            f"after {VALVE_CLOSE_TIMEOUT_TICKS} ticks",
        )
        self._record(EventType.CRITICAL, f"Safety shutdown requested: {reason}")
        self._record(EventType.LOCK, "System LOCKED - SAFE STATE NOT VERIFIED")
        return False

    def _safe_shutdown(self, reason: str) -> bool:
        return self._verify_valve_closed(reason)

    def emergency_shutdown(self, pressure: float) -> None:
        self.state = State.EMERGENCY
        self._record(
            EventType.EMERGENCY,
            f"Emergency shutdown: {pressure:.1f} bar",
            pressure=pressure,
        )
        self._safe_shutdown("Emergency shutdown - filling disabled")

    def emergency_stop(self) -> None:
        if self.state != State.LOCK:
            self._safe_shutdown("Emergency stop activated")

    def power_failure(self) -> None:
        if self.state != State.LOCK:
            self._safe_shutdown("Power failure - filling disabled")

    def watchdog_failure(self) -> None:
        if self.state != State.LOCK:
            self._safe_shutdown("Watchdog failure - filling disabled")

    def lock(self, reason: str) -> None:
        """Immediate lock path used for sensor / interlock faults."""
        self.valve.close()

        if not self.valve.physically_closed:
            self.state = State.LOCK
            self._record(EventType.VALVE_FAULT, f"FAULT: {reason}")
            self._record(EventType.VALVE_FAULT, "FAULT: Valve could not be verified CLOSED")
            self._record(EventType.LOCK, "System LOCKED - VALVE NOT VERIFIED CLOSED")
            return

        self.state = State.LOCK
        self._record(EventType.LOCK, f"FAULT: {reason}")
        self._record(EventType.LOCK, "System LOCKED")

    # ------------------------------------------------------------------
    # Status snapshot
    # ------------------------------------------------------------------
    def status(self) -> dict:
        p = self.sensor.read()
        return {
            "state": self.state.value,
            "pressure": None if p is None else round(p, 1),
            "valve": "OPEN" if self.valve.open_feedback else "CLOSED",
            "valve_closed_feedback": self.valve.closed_feedback,
            "valve_physically_closed": self.valve.physically_closed,
            "sensor": "OK" if self.sensor.healthy() else "FAULT",
            "e_stop": "ACTIVE" if self.e_stop else "RELEASED",
            "power": "AVAILABLE" if self.power_available else "FAILED",
            "watchdog": "EXPIRED" if self.watchdog_expired else "HEALTHY",
            "max_pressure": round(self.max_pressure, 1),
        }
