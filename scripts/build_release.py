#!/usr/bin/env python3
"""Build a version-stamped Fusion add-in release archive."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import zipfile
from pathlib import Path


ADDIN_FOLDER = "Makera Community"
ARCHIVE_PREFIX = "Makera-Community-Fusion-Plugin-v"
SEMVER = re.compile(
    r"^(?:0|[1-9][0-9]*)\."
    r"(?:0|[1-9][0-9]*)\."
    r"(?:0|[1-9][0-9]*)"
    r"(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)
ROOT_FILES = (
    "Makera Community.py",
    "Makera Community.manifest",
    "Makera Community.svg",
    "config.py",
    "README.md",
)
ROOT_DIRECTORIES = ("commands", "lib")
IGNORED_NAMES = {".DS_Store", "__pycache__"}


def validate_version(version: str) -> str:
    if not SEMVER.fullmatch(version):
        raise ValueError(
            "version must be SemVer without a leading 'v', for example "
            "0.9.2 or 0.9.2-beta.1"
        )
    prerelease = version.split("+", 1)[0].partition("-")[2]
    if prerelease and any(
        identifier.isdigit()
        and len(identifier) > 1
        and identifier.startswith("0")
        for identifier in prerelease.split(".")
    ):
        raise ValueError("numeric SemVer prerelease identifiers cannot have leading zeroes")
    return version


def is_prerelease(
    version: str,
    ref_name: str,
    publish_stable_from_non_main: bool = False,
) -> bool:
    validate_version(version)
    if "-" in version.split("+", 1)[0]:
        return True
    if ref_name == "main":
        return False
    return not publish_stable_from_non_main


def stamp_manifest(path: Path, version: str) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data.get("version"), str):
        raise ValueError(f"{path}: missing string version field")
    data["version"] = version
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def stamp_config(path: Path, version: str) -> None:
    source = path.read_text(encoding="utf-8")
    stamped, version_replacements = re.subn(
        r"^PLUGIN_VERSION\s*=\s*(['\"]).*?\1\s*$",
        f"PLUGIN_VERSION = '{version}'",
        source,
        flags=re.MULTILINE,
    )
    stamped, debug_replacements = re.subn(
        r"^DEBUG\s*=\s*(?:True|False)\s*$",
        "DEBUG = False",
        stamped,
        flags=re.MULTILINE,
    )
    if version_replacements != 1:
        raise ValueError(
            f"{path}: expected exactly one PLUGIN_VERSION assignment, "
            f"found {version_replacements}"
        )
    if debug_replacements != 1:
        raise ValueError(
            f"{path}: expected exactly one DEBUG assignment, "
            f"found {debug_replacements}"
        )
    path.write_text(stamped, encoding="utf-8")


def read_stamped_versions(addin_dir: Path) -> tuple[str, str]:
    manifest = json.loads(
        (addin_dir / "Makera Community.manifest").read_text(encoding="utf-8")
    )
    config = (addin_dir / "config.py").read_text(encoding="utf-8")
    match = re.search(
        r"^PLUGIN_VERSION\s*=\s*(['\"])(?P<version>.*?)\1\s*$",
        config,
        flags=re.MULTILINE,
    )
    if match is None:
        raise ValueError("staged config.py has no readable PLUGIN_VERSION")
    return manifest["version"], match.group("version")


def copy_runtime_files(project_root: Path, addin_dir: Path) -> None:
    for relative in ROOT_FILES:
        source = project_root / relative
        if not source.is_file():
            raise FileNotFoundError(f"required release file is missing: {source}")
        shutil.copy2(source, addin_dir / relative)

    for relative in ROOT_DIRECTORIES:
        source = project_root / relative
        if not source.is_dir():
            raise FileNotFoundError(f"required release directory is missing: {source}")
        shutil.copytree(
            source,
            addin_dir / relative,
            ignore=shutil.ignore_patterns(
                "__pycache__",
                "*.pyc",
                ".DS_Store",
                "settings.settings",
            ),
        )


def write_reproducible_zip(addin_dir: Path, archive: Path) -> None:
    if archive.exists():
        archive.unlink()
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as output:
        for source in sorted(path for path in addin_dir.rglob("*") if path.is_file()):
            relative = source.relative_to(addin_dir.parent)
            info = zipfile.ZipInfo(str(relative).replace("\\", "/"))
            info.date_time = (1980, 1, 1, 0, 0, 0)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            output.writestr(info, source.read_bytes())


def build_release(project_root: Path, output_dir: Path, version: str) -> Path:
    version = validate_version(version)
    staging_root = output_dir / "staging"
    addin_dir = staging_root / ADDIN_FOLDER
    if staging_root.exists():
        shutil.rmtree(staging_root)
    addin_dir.mkdir(parents=True)

    copy_runtime_files(project_root, addin_dir)
    stamp_manifest(addin_dir / "Makera Community.manifest", version)
    stamp_config(addin_dir / "config.py", version)

    manifest_version, config_version = read_stamped_versions(addin_dir)
    if manifest_version != version or config_version != version:
        raise ValueError(
            "release version mismatch: "
            f"manifest={manifest_version!r}, config={config_version!r}, "
            f"requested={version!r}"
        )

    archive = output_dir / f"{ARCHIVE_PREFIX}{version}.zip"
    write_reproducible_zip(addin_dir, archive)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    archive.with_suffix(".zip.sha256").write_text(
        f"{digest}  {archive.name}\n",
        encoding="utf-8",
    )
    return archive


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True)
    parser.add_argument("--output", type=Path, default=Path("dist"))
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
    )
    args = parser.parse_args()

    args.output.mkdir(parents=True, exist_ok=True)
    archive = build_release(
        args.project_root.resolve(),
        args.output.resolve(),
        args.version,
    )
    print(archive)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
