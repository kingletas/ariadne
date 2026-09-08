# Changelog

All notable changes to this project are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
