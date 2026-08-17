# Gas Cylinder Filling Safety System — Digital Prototype

## Fault Injection Engine

This phase extends the original control/safety simulation with a **Fault Injection Engine** for digital verification of safe-state behaviour.

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
- the valve is actually verified `CLOSED`

This is deliberately stricter than merely checking the controller state. In particular, valve actuator and feedback faults are expected to expose a failure if the simulated valve cannot be verified closed. That is useful because the test suite should reveal unsafe conditions rather than silently marking them as successful.

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
