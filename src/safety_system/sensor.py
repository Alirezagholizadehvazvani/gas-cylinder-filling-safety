"""Pressure sensor model with fault-injection support."""

from dataclasses import dataclass, field

from .config import (
    MAX_SENSOR_PRESSURE,
    MIN_SENSOR_PRESSURE,
    FROZEN_SENSOR_TICKS,
)


@dataclass
class PressureSensor:
    """Simulated 4–20 mA-style pressure transducer.

    Supports intentional fault injection for digital verification:
    disconnect, invalid/out-of-range, and frozen (stuck) signal.
    """

    pressure: float = 0.0
    connected: bool = True
    valid: bool = True
    frozen: bool = False
    _last_value: float = field(default=0.0, repr=False)
    _frozen_ticks: int = field(default=0, repr=False)

    def read(self) -> float | None:
        """Return current pressure or None if the measurement is unavailable."""
        if not self.connected or not self.valid:
            return None

        if self.frozen:
            self._frozen_ticks += 1
            return self._last_value

        self._frozen_ticks = 0
        self._last_value = self.pressure
        return self.pressure

    def healthy(self) -> bool:
        """True when the sensor produces a usable in-range value."""
        value = self.read()
        if value is None:
            return False

        if not MIN_SENSOR_PRESSURE <= value <= MAX_SENSOR_PRESSURE:
            return False

        if self.frozen and self._frozen_ticks >= FROZEN_SENSOR_TICKS:
            return False

        return True
