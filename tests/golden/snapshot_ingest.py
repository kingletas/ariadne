"""Record what the reader makes of every ingest fixture.

The books this tool was built against are not on disk, so ingest has no
baseline that can be recovered. These fixtures are the baseline instead: run
this against a version known to be good, commit the table, and any later change
to segmentation or convention detection shows up as a diff rather than as a
book that quietly reads differently.
"""

import hashlib
import pathlib
import sys

FIXTURES = pathlib.Path(__file__).resolve().parents[1] / "fixtures" / "ingest"
TABLE = pathlib.Path(__file__).resolve().parent / "ingest.tsv"


def rows(load, refusal, quote_convention, build_model):
    for path in sorted(
        p for p in FIXTURES.iterdir() if p.suffix in (".txt", ".epub") or p.is_dir()
    ):
        name = path.stem if path.is_file() else path.name
        try:
            _, convention, chapters = load(str(path))
        except refusal as why:
            yield name, "REFUSAL", "0", str(why).split(" -- ")[0][:70], ""
            continue
        try:
            quotes = quote_convention("\n".join(chapters))
        except refusal:
            quotes = "refused"
        build_model(chapters, min_uses=3)
        yield (
            name,
            convention,
            str(len(chapters)),
            quotes,
            hashlib.sha256("\x00".join(chapters).encode()).hexdigest(),
        )


def main(module):
    table = list(rows(module.load, module.Refusal, module.quote_convention, module.build_model))
    TABLE.write_text(
        "# fixture\tsegmentation\tchapters\tquote convention\t"
        "sha256 of the chapter texts\n" + "\n".join("\t".join(r) for r in table) + "\n",
        encoding="utf-8",
    )
    for r in table:
        print(f"  {r[0]:18} {r[1]:34} {r[2]:>2} ch  {r[3][:40]}")
    print(f"\n{len(table)} rows -> {TABLE}")
    return 0


if __name__ == "__main__":
    import importlib.machinery
    import importlib.util
    import os

    target = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/bin/ariadne")
    spec = importlib.util.spec_from_loader(
        "ariadne_snapshot", importlib.machinery.SourceFileLoader("ariadne_snapshot", target)
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    sys.exit(main(mod))
