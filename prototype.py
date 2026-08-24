from dataclasses import dataclass, field
from enum import Enum
from time import strftime

WARNING_PRESSURE = 120.0
EMERGENCY_PRESSURE = 125.0
MAX_SENSOR_PRESSURE = 200.0
FROZEN_SENSOR_TICKS = 2
VALVE_CLOSE_TIMEOUT_TICKS = 2


class State(Enum):
    POWER_OFF = "POWER_OFF"
    SELF_CHECK = "SELF_CHECK"
    READY = "READY"
    FILLING = "FILLING"
    WARNING = "WARNING"
    EMERGENCY = "EMERGENCY"
    LOCK = "LOCK"


@dataclass
class Valve:
    open_command: bool = False
    open_feedback: bool = False
    closed_feedback: bool = True

    # Fault-injection flags
    fail_to_close: bool = False
    feedback_failure: bool = False

    def command(self, open_: bool):
        self.open_command = open_

        if open_:
            # Normal opening behaviour.
            self.open_feedback = True
            self.closed_feedback = False
            return

        # Closing command.
        if self.fail_to_close:
            # Physical valve remains open: the controller cannot make
            # the simulated actuator reach the requested safe position.
            self.open_feedback = True
            self.closed_feedback = False
        else:
            self.open_feedback = False
            self.closed_feedback = True

        if self.feedback_failure:
            # Physical position changes, but feedback lies/stays inconsistent.
            self.open_feedback = True
            self.closed_feedback = False

    def close(self):
        self.command(False)

    @property
    def physically_closed(self) -> bool:
        return not self.open_feedback and self.closed_feedback


@dataclass
class PressureSensor:
    pressure: float = 0.0
    connected: bool = True
    valid: bool = True
    frozen: bool = False
    _last_value: float = 0.0
    _frozen_ticks: int = 0

    def read(self):
        if not self.connected or not self.valid:
            return None

        if self.frozen:
            self._frozen_ticks += 1
            return self._last_value

        self._frozen_ticks = 0
        self._last_value = self.pressure
        return self.pressure

    def healthy(self):
        value = self.read()
        if value is None:
            return False

        if not 0 <= value <= MAX_SENSOR_PRESSURE:
            return False

        if self.frozen and self._frozen_ticks >= FROZEN_SENSOR_TICKS:
            return False

        return True


@dataclass
class SafetySystem:
    state: State = State.POWER_OFF
    sensor: PressureSensor = field(default_factory=PressureSensor)
    valve: Valve = field(default_factory=Valve)
    e_stop: bool = False
    power_available: bool = True
    external_fault: bool = False
    watchdog_expired: bool = False
    max_pressure: float = 0.0
    events: list[str] = field(default_factory=list)

    def log(self, text):
        self.events.append(f"{strftime('%H:%M:%S')}  {text}")

    def power_on(self):
        if not self.power_available:
            self.lock("Power unavailable")
            return

        self.state = State.SELF_CHECK
        self.log("System powered on")
        self.self_check()

    def self_check(self):
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
        else:
            if not self.valve.physically_closed:
                self.valve.close()
            if not self.valve.physically_closed:
                self.lock("Valve failed to close during self-check")
                return
            self.state = State.READY
            self.log("Self-check passed - READY")

    def start(self):
        if self.state != State.READY:
            self.log("Start rejected - system not READY")
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
        self.log("Filling started")

    def reset(self):
        if self.state != State.LOCK:
            self.log("Reset ignored - system not LOCKED")
            return

        self.log("Reset requested")
        self.self_check()

    def update(self):
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
                self.log(f"Warning threshold reached: {pressure:.1f} bar")
        else:
            self.state = State.FILLING

    def _verify_valve_closed(self, reason):
        """
        Simulate a bounded-time valve-close confirmation.

        A safe shutdown is successful only when the valve can be verified
        CLOSED before the timeout. If it cannot, the controller remains
        LOCKED and records a critical valve-position fault. Restart is
        therefore impossible until the underlying fault is removed and a
        subsequent self-check succeeds.
        """
        self.valve.close()

        for tick in range(1, VALVE_CLOSE_TIMEOUT_TICKS + 1):
            if self.valve.physically_closed:
                self.log(
                    f"Valve CLOSED confirmation received at tick {tick}/{VALVE_CLOSE_TIMEOUT_TICKS}"
                )
                self.state = State.LOCK
                self.log(reason)
                self.log("System LOCKED - SAFE STATE VERIFIED")
                return True

        self.state = State.LOCK
        self.log(
            f"CRITICAL FAULT: Valve CLOSED confirmation timeout "
            f"after {VALVE_CLOSE_TIMEOUT_TICKS} ticks"
        )
        self.log(f"Safety shutdown requested: {reason}")
        self.log("System LOCKED - SAFE STATE NOT VERIFIED")
        return False

    def _safe_shutdown(self, reason):
        return self._verify_valve_closed(reason)

    def emergency_shutdown(self, pressure):
        self.state = State.EMERGENCY
        self.log(f"Emergency shutdown: {pressure:.1f} bar")
        self._safe_shutdown("System LOCKED")

    def emergency_stop(self):
        self._safe_shutdown("Emergency stop activated")

    def power_failure(self):
        if self.state != State.LOCK:
            self._safe_shutdown("Power failure - filling disabled")

    def watchdog_failure(self):
        if self.state != State.LOCK:
            self._safe_shutdown("Watchdog failure - filling disabled")

    def lock(self, reason):
        self.valve.close()

        if not self.valve.physically_closed:
            self.state = State.LOCK
            self.log(f"FAULT: {reason}")
            self.log("FAULT: Valve could not be verified CLOSED")
            self.log("System LOCKED - VALVE NOT VERIFIED CLOSED")
            return

        self.state = State.LOCK
        self.log(f"FAULT: {reason}")
        self.log("System LOCKED")

    def status(self):
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
        }


if __name__ == "__main__":
    system = SafetySystem()
    system.power_on()
    system.start()

    for pressure in (20, 60, 90, 110, 119, 120, 124, 125):
        system.sensor.pressure = pressure
        system.update()

    print(system.status())
    print("\nEvent log:")
    print("\n".join(system.events))
