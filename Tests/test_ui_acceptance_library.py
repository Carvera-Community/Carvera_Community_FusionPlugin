import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).parent / "UI"
SPEC = importlib.util.spec_from_file_location("ui_acceptance_runner", ROOT / "run_ui_tests.py")
runner = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(runner)


def test_ui_catalog_is_consistent_and_all_active_controls_have_scenarios():
    catalog = runner.load_catalog()

    assert runner.check_catalog(catalog) == []
    assert all(control["scenarios"] for control in catalog["controls"])


def test_single_file_shrink_verifier_accepts_one_tail_shrink(tmp_path):
    artifact = tmp_path / "valid.cnc"
    artifact.write_text("G1 X1\nM9\nG92.4 A0 R0\nM5\nM30\n", encoding="utf-8")

    result = runner.verify_single_file_shrink(artifact)

    assert result["passed"]
    assert result["shrink_lines"] == [3]
    assert result["m30_lines"] == [5]


def test_single_file_shrink_verifier_rejects_body_and_tail_shrink(tmp_path):
    artifact = tmp_path / "invalid.cnc"
    artifact.write_text(
        "G92.4 A0 R0\nG1 X1\nM9\nG92.4 A0 R0\nM30\n",
        encoding="utf-8",
    )

    result = runner.verify_single_file_shrink(artifact)

    assert not result["passed"]
    assert result["shrink_count"] == 2


def test_a_axis_y_retraction_verifier_accepts_retraction_before_rotation(tmp_path):
    artifact = tmp_path / "valid.cnc"
    artifact.write_text(
        "G90 G53 G0 Z-3 Y-90\nG0 A90\n",
        encoding="utf-8",
    )

    result = runner.verify_a_axis_y_retraction(artifact)

    assert result["passed"]
    assert result["retraction_lines"] == [1]
    assert result["rotation_lines"] == [2]


def test_a_axis_y_retraction_verifier_rejects_wrong_coordinate(tmp_path):
    artifact = tmp_path / "invalid.cnc"
    artifact.write_text(
        "G90 G53 G0 Z-3 Y-100\nG0 A90\n",
        encoding="utf-8",
    )

    result = runner.verify_a_axis_y_retraction(artifact)

    assert not result["passed"]
    assert result["retraction_count"] == 0


def test_catalog_json_remains_plain_json():
    parsed = json.loads((ROOT / "catalog.json").read_text(encoding="utf-8"))

    assert parsed["schema_version"] == 1
