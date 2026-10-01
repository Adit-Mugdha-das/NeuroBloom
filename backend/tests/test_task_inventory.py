"""Contract checks for the 35-task provenance inventory."""

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INVENTORY_PATH = ROOT / "docs" / "task_inventory.csv"
FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "task_inventory_cases.json"

REQUIRED_FIELDS = {
    "task_code", "task_name", "domain", "purpose", "software_module",
    "frontend_route", "paradigm", "stimulus_input", "trials_and_timing",
    "primary_outputs", "scoring_definition", "difficulty_levels",
    "bengali_adaptation", "source_and_provenance", "licensing_status",
    "standardized_instrument_equivalence", "unit_test_fixture",
    "expected_output", "verification_status",
}


def load_inventory():
    with INVENTORY_PATH.open(encoding="utf-8", newline="") as inventory_file:
        return list(csv.DictReader(inventory_file))


def load_cases():
    with FIXTURE_PATH.open(encoding="utf-8") as fixture_file:
        return json.load(fixture_file)


def test_inventory_has_exactly_35_unique_tasks_and_required_fields():
    rows = load_inventory()
    assert len(rows) == 35
    assert set(rows[0]) == REQUIRED_FIELDS
    assert len({row["task_code"] for row in rows}) == 35
    for row in rows:
        assert all(row[field].strip() for field in REQUIRED_FIELDS)


def test_inventory_matches_authoritative_fixture():
    rows = {row["task_code"]: row for row in load_inventory()}
    cases = load_cases()
    assert len(cases) == 35
    for case in cases:
        row = rows[case["task_code"]]
        assert row["domain"] == case["domain"]
        assert row["frontend_route"] == case["route"]


def test_every_referenced_module_and_frontend_route_exists():
    for row in load_inventory():
        assert (ROOT / row["software_module"]).is_file(), row["task_code"]
        route_name = row["frontend_route"].removeprefix("/training/")
        route_file = ROOT / "frontend-svelte" / "src" / "routes" / "training" / route_name / "+page.svelte"
        assert route_file.is_file(), row["task_code"]


def test_reproducibility_and_licensing_fields_are_explicit():
    allowed_status = {"verified", "partial"}
    for row in load_inventory():
        assert "score" in row["scoring_definition"].lower() or "output" in row["scoring_definition"].lower()
        assert "level" in row["difficulty_levels"].lower()
        assert "equivalence not evaluated" in row["bengali_adaptation"].lower()
        assert "MIT" in row["licensing_status"]
        assert row["standardized_instrument_equivalence"] == "No"
        assert row["verification_status"] in allowed_status


def test_all_tasks_have_numerical_scoring_fixtures():
    for row in load_inventory():
        assert row["verification_status"] == "verified"
        assert "pending" not in row["expected_output"].lower()


def test_every_fixture_is_executed_by_continuous_integration():
    """CI runs `pytest tests/` (backend) and `npm test` (frontend); anything else is unchecked."""
    for row in load_inventory():
        fixture = row["unit_test_fixture"]
        assert (ROOT / fixture).is_file(), row["task_code"]
        in_backend_ci = fixture.startswith("backend/tests/test_")
        in_frontend_ci = fixture.startswith("frontend-svelte/src/") and fixture.endswith(".test.js")
        assert in_backend_ci or in_frontend_ci, f"{row['task_code']} fixture is outside CI: {fixture}"
