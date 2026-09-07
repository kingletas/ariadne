# From nothing to reading without being lost

By the end of this you'll have Ariadne installed, pointed at a book you own, and showing you that book's cast as it stands at your bookmark — with nothing past it. It takes about ten minutes.

You don't need to be technical. Most of this is one install and one command.

## Contents

- [The problem this is for](#the-problem-this-is-for)
- [Step 1: install it](#step-1-install-it)
- [Step 2: check the window can open](#step-2-check-the-window-can-open)
- [Step 3: ask about a book before you start it](#step-3-ask-about-a-book-before-you-start-it)
- [Step 4: make a page](#step-4-make-a-page)
- [Step 5: open the reader, and correct it](#step-5-open-the-reader-and-correct-it)
- [Warning yourself about a chapter](#warning-yourself-about-a-chapter)
- [What it won't do, and why](#what-it-wont-do-and-why)
- [Where the numbers come from](#where-the-numbers-come-from)
- [Where to go next](#where-to-go-next)

## The problem this is for

You're three hundred pages into a long novel, somebody walks into the room, and you have no idea who they are.

Everywhere you could look will tell you something you haven't reached. A wiki article is written from the ending. A character list on a retail page names whoever survives long enough to be worth naming. Searching the name finds a forum thread about the last act. So you read on and stay lost, or you spoil the book to stop being lost — and plenty of people just put it down.

**Ariadne builds the book's cast from your own copy and shows you nothing past your bookmark.** Move the bookmark to chapter 40 and you see the book as it stands at chapter 40: who you've met, who you haven't seen in a while, who tends to be in the room with whom, where the book has been. Chapter 41 doesn't exist in the view.

**That's structural, not a filter.** Every view is built only from the chapters behind your position, so there's no later data sitting in the page waiting for a bug to reveal it. A test asserts it on every commit.

## Step 1: install it

Three routes. **If you're on Ubuntu and not sure, take the `.deb`.**

**From a release** — the `.deb` is on the [releases page](https://github.com/kingletas/ariadne/releases):

```bash
sudo apt install ./ariadne_*_all.deb
```

**As a Flatpak** — the bundle sits beside the `.deb`:

```bash
flatpak install ./ariadne_0.1.0.flatpak
```

It asks for your home directory, because the file holding your corrections goes next to the book and the file portal only grants the one file you picked. **It asks for no network at all.**

**From a clone:**

```bash
make venv && make install
```

This puts `ariadne` on your `PATH` and an entry in your applications menu.

> [!WARNING]
> **Pick one route, not two.** `make install` puts a wrapper in `~/bin`, which on most setups comes before `/usr/bin` — so with both installed, `ariadne` is the wrapper and the packaged binary is never reached. `which -a ariadne` settles it.

You need **Python 3.12 or newer and nothing else**. The engine uses only the standard library, and a test proves it by importing every engine module with the toolkit blocked.

## Step 2: check the window can open

The GTK pieces come from your system rather than from pip, so they might not be there.

```bash
ariadne --doctor
```

```text
ariadne: the desktop reader can open here.
  GTK 4.14  ·  libadwaita 1.5  ·  PyGObject 3.48.2
```

If something's missing it says which, and gives you the command to install it. **Everything except the window works without them** — pages, `--inspect`, `--about`, the whole command line.

## Step 3: ask about a book before you start it

Point it at a book you own. A DRM-free epub, a Word document, a folder of Markdown, or plain text.

```bash
ariadne ~/Books/some-book.epub --about
```

```text
The Gate and the Yard
6 chapters, 12,318 words, about 1 hours at 250 words a minute

HOW MANY PEOPLE YOU WILL BE HOLDING
  6 names in the whole book
  by a tenth in          33% of them — about 2 people  (middle half of the corpus is 35-57%, this is below)
  by a quarter in        50% of them — about 3 people  (middle half of the corpus is 57-77%, this is below)
  by halfway             83% of them — about 5 people  (middle half of the corpus is 79-93%, this is inside)
  by three quarters in  100% of them — about 6 people  (middle half of the corpus is 92-100%, this is inside)
```

That's what you're in for, before you start: how many people you'll be holding in your head, and how early the book expects you to have met them. **A number outside a band is a difference, never a fault** — some books introduce everyone at once on purpose.

To see what it found without writing anything:

```bash
ariadne ~/Books/some-book.epub --inspect
```

```text
title        The Gate and the Yard
chapters     6
words        12318
segmented    epub spine (>= 600 words)
quotes       double
entities     6 (>= 5 uses)
commonest    Alda, Bertrand, Cosima, Dmitri, Evremonde, Fyodor
```

## Step 4: make a page

```bash
ariadne ~/Books/some-book.epub -o some-book.html
```

```text
ariadne: The Gate and the Yard -- 6 chapters, 6 names -> page.html
```

About a second, even for War and Peace.

What comes out is **one HTML file**. No install, no account, nothing to sign up for, and it works offline. **It contains no text from the book at all** — names, counts and chapter numbers only — so you can send it to a friend reading the same thing without sending them the book.

## Step 5: open the reader, and correct it

```bash
ariadne ~/Books/some-book.epub --app
```

Or open Ariadne from your applications menu and pick a book.

Down the left: everyone you've met, split into people and places. A map of who shares chapters with whom. Where the book has been. A pace chart. Click any name and a panel opens with everything known about them so far, and nothing after.

**The reader is also where you fix what it got wrong**, and it will get things wrong:

- When it lists *Prince Andrew* and *Prince Andrew Bolkónski* as two people, click one and tell it they're the same man.
- Each place it found started as a guess. The guess is right about four times in five, so you keep or bin each one. **Moby Dick is a whale.**

Your corrections, merges and warnings go into a small file next to the book, and there are fifty steps of undo.

**It doesn't guess at any of this on your behalf.** Two names might be one person or they might be two, and in some books that's the plot.

## Warning yourself about a chapter

```bash
ariadne book.epub --warn "24=someone does not make it through this chapter"
```

At chapter 23 it says *something is coming*, and keeps your text folded shut until you open it.

**Ariadne finds none of these itself.** Tagging books by what happens in them is a fight it has no business joining, and a false positive costs somebody a book they'd have been fine with. The warning is yours, it lives in the file beside the book, and you can hand it to somebody else reading the same one.

## What it won't do, and why

Of 59 books tried, it handles 48. **The other 11 it turns down and tells you why** — usually because it can't work out where the chapters start.

It also won't tell you who's speaking a line of dialogue, decide whether something was written by a machine, guess an author by comparing against others, or give a book a score.

```bash
ariadne --refusals
```

Each refusal has a reason and a number behind it. Attributing dialogue, for instance, works on 6.6% of lines — **which isn't a rough answer, it's a wrong one nine times out of ten.**

## Where the numbers come from

```bash
ariadne --corpus
```

```text
  selection                  1000 Gutenberg texts, stratified
  strata                     english/romance/germanic/slavic x 5 eras x 6 genres
  segmented into chapters    786 books
  measured for prose shape   786 books
```

Every band in `--about` comes from that, measured rather than chosen.

> [!NOTE]
> **Early days.** It works on the sixteen books in its own list and on any DRM-free epub you own. It's also convinced that Moby Dick is a place until you tell it otherwise, and nobody has read a whole book with it yet.

## Where to go next

- [README](../README.md) — what it is, in one page
- [CONTRIBUTING.md](../CONTRIBUTING.md) — the shape a change should arrive in
- [SECURITY.md](../SECURITY.md) — the model, and where to report something
