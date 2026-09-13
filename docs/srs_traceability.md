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

## Digital Safety Test Plan (T-01 to T-17)

This is the test-ID numbering from the design-baseline test plan, kept
separate from the SRS table above since it maps test IDs, not requirements.

| Test ID | Condition                     | Covered by |
|---------|--------------------------------|------------|
| T-01    | Pressure = 119 bar             | `test_pressure_below_warning_stays_filling` |
| T-02    | Pressure = 120 bar             | `test_warning_state_entered_at_120` |
| T-03    | Pressure = 124.9 bar           | `test_warning_state_entered_at_120` |
| T-04    | Pressure ≥ 125 bar             | `test_overpressure_locks_and_closes`; FI scenario 9 |
| T-05    | Pressure spike                 | `test_pressure_spike_direct_to_emergency_is_caught` |
| T-06    | Sensor disconnected            | `test_sensor_disconnect_locks`; FI scenario 1 |
| T-07    | Sensor out of range            | `test_sensor_out_of_range_locks`; FI scenario 2 |
| T-08    | Sensor frozen                  | `test_frozen_sensor_is_detected`; FI scenario 3 |
| T-09    | Valve fails to close           | `test_valve_fail_to_close_is_exposed`; FI scenario 4 |
| T-10    | Valve feedback mismatch        | `test_valve_feedback_failure_is_exposed`; `test_valve_mismatch_during_filling_is_detected`; FI scenario 5 |
| T-11    | E-Stop during filling          | `test_emergency_stop_locks_and_closes`; FI scenario 6 |
| T-12    | Power failure during filling   | `test_power_failure_locks_and_closes`; FI scenario 7 |
| T-13    | Power restored                 | `test_power_restore_requires_reset_not_automatic` |
| T-14    | Controller/watchdog failure    | `test_watchdog_failure_locks_and_closes`; FI scenario 8 |
| T-15    | Reset after fault              | `test_reset_rejects_pressure_still_above_warning`; `test_reset_accepts_pressure_back_in_range` |
| T-16    | Start from READY               | `test_start_rejected_before_power_on` |
| T-17    | Invalid startup condition      | `test_start_rejected_after_invalid_startup` |

T-13 is implemented as a stricter requirement than the original design-baseline
wording. The design baseline states power restoration alone leads to
self-check and READY. This prototype requires an explicit Reset even after
power returns, on the same reasoning as `docs/engineering_decisions.md`: a
gas-filling system re-arming itself the moment power blips back should not
happen without a positive operator action. The design baseline document
should be read as superseded by this decision for the power-recovery case.
