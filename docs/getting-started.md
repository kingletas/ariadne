# Getting started

## Install it

```bash
sudo apt install ./ariadne_*_all.deb
```

Or from a clone:

```bash
make venv && make install
```

Then check the window can open:

```bash
ariadne --doctor
```

If it cannot, that command prints the packages to install. **Nothing else is blocked by them** — pages and the whole command line work without the toolkit.

## Open a book

```bash
ariadne ~/Books/moby-dick.epub --app
```

Ariadne reads the file, finds who and what appears in which chapter, and opens a window. **Drag the bookmark to the chapter you are on.** Everything in the window is now clipped to that point, and nothing later exists to it.

**It takes an epub, a docx, a folder of Markdown, or a plain text file you already own.** It never downloads a book and has no library of its own.

## What to do first

**Move the bookmark to where you actually are.** That is the whole interface — every view is built from it, and it is remembered in a file beside the book, so it is still there tomorrow.

**Open `About this book` once, at the start.** Cast size, how fast the names arrive against a thousand-book corpus, whether it is told in the first person, and whether one character holds it. It is the only thing here about the whole book, and it is structure rather than story, which is why it can be.

**Then leave it shut and read.**

## When you lose track of somebody

Click **Away a while**. It shows people who have been gone unusually long *for them* and long enough in reading time to have lost the thread — not everybody you have not seen lately, which would be most of the book.

Each card says where you last met them and **who was there at the time**, which is usually the hook that brings it back.

## When two names might be one person

Ariadne will show you `Prince Andrew`, `Prince Andrew Bolkónski` and `Andrew` as three people, because it cannot prove they are one.

Open any of them and it asks. **Merge names** folds them together everywhere; **Keep separate** stops it asking again. Both are undoable, and both are written to a plain file beside the book.

**It will never do this on its own.** Two mechanical ways of guessing were tested over six novels and both failed — and in some books the identity is the plot.

## Where the book has been

**Where you've been** draws one band per setting, chapters left to right, in the order the book arrived at them. Reading down the list is reading the journey.

Every row starts as a proposal, because the measure behind it is right about four times in five — *Moby Dick* is a whale, not a place. Keep or strike each one and the map becomes yours.

## Warning yourself about a chapter

```bash
ariadne book.epub --warn "24=someone does not make it through this chapter"
```

At chapter 23 the reader says **something is coming** and keeps what it says folded shut until you open it.

**Ariadne detects nothing.** A false positive costs somebody a book they would have been fine with, so the warning is yours, and it is a file you can hand to a friend reading the same book.

## What it will not do

```bash
ariadne --refusals
```

Eight things it could plausibly be asked for and does not do, each with the measurement or the citation that settles it. It is worth reading before asking for a feature.

## Sending somebody a page

```bash
ariadne ~/Books/moby-dick.epub -o moby-dick.html
```

One self-contained HTML file. No install, no account, no network. **It holds no text from the book** — names, counts and chapter numbers only — so it is derived data about a book rather than a copy of one.

That is the version to put on a phone.
