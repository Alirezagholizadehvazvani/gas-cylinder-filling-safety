# Design Documents

Source specifications the code and tests in this repository are built
against. These are engineering design documents, not certified
functional-safety deliverables.

| Document | Contents |
|---|---|
| `Design_Baseline_Rev2.pdf` | Process description, hazard analysis, safety requirements (SR-01 to SR-16), state machine, hardware and electrical architecture, defense-in-depth layers (mechanical relief valve, PG1 gauge, transducer/controller, E-stop), BOM. |
| `Consolidated_Project_Document_Rev3.pdf` | Merges the design baseline above with the project status report: adds the digital prototype strategy, the T-01 to T-17 digital safety test plan, component requirements, and project roadmap/status. |

`docs/srs_traceability.md` in the repository root maps both the SRS
items and the T-01 to T-17 test plan from these documents directly to
the unit tests and fault-injection scenarios in this codebase.

One known, deliberate deviation: Rev3 Section 20 states power
restoration alone returns the system to READY. The implementation
requires an explicit Reset in that case as well — see
`docs/engineering_decisions.md` for the reasoning. This repo's
behavior should be read as superseding that specific line in Rev3.
