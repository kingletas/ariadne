# Security

## What it reads

Ariadne opens a book file you point it at — an epub, a docx, a folder of Markdown, or plain text — and either writes an HTML page or opens a window. It makes no network request of any kind unless you use one of the two commands that need an account, and the page it produces makes none either.

## What it writes

Two things, and both are yours.

**The page**, wherever you asked for it. **The sidecar**, beside the book — a plain JSON file holding the rulings you have made: which names are one person, your notes, your warnings, which places are settings, and where you are. You can read it, edit it, delete it or hand it to somebody else, and removing Ariadne leaves it intact.

**It writes nothing else.** No configuration outside that file, no cache, no telemetry, no account.

## What the page contains, and what it doesn't

**The page holds no text from the book.** Names, counts and chapter numbers only. Checked across the corpus, the longest string in any generated page is a title-and-author line.

That's what makes a page safe to send to somebody. It's derived data about a book rather than a copy of one.

**The page makes no external request, sets no cookie, and stores one thing** — the chapter you are on, in `localStorage`. It's one self-contained file and works from a filesystem with no server and no network.

## What the Flatpak asks for

`--filesystem=home` and nothing else beyond a display. That's broader than it looks like it should be, and the reason is the sidecar: your rulings are written next to the book so that removing Ariadne leaves them behind. The file portal grants the one file you picked and not its neighbours, so it can't write that.

`--unshare=network` is stated rather than left to the default, so the sandbox has no network at all. The two commands that would want one don't work inside it.

## The two flags that leave the machine

`--explain` and `--relations` send text to the Anthropic API, and they are the only things here that do. They need `ANTHROPIC_API_KEY` in the environment and refuse without it.

**Everything else is offline.** If you never use those two flags, nothing this tool touches leaves your machine.

## Where your own decisions live

Merges, notes and warnings go in a sidecar file beside the book. It's plain, readable, and yours — you can read it, edit it, delete it or hand it to someone else. Nothing is uploaded and there's no account.

## Known, and not yet closed

**An epub and a docx are zip archives holding XML, parsed with `xml.etree.ElementTree`.** It doesn't resolve external entities, so there's no XXE here, but it has no ceiling on entity expansion either — a deliberately hostile file could cost a lot of memory before anything stopped it.

The exposure is a book you chose to open, which is a much smaller thing than a service parsing what a stranger uploaded. Closing it properly means either a dependency or a parser configured to refuse a DTD, and neither has been done. **It's recorded here rather than left to be discovered.**

## Reporting something

Open an issue, or write to code@kingletas.com.
