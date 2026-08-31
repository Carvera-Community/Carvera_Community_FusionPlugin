#!/usr/bin/env python3
"""Catalog and artifact runner for Fusion UI acceptance scenarios."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CATALOG_PATH = ROOT / "catalog.json"
QUESTION_PATTERN = re.compile(r"^## (UIQ-[0-9]{3}):", re.MULTILINE)


def load_catalog() -> dict:
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def scenario_by_id(catalog: dict, scenario_id: str) -> dict:
    scenario = next(
        (item for item in catalog["scenarios"] if item["id"] == scenario_id),
        None,
    )
    if scenario is None:
        raise ValueError(f"Unknown scenario: {scenario_id}")
    return scenario


def check_catalog(catalog: dict) -> list[str]:
    errors: list[str] = []
    scenarios = catalog.get("scenarios", [])
    scenario_ids = [item.get("id") for item in scenarios]
    if len(scenario_ids) != len(set(scenario_ids)):
        errors.append("Scenario IDs must be unique")

    controls = catalog.get("controls", [])
    control_ids = [item.get("id") for item in controls]
    if len(control_ids) != len(set(control_ids)):
        errors.append("Control IDs must be unique")

    questions_text = (ROOT / "OPEN_QUESTIONS.md").read_text(encoding="utf-8")
    question_ids = set(QUESTION_PATTERN.findall(questions_text))
    known_scenarios = set(scenario_ids)

    for scenario in scenarios:
        path = ROOT / scenario.get("file", "")
        if not path.is_file():
            errors.append(f"{scenario.get('id')}: missing runbook {path.relative_to(ROOT)}")
            continue
        heading = path.read_text(encoding="utf-8").splitlines()[0]
        if scenario["id"] not in heading:
            errors.append(f"{scenario['id']}: runbook heading does not contain its ID")

    allowed_statuses = {"covered", "question"}
    for control in controls:
        control_id = control.get("id", "<missing>")
        status = control.get("status")
        if status not in allowed_statuses:
            errors.append(f"{control_id}: invalid status {status!r}")
        linked = control.get("scenarios", [])
        if not linked:
            errors.append(f"{control_id}: active control has no scenario")
        for scenario_id in linked:
            if scenario_id not in known_scenarios:
                errors.append(f"{control_id}: unknown scenario {scenario_id}")
        if status == "question":
            question = control.get("question")
            if question not in question_ids:
                errors.append(f"{control_id}: unresolved question {question!r} is not documented")

    return errors


def verify_single_file_shrink(path: Path) -> dict:
    shrink = re.compile(r"^G92\.4\s+A0(?:\.0*)?\s+R[^\s(]+(?:\s|$)", re.IGNORECASE)
    m9 = re.compile(r"^M9(?:\s|$)", re.IGNORECASE)
    m30 = re.compile(r"^M30(?:\s|$)", re.IGNORECASE)
    shrink_lines: list[int] = []
    m9_lines: list[int] = []
    m30_lines: list[int] = []

    with path.open(encoding="utf-8", errors="replace") as source:
        for line_number, line in enumerate(source, start=1):
            stripped = line.strip()
            if shrink.match(stripped):
                shrink_lines.append(line_number)
            if m9.match(stripped):
                m9_lines.append(line_number)
            if m30.match(stripped):
                m30_lines.append(line_number)

    failures: list[str] = []
    if len(shrink_lines) != 1:
        failures.append(f"expected exactly one shrink, found {len(shrink_lines)}")
    if len(m30_lines) != 1:
        failures.append(f"expected exactly one M30, found {len(m30_lines)}")
    if shrink_lines and not any(line < shrink_lines[0] for line in m9_lines):
        failures.append("shrink is not after an M9 tail marker")
    if shrink_lines and m30_lines and shrink_lines[0] >= m30_lines[0]:
        failures.append("shrink is not before M30")

    return {
        "passed": not failures,
        "artifact": str(path),
        "shrink_count": len(shrink_lines),
        "shrink_lines": shrink_lines,
        "m9_lines": m9_lines,
        "m30_count": len(m30_lines),
        "m30_lines": m30_lines,
        "failures": failures,
    }


VERIFIERS = {"single_file_shrink": verify_single_file_shrink}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("check", help="validate the UI acceptance catalog")
    subparsers.add_parser("list", help="list available scenarios")
    show = subparsers.add_parser("show", help="print one scenario runbook")
    show.add_argument("scenario")
    verify = subparsers.add_parser("verify", help="verify a scenario artifact")
    verify.add_argument("scenario")
    verify.add_argument("artifact", type=Path)
    args = parser.parse_args(argv)
    catalog = load_catalog()

    if args.command == "check":
        errors = check_catalog(catalog)
        if errors:
            for error in errors:
                print(f"ERROR: {error}")
            return 1
        print(f"UI catalog valid: {len(catalog['scenarios'])} scenarios, {len(catalog['controls'])} active controls")
        return 0

    if args.command == "list":
        for scenario in catalog["scenarios"]:
            verifier = " [artifact verifier]" if scenario.get("verifier") else ""
            print(f"{scenario['id']}: {scenario['title']}{verifier}")
        return 0

    scenario = scenario_by_id(catalog, args.scenario)
    if args.command == "show":
        print((ROOT / scenario["file"]).read_text(encoding="utf-8"))
        return 0

    verifier_name = scenario.get("verifier")
    if verifier_name is None:
        print(f"Scenario {args.scenario} has no artifact verifier", file=sys.stderr)
        return 2
    if not args.artifact.is_file():
        print(f"Artifact does not exist: {args.artifact}", file=sys.stderr)
        return 2
    result = {"scenario": args.scenario, **VERIFIERS[verifier_name](args.artifact)}
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
