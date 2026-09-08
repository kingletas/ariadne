"""The two faces ship, and they are asked for in time to matter.

Pango builds its font map from whatever fontconfig was reading when the first
`gi.repository` module was imported, and never looks again. So the shipped
faces are not a question of whether the files are present -- they were present
and invisible, and the window drew in the system's faces with nothing anywhere
saying so.

The ordering is the whole defect, so the ordering is what these check.
"""

import ast
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "src" / "ariadne"
FONTS = PACKAGE / "app" / "assets" / "fonts"

FAMILIES = ("Manrope", "Literata")

# Every way a window gets opened. Each has to ask for the faces before it
# touches the toolkit, and each is a separate file that can forget.
ENTRY_POINTS = (PACKAGE / "app" / "main.py", ROOT / "scripts" / "gui-smoke.py")


def test_both_faces_ship_with_their_licence():
    """The OFL requires the licence to travel with the font."""
    faces = sorted(p.name for p in FONTS.glob("*.ttf"))
    assert len(faces) == len(FAMILIES), f"expected {len(FAMILIES)} faces, found {faces}"
    for face in faces:
        assert face.startswith(FAMILIES), f"{face} is not one of the two the profile names"
    licences = {p.name for p in FONTS.glob("*-OFL.txt")}
    assert licences == {f"{family}-OFL.txt" for family in FAMILIES}, (
        f"a face is shipping without its licence: {licences}"
    )


def _first_toolkit_import(path: Path) -> int:
    """The line that makes it too late, or a line past the end of the file."""
    body = path.read_text(encoding="utf-8")
    for node in ast.walk(ast.parse(body)):
        if isinstance(node, ast.ImportFrom) and (node.module or "").startswith("gi.repository"):
            return node.lineno
        if isinstance(node, ast.Import) and any(
            a.name.startswith("gi.repository") for a in node.names
        ):
            return node.lineno
    return len(body.splitlines()) + 1


def _asks_for_fonts(path: Path) -> int:
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "use_bundled_fonts"
        ):
            return node.lineno
    return -1


@pytest.mark.parametrize("path", ENTRY_POINTS, ids=lambda p: p.name)
def test_every_window_asks_for_the_faces_before_the_toolkit(path):
    asked = _asks_for_fonts(path)
    assert asked > 0, f"{path.name} never calls use_bundled_fonts()"
    toolkit = _first_toolkit_import(path)
    assert asked < toolkit, (
        f"{path.name} imports gi.repository at line {toolkit} and asks for the faces at "
        f"line {asked}; by then Pango has already built its font map"
    )


def test_asking_too_late_is_refused_rather_than_pretended():
    """A variable that is set but does nothing reads as having worked."""
    program = (
        "import gi\n"
        "gi.require_version('Gtk', '4.0')\n"
        "from gi.repository import Gtk\n"
        "from ariadne.app.assets import use_bundled_fonts\n"
        "import os\n"
        "assert use_bundled_fonts() is None, 'it claimed to work after the toolkit'\n"
        "assert 'FONTCONFIG_FILE' not in os.environ, 'it set a variable that does nothing'\n"
        "print('ok')\n"
    )
    done = subprocess.run(  # noqa: S603
        [sys.executable, "-c", program],
        capture_output=True,
        text=True,
        cwd=ROOT,
        env={"PYTHONPATH": str(ROOT / "src"), "PATH": "/usr/bin:/bin"},
    )
    if "No module named 'gi'" in done.stderr:
        pytest.skip("no toolkit on this machine")
    assert done.returncode == 0, done.stderr


def test_pango_can_actually_see_them():
    """The end of the chain, in a fresh process: the faces reach the font map.

    This asks the toolkit rather than the code meant to configure it, so it
    proves the shipped path works. It cannot see a driver that imports the
    toolkit first, because it does not use one -- that is what the check above
    is for, and both are needed.
    """
    program = (
        "from ariadne.app.main import ReaderApplication\n"
        "from gi.repository import PangoCairo\n"
        "seen = {f.get_name() for f in PangoCairo.FontMap.get_default().list_families()}\n"
        f"missing = {set(FAMILIES)!r} - seen\n"
        "assert not missing, f'pango cannot see {missing}'\n"
        "print('ok')\n"
    )
    done = subprocess.run(  # noqa: S603
        [sys.executable, "-c", program],
        capture_output=True,
        text=True,
        cwd=ROOT,
        env={"PYTHONPATH": str(ROOT / "src"), "PATH": "/usr/bin:/bin", "HOME": str(Path.home())},
    )
    if "No module named 'gi'" in done.stderr or "Namespace" in done.stderr:
        pytest.skip("no toolkit on this machine")
    assert done.returncode == 0, done.stderr
