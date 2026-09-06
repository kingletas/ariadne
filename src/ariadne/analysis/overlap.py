from collections import Counter

# ---------------------------------------------------------------------------
# What you already know
# ---------------------------------------------------------------------------
#
# A reader finishing one series and starting a neighbouring one is asking a
# question no single book can answer: how much of this do I already have. It
# is the same question as the series carried-in count, pointed sideways.
#
# The Ender books are the case that produced it. The Shadow Saga retells the
# events of the Ender Saga from another character's side, and shares only 33%
# of its cast -- so a reader who expects to know everybody is wrong about two
# names in three. The inversion is visible in the counts: Ender is named 4,382
# times in his own saga and 1,108 in Bean's, Bean 143 and 3,865. Each is a
# background figure in the other's books.
#
# LIKE --about, THIS IS ABOUT WHOLE BOOKS AND SAYS SO. It is a CLI report and
# never reaches the page, because it cannot be bounded by a position: the
# question is asked before the second book is started.


def overlap_report(title, counts, other_title, other_counts):
    """Which names both sets hold, and which are new to the one in hand."""
    mine = {n for c in counts for n in c}
    theirs = {n for c in other_counts for n in c}
    tot = Counter()
    for c in counts:
        tot.update(c)
    otot = Counter()
    for c in other_counts:
        otot.update(c)
    shared = mine & theirs
    fresh = mine - theirs

    print("%s  \u2190  %s" % (title, other_title))
    print("%d names here, %d there, %d in both" % (len(mine), len(theirs), len(shared)))
    if mine:
        print("%.0f%% of this one you have already met." % (100 * len(shared) / len(mine)))

    if shared:
        print("\nCARRIED OVER, and how much each matters on either side")
        print("  %-30s %10s %10s" % ("", "here", "there"))
        for n in sorted(shared, key=lambda x: -(tot[x] + otot[x]))[:16]:
            print("  %-30s %10s %10s" % (n[:30], format(tot[n], ","), format(otot[n], ",")))
        print("\n  A name heavy on one side and light on the other is a background")
        print("  figure in one book and a lead in the other. That asymmetry is the")
        print("  thing a reader is unprepared for, and it does not show up in a count.")

    if fresh:
        print("\nNEW TO THIS ONE  (%d names the other never uses)" % len(fresh))
        for n in sorted(fresh, key=lambda x: -tot[x])[:16]:
            print("  %-30s %10s" % (n[:30], format(tot[n], ",")))

    print("\nBoth sides are read whole, so this says nothing about where you are")
    print("in either. Names only -- an unlinked alias counts twice on both sides.")
