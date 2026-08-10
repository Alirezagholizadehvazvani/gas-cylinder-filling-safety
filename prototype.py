from dataclasses import dataclass, field
from enum import Enum
from time import strftime

WARNING_PRESSURE = 120.0
EMERGENCY_PRESSURE = 125.0


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

    def command(self, open_: bool):
        self.open_command = open_
        self.open_feedback = open_
        self.closed_feedback = not open_

    def close(self):
        self.command(False)


@dataclass
class PressureSensor:
    pressure: float = 0.0
    connected: bool = True
    valid: bool = True
    frozen: bool = False
    _last_value: float = 0.0

    def read(self):
        if not self.connected or not self.valid:
            return None
        if self.frozen:
            return self._last_value
        self._last_value = self.pressure
        return self.pressure

    def healthy(self):
        value = self.read()
        return value is not None and 0 <= value <= 200


@dataclass
class SafetySystem:
    state: State = State.POWER_OFF
    sensor: PressureSensor = field(default_factory=PressureSensor)
    valve: Valve = field(default_factory=Valve)
    e_stop: bool = False
    power_available: bool = True
    external_fault: bool = False
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
            self.lock("External fault")
        elif not self.sensor.healthy():
            self.lock("Pressure sensor fault")
        else:
            self.valve.close()
            self.state = State.READY
            self.log("Self-check passed - READY")

    def start(self):
        if self.state != State.READY:
            self.log("Start rejected - system not READY")
            return
        if self.e_stop or not self.power_available:
            self.lock("Start interlock failed")
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

    def emergency_shutdown(self, pressure):
        self.valve.close()
        self.state = State.EMERGENCY
        self.log(f"Emergency shutdown: {pressure:.1f} bar")
        self.state = State.LOCK
        self.log("System LOCKED")

    def emergency_stop(self):
        self.valve.close()
        self.state = State.LOCK
        self.log("Emergency stop activated")
        self.log("System LOCKED")

    def power_failure(self):
        if self.state != State.LOCK:
            self.valve.close()
            self.state = State.LOCK
            self.log("Power failure - filling disabled")
            self.log("System LOCKED")

    def lock(self, reason):
        self.valve.close()
        self.state = State.LOCK
        self.log(f"FAULT: {reason}")
        self.log("System LOCKED")

    def status(self):
        p = self.sensor.read()
        return {
            "state": self.state.value,
            "pressure": None if p is None else round(p, 1),
            "valve": "OPEN" if self.valve.open_feedback else "CLOSED",
            "sensor": "OK" if self.sensor.healthy() else "FAULT",
            "e_stop": "ACTIVE" if self.e_stop else "RELEASED",
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
