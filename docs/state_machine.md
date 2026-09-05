# System State Machine

```
POWER_OFF
    │ power_on()
    ▼
SELF_CHECK ──fault──► LOCK
    │ OK
    ▼
READY
    │ start()  (interlocks must pass)
    ▼
FILLING ◄──────────────────────────────┐
    │                                  │
    │ P ≥ 120 bar                      │ P < 120 bar
    ▼                                  │
WARNING ───────────────────────────────┘
    │
    │ P ≥ 125 bar
    ▼
EMERGENCY
    │
    ▼
LOCK ◄── SENSOR FAULT
     ◄── VALVE FAULT
     ◄── E-STOP
     ◄── POWER FAILURE
     ◄── WATCHDOG / CONTROLLER FAULT

LOCK
    │ authorized reset()
    ▼
SELF_CHECK → READY   (never direct LOCK → FILLING)
```

## Transition rules (summary)

| From        | Condition                          | To          |
|-------------|------------------------------------|-------------|
| POWER_OFF   | power_on, self-check OK            | READY       |
| READY       | start request + interlocks OK      | FILLING     |
| FILLING     | 120 ≤ P < 125                      | WARNING     |
| WARNING     | P < 120                            | FILLING     |
| FILLING/WARNING | P ≥ 125                        | EMERGENCY → LOCK |
| FILLING/WARNING | sensor unhealthy               | LOCK        |
| FILLING/WARNING | command ≠ feedback             | LOCK        |
| any active  | E-stop / power loss / watchdog     | LOCK        |
| LOCK        | authorized reset + self-check OK   | READY       |

There is **no** automatic restart after pressure falls or after power is
restored. The operator must issue Reset (when conditions allow) and then
Start.
