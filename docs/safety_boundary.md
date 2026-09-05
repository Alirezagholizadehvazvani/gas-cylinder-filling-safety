# Safety Boundary

**This repository is a digital logic simulation only.**

- It models pressure thresholds, sensor and valve faults, E-stop, power
  failure, watchdog behaviour, and the fail-safe lockout philosophy.
- It is **not** connected to, and must **not** be used to control, real
  high-pressure gas equipment, valves, or filling manifolds.
- The 120 bar (warning) and 125 bar (emergency) values are company-approved
  setpoints for the project documentation. They are not independently
  validated legal or equipment limits.
- Mechanical layers (relief valve, analog ramp gauge PG1) are outside the
  digital test matrix by design; they provide independent protection in the
  physical system.
- No claim is made of SIL rating, certification, or readiness for production
  deployment.

Any future physical prototype or real-equipment integration is a separate
engineering activity that requires qualified component selection, standards
review, and formal safety approval.
