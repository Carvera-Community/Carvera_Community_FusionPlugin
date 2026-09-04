import hashlib
import importlib.util
import json
import zipfile
from pathlib import Path

import pytest


ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location(
    "release_builder",
    ROOT / "scripts" / "build_release.py",
)
builder = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(builder)

@pytest.mark.parametrize(
    "version",
    ["1.0.0", "0.9.2-beta.1", "10.20.30-rc.2", "1.0.0+build.7"],
)
def test_validate_version_accepts_supported_semver(version):
    assert builder.validate_version(version) == version


@pytest.mark.parametrize(
    "version",
    [
        "v1.0.0",
        "V1.0.0",
        "release-1.0.0",
        " 1.0.0",
        "1.0.0 ",
        "1.0",
        "01.0.0",
        "1.0.0-beta..1",
        "1.0.0-beta.01",
    ],
)
def test_validate_version_rejects_unsupported_versions(version):
    with pytest.raises(ValueError):
        builder.validate_version(version)


def test_validate_version_explains_that_leading_v_is_not_allowed():
    with pytest.raises(ValueError, match="must not start with 'v'"):
        builder.validate_version("v1.2.3")


def test_build_release_stamps_only_packaged_plugin_versions(tmp_path):
    output = tmp_path / "dist"
    source_manifest = (ROOT / "Makera Community.manifest").read_bytes()
    source_config = (ROOT / "config.py").read_bytes()

    archive = builder.build_release(
        ROOT,
        output,
        "2.3.4-beta.5",
        source_revision="0123456789abcdef",
    )

    assert archive.name == "Makera-Community-Fusion-Plugin-v2.3.4-beta.5.zip"
    with zipfile.ZipFile(archive) as package:
        names = set(package.namelist())
        manifest = json.loads(
            package.read("Makera Community/Makera Community.manifest")
        )
        config = package.read("Makera Community/config.py").decode()
        readme = package.read("Makera Community/README.md").decode()

    assert manifest["version"] == "2.3.4-beta.5"
    assert "PLUGIN_VERSION = '2.3.4-beta.5'" in config
    assert "DEBUG = False" in config
    assert 'src="resources/' not in readme
    assert (
        "https://raw.githubusercontent.com/Carvera-Community/"
        "Carvera_Community_FusionPlugin/0123456789abcdef/"
        "resources/readme/installation/step1.png"
    ) in readme
    assert "Makera Community/Makera Community.py" in names
    assert any(name.startswith("Makera Community/commands/") for name in names)
    assert any(name.startswith("Makera Community/lib/") for name in names)
    assert not any("Tests/" in name for name in names)
    assert not any("__pycache__" in name or name.endswith(".pyc") for name in names)
    assert not any(name.endswith("settings.settings") for name in names)
    assert (ROOT / "Makera Community.manifest").read_bytes() == source_manifest
    assert (ROOT / "config.py").read_bytes() == source_config
    assert 'src="resources/' in (ROOT / "README.md").read_text()

    checksum = archive.with_suffix(".zip.sha256").read_text().split()[0]
    assert checksum == hashlib.sha256(archive.read_bytes()).hexdigest()


def test_build_release_is_reproducible(tmp_path):
    first = builder.build_release(ROOT, tmp_path / "first", "1.2.3")
    second = builder.build_release(ROOT, tmp_path / "second", "1.2.3")

    assert first.read_bytes() == second.read_bytes()


def test_readme_rewrite_rejects_an_invalid_source_revision(tmp_path):
    readme = tmp_path / "README.md"
    readme.write_text('<img src="resources/image.png">', encoding="utf-8")

    with pytest.raises(ValueError, match="source revision"):
        builder.rewrite_readme_images(readme, "invalid revision")


@pytest.mark.parametrize(
    ("version", "ref_name", "allow_stable", "expected"),
    [
        ("1.0.0", "main", False, False),
        ("1.0.0-beta.1", "main", True, True),
        ("1.0.0", "dev", False, True),
        ("1.0.0", "feature/test", False, True),
        ("1.0.0", "dev", True, False),
        ("1.0.0-beta.1", "dev", True, True),
    ],
)
def test_release_policy_defaults_non_main_to_prerelease(
    version,
    ref_name,
    allow_stable,
    expected,
):
    assert builder.is_prerelease(version, ref_name, allow_stable) is expected
