#!/usr/bin/env python3
"""Generate the fixed read-only snippets page-1.js … page-8.js from source.js and print their sha256 hashes.

Chrome's javascript_tool cuts every result at 1,000 characters, so the field read is paged: each page file is
source.js with one constant (PAGE) set, and each returns at most ~900 characters ending in `MORE: run page N`
or `END: n fields`. The hashes printed here must match APPROVED_SHA256 in hooks/fill_js_guard.py. Changing
source.js means regenerating, and updating that list is a guardrail change that needs its own approval.
"""
import hashlib
import os

HERE = os.path.dirname(os.path.abspath(__file__))
PAGES = 8


def main():
    src = open(os.path.join(HERE, "source.js"), encoding="utf-8").read()
    if src.count("__PAGE__") != 1:
        raise SystemExit("FAIL  source.js must contain __PAGE__ exactly once")
    for n in range(1, PAGES + 1):
        body = src.replace("__PAGE__", str(n))
        with open(os.path.join(HERE, f"page-{n}.js"), "w", encoding="utf-8") as f:
            f.write(body)
        print(f'    "{hashlib.sha256(body.strip().encode("utf-8")).hexdigest()}",  # page-{n}.js')


if __name__ == "__main__":
    main()
