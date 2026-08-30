import ast
from pathlib import Path

from addin_import import import_addin_module


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
POST_PROCESSOR_ROOT = REPOSITORY_ROOT / "commands" / "postProcessor"


def core_module_paths():
    for path in POST_PROCESSOR_ROOT.rglob("*.py"):
        relative = path.relative_to(POST_PROCESSOR_ROOT)
        if relative.parts[0] in {"dialog", "fusion_adapters"}:
            continue
        yield path, relative


def test_all_core_modules_import_without_fusion_runtime():
    for path, relative in core_module_paths():
        module_parts = ["commands", "postProcessor", *relative.with_suffix("").parts]
        if module_parts[-1] == "__init__":
            module_parts.pop()
        import_addin_module(".".join(module_parts))


def test_core_has_no_top_level_adsk_imports():
    violations = []
    for path, relative in core_module_paths():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in tree.body:
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            else:
                continue
            if any(name == "adsk" or name.startswith("adsk.") for name in names):
                violations.append(str(relative))

    assert violations == []


def test_core_has_no_top_level_fusion_adapter_imports():
    violations = []
    for path, relative in core_module_paths():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in tree.body:
            if not isinstance(node, ast.ImportFrom):
                continue
            if "fusion_adapters" in (node.module or ""):
                violations.append(str(relative))

    assert violations == []


def test_only_processing_snapshot_reads_global_settings_in_core():
    violations = []
    allowed = {Path("processing_settings.py"), Path("settings/settings.py")}
    for path, relative in core_module_paths():
        if relative in allowed:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom):
                continue
            if (node.module or "").endswith("settings.settings"):
                violations.append(str(relative))

    assert violations == []


def test_gcode_pipeline_does_not_materialize_entire_files():
    operation_root = POST_PROCESSOR_ROOT / "operations" / "operation"
    violations = []
    for path in operation_root.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                continue
            if node.func.attr in {"read", "readlines"}:
                violations.append(str(path.relative_to(POST_PROCESSOR_ROOT)))

    assert violations == []


def test_refactored_facades_stay_within_size_boundaries():
    limits = {
        Path("operations/operation/rapidsParser.py"): 60,
        Path("dialog/layout/input_tab.py"): 270,
        Path("dialog/layout/output_tab.py"): 200,
        Path("dialog/dialog.py"): 300,
    }
    violations = {
        str(relative): len((POST_PROCESSOR_ROOT / relative).read_text(encoding="utf-8").splitlines())
        for relative, limit in limits.items()
        if len((POST_PROCESSOR_ROOT / relative).read_text(encoding="utf-8").splitlines()) > limit
    }

    assert violations == {}


def test_stable_dialog_input_ids_are_unchanged():
    constants_path = POST_PROCESSOR_ROOT / "dialog" / "constants.py"
    tree = ast.parse(constants_path.read_text(encoding="utf-8"))
    values = {
        target.id: node.value.value
        for node in tree.body[0].body
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance((target := node.targets[0]), ast.Name)
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
    }
    expected = {
        "PROGRAM_DROPDOWN_ID": "program",
        "OUTPUT_FOLDER_ID": "outputFolder",
        "OPERATIONS_GROUPING_ID": "operationsGrouping",
        "RENAME_SETUPS_GROUP_ID": "renameSetupsGroup",
        "FILE_NAME_ID": "fileName",
        "SELECT_ALL_SETUPS_ID": "selectAllSetups",
    }

    assert {name: values[name] for name in expected} == expected
