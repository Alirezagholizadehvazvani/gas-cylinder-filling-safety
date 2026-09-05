# Architecture

## Purpose

Digital logic simulation of a safety-oriented control system for an O₂/N₂
cylinder filling process. The design separates the **safety function** from
monitoring/operator-interface functions and enforces a fail-safe operating
philosophy.

This repository models only the electronic safety chain and its fault
behaviour. The mechanical relief valve and the existing ramp gauge (PG1) are
independent passive/visual layers and are outside the digital test matrix.

## Defense-in-depth (design baseline)

| # | Layer                         | Type              | Trigger              | Independence |
|---|-------------------------------|-------------------|----------------------|--------------|
| 1 | Mechanical relief valve       | Passive/mechanical| Overpressure         | No controller, power, or software dependency |
| 2 | Ramp gauge PG1                | Mechanical/visual | Operator observation | No shared failure mode with transducer/controller |
| 3 | Pressure transducer + Safety Controller | Electronic | Automatic            | Primary automated measurement & shutdown |
| 4 | Physical E-Stop               | Electromechanical | Manual               | Independent of normal software execution |

The digital prototype implements **Layer 3** and the E-Stop input path of
**Layer 4**.

## Safety chain (Layer 3)

```
Pressure Transducer
        ↓
Safety Controller
        ↓
Safety Logic (state machine)
        ↓
Valve Control
        ↓
Electric Shutoff Valve
```

## Independent E-Stop path

```
Physical E-Stop → Safety Shutdown Path → Valve Safe State
```

This path is modelled as a discrete input that forces the same bounded
valve-close verification used by other emergency conditions.

## Monitoring layer

Controller → Display / Alarm / Logging / UI

Monitoring must never override a safety shutdown. In this prototype the
monitoring surface is the structured event log and the `status()` snapshot.

## Package layout

```
src/safety_system/
  config.py      Thresholds and timing windows
  states.py      State enumeration
  sensor.py      Pressure transducer model + fault injection
  valve.py       Shutoff valve model + feedback + fault injection
  logging.py     Structured event log
  controller.py  State machine, decision logic, safe shutdown
```

## Defined safe state

Filling disabled, shutoff valve commanded closed, system **LOCKED**, no
automatic restart. Applies to emergency pressure, E-stop, sensor faults,
valve faults, controller/watchdog faults, and power failure.

Reset requires an intentional action and only returns the system to
SELF_CHECK → READY. A separate Start request is required before filling
can resume.
