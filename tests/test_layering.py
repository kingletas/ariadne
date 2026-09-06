"""The layers are a rule, not a folder arrangement.

A directory called `core` proves nothing. These are the checks that make the
names true: what each layer may import, and that the engine can be imported on
a machine with no GUI toolkit installed at all.
"""

import ast
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "src" / "ariadne"

# Read top to bottom: each layer may import the ones above it and nothing else.
ALLOWED = {
    "core": set(),
    "ingest": {"core"},
    "model": {"core"},
    "decisions": {"core"},
    "position": {"core"},
    "analysis": {"core", "model"},
    "ai": {"core"},
    "render": {"core", "model", "analysis", "decisions"},
    # The desktop reader may not reach `render` or `ai`: it draws its own
    # widgets rather than a page, and nothing it does needs an account.
    "app": {
        "core",
        "ingest",
        "model",
        "decisions",
        "position",
        "analysis",
        "invariant",
        "assemble",
    },
    "cli": {
        "app",
        "core",
        "ingest",
        "model",
        "decisions",
        "position",
        "analysis",
        "ai",
        "render",
        "invariant",
    },
}

# What the engine must never need. A front end may import any of them.
FRONT_END_ONLY = ("gi", "fastapi", "uvicorn", "starlette", "jinja2")

ENGINE = ("core", "ingest", "model", "decisions", "position", "analysis", "ai")


def layers():
    """Directories that hold code. A folder of data is not a layer, and asking
    it what it imports could only ever be answered with nothing."""
    return sorted(
        p.name
        for p in PACKAGE.iterdir()
        if p.is_dir() and not p.name.startswith(("_", ".")) and any(p.rglob("*.py"))
    )


def modules_in(layer):
    return sorted((PACKAGE / layer).rglob("*.py"))


def reaches(path):
    """Which sibling layers this file imports, by reading its imports."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.level == 2 and node.module:
            found.add(node.module.split(".")[0])
    return found


def test_every_layer_is_declared():
    """A new folder is a decision, so it fails here until somebody makes it."""
    assert set(layers()) == set(ALLOWED), (
        "layers on disk and layers in ALLOWED disagree; declare the new one"
    )


def test_no_layer_reaches_below_itself():
    for layer in layers():
        for path in modules_in(layer):
            for reached in reaches(path):
                assert reached in ALLOWED[layer] | {layer}, (
                    f"{path.relative_to(ROOT)} imports `{reached}`, which {layer} may not reach"
                )


def test_the_engine_needs_no_toolkit():
    """Importing the engine must not pull in a front end's dependencies.

    This is the check behind the claim that the reader and the index are
    standard library only. It runs in a subprocess with those names poisoned,
    because an import that already happened in this process would pass anyway.
    """
    blocked = ", ".join(repr(name) for name in FRONT_END_ONLY)
    program = (
        "import sys\n"
        f"for name in ({blocked},):\n"
        "    sys.modules[name] = None\n"
        "import importlib\n"
        f"for layer in {ENGINE!r}:\n"
        "    for mod in ('',):\n"
        "        pass\n"
        "import pkgutil, ariadne\n"
        "for m in pkgutil.walk_packages(ariadne.__path__, 'ariadne.'):\n"
        f"    if m.name.split('.')[1] in {ENGINE!r}:\n"
        "        importlib.import_module(m.name)\n"
        "print('ok')\n"
    )
    done = subprocess.run(  # noqa: S603
        [sys.executable, "-c", program],
        capture_output=True,
        text=True,
        cwd=ROOT,
        env={"PYTHONPATH": str(ROOT / "src"), "PATH": "/usr/bin:/bin"},
    )
    assert done.returncode == 0, f"the engine does not import without a toolkit:\n{done.stderr}"
