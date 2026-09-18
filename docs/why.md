# Why Ariadne exists

**Because there is no safe place to look up who somebody is in a book you are halfway through.**

## The problem

You are three hundred pages into a long novel, a character walks into the room, and you have no idea who they are. Every place you could go to find out is written from a position further along than yours:

- A wiki article is written from the ending. The first sentence often contains the death.
- A character list on a retail page names the people who survive to be worth naming.
- Searching the name finds a forum thread about what they do in the last act.
- The blurb was never going to help. Measured over 113 fiction nominees from the 2025 Goodreads Choice Awards, **a synopsis names a median of two people.**

So the reader picks between staying lost and spoiling the book to stop being lost. A lot of them put the book down instead.

This is not a problem with difficult books or old ones. Over 53 novels measured whole, a book has introduced nineteen people by a tenth of the way in and finishes with sixty; across 48 books in two corpora, the heaviest decile opens with 37 to 61 named entities in chapter one. **Cast load is a property of the individual book, not of its era or its genre** — a 2021 bestseller opens with 48 named entities, and a 19th-century novel opens with 61.

## Why not a wiki, a fandom page or a character list

All three exist, all three are maintained by people who have finished the book, and none of them has any notion of where you are. The information is not wrong; it is **arriving in the wrong order**, and there is no setting that fixes that because the data was never captured with a position attached.

## Why not just take notes

That is the existing answer and it works. It also means doing clerical work during the thing you took up to stop doing clerical work, and it fails precisely when you need it — the character you did not write down is the one you do not recognise four hundred pages later.

## What the reason decided

Everything structural in this project falls out of one sentence: *nothing may appear that the reader has not read.*

- **The spoiler rule is structural, not a filter.** Every view is built from the chapters behind the bookmark. Later chapters are not in the page waiting to be revealed by a bug, because they were never assembled. A test asserts zero leaks on every commit.
- **It reads your copy, and does not own it.** Point it at a book you already have. The file is read and never copied.
- **The output holds no book text.** Only names, counts and chapter numbers — the longest string in a generated payload is the title. That makes the page derived data about a book rather than a copy of one.
- **Interpretation is a suggestion, never an assertion.** Deciding that two names are the same person is the one thing a rule cannot do reliably. It is offered to the reader to confirm, and it is convinced that Moby Dick is a place until you tell it otherwise.
- **It does not grade anything.** An earlier line of this work scored prose quality. It was cut: across 58 books, nothing scored above a D on any correct segmentation, which is a measurement saying the scale is wrong rather than that the books are.

## Where the name came from

Ariadne gave Theseus the thread so he could find his way back out of the labyrinth. She did not give him a map of it.
