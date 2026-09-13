# Gas Cylinder Filling Safety System — Digital Prototype

[![CI](https://github.com/Alirezagholizadehvazvani/gas-cylinder-filling-safety/actions/workflows/ci.yml/badge.svg)](https://github.com/Alirezagholizadehvazvani/gas-cylinder-filling-safety/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Digital logic simulation of a safety-oriented control system for an O₂/N₂ cylinder filling process.**

This repository demonstrates the safety architecture, state machine, fault handling, and automated fault-injection verification that precede any physical high-pressure integration. It is a **logic prototype only** and must not control real gas equipment.

---

## Problem

Cylinder filling shops handle high-pressure oxygen and nitrogen. Uncontrolled overpressure, sensor failure, valve failure, or controller faults can create critical hazards. The design goal is a fail-safe electronic safety layer that:

- continuously monitors pressure,
- warns at a company-approved target (120 bar),
- forces emergency shutdown at ≥125 bar,
- detects sensor, valve, power, and controller faults,
- locks the system with no automatic restart,
- works alongside independent mechanical (relief valve) and visual (ramp gauge) protection.

## What this repository contains

| Area | Content |
|------|---------|
| Safety state machine | POWER_ON → SELF_CHECK → READY → FILLING / WARNING → LOCK |
| Pressure decision logic | 120 bar warning, ≥125 bar emergency shutdown |
| Sensor fault model | Disconnect, invalid/out-of-range, frozen signal |
| Valve model | Command/feedback, fail-to-close, feedback lie, close-verification timeout |
| Fault injection engine | 9 automated scenarios with PASS/FAIL reports |
| Unit tests | 23 regression tests covering SRS-relevant behaviours |
| Documentation | Architecture, state machine, SRS→test traceability, safety boundary |

## Defense-in-depth (summary)

```
1. Mechanical relief valve     (passive, independent of electronics)
2. Ramp gauge PG1              (visual, independent sensing path)
3. Transducer + Safety Controller + Shutoff Valve   ← this prototype
4. Physical E-Stop             (electromechanical, independent of software)
```

Only layers 3 and the E-Stop input of layer 4 are simulated digitally.

## Quick start

```bash
# From repository root
python -m pytest tests/ -v          # or: python -m unittest tests.test_prototype -v
python -m safety_system             # short demo run
python tools/fault_injection.py     # full fault-injection report → reports/
```

Requires Python 3.10+.

## Example fault-injection result

```
PASS 01 - Sensor Disconnect
PASS 02 - Sensor Invalid / Out of Range
PASS 03 - Sensor Frozen
PASS 04 - Valve Fails to Close
PASS 05 - Valve Feedback Failure
PASS 06 - Emergency Stop
PASS 07 - Power Failure
PASS 08 - Controller / Watchdog Failure
PASS 09 - Overpressure

Overall: PASS (9/9 passed)
```

Scenarios 4 and 5 intentionally leave the valve **not verified closed**. The test passes when the controller correctly detects that condition, records a confirmation timeout, and remains LOCKED.

## Project structure

```
gas-cylinder-filling-safety/
├── src/safety_system/     # Core package (config, states, sensor, valve, controller, logging)
├── tests/                 # Unit & regression tests
├── tools/                 # Fault-injection engine
├── docs/                  # Architecture, state machine, SRS traceability, safety boundary
├── reports/               # Generated verification reports (sample included)
└── .github/workflows/     # CI
```

## Engineering decisions highlighted

- **Bounded valve-close verification** — a CLOSE command is not trusted until feedback confirms CLOSED within a timeout; otherwise the system records `SAFE STATE NOT VERIFIED` and stays locked.
- **No automatic restart** — pressure drop or power restore never re-opens the path; Reset + Start are required.
- **Reset blocked while pressure elevated** — self-check rejects return to READY if pressure is still ≥ warning threshold.
- **Continuous command/feedback monitoring** while filling, not only at the moment of CLOSE.
- **Structured event log** with typed events for later analysis and SRS coverage.

## Safety boundary

This is a **digital logic simulation only**. It must not be connected to or used to control real high-pressure gas equipment. The setpoints used here are project documentation values, not certified limits. See [docs/safety_boundary.md](docs/safety_boundary.md).

## Documentation

- [Architecture](docs/architecture.md)
- [State machine](docs/state_machine.md)
- [SRS → test traceability](docs/srs_traceability.md)
- [Safety boundary](docs/safety_boundary.md)

## Status

Digital prototype / simulation stage. Component selection, physical prototype, and real-equipment integration are future project stages and are outside this repository.

## License

MIT — see [LICENSE](LICENSE).
