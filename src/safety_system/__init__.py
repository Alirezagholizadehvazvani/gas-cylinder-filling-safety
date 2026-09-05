"""
Gas Cylinder Filling Safety System — Digital Prototype

Logic simulation of the safety controller for an O2/N2 cylinder filling process.
This package models pressure measurement, valve control, state machine behaviour,
sensor/valve/controller faults, and fail-safe shutdown. It is not connected to
and must not control real gas equipment.
"""

from .states import State
from .sensor import PressureSensor
from .valve import Valve
from .controller import SafetySystem
from .config import (
    WARNING_PRESSURE,
    EMERGENCY_PRESSURE,
    MAX_SENSOR_PRESSURE,
    FROZEN_SENSOR_TICKS,
    VALVE_CLOSE_TIMEOUT_TICKS,
)

__all__ = [
    "State",
    "PressureSensor",
    "Valve",
    "SafetySystem",
    "WARNING_PRESSURE",
    "EMERGENCY_PRESSURE",
    "MAX_SENSOR_PRESSURE",
    "FROZEN_SENSOR_TICKS",
    "VALVE_CLOSE_TIMEOUT_TICKS",
]

__version__ = "0.3.0"
