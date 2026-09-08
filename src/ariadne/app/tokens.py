"""The reading profile, as data.

The base design system has no role for magnitude and no serif, so every bar in
it is drawn in a neutral and everything is set in the UI face. A reading
instrument needs both, and it needs paper rather than the system's grey.

Held as a dict rather than written into the stylesheet because GTK 4.14
predates CSS `var()` -- the sheet is generated with `@define-color`, and the
same values will emit the web profile when that is written.
"""

LIGHT = {
    "paper": "#faf9f7",
    "surface": "#ffffff",
    "surface_muted": "#f1efeb",
    "ink": "#1b1917",
    "ink_muted": "#726e68",
    "ink_faint": "#8f8a83",
    "line": "#e4e1da",
    "line_strong": "#d3cec4",
    "accent": "#14684f",
    "accent_dark": "#0d5540",
    "accent_soft": "#e0ece7",
    "accent_faint": "#eef4f1",
    "magnitude": "#a07c2c",
    "magnitude_soft": "#efe6d3",
    "warning": "#8a5d16",
    "danger": "#a3372a",
}

# Night is when people read. The paper warms rather than brightens, and the
# accent lightens so it still clears 3:1 against its own ground.
#
# `surface_muted` is darker than `paper` in both palettes. It is the rail and
# the foot, and a rail that lifts off the canvas at night reads as a raised
# panel rather than as the edge of the window.
DARK = {
    "paper": "#191817",
    "surface": "#22201e",
    "surface_muted": "#121110",
    "ink": "#e9e5de",
    "ink_muted": "#8e8880",
    "ink_faint": "#6f6a63",
    "line": "#2e2b28",
    "line_strong": "#454039",
    "accent": "#2e9a76",
    "accent_dark": "#4fb694",
    "accent_soft": "#1d2f28",
    "accent_faint": "#15211d",
    "magnitude": "#d0a44e",
    "magnitude_soft": "#332a18",
    "warning": "#d0a04a",
    "danger": "#e0705c",
}

SANS = '"Manrope", "Cantarell", "Ubuntu", system-ui, sans-serif'
SERIF = '"Literata", "Source Serif 4", "Noto Serif", Cambria, Georgia, serif'


def rgb(value: str) -> tuple[float, float, float]:
    """A hex token as the floats Cairo wants, for anything drawn rather than styled."""
    value = value.lstrip("#")
    return tuple(int(value[i : i + 2], 16) / 255 for i in (0, 2, 4))


def stylesheet(palette: dict) -> str:
    """The sheet, with every colour resolved. `@define-color` is global, so a
    theme change reloads this rather than switching a selector."""
    colours = "\n".join(f"@define-color {name} {value};" for name, value in palette.items())
    return colours + "\n" + SHEET.replace("__SERIF__", SERIF).replace("__SANS__", SANS)


SHEET = """
window, .reader-root { background: @paper; color: @ink; font-family: __SANS__; }

.book-title, .cast-name, .section-heading { font-family: __SERIF__; }
.book-title { font-size: 1.15rem; font-weight: 600; color: @ink; }
.book-author { color: @ink_muted; font-size: 0.85rem; }
.reading-position { color: @ink_muted; font-size: 0.85rem; }

/* --- the navigation rail --- */

.rail { background: @surface_muted; border-right: 1px solid @line; }
.rail-group {
  color: @ink_faint; font-size: 0.75rem; font-weight: 700;
  margin: 14px 14px 2px;
}
.rail listview, .rail list { background: transparent; }
row.rail-item {
  border-radius: 6px; margin: 1px 8px; padding: 5px 10px; min-height: 30px;
  border-left: 3px solid transparent; color: @ink;
}
row.rail-item:hover { background: @surface; }
row.rail-item:selected {
  background: @accent_soft; border-left-color: @accent; font-weight: 600;
}
row.rail-item:selected label { color: @accent_dark; }

/* --- the axis, which is the bookmark --- */

.bookmark { margin-top: 8px; margin-bottom: 0; }
.bookmark:focus-visible { outline: 2px solid @accent; outline-offset: 4px; }

/* --- the pictures --- */

.plate { padding: 4px 0; }
.plate picture {
  border: 1px solid @line; border-radius: 8px; background: @surface;
}
.plate-caption { color: @ink; font-size: 0.95rem; font-family: __SERIF__; }
.plate-where { color: @ink_faint; font-size: 0.8rem; padding: 0 6px; min-height: 22px; }
.plate-where:hover { color: @accent_dark; background: @accent_faint; }

/* --- the cast facets --- */

button.chip {
  border-radius: 999px; padding: 3px 14px; min-height: 26px;
  background: @surface; color: @ink_muted; border: 1px solid @line;
  box-shadow: none; font-size: 0.88rem;
}
button.chip:hover { background: @accent_faint; color: @accent_dark; }
button.chip:checked {
  background: @accent_soft; color: @accent_dark; border-color: @accent_soft;
  font-weight: 600;
}
.facets entry { border-radius: 999px; }
.position-button { padding: 0 6px; min-height: 26px; background: none; box-shadow: none; }
.position-button:hover { background: @surface_muted; }
.menu-popover button { padding: 4px 10px; min-height: 30px; }
.menu-heading {
  color: @ink_faint; font-size: 0.72rem; font-weight: 700;
  margin: 2px 4px 0;
}
.appearance button {
  min-height: 28px; padding: 2px 12px; background: @surface;
  color: @ink_muted; border: 1px solid @line; box-shadow: none;
  font-size: 0.88rem;
}
.menu-check { margin: 6px 4px 0; font-size: 0.88rem; color: @ink; }
.appearance button:checked {
  background: @accent_soft; color: @accent_dark; border-color: @accent_soft;
  font-weight: 600;
}

/* --- cast cards --- */

/* 23 and not 24: the border is the twenty-fourth pixel, so the card's content
   box -- and the strip that fills it -- begins exactly where the axis does.
   `gui-smoke.py` measures the two and fails if they part. */
.cast-card {
  background: @surface; border: 1px solid @line; border-radius: 10px;
  padding: 14px 0; margin: 5px 23px;
}
/* The strip is registered with the axis, so it spans the card edge to edge and
   the writing is what carries the inset. */
.card-text { margin-left: 18px; margin-right: 18px; }
.cast-name { font-size: 1.05rem; font-weight: 600; color: @ink; }
.cast-alias { color: @ink_muted; font-style: italic; font-size: 0.85rem; }
.cast-facts { color: @ink_muted; font-size: 0.85rem; }
.cast-with { color: @ink_muted; font-size: 0.85rem; }
.cast-note { color: @ink_muted; font-size: 0.85rem; font-weight: 600; }
.cast-kind {
  background: @surface_muted; color: @ink_muted; border-radius: 4px;
  padding: 0 6px; font-size: 0.75rem;
}
.cast-new {
  background: @accent_soft; color: @accent_dark; border-radius: 4px;
  padding: 0 6px; font-size: 0.75rem; font-weight: 700;
}
.name-button { padding: 0; min-height: 0; background: none; border: none; box-shadow: none; }
.name-button:hover label { color: @accent_dark; text-decoration: underline; }

/* --- the detail drawer --- */

.drawer { background: @surface; border-left: 1px solid @line_strong; }
.drawer-head { padding: 12px 14px 8px 18px; border-bottom: 1px solid @line; }
.drawer-title { font-size: 1.15rem; font-weight: 600; font-family: __SERIF__; color: @ink; }
.drawer-body { padding: 16px 18px 24px; }
.drawer-label {
  color: @ink_faint; font-size: 0.72rem; font-weight: 700;
}
.drawer-value { color: @ink; font-size: 0.95rem; }
button.chapter-chip {
  min-height: 24px; min-width: 30px; padding: 0 6px;
  background: @surface_muted; color: @ink_muted; border: 1px solid @line;
  border-radius: 4px; font-size: 0.8rem;
}
button.chapter-chip:hover { background: @accent_soft; color: @accent_dark; }
.note-entry {
  background: @paper; border: 1px solid @line_strong;
  border-radius: 6px; padding: 6px;
}
.note-entry text { background: @paper; color: @ink; }
.merge-box {
  background: @accent_faint; border: 1px solid @accent_soft;
  border-radius: 8px; padding: 12px;
}

/* --- the panels --- */

.about-book, .about-book row { background: @surface; }
.about-book { border-radius: 10px; }
.panel-note { color: @ink_faint; }
.warning-text { color: @warning; }
.pace-readout {
  color: @ink_muted; font-size: 0.85rem; padding: 0 24px 6px;
  font-family: monospace;
}
/* The system accent is whatever the desktop is set to, and here it arrived
   pink. Green means safe to proceed in this profile and nothing else does, so
   the primary action carries it rather than the theme's. */
button.suggested-action {
  background: @accent; color: @surface; border: 1px solid @accent_dark;
}
button.suggested-action:hover { background: @accent_dark; }
button.suggested-action:disabled { background: @surface_muted; color: @ink_faint; }

.welcome-title { font-family: __SERIF__; }

.ground-caption { color: @ink_faint; font-size: 0.82rem; padding: 0 24px 4px; }
.ground-row { padding: 4px 0 6px; }
.ground-row:hover { background: @surface; border-radius: 6px; }
.ground-name { color: @ink; font-size: 0.9rem; font-family: __SERIF__; }
.ground-row button.flat { min-width: 26px; min-height: 26px; padding: 0; }
.ground-row .cast-facts { margin-left: 8px; }

.saved-locally { color: @ink_faint; font-size: 0.78rem; }
/* The one state in the header that is bad news, so it is the one that
   carries a colour. Never for the ordinary case. */
.saved-locally.cannot-save { color: @danger; font-weight: 700; }

.summary-line { color: @ink_muted; font-size: 0.85rem; padding: 2px 24px 6px; }
.empty-state { color: @ink_muted; padding: 48px 24px; font-size: 1rem; }
listview.cast, listview.cast > row { background: transparent; }
/* The list's own padding pushed every card off the axis by two pixels and down
   the page by fifteen. The card carries its own spacing. */
listview.cast { padding: 0; }
listview.cast > row { padding: 0; margin: 0; min-height: 0; }
"""
