"""What a clone actually contains.

`~/.gitignore` is `core.excludesFile` for every repository under this account,
and it carries broad patterns — `*.sh`, `tools/*` — that silently exclude whole
directories here. There is no warning at commit and `git status` stays clean;
the first sign is a CI job that cannot find a file, or a clone that ships a
feature with its code missing.

It has happened twice: the build scripts, and then the corpus pipeline. This is
the check that ends it, and it is cheap because it asks git rather than
guessing.
"""

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Everything under these is source, and a clone that lacks any of it is broken.
SHIPPED = ("src", "tests", "scripts", "packaging", "tools", "data", ".github")

# Build products and caches, which are ignored on purpose.
DISPOSABLE = (
    "build/",
    "dist/",
    "repo/",
    ".venv/",
    ".flatpak-builder/",
    ".pytest_cache/",
    ".ruff_cache/",
    "__pycache__",
)


def git(*args):
    """`git` from PATH with a fixed argument list and no shell, reading only."""
    command = ["git", *args]  # noqa: S603,S607
    done = subprocess.run(  # noqa: S603
        command, cwd=ROOT, capture_output=True, text=True, check=True
    )
    return done.stdout


def test_nothing_that_ships_is_being_ignored():
    """A file present on disk, inside a source directory, and invisible to git."""
    ignored = [
        line
        for line in git("ls-files", "--others", "--ignored", "--exclude-standard").splitlines()
        if line.startswith(SHIPPED) and not any(d in line for d in DISPOSABLE)
    ]
    assert not ignored, (
        "these are on disk, belong in the repository, and git cannot see them — "
        f"the excludes file is swallowing them: {ignored}"
    )


def test_every_source_directory_has_tracked_files():
    """A whole directory can be excluded by one pattern, which is how it hides."""
    for name in SHIPPED:
        directory = ROOT / name
        if not directory.exists():
            continue
        tracked = git("ls-files", name).splitlines()
        assert tracked, f"{name}/ exists on disk and nothing in it is tracked"


def test_the_shell_scripts_are_all_tracked():
    """`*.sh` is excluded globally, which is why the entry points have no
    extension and why the negation in .gitignore is unscoped."""
    on_disk = {
        str(p.relative_to(ROOT))
        for p in ROOT.rglob("*.sh")
        if not any(d in str(p) for d in DISPOSABLE)
    }
    tracked = set(git("ls-files", "*.sh").splitlines())
    assert on_disk <= tracked, f"untracked shell scripts: {sorted(on_disk - tracked)}"
