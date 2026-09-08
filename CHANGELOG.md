# Changelog

All notable changes to this project are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Light, dark or the system's choice, from the menu.** It followed the desktop's setting and there was no way to say otherwise; night is when people read, and a reader whose desktop is light should not have to change the desktop to read in the dark. The choice is remembered beside the book store, because a theme belongs to the person rather than to what they are reading.
- **Illustrations, if the book has any.** A folder beside the book — `the-book.epub.illustrations/` — with a `plates.tsv` saying which chapter each picture may be seen from. Nothing is generated and nothing is inferred: Ariadne decides *when* a picture already drawn may be shown, which is the question it is built to answer. The pictures are marks on the same axis as everything else, so you can see where the book is illustrated and where it is bare, and a picture past your bookmark is not drawn. A Pictures view appears only when there is a folder to show.
- The manifest is a manifest rather than a filename convention on purpose. `ch12-vael.png` breaks silently the day a chapter is inserted. Every way this one can be wrong — a missing file, a chapter outside the book, a plate listed twice, a path reaching out of the folder — is a named refusal.
- The chapter a picture may be seen *from* is not the chapter it illustrates. A drawing of somebody at a place they have not reached is a spoiler filed under the wrong number, and only the person who drew it knows the difference.

- `--inspect` now answers for the illustrations folder too, including refusing on a manifest it cannot trust. Reading the book and then refusing an hour later is two answers to one question.

### Changed

- **Rulings are no longer kept next to the book.** They live in `~/.local/share/ariadne/books/`, one file per book, because books live where their owner keeps them and that is often somewhere nothing can be written. `ariadne --doctor` prints the path.
- **A book is identified by its contents rather than its path or its name.** Move your library, rename a file, copy it to another disk, and the rulings follow it. Five spellings of one book — a series index, a year, a `RETAIL` tag, different case — are one file. The readable half of the name comes from the book's own title, normalised, and keeps the alphabet it was written in. A `.ariadne.json` already beside a book is read once and moved into the store; nothing is written beside a book again. `--decisions PATH` still overrides.

- **`ariadne --doctor` says when more than one Ariadne is installed**, names them, and says which one a launch reaches. They all answer to one application id, so a running copy of any of them takes the launch of any other and the window that opens is whichever was already there. `make install` says the same thing when it puts a wrapper beside a packaged copy. An app that ships an installation does not also keep a wrapper in `~/bin`.

### Fixed

- **A book Ariadne cannot write beside lost every ruling silently, and the header said it had saved them.** Found on a real book opened from a removable drive through the Flatpak file portal, which grants the one file you picked and not the directory around it. Every bookmark move wrote a temporary file whose rename failed; the error went into a signal handler that prints and carries on; the header went on saying "Saved locally" for an hour of reading. It is now asked once, up front, before anything is relied on — and the header says **Cannot save**, with the reason, and says it out loud once.
- **Changing the theme left the drawn strips in the old palette.** The stylesheet reloaded and the cast strips, place bands and pace lines kept the colours they were last painted with until something else happened to redraw them. They are repainted now — and that was true of a system theme change too, not just the new switch.
- **A chapter mark had a floor and no ceiling.** A long book was stopped from smearing into a solid bar and a short one was not stopped from drawing slabs: Divergent's 41 chapters put a 24px block on each, so "in every chapter" read as a progress bar rather than a presence. Both ends are the axis's answer now, so the cast strips and the place bands cannot disagree about it.

### Changed

- The bookmark is the chapter axis. It was a panel under the header with its own scale; it is now a strip at the top of the content column, and every chapter-indexed thing below it — cast strips, place bands, pace lines — is drawn to the same 1-to-the-book's-length scale. A line dropped through your position lands on the same chapter on all of them.
- Cast strips and place bands span the whole book rather than the part you have read, so a strip shows how much book is left as well as where somebody has been.
- Five views down the side instead of eight in three groups. Everyone, people, places and away-a-while were four filters of one list, so they are now chips across the top of the cast.
- About this book moved out of the content flow and behind the menu, where it has room to be read. What changed since your bookmark, and the note after a ruling, are toasts.
- New palette and type: Manrope in the chrome, Literata for names and headings. Both ship with the application under the SIL Open Font License.

### Fixed

- The cast strips were drawn in light-mode colours in dark mode. They were never told which mode the window was in.
- A card strip's scale ran 1 to your bookmark while the scale above it ran 1 to the book's length, so at chapter 180 of 365 the middle of a strip was chapter 90 and the middle of the scale was chapter 182.
- Keeping a place and merely proposing one were told apart by colour alone. A kept band is now full height and a proposal is half of one.
- `make smoke` reported success while taking no screenshots at all when an installed copy held the application's bus name.

## [0.1.0] — 2026-09-06

The first one.

Ariadne reads a book you already own and keeps track of who is in it. Set the bookmark to the chapter you are on, and that is all it shows you: the people you have met, the ones you have not seen in a while, who tends to turn up with whom, and where the book has been. It is not hiding the rest. It never had it.

There are two ways to use it. It can write a single HTML file you can email to someone, which works offline and holds no text from the book, only names and chapter numbers. Or it opens a window, and that is where you can tell it that Prince Andrew and Prince Andrew Bolkónski are one man.

It will not guess at that on its own. It also will not tell you who is speaking a line, score a book, or decide whether something was written by a machine. `ariadne --refusals` gives the reason for each, with the numbers behind it.

Of the 59 books tried so far it handles 48. The other 11 it turns down and says why, usually because it cannot work out where the chapters start. When it compares your book to others, the comparison comes from a thousand Gutenberg texts; `ariadne --corpus` shows the working.

Rough edges: it is convinced Moby Dick is a place until you tell it otherwise, and nobody has read a whole book with it yet.
