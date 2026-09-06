#!/usr/bin/env bash
#
# version.sh -- print the version this working tree builds as.
#
# Usage:
#   packaging/version.sh
#
# The version is declared once, as __version__ in src/ariadne/__init__.py, and
# pyproject.toml reads it from there through hatchling. Everything that needs it
# outside Python asks this script, so the pattern that finds it exists in one
# place rather than in each build script and CI job.
#
# Exits 1 when no version can be read, so a caller cannot build an artifact
# named after an empty string.

set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source_file="${SOURCE:-$here/src/ariadne/__init__.py}"

version="$(sed -n 's/^__version__ = "\(.*\)"$/\1/p' "$source_file" | head -1)"

if [ -z "$version" ]; then
	echo "version.sh: no __version__ in $source_file" >&2
	exit 1
fi

printf '%s\n' "$version"
