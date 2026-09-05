"""Electric shutoff valve model with command/feedback and fault injection."""

from dataclasses import dataclass


@dataclass
class Valve:
    """Simulated high-pressure electric shutoff valve.

    Models open/close command, dual feedback (OPEN / CLOSED), and two
    intentional fault modes used by the fault-injection engine:
    - fail_to_close: actuator cannot reach the safe (closed) position
    - feedback_failure: physical position may change but feedback lies
    """

    open_command: bool = False
    open_feedback: bool = False
    closed_feedback: bool = True

    # Fault-injection flags
    fail_to_close: bool = False
    feedback_failure: bool = False

    def command(self, open_: bool) -> None:
        """Issue an open (True) or close (False) command."""
        self.open_command = open_

        if open_:
            self.open_feedback = True
            self.closed_feedback = False
            return

        # Closing command
        if self.fail_to_close:
            # Physical valve remains open
            self.open_feedback = True
            self.closed_feedback = False
        else:
            self.open_feedback = False
            self.closed_feedback = True

        if self.feedback_failure:
            # Feedback stays inconsistent even if actuator moved
            self.open_feedback = True
            self.closed_feedback = False

    def close(self) -> None:
        """Convenience: command the valve closed."""
        self.command(False)

    @property
    def physically_closed(self) -> bool:
        """True only when feedback reports CLOSED and not OPEN."""
        return not self.open_feedback and self.closed_feedback

    @property
    def matches_command(self) -> bool:
        """True when feedback is consistent with the last command."""
        if self.open_command:
            return self.open_feedback and not self.closed_feedback
        return self.closed_feedback and not self.open_feedback
