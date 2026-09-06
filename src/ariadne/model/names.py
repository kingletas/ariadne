import re
from collections import Counter

# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------

# Unicode throughout. An ASCII [A-Z][a-z]+ truncates an accented name at the
# accent, and the truncated stems then MERGE distinct people -- Kutuzov with
# Kutaysov, Boris with the battlefield Borodino.
UPPER = "A-ZÀ-ÖØ-Þ"


LOWER = "a-zß-öø-ÿ"


WORD = "[%s][%s'’-]+" % (UPPER, LOWER)


RUN = re.compile(r"\b(%s(?:\s+%s)*)" % (WORD, WORD))


# An opening quote abuts the word it precedes -- `"Just tell me` has no space
# in it -- so a rule that requires whitespace after the punctuation cannot see
# the commonest sentence start there is in dialogue. The quote class below is
# therefore matched zero-width, and it is an added alternative rather than a
# replacement, so it can only ever classify more positions as sentence starts.
#
# Measured over eight novels: it drops 28 to 73 candidates per book -- Ach,
# Halloa, Thank God, He-he-he, To-morrow, Just, Excuse, Quite -- and loses no
# name from a hand-checked list of twenty-two real characters and places.
SENT_START = re.compile(r"(?:^|[.!?\"”’]\s+|[“\"‘]|\n)\s*(%s)" % WORD)


TITLES = {
    "Mr",
    "Mrs",
    "Ms",
    "Miss",
    "Dr",
    "Sir",
    "Lady",
    "Lord",
    "Prince",
    "Princess",
    "Count",
    "Countess",
    "Duke",
    "Duchess",
    "King",
    "Queen",
    "Emperor",
    "Empress",
    "General",
    "Colonel",
    "Captain",
    "Major",
    "Doctor",
    "Professor",
    "Madame",
    "Monsieur",
    "Madam",
    "Saint",
    "Father",
    "Mother",
    "Uncle",
    "Aunt",
    "Baron",
    "Duc",
    # Non-English honorifics reach an English text through translation
    # and through dialogue that keeps the original form.
    "Señor",
    "Señora",
    "Señorita",
    "Herr",
    "Frau",
    "Fräulein",
    "Signor",
    "Signora",
    "Don",
    "Doña",
    "Mademoiselle",
    "Mynheer",
}


STOP = {
    "I",
    "The",
    "A",
    "An",
    "And",
    "But",
    "He",
    "She",
    "They",
    "It",
    "We",
    "You",
    "There",
    "That",
    "This",
    "What",
    "When",
    "Where",
    "Why",
    "How",
    "Then",
    "Now",
    "Yes",
    "No",
    "Not",
    "So",
    "If",
    "As",
    "At",
    "In",
    "On",
    "Of",
    "For",
    "To",
    "His",
    "Her",
    "Their",
    "My",
    "Our",
    "Your",
    "Well",
    "Come",
    "Here",
    "Very",
    "Pray",
    "Let",
    "Have",
    "One",
    "Two",
    "All",
    "Chapter",
    "Book",
    "Part",
    "Illustration",
    "Nobody",
    "Somebody",
    "Nothing",
    "Anything",
    "Because",
    "Never",
    "Still",
    "Perhaps",
    "Maybe",
    "Oh",
    "Ah",
    "God",
    "Good",
    "Sir",
    "Madam",
    "Yet",
    "Only",
    "Even",
    "Such",
    "Some",
    "Every",
    "Both",
    "After",
    "Before",
    "While",
    "Though",
    "Thy",
    "Thou",
    "Thee",
    "Thine",
    "Ye",
    "Nay",
    "Aye",
    "Alas",
    "Behold",
    # Sentence-openers and interjections. Each of these clears the
    # mid-sentence test in dialogue-heavy prose, because a line of speech
    # that begins "Indeed, sir --" puts the word after a comma rather than
    # after a full stop. They surfaced together in the writer report,
    # where a frequency-sorted list is not there to bury them.
    "Once",
    "Would",
    "Should",
    "Could",
    "Certainly",
    "Indeed",
    "However",
    "Nevertheless",
    "Moreover",
    "Meanwhile",
    "Presently",
    "Suddenly",
    "Besides",
    "Goodbye",
    "Good-bye",
    "Farewell",
    "Mum",
    "Ma'am",
    "Truly",
    "Surely",
    "Doubtless",
    "Anyhow",
    "Anyway",
    "Meantime",
    "Hush",
    "Hark",
    "Lo",
    "Oho",
    "Eh",
    "Hey",
    "Hallo",
    "Hello",
    # Expletives open a line of dialogue the way Alas and Behold do, and
    # they clear the mid-sentence test for the same reason. None has ever
    # been a character, and a cast list is the wrong place to meet one.
    "Damn",
    "Damned",
    "Shit",
    "Fuck",
    "Fucking",
    "Hell",
    "Christ",
    "Jesus",
    "Ach",
    "Bah",
    "Ugh",
    "Whoa",
    "Wow",
    "Aw",
    "Ow",
    "Huh",
    "Yeah",
    "Okay",
    "Nope",
    "Yep",
    "Hmm",
    "Hm",
    "Hi",
    "Upon",
    "Did",
    "Was",
    "Were",
    "Are",
    "Has",
    "Had",
    "Will",
    "Shall",
    "Take",
    "Give",
    "Look",
    "Listen",
    "Stay",
    "Wait",
    "Tell",
    "Since",
    "Until",
    "Unless",
    "Whether",
    "Whatever",
    "Whenever",
    "Who",
    "Whom",
    "Whose",
    "Which",
    "Whereas",
    "Wherever",
    "Neither",
    "Either",
    "Another",
    "Others",
    "Everyone",
    "Everybody",
    "Anyone",
    "Can",
    "May",
    "Must",
    "Might",
    "Ought",
    "Dare",
    "Need",
    "Does",
    "Am",
    "Been",
    "Being",
    "Having",
    "Doing",
    "Went",
    "Came",
}


# A contraction of a pronoun is not a name. The apostrophe is inside the word,
# so the capitalised-run pattern picks up I'm, I've, I'll and I'd.
CONTRACTION = re.compile(
    "^(?:I|We|He|She|They|You|It|That|There|What|Who|Let|Don|Can|Won|Ain"
    "|Didn|Doesn|Isn|Aren|Wasn|Weren|Couldn|Wouldn|Shouldn|Haven|Hasn"
    "|Hadn|Mustn|Needn|Shan|Here|Where|How|Why|Nothing|Something)"
    "[\u2019']"
    "(?:m|ve|ll|d|s|re|t)$",
    re.I,
)


def normalise(name):
    """One canonical spelling of a captured run.

    Collapses internal whitespace, because the run pattern allows any space
    between words and a name that wraps across a line would otherwise become a
    second entity -- "Prince Andrew" and "Prince\\nAndrew" indexed apart, each
    with its own counts, and listed as associates of each other. Also drops a
    possessive, so Ahab's and Ahab are one entity.
    """
    name = re.sub(r"\s+", " ", name).strip()
    return re.sub(r"[’']s$", "", name).strip()


def candidates(text, min_uses):
    """A capitalised run counts only if it appears mid-sentence at least twice,
    at least a quarter of its uses, and min_uses times overall. Sentence-initial
    capitals are grammar: He, Then, Because are not names."""
    starts = {m.start(1) for m in SENT_START.finditer(text)}
    total, mid = Counter(), Counter()
    for m in RUN.finditer(text):
        name = normalise(m.group(1))
        if not name or name in STOP or len(name) < 3:
            continue
        if CONTRACTION.match(name):
            continue
        head = name.split(" ")[0]
        # A bare honorific is not a person. "Prince Andrew" is.
        if name in TITLES:
            continue
        if head in TITLES and len(name.split()) == 1:
            continue
        total[name] += 1
        if m.start(1) not in starts:
            mid[name] += 1
    out = []
    for name, n in total.items():
        if n < min_uses or mid[name] < 2 or mid[name] / n < 0.25:
            continue
        out.append(name)
    return set(out)
