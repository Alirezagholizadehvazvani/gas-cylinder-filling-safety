"""Configuration constants for the digital safety prototype.

Thresholds match the company-approved setpoints documented in the
engineering design baseline (120 bar warning / 125 bar emergency).
They are simulation parameters only and are not independently validated
legal or equipment limits.
"""

# Company-approved setpoints (digital prototype only)
WARNING_PRESSURE: float = 120.0
EMERGENCY_PRESSURE: float = 125.0

# Sensor validity window (bar)
MAX_SENSOR_PRESSURE: float = 200.0
MIN_SENSOR_PRESSURE: float = 0.0

# Discrete-tick fault detection windows
FROZEN_SENSOR_TICKS: int = 2
VALVE_CLOSE_TIMEOUT_TICKS: int = 2
