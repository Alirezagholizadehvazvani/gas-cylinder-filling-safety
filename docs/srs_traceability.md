# Safety Requirements → Test Traceability

Mapping of the design-baseline Safety Requirements Specification (SRS) items
to the digital prototype tests. This is a **logic-level** traceability matrix
for the simulation only; it does not constitute a certified functional-safety
assessment.

| SRS ID | Requirement (summary)                                      | Covered by |
|--------|------------------------------------------------------------|------------|
| SR-01  | Continuously measure/monitor pressure                      | `update()` pressure path; overpressure & sensor tests |
| SR-02  | Display current pressure to the operator                   | `status()` snapshot |
| SR-03  | Detect pressure increase/decrease                          | FILLING ↔ WARNING transitions |
| SR-04  | At 120 bar activate Warning/Target Reached                 | `test_warning_state_entered_at_120` |
| SR-05  | At ≥125 bar initiate Emergency Shutdown                    | `test_overpressure_locks_and_closes`; FI scenario 9 |
| SR-06  | After Emergency Shutdown enter LOCKED/FAULT                | same as SR-05 |
| SR-07  | No automatic restart after pressure drops or restart       | `test_no_auto_restart_after_lock` |
| SR-08  | Reset requires intentional action; does not auto-start     | `test_reset_*`; reset only from LOCK |
| SR-09  | Detect sensor disconnect / invalid / frozen / electrical   | sensor unit tests; FI scenarios 1–3 |
| SR-10  | Sensor failure → safe state, filling disabled              | same as SR-09 |
| SR-11  | Power loss must not cause unsafe continuation              | `test_power_failure_locks_and_closes`; FI scenario 7 |
| SR-12  | Startup: Power ON → Self Check → READY → Start             | `test_startup_reaches_ready` |
| SR-13  | Physical E-Stop → safety action, disable, lock             | `test_emergency_stop_*`; FI scenario 6 |
| SR-14  | Log Start, Stop, Warning, ESD, Sensor/Valve fault, …      | structured `EventLog` |
| SR-15  | Mechanical relief (passive) — out of digital scope         | Documented in architecture; not simulated |
| SR-16  | Start is a request; controller verifies interlocks first   | `start()` interlock checks |

## Fault-injection scenarios

| ID | Scenario                         | Primary SRS |
|----|----------------------------------|-------------|
| 1  | Sensor Disconnect                | SR-09, SR-10 |
| 2  | Sensor Invalid / Out of Range     | SR-09, SR-10 |
| 3  | Sensor Frozen                     | SR-09, SR-10 |
| 4  | Valve Fails to Close             | Valve verification path |
| 5  | Valve Feedback Failure           | Valve verification path |
| 6  | Emergency Stop                   | SR-13 |
| 7  | Power Failure                    | SR-11 |
| 8  | Controller / Watchdog Failure    | Controller integrity |
| 9  | Overpressure                     | SR-05, SR-06 |
