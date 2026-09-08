"""The three things that are not the cast: warnings, the book, and what changed.

None of them sits in the content flow any more. A warning that shows its own
text is not a warning; a panel about the whole book belongs behind the menu,
not above every view including the ones it says nothing about; and a band you
can dismiss was always a toast wearing a band's clothes.
"""

from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gtk  # noqa: E402


class Warnings(Gtk.Box):
    """Folded shut, and it stays that way until the reader opens it.

    A warning fires a chapter early and never says what it is until asked.
    Every other product in this space makes you accept the answer as the price
    of the warning; the position model is the one mechanism that does not have
    to. So no colour, no icon and no count that leaks severity -- opening it is
    a deliberate act.
    """

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.set_margin_start(24)
        self.set_margin_end(24)
        self.set_margin_top(8)
        self._box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.append(self._box)

    def show_warnings(self, warn: dict, upto: int) -> None:
        child = self._box.get_first_child()
        while child is not None:
            nxt = child.get_next_sibling()
            self._box.remove(child)
            child = nxt

        rows = []
        for key, entries in (warn or {}).items():
            if int(key) <= upto:
                rows.extend(entries)
        if not rows:
            empty = Gtk.Label(
                label="No warnings set. Add one from a chapter and it will arrive "
                "a chapter early, folded shut.",
                xalign=0,
                wrap=True,
            )
            empty.add_css_class("empty-state")
            self._box.append(empty)
            return

        for row in sorted(rows, key=lambda r: r.get("at", 0)):
            at = row.get("at", 0)
            coming = at > upto
            expander = Adw.ExpanderRow()
            expander.set_title("Something is coming" if coming else f"Chapter {at + 1}")
            expander.set_subtitle(
                "Set by you · opens only when you choose" if coming else "You have reached this one"
            )
            expander.set_expanded(False)
            inner = Adw.ActionRow()
            inner.set_title(row.get("text", ""))
            inner.set_title_lines(0)
            inner.add_css_class("warning-text")
            expander.add_row(inner)
            self._box.append(expander)


class AboutBook(Adw.Dialog):
    """The one panel that is about the whole book, and it says so.

    Cast size, pace and narration are structure, not story, which is why this
    can be about the whole book without spoiling it. It opens from the menu
    rather than sitting above the cast, because everything else on screen stops
    at the bookmark and a permanent panel about the ending was the odd one out.
    """

    def __init__(self):
        super().__init__(title="About this book")
        self.set_content_width(580)
        self.set_content_height(620)
        self._filled = False

        self._list = Gtk.ListBox(selection_mode=Gtk.SelectionMode.NONE)
        self._list.add_css_class("boxed-list")
        self._list.add_css_class("about-book")
        self._list.set_margin_start(18)
        self._list.set_margin_end(18)
        self._list.set_margin_top(12)
        self._list.set_margin_bottom(18)

        scroller = Gtk.ScrolledWindow(vexpand=True)
        scroller.set_child(self._list)
        scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        page = Adw.ToolbarView()
        page.add_top_bar(Adw.HeaderBar())
        page.set_content(scroller)
        self.set_child(page)

    def fill(self, about: dict) -> None:
        if self._filled or not about:
            return
        self._filled = True
        names, words = about.get("names", 0), about.get("words", 0)
        hours = about.get("hours") or (words // 250 // 60)
        self._row(
            "How many people you will be holding",
            f"{names} names over {words:,} words — about {hours} hours reading",
        )

        curve, band = about.get("curve") or {}, about.get("band") or {}
        for share, label in (
            ("0.1", "a tenth in"),
            ("0.25", "a quarter in"),
            ("0.5", "halfway"),
            ("0.75", "three quarters in"),
        ):
            if share not in curve:
                continue
            pct = curve[share]
            edge = band.get(share)
            where = ""
            if edge:
                where = (
                    " · fewer than most"
                    if pct < edge[0]
                    else " · more than most"
                    if pct > edge[1]
                    else " · about usual"
                )
            self._row(f"By {label}", f"{round(names * pct / 100)} of them{where}")

        person = about.get("person") or {}
        kind = person.get("kind")
        if kind:
            said = {
                "first": "the first person",
                "mixed": "a mix of first and third",
                "third": "the third person",
            }.get(kind, kind)
            share = person.get("share")
            detail = f"{share * 100:.0f}% of the pronouns outside dialogue are I or me"
            self._row("Told in", f"{said} — {detail}" if share is not None else said)

        focus = about.get("focus") or {}
        if focus.get("lead"):
            # Where the narration is first person the lead measure refuses
            # rather than answering, so `lead` being absent is a decision.
            self._row(
                "Does one person hold it",
                f"{focus['lead']} is named most in "
                f"{focus.get('share', 0) * 100:.0f}% of chapters; "
                f"{focus.get('owners', 0)} different people lead one",
            )

        series = about.get("series")
        if series:
            self._row("Where in the series", str(series))

        note = Adw.ActionRow()
        note.set_title(
            "Cast size, pace and narration are structure, not story. "
            "Everything else here stops at the chapter you are on."
        )
        note.set_title_lines(0)
        note.add_css_class("panel-note")
        self._list.append(note)

    def _row(self, label: str, value: str) -> None:
        row = Adw.ActionRow()
        row.set_title(label)
        row.set_subtitle(value)
        row.set_subtitle_lines(0)
        self._list.append(row)


def since_bookmark(model, mark: int, upto: int, candidates: int) -> str:
    """What changed between where the reader was and where they are.

    Only ever backwards, and it returns a sentence rather than a widget: a
    dismissible band pinned above every view was a toast in the wrong clothes,
    and the window says it once when the reader has moved on rather than
    keeping it on screen for the rest of the session.
    """
    if upto <= mark:
        return ""
    fresh, back = [], []
    for entity in model["entities"]:
        if entity["first"] > upto:
            continue
        if entity["first"] > mark:
            fresh.append(entity)
        elif (
            not [c for c in entity["chapters"] if c <= mark]
            or max((c for c in entity["chapters"] if c <= mark), default=-1) < mark - 4
        ) and any(mark < c <= upto for c in entity["chapters"]):
            back.append(entity)

    parts = []
    if fresh:
        parts.append(f"{len(fresh)} {'person' if len(fresh) == 1 else 'people'} appeared")
    if back:
        parts.append(f"{len(back)} returned")
    if candidates:
        parts.append(f"{candidates} possible name matches to rule on")
    if not parts:
        return ""
    return f"Since chapter {mark + 1}: " + ", ".join(parts)
