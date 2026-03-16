"""Prepare release artifacts and optionally build an Inno Setup installer."""

from __future__ import annotations

import argparse
import datetime as dt
import os
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DIST_APP_DIR = PROJECT_ROOT / "dist" / "vision_app"
RELEASE_DIR = PROJECT_ROOT / "release"
RELEASE_APP_DIR = RELEASE_DIR / "app"
VERSION_FILE = PROJECT_ROOT / "VERSION"
INSTALLER_SCRIPT = PROJECT_ROOT / "installer.iss"


def read_version() -> str:
    if not VERSION_FILE.exists():
        raise FileNotFoundError(f"Missing version file: {VERSION_FILE}")
    value = VERSION_FILE.read_text(encoding="utf-8").strip()
    if not value:
        raise ValueError("VERSION file is empty")
    return value


def is_semver(value: str) -> bool:
    parts = value.split(".")
    if len(parts) != 3:
        return False
    return all(p.isdigit() for p in parts)


def write_version(version: str) -> None:
    if not is_semver(version):
        raise ValueError("Version must follow semantic versioning: MAJOR.MINOR.PATCH")
    VERSION_FILE.write_text(f"{version}\n", encoding="utf-8")


def ensure_dist_exists() -> None:
    if not DIST_APP_DIR.exists():
        raise FileNotFoundError(
            f"Build output not found: {DIST_APP_DIR}. Run PyInstaller build first."
        )


def _copytree(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def prune_staged_artifacts(app_dir: Path) -> None:
    """Remove transient files that should not ship to end users."""
    for relative in ["output.avi", "outputs"]:
        target = app_dir / relative
        if target.is_file():
            target.unlink()
        elif target.is_dir():
            shutil.rmtree(target)


def stage_release_artifacts(version: str) -> None:
    RELEASE_DIR.mkdir(parents=True, exist_ok=True)

    _copytree(DIST_APP_DIR, RELEASE_APP_DIR)
    prune_staged_artifacts(RELEASE_APP_DIR)

    (RELEASE_DIR / "VERSION").write_text(f"{version}\n", encoding="utf-8")
    (RELEASE_APP_DIR / "VERSION").write_text(f"{version}\n", encoding="utf-8")

    metadata = {
        "version": version,
        "built_at": dt.datetime.now().isoformat(timespec="seconds"),
        "python": sys.version.split()[0],
        "platform": sys.platform,
    }
    lines = [f"{k}={v}" for k, v in metadata.items()]
    (RELEASE_DIR / "release_info.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def resolve_iscc_path(explicit_path: str | None) -> str:
    if explicit_path:
        if not Path(explicit_path).exists():
            raise FileNotFoundError(f"ISCC not found: {explicit_path}")
        return explicit_path

    env_path = os.environ.get("INNO_SETUP_ISCC")
    if env_path and Path(env_path).exists():
        return env_path

    candidate_paths = [
        Path("C:/Program Files (x86)/Inno Setup 6/ISCC.exe"),
        Path("C:/Program Files/Inno Setup 6/ISCC.exe"),
    ]
    for candidate in candidate_paths:
        if candidate.exists():
            return str(candidate)

    # Last fallback: rely on PATH
    return "ISCC.exe"


def build_installer(version: str, iscc_path: str | None = None) -> None:
    compiler = resolve_iscc_path(iscc_path)
    cmd = [compiler, f"/DMyAppVersion={version}", str(INSTALLER_SCRIPT)]
    print("Running:", " ".join(cmd))
    subprocess.run(cmd, cwd=str(PROJECT_ROOT), check=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare release folder and build installer")
    parser.add_argument("--set-version", help="Update VERSION file before staging (format: MAJOR.MINOR.PATCH)")
    parser.add_argument("--installer", action="store_true", help="Build Inno Setup installer after staging")
    parser.add_argument("--iscc-path", help="Path to ISCC.exe (optional)")
    parser.add_argument("--clean", action="store_true", help="Clean existing release/app before staging")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.set_version:
        write_version(args.set_version)
        print(f"Updated VERSION -> {args.set_version}")

    version = read_version()
    print(f"Preparing release for version {version}")

    ensure_dist_exists()

    if args.clean and RELEASE_APP_DIR.exists():
        shutil.rmtree(RELEASE_APP_DIR)

    stage_release_artifacts(version)
    print(f"Staged app files at: {RELEASE_APP_DIR}")

    if args.installer:
        build_installer(version=version, iscc_path=args.iscc_path)
        print("Installer build completed")

    print("Release preparation completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
