#!/usr/bin/env python3
"""Read-only parse of application-profile.md for fill mode (modes/fill.md). Never writes anything.

Usage:
    python3 application_profile.py               # every field, as plain lists
    python3 application_profile.py --get "Email" # one value; exit 1 if missing or refused

Prints four plain lists, one line each as `SECTION | key | value`:
FACTUAL and KNOCKOUT (by the `## Factual` / `## Knockout` header the line sits under, read from the file),
MISSING (blank, or still a `[placeholder]`), and REFUSED (keys that look like government ID, date of birth or
bank details). A refused value is never printed, in any mode: the model never sees it.

Exit codes: 0 ok · 1 profile missing, tracked by git, malformed, or the --get key is missing or refused.
"""
import os
import re
import subprocess
import sys

from kit_paths import project_dir, require_project

PROFILE = os.path.join(project_dir(), "application-profile.md")

SECTIONS = {"factual": "FACTUAL", "knockout": "KNOCKOUT"}
FIELD = re.compile(r"^([A-Za-z][^:]{0,60}):(?:\s+(.*))?$")
PLACEHOLDER = re.compile(r"^\[.*\]$")

# A safety floor, not a user rule: these values never leave the file through this script, whatever the user writes.
DENY_KEY = re.compile(
    r"\bssn\b|social security|passport|licen[cs]e|\bdob\b|date of birth|birth ?date|birthday"
    r"|\bbank|routing|account (?:number|no)|\bacct\b|\biban\b|\bswift\b|tax id|\bitin\b|national id|government id",
    re.I)
DENY_VALUE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")  # SSN-shaped, whatever the key says


def stop(msg):
    print(f"STOP: {msg}")
    sys.exit(1)


def tracked(path):
    r = subprocess.run(["git", "ls-files", "--error-unmatch", "--", os.path.basename(path)],
                       cwd=os.path.dirname(path), capture_output=True)
    return r.returncode == 0


def parse(path):
    """Return a list of (list_name, key, value) in file order. Raises SystemExit on a malformed file."""
    out, seen, section = [], {}, None
    for n, raw in enumerate(open(path, encoding="utf-8"), 1):
        if raw.startswith("#"):  # a markdown header: `## Factual` / `## Knockout` open a section, any other closes it
            section = SECTIONS.get(raw[3:].strip().lower()) if raw.startswith("## ") else None
            continue
        line = raw.split(" #")[0].strip()  # inline comment
        if section is None or not line or line.startswith("#"):
            continue
        m = FIELD.match(line)
        if not m:
            continue
        key, value = m.group(1).strip(), (m.group(2) or "").strip()
        low = key.lower()
        if low in seen:
            stop(f"'{key}' appears twice (lines {seen[low]} and {n}); keep one")
        seen[low] = n
        if DENY_KEY.search(key) or DENY_VALUE.search(value):
            out.append(("REFUSED", key, "value withheld"))
        elif not value or PLACEHOLDER.match(value):
            out.append(("MISSING", key, f"({section.lower()})"))
        else:
            out.append((section, key, value))
    return out


def main(argv):
    require_project()
    if not os.path.exists(PROFILE):
        stop("no application-profile.md in the project folder. Run setup, then fill it in.")
    if tracked(PROFILE):
        stop("application-profile.md is tracked by git. It must be gitignored, never committed.")
    rows = parse(PROFILE)
    if not rows:
        stop("application-profile.md has no fields under '## Factual' or '## Knockout'.")

    if argv[:1] == ["--get"]:
        if len(argv) != 2:
            stop('usage: application_profile.py --get "<key>"')
        want = argv[1].strip().lower()
        for kind, key, value in rows:
            if key.lower() == want:
                if kind == "REFUSED":
                    stop(f"refused: '{key}' is a denylisted key; enter it on the form yourself")
                if kind == "MISSING":
                    stop(f"missing: '{key}' has no answer in application-profile.md")
                print(value)
                return 0
        stop(f"missing: no '{argv[1]}' key in application-profile.md")
    if argv:
        stop(f"unknown argument {argv[0]!r}")

    for kind in ("FACTUAL", "KNOCKOUT", "MISSING", "REFUSED"):
        print(kind)
        hits = [(k, v) for t, k, v in rows if t == kind]
        for key, value in hits:
            print(f"{kind} | {key} | {value}")
        if not hits:
            print("(none)")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
