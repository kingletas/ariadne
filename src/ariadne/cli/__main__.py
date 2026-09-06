"""`python -m ariadne.cli`, which is what the installed wrapper runs."""

import sys

from .main import main

if __name__ == "__main__":
    sys.exit(main())
