"""The working-directory guard in chapters 2, 3 and 4 must actually hold.

Each chapter's `_inside_root()` is the one line standing between the model and
the rest of the disk. This test drives it with the paths a confused or
prompt-injected model would send: traversal, absolute paths, Windows drive
letters and backslashes, a sibling directory whose name merely starts with the
working directory's, and a symlink (or junction) inside the repository that
points outside it.
"""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
CHAPTERS_DIR = REPO_ROOT / "chapters"
GUARDED = ["02_tools", "03_errors", "04_loop_control"]


def _load(stem: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(stem, CHAPTERS_DIR / f"{stem}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _allowed(module: ModuleType, path: str) -> bool:
    """True if the chapter's guard lets the path through, whichever way it signals refusal.

    Chapter 2 returns the resolved Path, or None to refuse. Chapters 3 and 4
    return None on success and raise PermissionError to refuse.
    """
    returns_path = "Path" in str(module._inside_root.__annotations__.get("return", ""))
    try:
        result = module._inside_root(path)
    except PermissionError:
        return False
    return result is not None if returns_path else True


@pytest.fixture(scope="module")
def modules() -> Iterator[dict[str, ModuleType]]:
    """The chapters take ROOT from the cwd at import time, so import them from the repo."""
    previous = Path.cwd()
    os.chdir(REPO_ROOT)
    try:
        yield {stem: _load(stem) for stem in GUARDED}
    finally:
        os.chdir(previous)


@pytest.fixture(scope="module")
def outside(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A directory outside the repo with one file whose contents we must never see."""
    directory = tmp_path_factory.mktemp("outside")
    (directory / "secret.txt").write_text("outside", encoding="utf-8")
    return directory


def _hostile_paths(outside: Path) -> list[str]:
    root = str(REPO_ROOT)
    return [
        "..",
        "../..",
        "chapters/../../secret.txt",
        "..\\secret.txt",
        str(outside),
        str(outside / "secret.txt"),
        root + "2",  # /work vs /work2: a prefix match is not containment
        root + "2/secret.txt",
        "/etc/passwd",
        "\\etc\\passwd",
        "C:\\Windows\\win.ini",
        "C:/Windows/win.ini",
        "\\\\localhost\\c$\\Windows\\win.ini",
    ]


@pytest.mark.parametrize("stem", GUARDED)
def test_paths_outside_the_working_directory_are_refused(
    stem: str, modules: dict[str, ModuleType], outside: Path
) -> None:
    module = modules[stem]
    leaked = [path for path in _hostile_paths(outside) if _allowed(module, path)]
    assert not leaked, f"{stem} let these paths through: {leaked}"


@pytest.mark.parametrize("stem", GUARDED)
def test_paths_inside_the_working_directory_are_allowed(
    stem: str, modules: dict[str, ModuleType]
) -> None:
    module = modules[stem]
    for path in [".", "", "chapters", "chapters/01_the_loop.py", "./chapters/../README.md"]:
        assert _allowed(module, path), f"{stem} refused {path!r}, which is inside the repo"


@pytest.mark.parametrize("stem", GUARDED)
def test_link_inside_the_repo_pointing_outside_is_refused(
    stem: str, modules: dict[str, ModuleType], outside: Path
) -> None:
    """A symlink (junction on Windows) is the classic way past a naive prefix check."""
    link = REPO_ROOT / "tmp_link_for_path_guard_test"
    if link.exists() or link.is_symlink():
        pytest.fail(f"{link} already exists; remove it and re-run")
    try:
        if sys.platform == "win32":
            done = subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(link), str(outside)],
                capture_output=True,
                text=True,
            )
            if done.returncode != 0:
                pytest.skip(f"cannot create a junction here: {done.stderr.strip()}")
        else:
            link.symlink_to(outside, target_is_directory=True)
        module = modules[stem]
        assert not _allowed(module, link.name)
        assert not _allowed(module, f"{link.name}/secret.txt")
    finally:
        if link.is_symlink():
            link.unlink()
        elif link.is_dir():
            os.rmdir(link)  # a junction is a directory entry, not a symlink, to pathlib
