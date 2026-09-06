"""The reader's own rulings, and the undo behind them.

Everything here writes the same sidecar the command line writes, in the same
shape, beside the same book. Deleting the application leaves the file intact,
which is the whole of the portability requirement -- so this is a second way
into one store rather than a second store.

Nothing merges on its own. Two mechanical signals for "these two names are one
person" were tested over six novels and both failed, so ariadne proposes only
what it can prove -- one name wholly containing another -- and every other link
comes from the reader. In some books the identity is the plot.
"""

from __future__ import annotations

import copy

from ..analysis.prose import warning_map
from ..decisions.sidecar import apply_decisions, containment_links, load_decisions, save_decisions

UNDO_DEPTH = 50


class Curation:
    """One book's rulings, with the model they produce.

    The pristine entities are kept so a ruling can be taken back: applying a
    merge rewrites the index, and un-applying it means rebuilding from what was
    there before rather than trying to invert the merge.
    """

    def __init__(self, model: dict, path: str | None):
        self._path = path
        self._pristine = copy.deepcopy(model)
        self.decisions = load_decisions(path) if path else load_decisions("")
        self._undo: list[tuple[str, dict]] = []
        self.model = self._rebuild()

    # --- what the reader can do ---

    def merge(self, keep: str, also: str) -> str:
        self._remember(f"Merged {also} into {keep}")
        self._set_link(keep, also, "accepted")
        return f"{also} is now part of {keep}"

    def separate(self, keep: str, also: str) -> str:
        self._remember(f"Kept {also} separate from {keep}")
        self._set_link(keep, also, "rejected")
        return f"{also} and {keep} stay separate"

    def rename(self, name: str, to: str) -> str:
        self._remember(f"Renamed {name}")
        self.decisions.setdefault("renamed", {})[name] = to
        return self._commit(f"{name} now reads {to}")

    def note(self, name: str, text: str, at: int) -> str:
        self._remember(f"Note on {name}")
        if text.strip():
            self.decisions.setdefault("glosses", {})[name] = {"at": at, "text": text.strip()}
        else:
            self.decisions.get("glosses", {}).pop(name, None)
        return self._commit(f"Note saved for {name}")

    def warn(self, at: int, text: str) -> str:
        self._remember(f"Warning for chapter {at + 1}")
        self.decisions.setdefault("warnings", []).append({"at": at, "text": text.strip()})
        return self._commit(f"Warning set for chapter {at + 1}")

    def hide(self, name: str) -> str:
        self._remember(f"Hid {name}")
        hidden = self.decisions.setdefault("hidden", [])
        if name not in hidden:
            hidden.append(name)
        return self._commit(f"{name} hidden")

    @property
    def position(self) -> int:
        """Where the reader left off. The sidecar already carried this field;
        the page kept its own copy in localStorage and the two never met."""
        try:
            return max(0, int(self.decisions.get("position") or 0))
        except (TypeError, ValueError):
            return 0

    def remember_position(self, chapter: int) -> None:
        """Written without an undo entry: moving a bookmark is not a ruling."""
        if self.decisions.get("position") == chapter:
            return
        self.decisions["position"] = chapter
        self._write()

    # --- where the book has been ---

    def keep_setting(self, name: str) -> str:
        self._remember(f"Kept {name} as a setting")
        self.decisions.setdefault("settings", {})[name] = True
        return self._commit(f"{name} is a setting")

    def strike_setting(self, name: str) -> str:
        self._remember(f"Struck {name} from the settings")
        self.decisions.setdefault("settings", {})[name] = False
        return self._commit(f"{name} is not a setting")

    @property
    def kept_settings(self) -> set[str]:
        return {name for name, keep in (self.decisions.get("settings") or {}).items() if keep}

    @property
    def struck_settings(self) -> set[str]:
        return {
            name for name, keep in (self.decisions.get("settings") or {}).items() if keep is False
        }

    # --- taking it back ---

    @property
    def can_undo(self) -> bool:
        return bool(self._undo)

    @property
    def last_action(self) -> str:
        return self._undo[-1][0] if self._undo else ""

    def undo(self) -> str:
        """One step back, from the state before the ruling rather than by
        inverting it -- a merge cannot be inverted once the index is rewritten."""
        if not self._undo:
            return "Nothing to undo"
        label, snapshot = self._undo.pop()
        self.decisions = snapshot
        self.model = self._rebuild()
        self._write()
        return f"Undid: {label.lower()}"

    # --- what the reader is asked ---

    def candidates(self, upto: int) -> list[tuple[str, str]]:
        """Pairs worth asking about, and only ones the reader has reached.

        Containment is the one link ariadne can prove: `Prince Andrew` inside
        `Prince Andrew Bolkónski`. It measured 79.5% on the two halves of a
        single name where adjacency managed 8.9%.
        """
        met = {e["name"] for e in self.model["entities"] if e["first"] <= upto}
        ruled = {
            (link["keep"], link["also"])
            for link in self.decisions.get("links", [])
            if link.get("state") in ("accepted", "rejected")
        }
        # containment_links yields (longer, shorter) tuples; the longer name is
        # the one kept, because it is the one that identifies the person.
        return [
            pair
            for pair in containment_links(sorted(met))
            if pair not in ruled and pair[0] in met and pair[1] in met
        ]

    def note_for(self, name: str) -> str:
        return (self.decisions.get("glosses", {}).get(name) or {}).get("text", "")

    # --- the machinery ---

    def _set_link(self, keep: str, also: str, state: str) -> str:
        links = [
            link
            for link in self.decisions.setdefault("links", [])
            if (link.get("keep"), link.get("also")) != (keep, also)
        ]
        links.append({"keep": keep, "also": also, "state": state})
        self.decisions["links"] = links
        return self._commit("")

    def _remember(self, label: str) -> None:
        self._undo.append((label, copy.deepcopy(self.decisions)))
        del self._undo[:-UNDO_DEPTH]

    def _commit(self, message: str) -> str:
        self.model = self._rebuild()
        self._write()
        return message

    def _write(self) -> None:
        if self._path:
            save_decisions(self._path, self.decisions)

    def _rebuild(self) -> dict:
        model = copy.deepcopy(self._pristine)
        model["entities"] = apply_decisions(model["entities"], self.decisions)
        model["glosses"] = {
            name: gloss for name, gloss in (self.decisions.get("glosses") or {}).items()
        }
        model["warn"] = warning_map(
            self.decisions.get("warnings") or [], model["chapters"], spoil=model.get("spoil")
        )
        return model

    @property
    def saves_to(self) -> str:
        return self._path or ""
