#!/usr/bin/env bash
#
# Prints one version's section of the CHANGELOG, for a GitHub Release body.
#
# The release notes are the changelog rather than a second account of the same
# release written by hand -- two accounts of one change disagree eventually,
# and the one nobody edits is the one that goes stale.
#
# Usage:
#   packaging/release-notes.sh 1.0.0

set -euo pipefail

version="${1:?usage: release-notes.sh VERSION}"
here="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
changelog="$here/CHANGELOG.md"

notes="$(awk -v want="## [$version]" '
	index($0, want) == 1 { collecting = 1; next }
	collecting && /^## \[/ { exit }
	collecting { print }
' "$changelog")"

if [ -z "$(printf '%s' "$notes" | tr -d '[:space:]')" ]; then
	echo "release-notes.sh: CHANGELOG.md has no section for $version" >&2
	exit 1
fi

printf '%s\n' "$notes"
