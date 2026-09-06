"""Text primitives every layer above may need.

A quoted span is what separates dialogue from narration, and two layers ask
that question for different reasons: the classifier to decide what a name is
doing, the pace measure to say how much of a chapter is speech.
"""

import re

QUOTED = re.compile(r'[\u201c"]([^\u201c\u201d"]{1,4000})[\u201d"]')
