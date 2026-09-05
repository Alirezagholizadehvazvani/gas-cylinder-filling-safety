#!/usr/bin/env python3
"""
Fault Injection Engine
----------------------
Digital-only verification harness for the SafetySystem prototype.

Each scenario:
1. creates a fresh system,
2. powers it on,
3. starts filling where appropriate,
4. injects exactly one fault,
5. advances the simulation,
6. verifies the expected safe-state properties,
7. records PASS/FAIL evidence.

This file never interfaces with real equipment.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

# Allow running from repo root without installation
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from safety_system import SafetySystem, State, EMERGENCY_PRESSURE  # noqa: E402


@dataclass
class TestResult:
    id: int
    scenario: str
    injected_fault: str
    expected_state: str
    actual_state: str
    expected_valve_closed: bool
    actual_valve_closed: bool
    fault_detected: bool
    passed: bool
    evidence: str


def fresh_running_system() -> SafetySystem:
    system = SafetySystem()
    system.power_on()
    system.start()
    return system


def has_lock_evidence(system: SafetySystem) -> bool:
    return system.state == State.LOCK and any(
        "LOCKED" in event for event in system.events
    )


def run_scenario(number: int) -> TestResult:
    system = fresh_running_system()

    names = {
        1: "Sensor Disconnect",
        2: "Sensor Invalid / Out of Range",
        3: "Sensor Frozen",
        4: "Valve Fails to Close",
        5: "Valve Feedback Failure",
        6: "Emergency Stop",
        7: "Power Failure",
        8: "Controller / Watchdog Failure",
        9: "Overpressure",
    }

    if number == 1:
        system.sensor.connected = False
        system.update()
        injected = "Pressure sensor disconnected"

    elif number == 2:
        system.sensor.pressure = 250.0
        system.update()
        injected = "Sensor value forced beyond 0..200 bar"

    elif number == 3:
        system.sensor.pressure = 40.0
        system.update()
        system.sensor.frozen = True
        system.sensor.pressure = 130.0
        system.update()
        system.update()
        injected = "Sensor output frozen while process pressure changes"

    elif number == 4:
        system.valve.fail_to_close = True
        system.e_stop = True
        system.update()
        injected = "Valve actuator prevented from reaching CLOSED"

    elif number == 5:
        system.valve.feedback_failure = True
        system.e_stop = True
        system.update()
        injected = "Valve feedback forced inconsistent with physical close"

    elif number == 6:
        system.e_stop = True
        system.update()
        injected = "Emergency-stop input activated"

    elif number == 7:
        system.power_available = False
        system.update()
        injected = "Power availability removed"

    elif number == 8:
        system.watchdog_expired = True
        system.update()
        injected = "Controller watchdog expired"

    elif number == 9:
        system.sensor.pressure = EMERGENCY_PRESSURE
        system.update()
        injected = f"Pressure forced to emergency threshold ({EMERGENCY_PRESSURE} bar)"

    else:
        raise ValueError("Scenario number must be 1..9")

    actual_closed = system.valve.physically_closed
    # Valve actuator/feedback faults are expected to leave the valve
    # unverified closed; the test PASSes when the controller correctly
    # detects that condition and locks.
    expected_closed = False if number in (4, 5) else True
    expected_state = State.LOCK.value
    detected = has_lock_evidence(system)

    passed = (
        system.state.value == expected_state
        and actual_closed == expected_closed
        and detected
    )

    evidence = " | ".join(system.events[-4:])

    return TestResult(
        id=number,
        scenario=names[number],
        injected_fault=injected,
        expected_state=expected_state,
        actual_state=system.state.value,
        expected_valve_closed=expected_closed,
        actual_valve_closed=actual_closed,
        fault_detected=detected,
        passed=passed,
        evidence=evidence,
    )


def run_all_scenarios() -> list[TestResult]:
    return [run_scenario(i) for i in range(1, 10)]


def write_reports(results: list[TestResult], report_dir: Path | None = None) -> dict:
    if report_dir is None:
        report_dir = ROOT / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)

    passed = sum(r.passed for r in results)
    failed = len(results) - passed

    payload = {
        "summary": {
            "total": len(results),
            "passed": passed,
            "failed": failed,
            "overall": "PASS" if failed == 0 else "FAIL",
        },
        "results": [asdict(r) for r in results],
    }

    (report_dir / "fault_injection_report.json").write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )

    lines = [
        "FAULT INJECTION VERIFICATION REPORT",
        "=" * 38,
        f"Total scenarios : {len(results)}",
        f"Passed          : {passed}",
        f"Failed          : {failed}",
        f"Overall         : {'PASS' if failed == 0 else 'FAIL'}",
        "",
        "Scenario results",
        "-" * 38,
    ]

    for r in results:
        valve_label = (
            "FAULT/NOT VERIFIED" if r.id in (4, 5) else "CLOSED"
        )
        lines.extend(
            [
                f"[{'PASS' if r.passed else 'FAIL'}] {r.id}. {r.scenario}",
                f"  Injected : {r.injected_fault}",
                f"  State    : expected={r.expected_state}, actual={r.actual_state}",
                f"  Valve    : expected={valve_label}, "
                f"actual={'CLOSED' if r.actual_valve_closed else 'OPEN'}",
                f"  Detected : {'YES' if r.fault_detected else 'NO'}",
                f"  Evidence : {r.evidence}",
                "",
            ]
        )

    lines.extend(
        [
            "Interpretation",
            "-" * 38,
            "PASS means the system reached LOCK and the valve behaviour",
            "matched the scenario expectation (verified CLOSED, or correctly",
            "reported NOT VERIFIED for actuator/feedback faults).",
            "",
            "Safety boundary",
            "-" * 38,
            "This is a digital logic simulation only. It must not be connected",
            "to or used to control real gas equipment.",
        ]
    )

    (report_dir / "fault_injection_report.txt").write_text(
        "\n".join(lines),
        encoding="utf-8",
    )

    return payload


def main() -> None:
    results = run_all_scenarios()
    payload = write_reports(results)

    for result in results:
        print(
            f"{'PASS' if result.passed else 'FAIL'} "
            f"{result.id:02d} - {result.scenario}"
        )

    print(
        f"\nOverall: {payload['summary']['overall']} "
        f"({payload['summary']['passed']}/{payload['summary']['total']} passed)"
    )


if __name__ == "__main__":
    main()
