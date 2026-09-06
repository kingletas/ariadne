# ---------------------------------------------------------------------------
# What this refuses to do
# ---------------------------------------------------------------------------
#
# Each entry is a thing ariadne could plausibly be asked for and does not do,
# with the measurement or the citation that settles it. This is a register
# rather than a paragraph so `--refusals` can print it and so a new refusal
# has somewhere to go with its evidence attached.
#
# A refusal without a number is an opinion. Every row here carries one.

REFUSALS = [
    {
        "name": "Say who is speaking a line of dialogue",
        "why": "Measured, and it does not work.",
        "evidence": [
            "44 books drawn at random from the corpus. About 54% of quoted lines",
            "carry a speech verb nearby, 10% of those tags are pronouns, and only",
            "6.6% name a character the model already knows. Half of all dialogue in",
            "a novel is untagged, because in a back-and-forth only the first line",
            "says who is talking.",
            "",
            "The spread is the sharper problem. The Castle of Otranto reaches 34.8%;",
            "The Turn of the Screw manages 0.3%, because a first-person narrator",
            "almost never names a speaker. One method cannot serve both.",
            "",
            "A partial answer here is not a rough answer. It leans toward characters",
            "whose names get spelled out rather than pronouned -- which is away from",
            "whoever the narrator is closest to.",
        ],
    },
    {
        "name": "Decide whether text was written by a machine",
        "why": "Nobody's detector works -- including the one built by the\n   people who built the generator.",
        "evidence": [
            "OpenAI withdrew its own classifier in July 2023. It identified 26% of",
            "AI-written text correctly and flagged 9% of human writing as having",
            "been machine-written. Tools still being sold report no better, and are",
            "worst on writers whose first language is not English, whose plainer",
            "sentences read to a detector as generated.",
            "",
            "The harm from a false positive here lands on a person being accused,",
            "and there is no appeal against a number with no working shown.",
        ],
    },
    {
        "name": "Match a book against other authors to say who wrote it",
        "why": "It works. That is the objection.",
        "evidence": [
            "Stylometry identified J.K. Rowling behind the Robert Galbraith",
            "pseudonym in 2013, and the same method identifies a pseudonymous",
            "writer who has reasons -- a concern raised in the security literature",
            "since 2000 and still live.",
            "",
            "The version that is safe already exists here: --compare asks whether a",
            "revision moved the voice of THIS book against ITSELF. Comparing across",
            "authors is a different tool with a different victim.",
        ],
    },
    {
        "name": "Give a book a reading level, a grade or a score",
        "why": "A number comparable against a threshold is an instrument for "
        "removing books, whatever it was built for.",
        "evidence": [
            "PEN America recorded 4,235 challenges in 2025, the second-highest",
            "count on record, and age-appropriateness is the commonest stated",
            "reason a librarian declines to buy a book.",
            "",
            "The shape is reported instead and always will be: sentence length,",
            "its variation, vocabulary turnover. Those describe the prose without",
            "collapsing to a number somebody can put in a policy.",
        ],
    },
    {
        "name": "Grade a book, or a revision of one, as better or worse",
        "why": "The measurements cannot carry a direction.",
        "evidence": [
            "Across 58 books in three corpora not one scored above D on the bands",
            "this tool reports, and adverb density spread 13.6x among books that",
            "all succeeded. A book whose vocabulary narrows is narrower, not worse.",
            "",
            "--compare says whether the prose kept its shape. A pass that fixed",
            "everything and a pass that broke everything read identically there.",
        ],
    },
    {
        "name": "Detect what is in a book that a reader might want warning of",
        "why": "Detection would import a fight it cannot win, and a false positive "
        "costs somebody a book.",
        "evidence": [
            "StoryGraph reworked its trigger-warning section after readers found",
            "books by marginalised authors were tagged disproportionately, and",
            "because a tag for a theme reads to a browser as an accusation about",
            "the book.",
            "",
            "So ariadne detects nothing and carries what you write. --warn puts a",
            "warning on a chapter; the page shows that one is coming without",
            "showing what it says until you ask. Every other product in this space",
            "gives away the answer as the price of the warning.",
        ],
    },
    {
        "name": "Name a narrator who is never spoken to",
        "why": "The one signal left is a phrase, and it does not survive a corpus.",
        "evidence": [
            "The vocative rule finds a narrator by other people saying their",
            "name. Ishmael is named nineteen times in the whole of Moby-Dick and",
            "three of those are in dialogue, so there is nothing there to find.",
            "",
            "What such a narrator does instead is introduce themselves once, in",
            "narration -- a construction rather than a statistic. Against the one",
            "book that motivated it, it worked: the pattern fires 2% into",
            "Moby-Dick and returns Ishmael.",
            "",
            "Against 98 first-person books it fired 23 times and agreed with the",
            "vocative rule ZERO times. Where both fired they disagreed. Several",
            "hits are plays, where dialogue carries no quotation marks, so a rule",
            "that trusts narration reads the whole text as narration and picks up",
            "any character introducing themselves aloud. One returned Appetite.",
            "",
            "A rule validated on the single case that motivated it is not",
            "validated. This is the second time that shape has appeared here in a",
            "day, so a narrator who left no trace stays unclassified.",
        ],
    },
    {
        "name": "Notice that a file starts in the middle of a book",
        "why": "It cannot, and a tried detector failed on the one case with a known answer.",
        "evidence": [
            "Everything here assumes the file begins where the book begins. Given",
            "chapters 340 to 450 of a novel, it reports a first chapter, an",
            "introduction curve and a first-met chapter for every name -- all",
            "confident, all plausible, and all wrong by 339 chapters.",
            "",
            "The obvious detector is front-loading: a fragment opens on people",
            "already established, so chapter one should introduce a crowd. Tested",
            "by cutting fourteen complete novels to their last third, that looked",
            "good -- whole books put a median 8% of the cast in chapter one and",
            "never more than 23%, the cut tails a median 26%.",
            "",
            "Against real data it inverted. A known fragment scored 17% and would",
            "not have been flagged; a complete novel scored 27% and would have",
            "been. The synthetic test was built from a corpus that front-loads and",
            "the real case was a web serial that does not.",
            "",
            "So there is no warning. Check that the file starts at chapter one",
            "yourself, because nothing here can.",
        ],
    },
    {
        "name": "Send your book anywhere, except through two named flags",
        "why": "The local half never copies the file.",
        "evidence": [
            "--explain and --relations post chapter text to the Anthropic API on",
            "the reader's own account. Nothing else here leaves the machine: the",
            "page, every report and all the counting read the file and copy none",
            "of it.",
            "",
            "The page itself carries names, counts and chapter numbers only.",
            "Checked on adult fiction, where it matters most: the longest string",
            "in the payload was the thirty-character title.",
        ],
    },
    {
        "name": "Guess when it cannot tell what it is looking at",
        "why": "Every failure this tooling has hit was a confident answer in a "
        "situation nobody had shown it.",
        "evidence": [
            "0.0% dialogue reported on thirteen bestsellers. A clean canon report",
            "over an index it could not read. Three Russian characters merged into",
            "one name.",
            "",
            "It now refuses by name on no chapter convention, fewer than three",
            "segments, and no quotation convention. A named refusal is cheap.",
        ],
    },
    {
        "name": "Assert that two names are one person",
        "why": "Two mechanical signals were tested and both failed.",
        "evidence": [
            "Adjacency finds true aliases 8.9% of the time against 79.5% for the",
            "two halves of one name. Co-occurrence is worse than useless: an alias",
            "pair shares chapters BY CONSTRUCTION, so aliases score HIGHER on it",
            "than unrelated characters do.",
            "",
            "Containment is proposed because it can be proved. Everything else is",
            "the reader's, and in some books the identity is the plot.",
        ],
    },
]


def print_refusals():
    """The register, and the four failures it is built out of."""
    print("WHAT ARIADNE WILL NOT DO, AND WHAT SETTLES EACH ONE\n")
    for i, r in enumerate(REFUSALS, 1):
        print("%d. %s" % (i, r["name"]))
        print("   %s" % r["why"])
        print()
        for line in r["evidence"]:
            print("   %s" % line if line else "")
        print()
    print("THE PATTERN ACROSS FOUR OF THESE")
    print("Adjacency for aliases, co-occurrence shape for aliases, frequency for")
    print("invented vocabulary, and speech tags for speakers. Four mechanical")
    print("shortcuts tried, four failed. What has worked every time is the other")
    print("move: propose, let the reader confirm, remember the answer.")
    print()
    print("So the line is drawn by measurement rather than by taste. Mechanical")
    print("where the question is arithmetic -- who appears in which chapter, how")
    print("long a chapter is, what changed between two drafts. Reader-confirmed")
    print("wherever being wrong would mean being wrong about a person.")
