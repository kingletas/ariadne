import re

# A play has no narration and no quotation marks: every line of speech is
# introduced by a speaker label. Detected separately, because the quotation
# rule cannot see dialogue here and would refuse an entire form.
SPEAKER = re.compile(r"^[ \t]*([A-Z][A-Za-z' .]{1,24})[.:]\s", re.M)


ACT_SCENE = re.compile(r"^[ \t]*(ACT|SCENE)\s+[IVXLC\d]+.*$", re.M | re.I)


def looks_like_a_play(text):
    """Speaker labels on many lines, and act or scene divisions."""
    sample = text[:200000]
    labels = len(SPEAKER.findall(sample))
    lines = max(1, sample.count("\n"))
    return labels / lines > 0.12 and len(ACT_SCENE.findall(text)) >= 3
