#!/usr/bin/env bash
#
# build.sh -- build the Ariadne .deb.
#
# Usage:
#   packaging/deb/build.sh [OUTDIR]     OUTDIR defaults to dist/
#
# The package is Architecture: all, and that is checked rather than asserted: a
# compiled extension anywhere in the staged tree fails the build. Nothing here
# should have one -- the engine is standard library only and the front ends
# bring no wheels.
#
# The GObject bindings are NOT vendored and cannot be: python3-gi and the
# gir1.2 typelibs are system packages, so the package declares them as
# dependencies instead. That is also why `ariadne --doctor` exists.
#
# Environment overrides:
#   VERSION   package version (default: whatever packaging/version.sh reads)

set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
outdir="${1:-$here/dist}"
app_id="com.kingletas.Ariadne"

version="${VERSION:-$("$here/packaging/version.sh")}"

stage="$(mktemp -d)"
trap 'rm -rf "$stage"' EXIT

mkdir -p "$stage/DEBIAN" \
	"$stage/usr/bin" \
	"$stage/usr/lib/ariadne" \
	"$stage/usr/share/applications" \
	"$stage/usr/share/icons/hicolor/scalable/apps" \
	"$stage/usr/share/metainfo" \
	"$stage/usr/share/doc/ariadne"

cp -r "$here/src/ariadne" "$stage/usr/lib/ariadne/ariadne"

# Architecture: all is a claim about the contents, so it is checked.
if find "$stage/usr/lib/ariadne" -name '*.so' -o -name '*.pyd' | grep -q .; then
	echo "build.sh: a compiled extension is staged; this cannot be Architecture: all" >&2
	exit 1
fi
find "$stage/usr/lib/ariadne" -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true

cat > "$stage/usr/bin/ariadne" <<'LAUNCHER'
#!/usr/bin/env bash
# Ariadne, installed from the .deb. The interpreter is the system one, which is
# the only one that can see the GObject typelibs the desktop reader needs.
set -euo pipefail
exec /usr/bin/python3 -c 'import sys; sys.path.insert(0, "/usr/lib/ariadne"); from ariadne.cli.main import main; sys.exit(main())' "$@"
LAUNCHER
chmod 0755 "$stage/usr/bin/ariadne"

sed 's|@LAUNCHER@|/usr/bin/ariadne|' "$here/data/$app_id.desktop" \
	> "$stage/usr/share/applications/$app_id.desktop"
install -m 0644 "$here/data/$app_id.svg" \
	"$stage/usr/share/icons/hicolor/scalable/apps/$app_id.svg"
install -m 0644 "$here/data/$app_id.metainfo.xml" \
	"$stage/usr/share/metainfo/$app_id.metainfo.xml"
install -m 0644 "$here/LICENSE" "$stage/usr/share/doc/ariadne/copyright"

# Recommends rather than Depends on the toolkit: everything except the desktop
# reader works without it, and a person who only wants pages should not be made
# to install GTK. `ariadne --doctor` is what closes the gap.
cat > "$stage/DEBIAN/control" <<CONTROL
Package: ariadne
Version: $version
Section: text
Priority: optional
Architecture: all
Depends: python3 (>= 3.12)
Recommends: python3-gi, python3-gi-cairo, gir1.2-gtk-4.0, gir1.2-adw-1
Maintainer: Luis Tineo <code@kingletas.com>
Homepage: https://github.com/kingletas/ariadne
Description: A reading companion that never shows you past your bookmark
 Ariadne reads a book you already own and builds its cast as you read.
 Move the bookmark and every view is clipped to that chapter: who you have
 met, who you have not seen for a while, who shares chapters with whom, and
 where the book has been.
 .
 The spoiler rule is structural rather than a filter, so there is no later
 data waiting to be revealed by a bug. It makes no network request and keeps
 no account.
CONTROL

mkdir -p "$outdir"
package="$outdir/ariadne_${version}_all.deb"
dpkg-deb --build --root-owner-group "$stage" "$package" > /dev/null
echo "built $package"
