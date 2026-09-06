"""The one property that must never regress.

`ariadne --self-test` is the documented gate and the suite calls the same
function rather than reimplementing it, so the two can never disagree about
what the invariant is.
"""

from ariadne.invariant import self_test


def test_nothing_leaks_past_the_reader_position():
    code, message = self_test()
    assert code == 0, message
