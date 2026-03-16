"""Shared application version helpers."""

from __future__ import annotations

import os
import sys
from pathlib import Path

DEFAULT_VERSION = "0.0.0-dev"


def _candidate_version_files() -> list[Path]:
    candidates: list[Path] = []

    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        candidates.extend([
            exe_dir / "VERSION",
            exe_dir / "_internal" / "VERSION",
        ])

    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        meipass_dir = Path(meipass)
        candidates.extend([
            meipass_dir / "VERSION",
            meipass_dir.parent / "VERSION",
        ])

    project_dir = Path(__file__).resolve().parent
    candidates.extend([
        project_dir / "VERSION",
        project_dir.parent / "VERSION",
    ])

    # Remove duplicates while preserving order.
    unique: list[Path] = []
    seen = set()
    for path in candidates:
        key = os.path.normcase(str(path))
        if key in seen:
            continue
        seen.add(key)
        unique.append(path)
    return unique


def get_app_version(default: str = DEFAULT_VERSION) -> str:
    for version_file in _candidate_version_files():
        if not version_file.is_file():
            continue
        value = version_file.read_text(encoding="utf-8").strip()
        if value:
            return value
    return default


def get_display_version(prefix: str = "v") -> str:
    version = get_app_version()
    return f"{prefix}{version}" if prefix else version
