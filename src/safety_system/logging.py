"""Structured event logging for the safety system."""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class EventType(str, Enum):
    """Categories of logged safety events (aligned with design baseline)."""

    POWER_ON = "POWER_ON"
    SELF_CHECK = "SELF_CHECK"
    START = "START"
    STOP = "STOP"
    WARNING = "WARNING"
    EMERGENCY = "EMERGENCY"
    SENSOR_FAULT = "SENSOR_FAULT"
    VALVE_FAULT = "VALVE_FAULT"
    E_STOP = "E_STOP"
    POWER_FAILURE = "POWER_FAILURE"
    WATCHDOG = "WATCHDOG"
    RESET = "RESET"
    LOCK = "LOCK"
    INFO = "INFO"
    CRITICAL = "CRITICAL"


@dataclass
class Event:
    """Single structured log entry."""

    timestamp: str
    event_type: EventType
    message: str
    state: str | None = None
    pressure: float | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["event_type"] = self.event_type.value
        return d

    def __str__(self) -> str:
        parts = [self.timestamp, self.event_type.value, self.message]
        if self.state is not None:
            parts.append(f"state={self.state}")
        if self.pressure is not None:
            parts.append(f"P={self.pressure:.1f}")
        return "  ".join(parts)


class EventLog:
    """Append-only structured event log."""

    def __init__(self) -> None:
        self._events: list[Event] = []

    def append(
        self,
        event_type: EventType,
        message: str,
        *,
        state: str | None = None,
        pressure: float | None = None,
        **extra: Any,
    ) -> Event:
        event = Event(
            timestamp=datetime.now(timezone.utc).strftime("%H:%M:%S"),
            event_type=event_type,
            message=message,
            state=state,
            pressure=pressure,
            extra=extra,
        )
        self._events.append(event)
        return event

    @property
    def events(self) -> list[Event]:
        return list(self._events)

    def messages(self) -> list[str]:
        """Plain string list for compatibility with older tests/reports."""
        return [str(e) for e in self._events]

    def contains(self, substring: str) -> bool:
        return any(substring in str(e) for e in self._events)

    def count_matching(self, substring: str) -> int:
        return sum(1 for e in self._events if substring in str(e))

    def clear(self) -> None:
        self._events.clear()

    def to_list(self) -> list[dict[str, Any]]:
        return [e.to_dict() for e in self._events]
