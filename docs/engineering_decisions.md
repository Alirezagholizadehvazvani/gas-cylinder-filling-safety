# Engineering Decisions

Short notes on choices that are useful to discuss in interviews or reviews.

## Why 120 / 125 bar?

Company-approved setpoints for this project. The 5 bar span is acceptable in the design baseline because filling is manual and sequential (operator opens one source cylinder, waits for stabilisation, closes, then moves on). Approach to final pressure is therefore relatively slow. The values must still be checked against actual equipment and standards before any physical installation.

## Why bounded valve-close verification?

A controller that only *commands* CLOSE can claim a safe state while the actuator is stuck or feedback is lying. The prototype therefore:

1. issues CLOSE,
2. waits up to `VALVE_CLOSE_TIMEOUT_TICKS` for CLOSED feedback,
3. records either `SAFE STATE VERIFIED` or `SAFE STATE NOT VERIFIED`,
4. remains LOCKED in both cases (no restart until the underlying condition is cleared and Reset succeeds).

Fault-injection scenarios 4 and 5 exist specifically to prove that the “not verified” path is detected and reported.

## Why no automatic restart?

Safety requirements SR-07 and SR-08: after emergency shutdown, sensor fault, power loss, or similar, the system must stay locked. Pressure falling again or power returning must not re-open the filling path. Only an intentional Reset (modelled as a key-switch style action) followed by a separate Start request is allowed, and only after self-check passes.

## Why continuous command/feedback monitoring?

Checking mismatch only at the moment of CLOSE would miss a valve that silently reports the wrong position while still in FILLING or WARNING. The cyclic `update()` path therefore tests `valve.matches_command` on every tick while filling is active.

## Why keep mechanical layers out of the digital model?

The mechanical relief valve and the analog ramp gauge PG1 are independent by design. Simulating them would create a false sense that the electronic chain covers those failure modes. They remain documented in the architecture and are validated by physical inspection/calibration in the real system.

## What this prototype deliberately does *not* claim

- SIL rating or functional-safety certification
- Readiness for connection to real high-pressure equipment
- Validation of the company setpoints against standards or vessel ratings
- Oxygen-service material/cleaning qualification (handled at detailed component selection)
