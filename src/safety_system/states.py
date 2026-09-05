"""System state enumeration for the safety controller."""

from enum import Enum


class State(Enum):
    """Operating states of the digital safety system.

    Transitions follow the design baseline state machine:
    POWER_OFF → SELF_CHECK → READY → FILLING / WARNING →
    EMERGENCY / SENSOR_FAULT / VALVE_FAULT / E_STOP / POWER_FAILURE → LOCK.
    Reset from LOCK returns only to SELF_CHECK → READY; there is never a
    direct LOCK → FILLING path.
    """

    POWER_OFF = "POWER_OFF"
    SELF_CHECK = "SELF_CHECK"
    READY = "READY"
    FILLING = "FILLING"
    WARNING = "WARNING"
    EMERGENCY = "EMERGENCY"
    LOCK = "LOCK"
