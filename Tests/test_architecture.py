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
