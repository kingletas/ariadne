import re
import sys

from ..ai.client import DEFAULT_MODEL, _thinking_for
from ..core.refusal import Refusal

RELATION_SYSTEM = (
    "Extract stated relationships between named people, places and groups from "
    "the excerpt. Only relationships the text states or makes plain -- never "
    "inferred, never from anything you know about this book from elsewhere.\n\n"
    "Return one line per relationship, in the form:\n"
    "  NAME | CHAPTER | short clause\n\n"
    "CHAPTER is the number in the [chapter N] marker where the relationship is "
    "established. The clause is at most twelve words, describes the relationship "
    "only, and must not quote the book. Write it as a fact about who someone is, "
    "for example: brother to Elphin, or married to Charis, or rules Atlantis.\n\n"
    "Say nothing about events, plot or outcomes -- only who is who to whom. If "
    "the excerpt states no relationships, return nothing."
)


def extract_relations(chapters, upto, model=DEFAULT_MODEL, chunk=8):
    """Stated relationships, from the reader's own account, up to a position.

    Returns {name: [{"at": chapter_index, "text": clause}]}. Chapters are sent
    in batches so a long book does not arrive as one enormous prompt.
    """
    try:
        import anthropic
    except ImportError as exc:
        raise Refusal(
            "the anthropic package is not installed. `uv tool install anthropic` "
            "or `pip install anthropic`, then set ANTHROPIC_API_KEY or run "
            "`ant auth login`."
        ) from exc

    client = anthropic.Anthropic()
    out = {}
    for lo in range(0, upto + 1, chunk):
        hi = min(lo + chunk - 1, upto)
        excerpt = "\n\n".join("[chapter %d]\n%s" % (i + 1, chapters[i]) for i in range(lo, hi + 1))
        try:
            resp = client.messages.create(
                model=model,
                max_tokens=4000,
                system=RELATION_SYSTEM,
                **_thinking_for(model),
                messages=[{"role": "user", "content": excerpt}],
            )
        except TypeError as exc:
            raise Refusal(
                "no Anthropic credentials found. Set ANTHROPIC_API_KEY, or run "
                "`ant auth login`. Ariadne ships no key of its own: this runs on "
                "your account, and nothing here needs one except this command."
            ) from exc
        except anthropic.AuthenticationError as exc:
            raise Refusal(
                "your Anthropic credentials were rejected. Ariadne "
                "ships no key of its own -- this runs on your "
                "account."
            ) from exc
        except anthropic.APIStatusError as exc:
            raise Refusal(
                "the API returned %s on chapters %d-%d: %s"
                % (exc.status_code, lo + 1, hi + 1, str(exc)[:120])
            ) from exc
        if resp.stop_reason == "refusal":
            continue
        text = "\n".join(b.text for b in resp.content if b.type == "text")
        for line in text.splitlines():
            parts = [x.strip() for x in line.split("|")]
            if len(parts) != 3:
                continue
            name, chap, clause = parts
            try:
                at = int(re.sub(r"[^0-9]", "", chap)) - 1
            except ValueError:
                continue
            if not name or not clause or not (lo <= at <= hi):
                continue
            # Proposed, never asserted. This is the one thing here a model
            # decides, and three mechanical inferences already failed this
            # month -- a relation nobody has read is a claim, not a fact.
            out.setdefault(name, []).append({"at": at, "text": clause[:90], "state": "proposed"})
        print("  chapters %d-%d read" % (lo + 1, hi + 1), file=sys.stderr)
    return out
