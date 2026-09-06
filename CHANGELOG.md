# Changelog

All notable changes to this project are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] — 2026-09-06

The first one.

Ariadne reads a book you already own and keeps track of who is in it. Set the bookmark to the chapter you are on, and that is all it shows you: the people you have met, the ones you have not seen in a while, who tends to turn up with whom, and where the book has been. It is not hiding the rest. It never had it.

There are two ways to use it. It can write a single HTML file you can email to someone, which works offline and holds no text from the book, only names and chapter numbers. Or it opens a window, and that is where you can tell it that Prince Andrew and Prince Andrew Bolkónski are one man.

It will not guess at that on its own. It also will not tell you who is speaking a line, score a book, or decide whether something was written by a machine. `ariadne --refusals` gives the reason for each, with the numbers behind it.

Of the 59 books tried so far it handles 48. The other 11 it turns down and says why, usually because it cannot work out where the chapters start. When it compares your book to others, the comparison comes from a thousand Gutenberg texts; `ariadne --corpus` shows the working.

Rough edges: it is convinced Moby Dick is a place until you tell it otherwise, and nobody has read a whole book with it yet.
