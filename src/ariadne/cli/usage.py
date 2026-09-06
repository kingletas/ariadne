"""What `ariadne -h` prints.

This was the comment block at the top of the single-file tool, which `-h`
reprinted by reading its own source. A package has no such block, and a
command that cannot describe itself at the prompt is worse than one that
never tried, so the text lives here as the one copy.
"""

USAGE = """\

ariadne — build a spoiler-safe reading companion page from a book file.

Reads an epub or a plain-text book, works out who and what is in it, and
writes ONE self-contained HTML file: a slider for where you are in the book,
and a cast list clipped to that point. Nothing you have not read is shown.

Usage:
    ariadne BOOK [-o OUT.html] [-t TITLE] [--min-uses N] [--json]
    ariadne BOOK --app              open the desktop reader
    ariadne BOOK --inspect          what was detected; write nothing
    ariadne --doctor                whether the desktop reader can open here
    ariadne --self-test             prove the spoiler invariant holds
    ariadne --refusals              what this will not do, and why
    ariadne --corpus                what every band it reports is made of
    ariadne -h                      this header

Everything below needs nothing but the file and this script:

    --find WORD                     chapters holding it, up to your position
    --position N | BOOK:CHAPTER     where you are; --position-from a KOReader file
    --note NAME=MEANING             write down what you understood; --notes lists them
    --warn N=TEXT                   warn yourself about chapter N, shown a chapter early
    --links / --accept / --reject   join two names for one person
    --compare OTHER                 what a revision changed, and whether the voice moved
    --writer                        the report for whoever is writing it
    --about                         what you are in for, before you start
    --overlap OTHER                 how much of this you already know
    --spoil                         drop the position bound entirely

These two need an Anthropic account of your own, and nothing else here does.
They are also the only two that send any of the book off this machine:

    --explain QUESTION              ask about the book so far
    --relations                     propose who is who to whom; --review to judge them

Flags:
    -o, --out PATH     where to write the page (default: <book>.html here)
    -t, --title TEXT   override the title read from the file
        --min-uses N   how often a name must appear to count (default 5)
        --inspect      report conventions and segmentation, write nothing
        --json         emit the model as JSON instead of a page
        --self-test    build every view of a fixture and check for leaks

Environment overrides:
    ARIADNE_MIN_USES   default for --min-uses

WHAT IT REFUSES TO DO, AND WHY THAT IS THE POINT
Every failure this tooling has hit across 58 books was a confident answer in
a situation nobody had shown it -- 0.0% dialogue on thirteen bestsellers, a
clean canon report over an index it could not read, three Russian characters
merged into one name. So this refuses, loudly and by name, when it cannot
tell what it is looking at: no chapter convention, fewer than three
segments, or no quotation convention. A named refusal is cheap. A plausible
wrong answer is what costs.

`--refusals` prints the full register with the measurement behind each one.
It will not name a speaker (6.6% of dialogue can be attributed), decide
whether text was machine-written (nobody's detector works), match a book
against other authors (it works, and that is the objection), or give a book
a score of any kind. Four mechanical shortcuts have been tried here and four
failed; what works is to propose and let the reader confirm.

ONE PANEL IS ABOUT THE WHOLE BOOK, AND SAYS SO
`--about`, and a folded panel on the page, answer the question a reader asks
before there is a position to bound it with: what am I in for. How many
people, how fast they arrive, whether it is narrated in the first person,
whether one character holds it, and which series it belongs to if the file
says. That is structure and never plot, so it can be read without learning
anything that happens -- and it is folded shut, because a reader who did not
ask should not be shown it.

It exists because a description does not say any of it. Over 113 fiction
nominees from the 2025 Goodreads Choice Awards a synopsis names a median of
two people; over 53 novels measured whole a book introduces nineteen by a
tenth of the way in and holds sixty. Seven of nineteen series entries mention
the series at all.

Narrative person is measured from narration with dialogue stripped, because
"I" inside speech is normal in any novel. Across eighteen books whose person
is not in doubt, first-person runs 30-74% and third-person 1-16%. It matters
because a first-person narrator is called "I" rather than by name, so the
lead measure is refused there rather than reporting Bessie as the lead of
Jane Eyre.

A SERIES IS READ IN BOOKS, NOT IN CHAPTER NUMBERS
Volumes are laid end to end, so every chapter index is across the whole run.
The page turns them back: `book 4, chapter 11` rather than `chapter 137`, a
`bk 5 . ch 1` position chip, a filter for names introduced in the volume in
hand, and a count of how many carried in from earlier books. Harry Potter is
919 names over seven volumes, and opening book five means holding 697.

`--overlap` points the same question sideways, at a neighbouring series
rather than an earlier volume. Measured: the Shadow Saga shares 33% of its
cast with the Ender Saga it retells, and 2% with Harry Potter.

WARNINGS COME FROM YOU, AND ARRIVE A CHAPTER EARLY
`--warn 24=...` puts a note on chapter 24. The page says something is coming
at chapter 23 and keeps what it says folded shut until the reader opens it.
Nothing is detected: a false positive would cost somebody a book, and tagging
by theme is a fight this tool has no business joining.

TWO FLAGS SEND BOOK TEXT OFF THIS MACHINE, AND ONLY TWO
`--explain` posts the chapters around your position to the Anthropic API,
and `--relations` posts them in chunks. Nothing else here does: the page,
every report and the whole local half read the file and never copy it.

That distinction is worth knowing before pointing this at anything private
or explicit. Names, counts and structure stay on the machine whatever the
book is; the two model-backed flags do not, and they are the reader's own
account being billed and their own provider's terms being accepted.

THE PAGE CONTAINS NO BOOK TEXT
Only names, counts and chapter numbers are written out. That is deliberate:
the page is derived data about a book rather than a copy of one, so it can be
shared and kept without redistributing anything. The book file is read and
never copied.

A FIRST-PERSON NARRATOR IS FOUND BY BEING SPOKEN TO
Nobody writes "Pip said" when Pip is telling the story, so a narrator scores
zero on the speech test and near zero on prepositions, and lands in unknown --
the protagonist, unclassified, at the top of the opening screen. What they do
have is being addressed: 94% of the uses of Pip's name sit inside quotation
marks, 93% of Jane's, 90% of Huck's.

That is not a person test on its own and was measured failing as one -- at the
same threshold it promotes England, France and every Highness in a costume
drama. It is applied only inside a book already detected as first person, and
then it finds Pip, Jane, Huck and Esther Summerson, misses Ishmael, and
changes exactly one name per book and none at all in eleven third-person
novels.

IT ASSUMES THE FILE STARTS WHERE THE BOOK STARTS
Given the back half of a novel it will report a first chapter and an
introduction curve for it, confidently and wrongly. A detector for this was
tried and failed on the one case whose answer was known -- see `--refusals`.
Check the file yourself.

THE SPOILER RULE IS STRUCTURAL, NOT A FILTER
Each entity carries the chapter it first appears in. A view at chapter N is
built from chapters 0..N only, so there is no path by which a later chapter
reaches it. `--self-test` builds every view of a fixture book and asserts
nothing leaks; it is the one property that must never regress.
"""
