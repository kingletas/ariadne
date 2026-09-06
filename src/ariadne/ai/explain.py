from ..ai.client import DEFAULT_MODEL, _thinking_for
from ..core.refusal import Refusal

# ---------------------------------------------------------------------------
# Asking about a passage
# ---------------------------------------------------------------------------
#
# THIS IS THE ONE THING HERE THAT LEAVES THE MACHINE, AND IT USES THE READER'S
# OWN ACCOUNT. Everything else in this tool is arithmetic over a local file and
# needs no network. An explanation needs a model, so the text goes to Anthropic
# under the reader's own key -- not through any service of ours, with no copy
# kept here, and only when they ask for it by running this command.
#
# Two rules make it safe rather than merely private:
#
#   Bounded by position. Only chapters at or before where the reader is are
#   ever sent, so the model cannot answer from a page they have not read. The
#   spoiler rule that governs the page governs the prompt.
#
#   Bounded in size. A book can be half a million words. Sending all of it
#   would be slow, expensive and worse -- so the window is the chapter the
#   reader is in plus a little before it, and the tool says how much it sent.
#
# The page never does this. A shareable HTML file must not carry an API key,
# and it holds no book text to ask about in any case.

EXPLAIN_SYSTEM = (
    "You are helping someone who is part-way through a book. They can see only "
    "what they have read, and so can you: the excerpt below ends exactly where "
    "they are.\n\n"
    "Answer only from the excerpt. If the answer is not in it, say so plainly "
    "and say what you would need -- never fill the gap from anything you may "
    "know about this book from elsewhere, because that is the reader's whole "
    "reason for asking here rather than searching.\n\n"
    "Do not speculate about what happens next, do not foreshadow, and do not "
    "hint that something is significant because of what it leads to. Be brief "
    "and concrete."
)


def explain_passage(chapters, question, upto, window=3, model=DEFAULT_MODEL):
    """Ask the reader's own Claude account about the book so far.

    Returns (answer, chapters_sent, words_sent). Raises Refusal with a plain
    reason when the SDK or a credential is missing, because a missing key is a
    setup problem the reader can fix and not a fault in the book.
    """
    try:
        import anthropic
    except ImportError as exc:
        raise Refusal(
            "the anthropic package is not installed. `uv tool install anthropic` "
            "or `pip install anthropic`, then set ANTHROPIC_API_KEY or run "
            "`ant auth login`. This is the only command here that needs either."
        ) from exc

    lo = max(0, upto - window + 1)
    excerpt = "\n\n".join("[chapter %d]\n%s" % (i + 1, chapters[i]) for i in range(lo, upto + 1))
    words = len(excerpt.split())

    client = anthropic.Anthropic()

    try:
        response = client.messages.create(
            model=model,
            max_tokens=4000,
            system=EXPLAIN_SYSTEM,
            **_thinking_for(model),
            messages=[
                {
                    "role": "user",
                    "content": "%s\n\n---\n\nThe reader has reached the end of chapter %d. "
                    "Here is what they have just read:\n\n%s" % (question, upto + 1, excerpt),
                }
            ],
        )
    except TypeError as exc:
        raise Refusal(
            "no Anthropic credentials found. Set ANTHROPIC_API_KEY, or run "
            "`ant auth login`. Ariadne ships no key of its own: this runs on "
            "your account, and nothing here needs one except this command."
        ) from exc
    except anthropic.AuthenticationError as exc:
        raise Refusal(
            "your Anthropic credentials were rejected. Check ANTHROPIC_API_KEY, "
            "or run `ant auth login`. Ariadne never ships a key of its own -- "
            "this runs on your account."
        ) from exc
    except anthropic.APIStatusError as exc:
        raise Refusal("the API returned %s: %s" % (exc.status_code, str(exc)[:160])) from exc
    except anthropic.APIConnectionError as exc:
        raise Refusal("could not reach the API: %s" % str(exc)[:160]) from exc

    if response.stop_reason == "refusal":
        raise Refusal("the model declined to answer this one.")
    text = "\n".join(b.text for b in response.content if b.type == "text")
    return text.strip(), (upto - lo + 1), words
