# Gas Cylinder Filling Safety System — Digital Prototype

## Fault Injection Engine

This phase extends the original control/safety simulation with a **Fault Injection Engine** for digital verification of safe-state behaviour.

The valve shutdown path now uses an explicit, bounded verification sequence:
`CLOSE command → feedback/position verification → timeout → critical fault if not verified → LOCK`.

The original prototype already covered startup/self-check, READY/FILLING/WARNING/EMERGENCY/LOCK, pressure thresholds, sensor faults, emergency stop, power failure, valve command/feedback modelling, reset behaviour and event logging. The README also explicitly defines the project as a logic simulation that must not be connected to real gas equipment.

This phase adds nine intentional fault scenarios, an automated test runner, and machine-readable/human-readable PASS/FAIL reports.

## Fault scenarios

1. Sensor Disconnect
2. Sensor Invalid / Out of Range
3. Sensor Frozen
4. Valve Fails to Close
5. Valve Feedback Failure
6. Emergency Stop
7. Power Failure
8. Controller / Watchdog Failure
9. Overpressure
10. Automated execution of all scenarios
11. PASS/FAIL report generation

## Safe-state definition

For this digital prototype, a successful safety response requires:

- controller state reaches `LOCK`
- the shutdown/fault is detected and recorded
- for normal shutdowns, the valve is verified `CLOSED` within the configured timeout
- for valve actuator/feedback faults, the system must detect that `CLOSED` cannot be verified and must remain `LOCKED`

This is deliberately stricter than merely checking the controller state. The controller must not falsely claim a safe state when valve position cannot be verified. Therefore scenarios 4 and 5 now PASS when the system correctly detects the valve problem, records a confirmation timeout, enters `LOCK`, and explicitly records `SAFE STATE NOT VERIFIED`.

## Run the prototype

```bash
python prototype.py
```

## Run the unit tests

```bash
python -m unittest test_prototype.py -v
```

## Run the complete Fault Injection Engine

```bash
python fault_injection.py
```

The engine executes scenarios 1–9 automatically and writes:

- `reports/fault_injection_report.txt`
- `reports/fault_injection_report.json`

## Important interpretation

A `FAIL` result is not automatically a bug in the test runner. It means the simulated safety requirement was not satisfied. For example, if a valve is injected with a "fail to close" fault, the controller may enter `LOCK` while the valve remains open; the report should then correctly identify the safe-state verification as failed.

## Safety boundary

**This is a digital logic simulation only. It is not connected to, and must not directly control, real gas equipment.**


## Valve shutdown verification

The digital prototype now models a bounded valve-close confirmation window using `VALVE_CLOSE_TIMEOUT_TICKS`.

Normal shutdown:

```text
CLOSE COMMAND
     ↓
Verify CLOSED
     ↓
within timeout?
  ┌──┴──┐
 YES    NO
  ↓      ↓
LOCK   CRITICAL FAULT
SAFE     ↓
STATE   LOCK
VERIFIED
```

The valve actuator and feedback fault scenarios deliberately exercise the `NO` branch. A test is considered successful when the system **detects and contains** that failure rather than pretending that the valve reached the safe position.
