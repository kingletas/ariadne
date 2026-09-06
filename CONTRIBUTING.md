# Contributing

## The gate

```bash
make check
```

Linting, the layering check, the invariant, the goldens and the desktop metadata. Run it before and after, every time.

```bash
make smoke
```

**A window cannot be reviewed from its source.** This drives the real reader through every view, moves the bookmark, opens the drawer, makes a ruling and undoes it, and writes a PNG of each into `build/smoke/`. It needs a display, which is why `make check` does not run it — but a change to `app/` is not done until it has.

## Four questions before adding anything

1. **Can it be wrong in a way the reader cannot see?** If yes, it refuses instead.
2. **Does it need book text in a front end?** Then it does not ship — the page holds names, counts and chapter numbers, and the window holds the same index in memory.
3. **Does it read from `first`, or around it?** Anything reaching past the reader's position is the one bug this tool exists not to have.
4. **What is the measurement?** A band, a threshold or a claim without one is not ready.

## The layers

A layer may import the ones above it and nothing below, and `tests/test_layering.py` reads the imports out of the AST to check it. **The engine — everything except the two front ends, `render` and `app`, and the `cli` above them — must import on a machine with no GUI toolkit installed**, which is what makes "standard library only" a fact rather than an intention.

Adding a folder under `src/ariadne/` fails the suite until it is declared in `ALLOWED`. That is deliberate: a new layer is a decision.

## The baselines

The books the corpus pages were built from are not in this repository, so **the pages are the baseline**. Each `tests/golden/model/<book>.json` is the model a real page was rendered from, and the renderer must still turn it back into that exact file.

Ingest has fixtures instead, under `tests/fixtures/ingest`, one per branch — each chapter form, both quote conventions, Gutenberg boilerplate, a table of contents, an epub, a Markdown folder, and two refusals.

**`make snapshot` re-records the ingest table. Only run it after a change you meant to make, and read the diff** — it is the difference between a fix and a regression nobody noticed.

## What refusing looks like

Adding a refusal is a feature here, not a gap. It goes in the register with the measurement or the citation that settles it, and `ariadne --refusals` prints it.

## Two implementations of the clipping, and never a third

`model/view.py` is the one the suite asserts. The page carries its own in JavaScript because it runs in a browser with no Python behind it. **Anything native uses the Python one** — a third copy is a third thing that can be wrong about the only property this tool must never get wrong.

## Cutting a release

```bash
make release VERSION=0.2.0 DRY_RUN=1
```

Writes `__version__`, retitles the changelog's Unreleased section, and seeds the AppStream release entry. Then write that entry — `make check` refuses the placeholder — commit, and `git tag v0.2.0 && git push --tags`, which is the whole trigger.

```bash
scripts/verify-package
```

Builds the `.deb` and proves everything about it that can be proved without root, including running the shipped tree through the system interpreter. The install itself needs root and is printed for you to run.

```bash
make bundle
```

Builds the single-file `.flatpak` the release attaches. Needs `org.gnome.Platform//50` and `org.gnome.Sdk//50`, and it builds with the network off — which costs nothing here, because the engine has no dependencies to pin.

## Style

`make format`. Comments say what the code does or what it guards against, and stop; the history goes in the commit message and the changelog.
