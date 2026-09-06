"""The reading profile, as data.

The base design system has no role for magnitude and no serif, so every bar in
it is drawn in a neutral and everything is set in the UI face. A reading
instrument needs both, and it needs paper rather than the system's grey.

Held as a dict rather than written into the stylesheet because GTK 4.14
predates CSS `var()` -- the sheet is generated with `@define-color`, and the
same values will emit the web profile when that is written.
"""

LIGHT = {
    "paper": "#F7F3EA",
    "surface": "#FFFDF8",
    "surface_muted": "#EFE9DC",
    "ink": "#282621",
    "ink_muted": "#706B61",
    "ink_faint": "#9A9488",
    "line": "#DDD6C8",
    "line_strong": "#C9C0B0",
    "accent": "#2F6F68",
    "accent_dark": "#245852",
    "accent_soft": "#DCEBE7",
    "accent_faint": "#EEF6F3",
    "magnitude": "#B8832F",
    "magnitude_soft": "#F4E7CC",
    "warning": "#8A5A24",
    "danger": "#9C4A42",
}

# Night is when people read. The paper warms rather than brightens, and the
# accent lightens so it still clears 3:1 against its own ground.
DARK = {
    "paper": "#1C1A17",
    "surface": "#26231F",
    "surface_muted": "#2F2B26",
    "ink": "#F2EDE3",
    "ink_muted": "#A9A296",
    "ink_faint": "#7C766B",
    "line": "#3A352E",
    "line_strong": "#4C463D",
    "accent": "#6FB3A8",
    "accent_dark": "#8FCBC1",
    "accent_soft": "#24413D",
    "accent_faint": "#1F302E",
    "magnitude": "#D6A354",
    "magnitude_soft": "#3A2E19",
    "warning": "#D19A50",
    "danger": "#D0796F",
}

SERIF = '"Source Serif 4", "Noto Serif", Cambria, Georgia, serif'


def rgb(value: str) -> tuple[float, float, float]:
    """A hex token as the floats Cairo wants, for anything drawn rather than styled."""
    value = value.lstrip("#")
    return tuple(int(value[i : i + 2], 16) / 255 for i in (0, 2, 4))


def stylesheet(palette: dict) -> str:
    """The sheet, with every colour resolved. `@define-color` is global, so a
    theme change reloads this rather than switching a selector."""
    colours = "\n".join(f"@define-color {name} {value};" for name, value in palette.items())
    return colours + "\n" + SHEET.replace("__SERIF__", SERIF)


SHEET = """
window, .reader-root { background: @paper; color: @ink; }

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

/* --- the bookmark --- */

.bookmark { background: @surface; border-bottom: 1px solid @line; padding: 10px 24px 6px; }
.bookmark spinbutton { background: @paper; }
.bookmark button.flat { min-width: 28px; padding: 2px 4px; }
.bookmark-label { color: @ink_faint; font-size: 0.7rem; font-weight: 700; }
.chapter-title { color: @ink_muted; font-style: italic; }
.bookmark-scale trough { min-height: 6px; background: @line; }
.bookmark-scale highlight { background: @accent; }
.bookmark-scale slider {
  min-width: 18px; min-height: 18px; background: @accent;
  border: 3px solid @surface; box-shadow: none;
}

/* --- cast cards --- */

.cast-card {
  background: @surface; border: 1px solid @line; border-radius: 10px;
  padding: 14px 18px; margin: 5px 24px;
}
.cast-name { font-size: 1.05rem; font-weight: 600; color: @ink; }
.cast-alias { color: @ink_muted; font-style: italic; font-size: 0.85rem; }
.cast-facts { color: @ink_muted; font-size: 0.85rem; }
.cast-with { color: @ink_muted; font-size: 0.85rem; }
.cast-note { color: @warning; font-size: 0.85rem; font-weight: 600; }
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
.since {
  background: @accent_faint; border: 1px solid @accent_soft; border-radius: 8px;
  margin: 8px 24px 0; padding: 10px 14px; color: @ink;
}
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

.announcement {
  color: @accent_dark; background: @accent_faint; border: 1px solid @accent_soft;
  border-radius: 6px; padding: 4px 10px; margin-top: 4px; font-size: 0.85rem;
}

.ground-caption { color: @ink_faint; font-size: 0.82rem; padding: 0 24px 4px; }
.ground-row { padding: 2px 0; }
.ground-row:hover { background: @surface; border-radius: 6px; }
.ground-name { color: @ink; font-size: 0.9rem; font-family: __SERIF__; }
.ground-row button.flat { min-width: 26px; min-height: 26px; padding: 0; }

.saved-locally { color: @ink_faint; font-size: 0.78rem; }

.summary-line { color: @ink_muted; font-size: 0.85rem; padding: 2px 24px 6px; }
.empty-state { color: @ink_muted; padding: 48px 24px; font-size: 1rem; }
listview.cast, listview.cast row { background: transparent; }
"""
