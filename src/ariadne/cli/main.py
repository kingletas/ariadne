import argparse
import copy
import json
import os
import sys
import zipfile
from collections import Counter
from xml.etree import ElementTree as ET

from ..ai.client import DEFAULT_MODEL
from ..ai.explain import explain_passage
from ..ai.relations import extract_relations
from ..analysis.about import about_report, crowding
from ..analysis.corpus import (
    band_note,
    introduction_curve,
    load_corpus,
    term_coverage,
    writer_report,
)
from ..analysis.overlap import overlap_report
from ..analysis.prose import (
    chapter_spread,
    compare_versions,
    focus,
    narrative_person,
    pace,
    prose_shape,
    summarise_words,
    warning_map,
)
from ..cli.refusals import print_refusals
from ..core.refusal import Refusal
from ..core.settings import MIN_USES
from ..decisions.sidecar import (
    apply_decisions,
    containment_links,
    load_decisions,
    save_decisions,
    sidecar_path,
)
from ..ingest.book import load
from ..ingest.epub import epub_series
from ..ingest.quotes import quote_convention
from ..ingest.series import load_series
from ..invariant import self_test
from ..model.build import build_model, model_json
from ..model.classify import classify
from ..position.reader import find_word, koreader_position
from ..position.series import resolve_series_position
from ..render.page import render_page
from .usage import USAGE

# ---------------------------------------------------------------------------
# The corpus
# ---------------------------------------------------------------------------


def print_corpus():
    """What the bands are made of, so a number from them can be argued with."""
    c = load_corpus()
    if not c:
        print("ariadne: no corpus file at ariadne.d/corpus.json")
        return 1
    src = c.get("sources", {})
    print("THE CORPUS BEHIND EVERY BAND THIS TOOL REPORTS\n")
    print(c.get("note", ""))
    print()
    print("  %-26s %s" % ("selection", src.get("selection", "?")))
    print("  %-26s %s" % ("strata", src.get("strata", "?")))
    print("  %-26s %s books" % ("segmented into chapters", src.get("segmented", "?")))
    print("  %-26s %s books" % ("measured for prose shape", src.get("lexical", "?")))
    curves = c.get("curve", {})
    for section in ("all", "english", "translated"):
        ref = curves.get(section)
        if not ref:
            continue
        n = (ref.get("0.25") or {}).get("n", 0)
        print("\nWHEN THE CAST ARRIVES -- %s (%d books)" % (section, n))
        print("  %-22s %8s %8s %8s" % ("by this point", "p25", "median", "p75"))
        for q, label in (
            ("0.1", "10% in"),
            ("0.25", "25% in"),
            ("0.5", "halfway"),
            ("0.75", "75% in"),
        ):
            b = ref.get(q)
            if b:
                print("  %-22s %7.1f%% %7.1f%% %7.1f%%" % (label, b["p25"], b["median"], b["p75"]))
        b = ref.get("last_new")
        if b:
            print(
                "  %-22s %7.1f%% %7.1f%% %7.1f%%"
                % ("last new name at", b["p25"], b["median"], b["p75"])
            )
    print("\nWHY QUARTILES AND NOT THE RANGE")
    print("Resampling moves the extremes a long way and barely moves the")
    print("quartiles. A min and a max quoted from one draw are not a band.")
    print("\nWHY THIS IS NOT A TARGET")
    print("Books that all succeeded spread 13.6x on adverb density inside this")
    print("same corpus. A number outside the band is a difference, and the tool")
    print("has no way to tell you which kind.")
    print("\nThe books were drawn by metadata -- language of composition, era,")
    print("genre -- from a frame of 14,678, so the selection is reproducible and")
    print("was not made by anybody's taste, including mine.")
    return 0


# ---------------------------------------------------------------------------


def print_header():
    print(USAGE)


def main():
    if "-h" in sys.argv or "--help" in sys.argv:
        print_header()
        return 0
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("book", nargs="*")
    ap.add_argument("-o", "--out")
    ap.add_argument("-t", "--title")
    ap.add_argument("--min-uses", type=int, default=MIN_USES)
    ap.add_argument("--inspect", action="store_true")
    ap.add_argument("--app", action="store_true")
    ap.add_argument("--doctor", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument(
        "--refusals",
        action="store_true",
        help="what this will not do, and the measurement behind each",
    )
    ap.add_argument(
        "--corpus",
        action="store_true",
        help="what the bands are made of, so a number can be argued with",
    )
    ap.add_argument("--links", action="store_true", help="list proposed and decided name links")
    ap.add_argument("--accept", action="append", default=[], metavar="KEEP=ALSO")
    ap.add_argument("--reject", action="append", default=[], metavar="KEEP=ALSO")
    ap.add_argument("--hide", action="append", default=[], metavar="NAME")
    ap.add_argument("--rename", action="append", default=[], metavar="OLD=NEW")
    ap.add_argument("--find", metavar="WORD", help="chapters containing WORD, up to --position")
    ap.add_argument(
        "--position",
        metavar="N|BOOK:CHAPTER",
        help="reading position, 1-based; BOOK:CHAPTER across a series",
    )
    ap.add_argument(
        "--position-from",
        metavar="PATH",
        help="read the position from a KOReader .sdr metadata file",
    )
    ap.add_argument(
        "--relations",
        action="store_true",
        help="work out who is who to whom, using your own account",
    )
    ap.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        metavar="ID",
        help="model for --explain and --relations (default %s)" % DEFAULT_MODEL,
    )
    ap.add_argument(
        "--review", action="store_true", help="list proposed relationships and their state"
    )
    ap.add_argument(
        "--accept-rel",
        action="append",
        default=[],
        metavar="NAME=CLAUSE",
        help="accept a proposed relationship (a unique prefix will do)",
    )
    ap.add_argument(
        "--reject-rel",
        action="append",
        default=[],
        metavar="NAME=CLAUSE",
        help="reject one, so it is never offered again",
    )
    ap.add_argument(
        "--spoil", action="store_true", help="drop the position bound: use and show the whole book"
    )
    ap.add_argument(
        "--warn",
        action="append",
        default=[],
        metavar="N=TEXT",
        help="warn yourself about chapter N; shown one chapter early",
    )
    ap.add_argument(
        "--unwarn",
        action="append",
        default=[],
        metavar="N=PREFIX",
        help="remove a warning from chapter N",
    )
    ap.add_argument("--warnings", action="store_true", help="list the warnings on this book")
    ap.add_argument(
        "--note",
        action="append",
        default=[],
        metavar="NAME=MEANING",
        help="record what you understood a name or term to mean",
    )
    ap.add_argument("--notes", action="store_true", help="list what you have written down")
    ap.add_argument(
        "--explain", metavar="QUESTION", help="ask your own Claude account about the book so far"
    )
    ap.add_argument(
        "--window",
        type=int,
        default=3,
        metavar="N",
        help="--explain: how many chapters of context to send",
    )
    ap.add_argument(
        "--compare", metavar="OTHER", help="another version of this book: what a revision changed"
    )
    ap.add_argument(
        "--writer",
        action="store_true",
        help="a report for whoever is writing the book, not reading it",
    )
    ap.add_argument(
        "--about",
        action="store_true",
        help="what you are in for: cast size, pace, narration, series",
    )
    ap.add_argument(
        "--overlap",
        nargs="+",
        metavar="PATH",
        help="another book or series: how much of this you already know",
    )
    ap.add_argument("--export", action="store_true", help="print the decisions file")
    ap.add_argument(
        "--decisions", metavar="PATH", help="decisions file (default: <book>.ariadne.json)"
    )
    args = ap.parse_args()

    if args.self_test:
        code, msg = self_test()
        print(("ariadne: self-test FAILED -- " if code else "ariadne: self-test ok -- ") + msg)
        return code

    if args.refusals:
        print_refusals()
        return 0

    if args.corpus:
        return print_corpus()

    if args.doctor:
        from ..app.availability import report

        return report()

    if not args.book:
        # Launched from an applications menu there is no argument and no
        # terminal to print into, so the window has to be what appears.
        if args.app:
            from ..app.main import run as run_app

            return run_app()
        print_header()
        return 2
    for b in args.book:
        if not os.path.exists(b):
            sys.exit("ariadne: no such file or folder: %s" % b)

    bounds = None
    try:
        if len(args.book) > 1:
            title, convention, chapters, bounds = load_series(args.book, args.title)
        else:
            title, convention, chapters = load(args.book[0], args.title)
        if convention.startswith("play:"):
            quotes = "speaker labels"
        else:
            quotes = quote_convention("\n".join(chapters))
    except Refusal as e:
        sys.exit("ariadne: %s\n  in %s" % (e, ", ".join(args.book)))
    except (zipfile.BadZipFile, ET.ParseError, KeyError) as e:
        sys.exit("ariadne: %s is not a readable epub (%s)" % (", ".join(args.book), e))

    if args.inspect:
        words = sum(len(c.split()) for c in chapters)
        print("%-12s %s" % ("title", title))
        print("%-12s %d" % ("chapters", len(chapters)))
        print("%-12s %d" % ("words", words))
        print("%-12s %s" % ("segmented", convention))
        print("%-12s %s" % ("quotes", quotes))
        presence, counts, first = build_model(chapters, args.min_uses)
        print("%-12s %d (>= %d uses)" % ("entities", len(first), args.min_uses))
        top = sorted(first, key=lambda n: -sum(c.get(n, 0) for c in counts))[:10]
        print("%-12s %s" % ("commonest", ", ".join(top)))
        return 0

    presence, counts, first = build_model(chapters, args.min_uses)
    if not first:
        sys.exit("ariadne: no names found at >= %d uses. Try --min-uses 3." % args.min_uses)

    # The position bounds --find and is reported by --writer as context. A
    # KOReader sidecar wins over a bare --position when both are given, since
    # naming a file is the more deliberate act.
    upto = len(chapters) - 1
    if args.position is not None:
        try:
            upto = resolve_series_position(args.position, bounds, len(chapters))
        except (Refusal, ValueError) as exc:
            sys.exit("ariadne: %s" % exc)
        if bounds:
            for bi, (btitle, bstart, bcount) in enumerate(bounds, 1):
                if bstart <= upto < bstart + bcount:
                    print(
                        "ariadne: book %d of %d, %s -- chapter %d of %d"
                        % (bi, len(bounds), btitle, upto - bstart + 1, bcount)
                    )
                    break
    if args.spoil:
        upto = len(chapters) - 1
        print(
            "ariadne: --spoil is on. The position bound is off and everything "
            "in this book\n  is fair game, including the ending. Any page "
            "written now says so on its face."
        )
    if args.position_from:
        try:
            upto = koreader_position(args.position_from, len(chapters))
        except Refusal as exc:
            sys.exit("ariadne: %s" % exc)
        print("ariadne: position read as chapter %d of %d" % (upto + 1, len(chapters)))

    dpath = args.decisions or sidecar_path(args.book[0])
    decisions = load_decisions(dpath)

    if args.export:
        json.dump(decisions, sys.stdout, ensure_ascii=False, indent=1, sort_keys=True)
        print()
        return 0

    def pair(spec, flag):
        if "=" not in spec:
            sys.exit("ariadne: %s wants KEEP=ALSO, got %r" % (flag, spec))
        keep, also = (s.strip() for s in spec.split("=", 1))
        if keep not in first or also not in first:
            missing = [n for n in (keep, also) if n not in first]
            sys.exit("ariadne: not a name in this book: %s" % ", ".join(missing))
        return keep, also

    changed = False
    for spec in args.accept + args.reject:
        state = "accepted" if spec in args.accept else "rejected"
        keep, also = pair(spec, "--" + state[:6])
        decisions["links"] = [
            link
            for link in decisions["links"]
            if not (link["keep"] == keep and link["also"] == also)
        ]
        decisions["links"].append({"keep": keep, "also": also, "state": state})
        changed = True
    for name in args.hide:
        if name not in first:
            sys.exit("ariadne: not a name in this book: %s" % name)
        if name not in decisions["hidden"]:
            decisions["hidden"].append(name)
        changed = True

    def _set_relation_state(spec, state, flag):
        if "=" not in spec:
            sys.exit("ariadne: %s wants NAME=CLAUSE, got %r" % (flag, spec))
        name, frag = (x.strip() for x in spec.split("=", 1))
        rows = (decisions.get("relations") or {}).get(name)
        if not rows:
            sys.exit(
                "ariadne: no proposed relationship for %r. "
                "Run --review to see what there is." % name
            )
        hits = [r for r in rows if r["text"].lower().startswith(frag.lower())]
        if not hits:
            sys.exit("ariadne: %r has no relationship starting %r" % (name, frag))
        if len(hits) > 1:
            sys.exit(
                "ariadne: %r matches %d relationships for %r; be more specific"
                % (frag, len(hits), name)
            )
        hits[0]["state"] = state
        return True

    for spec in args.accept_rel:
        changed = _set_relation_state(spec, "accepted", "--accept-rel") or changed
    for spec in args.reject_rel:
        changed = _set_relation_state(spec, "rejected", "--reject-rel") or changed

    for spec in args.note:
        if "=" not in spec:
            sys.exit("ariadne: --note wants NAME=MEANING, got %r" % spec)
        name, text = (x.strip() for x in spec.split("=", 1))
        if name not in first:
            sys.exit("ariadne: not a name in this book: %s" % name)
        # The chapter is recorded with the note because what a reader
        # understood at chapter 8 is a different thing from what they know at
        # chapter 40, and the earlier reading is the one a wiki cannot hold.
        decisions["glosses"][name] = {"at": upto, "text": text}
        changed = True
    for spec in args.warn:
        if "=" not in spec:
            sys.exit("ariadne: --warn wants N=TEXT, got %r" % spec)
        where, text = (x.strip() for x in spec.split("=", 1))
        if not where.isdigit() or not 1 <= int(where) <= len(chapters):
            sys.exit(
                "ariadne: --warn wants a chapter between 1 and %d, got %r" % (len(chapters), where)
            )
        if not text:
            sys.exit("ariadne: --warn needs something to say about chapter %s" % where)
        decisions["warnings"].append({"at": int(where) - 1, "text": text})
        changed = True
    for spec in args.unwarn:
        if "=" not in spec:
            sys.exit("ariadne: --unwarn wants N=PREFIX, got %r" % spec)
        where, frag = (x.strip() for x in spec.split("=", 1))
        if not where.isdigit():
            sys.exit("ariadne: --unwarn wants a chapter number, got %r" % where)
        at = int(where) - 1
        hits = [
            w
            for w in decisions["warnings"]
            if w["at"] == at and w["text"].lower().startswith(frag.lower())
        ]
        if not hits:
            sys.exit("ariadne: no warning on chapter %s starting %r" % (where, frag))
        if len(hits) > 1:
            sys.exit(
                "ariadne: %r matches %d warnings on chapter %s; be more specific"
                % (frag, len(hits), where)
            )
        decisions["warnings"].remove(hits[0])
        changed = True
    for spec in args.rename:
        if "=" not in spec:
            sys.exit("ariadne: --rename wants OLD=NEW, got %r" % spec)
        old_n, new_n = (s.strip() for s in spec.split("=", 1))
        decisions["renamed"][old_n] = new_n
        changed = True
    if changed:
        save_decisions(dpath, decisions)
        print("ariadne: decisions saved to %s" % dpath)

    if args.find:
        hits = find_word(chapters, args.find, upto)
        if not hits:
            print("ariadne: %r appears in no chapter up to %d." % (args.find, upto + 1))
            return 1
        total = sum(n for _, n in hits)
        print(
            "%r -- %d mention(s) across %d chapter(s), up to chapter %d"
            % (args.find, total, len(hits), upto + 1)
        )
        for i, n in hits:
            print("  chapter %-4d %d" % (i + 1, n))
        return 0

    if args.explain:
        try:
            answer, n_ch, n_words = explain_passage(
                chapters, args.explain, upto, max(1, args.window), args.model
            )
        except Refusal as exc:
            sys.exit("ariadne: %s" % exc)
        print(
            "Sent chapters %d-%d (%s words) to your own Anthropic account."
            % (upto - n_ch + 2, upto + 1, format(n_words, ","))
        )
        print("Nothing after chapter %d was included.\n" % (upto + 1))
        print(answer)
        return 0

    if args.compare:
        if not os.path.exists(args.compare):
            sys.exit("ariadne: no such file or folder: %s" % args.compare)
        try:
            b_title, b_conv, b_chapters = load(args.compare)
        except Refusal as exc:
            sys.exit("ariadne: %s\n  in %s" % (exc, args.compare))
        rows, absorbed = compare_versions(chapters, b_chapters)
        aw, bw = summarise_words(chapters), summarise_words(b_chapters)

        print("%s  ->  %s" % (title, b_title))
        print(
            "%d chapters, %s words   ->   %d chapters, %s words   (%+d words)"
            % (len(chapters), format(aw, ","), len(b_chapters), format(bw, ","), bw - aw)
        )

        kinds = Counter(r[2] for r in rows)
        print("\nWHAT THE SECOND VERSION IS MADE OF")
        for k in ("unchanged", "moved", "rewritten"):
            if kinds[k]:
                print("  %-12s %3d chapter(s)" % (k, kinds[k]))
        if absorbed:
            print("  %-12s %3d chapter(s) fewer than the first version" % ("absorbed", absorbed))
            print("               -- merged into their neighbours, or cut outright")

        moved = [r for r in rows if r[2] == "moved"]
        if moved:
            print("\nWHERE THE NUMBERING SHIFTS")
            prev = None
            for j, src, _ in moved:
                off = src - j
                if off != prev:
                    print("  from chapter %-4d the numbering runs %+d" % (j + 1, off))
                    prev = off
            print("  A shift with unchanged text is a renumbering, not a rewrite --")
            print("  which is what a merge upstream of it looks like.")

        rewritten = [r[0] for r in rows if r[2] == "rewritten"]
        if rewritten:
            if len(rewritten) == len(b_chapters):
                print("\nREWRITTEN: every chapter")
            else:
                shown = ", ".join(str(j + 1) for j in rewritten[:24])
                more = "" if len(rewritten) <= 24 else " and %d more" % (len(rewritten) - 24)
                print("\nREWRITTEN: %s%s" % (shown, more))
            # How much each one moved. A column of near-identical deltas is
            # almost never editing: it is one repeated block present on one
            # side only, and saying so here saves reading it as 23 rewritten
            # chapters when it is one piece of apparatus.
            deltas = []
            for j in rewritten:
                src = j if j < len(chapters) else None
                if src is not None:
                    deltas.append(len(b_chapters[j].split()) - len(chapters[src].split()))
            if len(deltas) >= 3:
                spread = max(deltas) - min(deltas)
                mid = sorted(abs(d) for d in deltas)[len(deltas) // 2]
                print("  word change per chapter: %+d to %+d" % (min(deltas), max(deltas)))
                # Relative, not absolute: a constant block shows up as deltas
                # that share a sign and sit inside a narrow band around their
                # own median, whatever that median happens to be. A fixed
                # threshold missed a 59-word block scattered over 22.
                same_sign = min(deltas) * max(deltas) > 0
                if same_sign and mid and spread <= mid:
                    print("  All in the same direction and within a narrow band, which is the")
                    print("  shape of a header or note block present on one side only rather")
                    print("  than of revision. Worth confirming before reading it as rewriting.")

        # The voice, on both sides, so a pass can show what it did not disturb.
        pa, pb = prose_shape("\n".join(chapters)), prose_shape("\n".join(b_chapters))
        if pa and pb:
            print("\nDID THE VOICE MOVE?")
            print("  %-22s %10s %10s %10s" % ("", "before", "after", "delta"))
            for key, label, fmt in (
                ("mattr", "lexical diversity", "%.4f"),
                ("sent_mean", "sentence length", "%.2f"),
                ("sent_cv", "sentence variety", "%.3f"),
            ):
                # The sign has to be produced by the number, not by the field
                # width: "%+10s" on a string pads it and adds nothing, so a
                # positive delta printed bare while a negative one carried its
                # own minus. Two columns that look different for no reason.
                delta = pb[key] - pa[key]
                print(
                    "  %-22s %10s %10s %10s"
                    % (
                        label,
                        fmt % pa[key],
                        fmt % pb[key],
                        ("+" if delta >= 0 else "") + fmt % delta,
                    )
                )
            # Scale, or the signs get read as a trend. Six small negatives in
            # a column look like decline however small they are, and these
            # measures cannot carry a direction: a book whose vocabulary
            # narrows is not worse, it is narrower.
            noise = chapter_spread(chapters, "mattr")
            biggest = abs(pb["mattr"] - pa["mattr"])
            if noise and biggest:
                print(
                    "\n  For scale: one chapter of this book differs from the next by %.4f" % noise
                )
                print(
                    "  in lexical diversity -- %.0fx the change above. A delta well inside"
                    % (noise / biggest if biggest else 0)
                )
                print("  that is jitter rather than movement.")
            print("\n  NONE OF THIS IS A QUALITY MEASURE. It says whether the prose kept its")
            print("  shape, not whether the revision improved the book -- a pass that fixed")
            print("  everything and one that broke everything read the same here. Whether it")
            print("  got better is a reading question, and only a reader answers it.")
        return 0

    if args.writer:
        kinds = classify(
            "\n".join(chapters), set(first), (narrative_person(chapters) or {}).get("kind")
        )
        m = model_json(title, convention, quotes, presence, counts, first, kinds)
        m["entities"] = apply_decisions(m["entities"], decisions)
        once, vanished, late, last_act = writer_report(m)
        print("%s -- %d chapters, %d names" % (title, m["chapters"], len(m["entities"])))
        print("the last act is taken as chapter %d onward.\n" % (last_act + 1))
        print("USED ONCE AND DROPPED  (%d)" % len(once))
        for name, ch, n in once[:15]:
            print("  %-32s chapter %-5d %d mention(s)" % (name[:32], ch + 1, n))
        print("\nGONE BEFORE THE LAST ACT  (%d, five or more mentions)" % len(vanished))
        for name, ch, n in vanished[:15]:
            print("  %-32s last in %-6d %d mentions" % (name[:32], ch + 1, n))
        print("\nARRIVES IN THE LAST ACT  (%d, five or more mentions)" % len(late))
        for name, ch, n in late[:15]:
            print("  %-32s first in %-5d %d mentions" % (name[:32], ch + 1, n))
        curve, last_new = introduction_curve(m)
        corpus = load_corpus()
        if curve:
            print("\nWHEN THE CAST ARRIVES")
            # "all" is the current key; "canon" was the 31-book file's.
            curves = (corpus or {}).get("curve", {})
            ref = curves.get("all") or curves.get("canon") or {}
            for q, label in (("0.1", "10%"), ("0.25", "25%"), ("0.5", "50%"), ("0.75", "75%")):
                b = ref.get(q)
                mark = (
                    (
                        "  middle half %2.0f-%2.0f%%, you are %s"
                        % (b["p25"], b["p75"], band_note(curve[q], b))
                    )
                    if b
                    else ""
                )
                print("  by %-4s of the book  %5.1f%% of the cast met%s" % (label, curve[q], mark))
            b = ref.get("last_new")
            mark = (
                ("  middle half %2.0f-%2.0f%%, %s" % (b["p25"], b["p75"], band_note(last_new, b)))
                if b
                else ""
            )
            print("  last new name at    %5.1f%%%s" % (last_new, mark))
            if corpus:
                print(
                    "\n  The middle half of %d books, not a target -- and the middle half"
                    % (ref.get("0.25", {}).get("n", 0))
                )
                print("  rather than the full range because resampling moves the extremes a long")
                print("  way and barely moves the quartiles. In this same corpus adverb density")
                print("  spread 13.6x among books that all succeeded, so being outside is a")
                print("  difference and never a fault.")
        terms = term_coverage(m)
        if terms:
            once = [t for t in terms if t["once"]]
            front = [t for t in terms if t["front"]]
            late = [t for t in terms if t["late"]]
            print("\nTHE INVENTED VOCABULARY  (%d terms the classifier called neither" % len(terms))
            print("person nor place -- your terms of art are in here, and so is noise)")
            for t in terms[:14]:
                mark = (
                    "  used once"
                    if t["once"]
                    else "  front third only"
                    if t["front"]
                    else "  last third only"
                    if t["late"]
                    else ""
                )
                print(
                    "  %-26s %4d uses  ch %d-%d  in %d chapters%s"
                    % (
                        t["name"][:26],
                        t["total"],
                        t["first"] + 1,
                        t["last"] + 1,
                        t["chapters"],
                        mark,
                    )
                )
            print("\n  used once and dropped      %3d" % len(once))
            print("  confined to the front third %3d" % len(front))
            print("  arriving in the last third  %3d" % len(late))
            print("\n  A term introduced and never used again is a thread or a stray, and")
            print("  only you can say which. Ariadne cannot tell your vocabulary from its")
            print("  own noise -- measured on one manuscript the two overlap completely.")

        print("\nNone of these is a defect. A name used once may be a passer-by,")
        print("and a late arrival may be the ending. They are the places to look.")
        return 0

    if args.overlap:
        for o in args.overlap:
            if not os.path.exists(o):
                sys.exit("ariadne: no such file or folder: %s" % o)
        try:
            if len(args.overlap) > 1:
                o_title, _, o_chapters, _ = load_series(args.overlap)
            else:
                o_title, _, o_chapters = load(args.overlap[0])
        except Refusal as exc:
            sys.exit("ariadne: %s\n  in %s" % (exc, ", ".join(args.overlap)))
        _, o_counts, _ = build_model(o_chapters, args.min_uses)
        overlap_report(title, counts, o_title, o_counts)
        return 0

    if args.about:
        person = narrative_person(chapters)
        kinds = classify("\n".join(chapters), set(first), (person or {}).get("kind"))
        m = model_json(title, convention, quotes, presence, counts, first, kinds)
        m["entities"] = apply_decisions(m["entities"], decisions)
        # As on the page: a series run loads every volume, so the first
        # file's own metadata would announce "book 1" over all of them.
        about_report(
            title,
            chapters,
            m,
            person,
            focus(counts, kinds, person, (person or {}).get("third_pronouns", 0)),
            None if bounds else epub_series(args.book[0]),
            load_corpus(),
            bounds,
        )
        return 0

    if args.relations:
        print(
            "Reading chapters 1-%d for stated relationships, on your own "
            "Anthropic account." % (upto + 1),
            file=sys.stderr,
        )
        try:
            found = extract_relations(chapters, upto, args.model)
        except Refusal as exc:
            sys.exit("ariadne: %s" % exc)
        merged = decisions.get("relations") or {}
        for name, rows in found.items():
            seen_txt = {r["text"] for r in merged.get(name, [])}
            merged.setdefault(name, []).extend(r for r in rows if r["text"] not in seen_txt)
        decisions["relations"] = merged
        save_decisions(dpath, decisions)
        total = sum(len(v) for v in merged.values())
        print("\n%d relationship(s) across %d name(s), saved to %s" % (total, len(merged), dpath))
        for name in sorted(merged)[:20]:
            for r in sorted(merged[name], key=lambda x: x["at"])[:3]:
                print("  %-24s ch %-4d %s" % (name[:24], r["at"] + 1, r["text"]))
        return 0

    if args.review:
        rel = decisions.get("relations") or {}
        if not rel:
            print("No relationships yet. Run --relations to work them out.")
            return 0
        counts = Counter(r.get("state", "proposed") for rows in rel.values() for r in rows)
        print("%-22s %-5s %-9s %s" % ("name", "ch", "state", "relationship"))
        for name in sorted(rel):
            for r in sorted(rel[name], key=lambda x: x["at"]):
                print(
                    "%-22s %-5d %-9s %s"
                    % (name[:22], r["at"] + 1, r.get("state", "proposed"), r["text"])
                )
        print("\n%s" % "  ".join("%s %d" % (k, v) for k, v in sorted(counts.items())))
        print("\nAccept one with:  ariadne %r --accept-rel 'NAME=first few words'" % args.book[0])
        print("A proposed relationship is not shown on the page until it is accepted.")
        return 0

    if args.warnings:
        rows = sorted(decisions.get("warnings") or [], key=lambda w: w["at"])
        if not rows:
            print("No warnings on this book. Add one with:")
            print("  ariadne %r --warn '24=someone does not make it'" % args.book[0])
            print("\nAriadne detects nothing. A warning is yours, it is stored beside")
            print("the book, and the page shows that one is coming without showing")
            print("what it says until the reader asks.")
            return 0
        print("%-9s %-9s %s" % ("chapter", "shown at", "what you wrote"))
        for w in rows:
            print("%-9d %-9d %s" % (w["at"] + 1, max(1, w["at"]), w["text"]))
        print("\n%d warning(s). Each appears one chapter early, folded shut." % len(rows))
        return 0

    if args.notes:
        gl = decisions.get("glosses") or {}
        if not gl:
            print("Nothing written down yet. Add one with:")
            print("  ariadne %r --note 'NAME=what you think it means' --position N" % args.book[0])
            return 0
        print("%-24s %-8s %s" % ("name", "chapter", "what you wrote"))
        for name, g in sorted(gl.items(), key=lambda kv: kv[1].get("at", 0)):
            print("%-24s %-8s %s" % (name[:24], g.get("at", 0) + 1, g.get("text", "")))
        return 0

    if args.links:
        decided = {(link["keep"], link["also"]): link["state"] for link in decisions["links"]}
        proposed = containment_links(set(first))
        print("%-34s %-24s %s" % ("keep", "also", "state"))
        seen = set()
        for keep, also in proposed:
            state = decided.get((keep, also), "proposed")
            seen.add((keep, also))
            print("%-34s %-24s %s" % (keep[:34], also[:24], state))
        for (keep, also), state in decided.items():
            if (keep, also) not in seen:
                print("%-34s %-24s %s (yours)" % (keep[:34], also[:24], state))
        print("\nAccept one with:  ariadne %r --accept 'KEEP=ALSO'" % args.book[0])
        print("A proposed link changes nothing until it is accepted.")
        return 0

    _person = narrative_person(chapters)
    kinds = classify("\n".join(chapters), set(first), (_person or {}).get("kind"))
    m = model_json(title, convention, quotes, presence, counts, first, kinds)
    # Kept before the rulings are folded in: the desktop reader lets a ruling be
    # taken back, and a merge cannot be inverted once the index is rewritten.
    undecided = copy.deepcopy(m["entities"])
    m["entities"] = apply_decisions(m["entities"], decisions)
    if bounds:
        m["books"] = [{"title": b[0], "start": b[1], "chapters": b[2]} for b in bounds]
    m["glosses"] = decisions.get("glosses") or {}
    # Only what the reader has accepted. A proposed relationship is invisible,
    # exactly as an unaccepted alias link is.
    m["relations"] = {
        name: [r for r in rows if r.get("state") == "accepted"]
        for name, rows in (decisions.get("relations") or {}).items()
    }
    m["relations"] = {k: v for k, v in m["relations"].items() if v}
    m["spoil"] = bool(args.spoil)
    m["pace"] = pace(chapters, presence, first)
    _words = summarise_words(chapters)
    _c = crowding(m, load_corpus())
    m["about"] = {
        "words": _words,
        "hours": round(_words / 250 / 60),
        "names": _c["names"],
        "curve": _c["curve"],
        "band": _c["band"],
        "person": _person,
        "focus": focus(counts, kinds, _person, (_person or {}).get("third_pronouns", 0)),
        # A series run loads every volume, so the first file's own metadata
        # would announce "book 1" over a page covering all seven. The volumes
        # table below says it properly.
        "series": None if bounds else epub_series(args.book[0]),
    }
    if bounds:
        # A series reader's question is not how big the cast is, it is how much
        # of it arrived before the volume in their hand.
        vols = []
        for btitle, bstart, bcount in bounds:
            end = bstart + bcount - 1
            new_here = sum(1 for e in m["entities"] if bstart <= e["first"] <= end)
            carried = sum(1 for e in m["entities"] if e["first"] < bstart)
            vols.append({"title": btitle, "new": new_here, "carried": carried, "chapters": bcount})
        m["about"]["volumes"] = vols
    m["warn"] = warning_map(decisions.get("warnings") or [], len(chapters), spoil=bool(args.spoil))

    if args.app:
        # Imported here rather than at the top: the toolkit is the app's
        # dependency alone, and `ariadne -h` has to work on a machine with
        # no GTK on it at all.
        from ..app.main import run as run_app

        return run_app(m, undecided, dpath)

    if args.json:
        json.dump(m, sys.stdout, ensure_ascii=False, indent=1)
        print()
        return 0

    out = args.out or (os.path.splitext(os.path.basename(args.book[0]))[0] + ".html")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(render_page(m))
    print("ariadne: %s -- %d chapters, %d names -> %s" % (title, m["chapters"], len(first), out))
    return 0
