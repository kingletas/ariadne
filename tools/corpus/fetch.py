#!/usr/bin/env python3
"""Fetch the drawn sample from Project Gutenberg, one request per second.

Progress is written after every book, so an interrupted run resumes instead of
starting over. A book with no plain-text edition is replaced from the reserve held
for its own cell, which keeps the stratification intact rather than leaving a hole.

Usage:  fetch.py SAMPLE.json OUTDIR [LIMIT]
"""

import json
import os
import sys
import time
import urllib.error
import urllib.request

UA = "ariadne-corpus/1.0 (personal research; contact via github.com/gutenbergtools)"
DELAY = 1.0
TIMEOUT = 45

URLS = [
    "https://www.gutenberg.org/cache/epub/{id}/pg{id}.txt",
    "https://www.gutenberg.org/files/{id}/{id}-0.txt",
    "https://www.gutenberg.org/files/{id}/{id}.txt",
]


def get(book_id):
    for tmpl in URLS:
        url = tmpl.format(id=book_id)
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                data = r.read()
            if len(data) > 20000:  # anything smaller is a stub or an error page
                return data, url
        except urllib.error.HTTPError as e:
            if e.code in (403, 429):
                time.sleep(20)  # asked to slow down: do
            continue
        except Exception:
            continue
        finally:
            time.sleep(DELAY)
    return None, None


def main():
    sample_path, outdir = sys.argv[1], sys.argv[2]
    limit = int(sys.argv[3]) if len(sys.argv) > 3 else None
    os.makedirs(outdir, exist_ok=True)
    data = json.load(open(sample_path))
    wanted = data["sample"][:limit] if limit else data["sample"]
    reserve = data["reserve"]

    state_path = os.path.join(outdir, "_fetch-state.json")
    state = (
        json.load(open(state_path))
        if os.path.exists(state_path)
        else {"done": {}, "failed": [], "replaced": []}
    )

    queue = list(wanted)
    used = {str(b["id"]) for b in wanted}
    i = 0
    while i < len(queue):
        b = queue[i]
        i += 1
        key = str(b["id"])
        if key in state["done"]:
            continue
        body, url = get(b["id"])
        if body is None:
            state["failed"].append({"id": b["id"], "title": b["title"], "cell": b["cell"]})
            # replace from the same cell so the stratum keeps its count
            for cand in reserve.get(b["cell"], []):
                if str(cand["id"]) not in used:
                    used.add(str(cand["id"]))
                    queue.append(cand)
                    state["replaced"].append(
                        {"dropped": b["id"], "added": cand["id"], "cell": b["cell"]}
                    )
                    break
        else:
            path = os.path.join(outdir, "pg%d.txt" % b["id"])
            with open(path, "wb") as fh:
                fh.write(body)
            state["done"][key] = {
                "title": b["title"],
                "authors": b["authors"],
                "cell": b["cell"],
                "group": b["group"],
                "era": b["era"],
                "genre": b["genre"],
                "bytes": len(body),
                "url": url,
            }
        json.dump(state, open(state_path, "w"))
        n = len(state["done"])
        if n % 25 == 0 or i == len(queue):
            print(
                "  %4d fetched, %3d failed, %3d replaced"
                % (n, len(state["failed"]), len(state["replaced"])),
                flush=True,
            )

    print(
        "DONE: %d fetched, %d failed, %d replaced"
        % (len(state["done"]), len(state["failed"]), len(state["replaced"]))
    )


if __name__ == "__main__":
    main()
