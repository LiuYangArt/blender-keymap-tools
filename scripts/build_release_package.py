from __future__ import annotations

import argparse
import tomllib
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "blender_manifest.toml"
PACKAGE_ID = "keymap_tools"

ROOT_FILES = (
    "__init__.py",
    "auto_load.py",
    "blender_manifest.toml",
)
PACKAGE_DIRS = (
    "functions",
    "operators",
    "panels",
    "properties",
    "blendfiles",
)
EXCLUDED_PARTS = {"__pycache__"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}
EXCLUDED_BLEND_BACKUPS = (".blend1", ".blend2", ".blend@", ".blend~")


def read_version() -> str:
    with MANIFEST_PATH.open("rb") as handle:
        manifest = tomllib.load(handle)
    version = manifest.get("version")
    if not isinstance(version, str) or not version:
        raise RuntimeError(f"Missing string version in {MANIFEST_PATH}")
    return version


def should_include(path: Path) -> bool:
    if EXCLUDED_PARTS.intersection(path.parts):
        return False
    if path.suffix in EXCLUDED_SUFFIXES:
        return False
    if path.name.endswith(EXCLUDED_BLEND_BACKUPS):
        return False
    return path.is_file()


def iter_package_files() -> list[Path]:
    files: list[Path] = []

    for relative in ROOT_FILES:
        path = ROOT / relative
        if not path.is_file():
            raise FileNotFoundError(f"Required package file not found: {path}")
        files.append(path)

    for relative in PACKAGE_DIRS:
        directory = ROOT / relative
        if not directory.is_dir():
            raise FileNotFoundError(f"Required package directory not found: {directory}")
        files.extend(path for path in directory.rglob("*") if should_include(path))

    return sorted(files, key=lambda path: path.relative_to(ROOT).as_posix())


def build_package(output_dir: Path) -> Path:
    version = read_version()
    files = iter_package_files()
    if not files:
        raise RuntimeError("No package files found")

    output_dir.mkdir(parents=True, exist_ok=True)
    archive_path = output_dir / f"{PACKAGE_ID}-v{version}.zip"
    if archive_path.exists():
        archive_path.unlink()

    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            archive.write(path, path.relative_to(ROOT).as_posix())

    return archive_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the Keymap Tools release zip.")
    parser.add_argument("--output", type=Path, default=ROOT / "dist", help="Output directory for the zip file.")
    args = parser.parse_args()

    archive_path = build_package(args.output.resolve())
    print(archive_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())