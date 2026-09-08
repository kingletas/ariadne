"""What ships beside the code: the two faces the reading profile is set in.

GTK resolves fonts through fontconfig, and fontconfig cannot see inside a
Python package. An installed Ariadne puts the faces in a real font directory --
`/usr/share/fonts/truetype/ariadne` from the `.deb`, `/app/share/fonts` from
the Flatpak -- and this module is the other case: a checkout, where the only
way to reach them is to hand fontconfig a config file naming this directory.

A missing face costs the chrome its typeface and nothing else, so everything
here fails quietly and the layout is unchanged either way.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

FONTS = Path(__file__).resolve().parent / "fonts"

# The include is load-bearing. `FONTCONFIG_FILE` replaces the system
# configuration rather than adding to it, so a fragment that only names this
# directory would take every other font on the machine away with it.
FRAGMENT = """<?xml version="1.0"?>
<!DOCTYPE fontconfig SYSTEM "urn:fontconfig:fonts.dtd">
<fontconfig>
  <include ignore_missing="yes">/etc/fonts/fonts.conf</include>
  <dir>{directory}</dir>
</fontconfig>
"""


def use_bundled_fonts() -> Path | None:
    """Point fontconfig at the shipped faces. Returns the file written, or None.

    Call it before the first `gi.repository` import. Pango builds its font map
    from whatever fontconfig was reading at that moment and never looks again,
    so setting the variable afterwards changes nothing -- and a variable that
    is set but does nothing is worse than one that is not, because it reads as
    having worked. Refuse instead.

    It also does nothing when the faces are absent or when somebody has set
    `FONTCONFIG_FILE` themselves; that setting is theirs, not ours.
    """
    if os.environ.get("FONTCONFIG_FILE"):
        return None
    if any(name.startswith("gi.repository.") for name in sys.modules):
        return None
    if not FONTS.is_dir() or not any(FONTS.glob("*.ttf")):
        return None
    try:
        home = os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache"
        config = Path(home) / "ariadne" / "fonts.conf"
        wanted = FRAGMENT.format(directory=FONTS)
        config.parent.mkdir(parents=True, exist_ok=True)
        if not config.is_file() or config.read_text(encoding="utf-8") != wanted:
            config.write_text(wanted, encoding="utf-8")
    except OSError:
        return None
    os.environ["FONTCONFIG_FILE"] = str(config)
    return config
