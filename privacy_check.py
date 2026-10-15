#!/usr/bin/env python3
"""Privacy check: look for personal terms before anything is committed or pushed. Read-only.

Patterns come from .privacy-patterns in the repo root: one literal per line, # comments allowed. Matching is
case-insensitive with letter/digit boundaries, so a pattern "cat" doesn't hit "category" and "12" doesn't hit "4123".
Exceptions come from .privacy-allow: `file | exact line text | YYYY-MM-DD | reason`. An allowed hit must match the
file and the whole stripped line, so a new or edited line still fails. Both files must be gitignored.

Usage:
    python3 privacy_check.py              # added lines in the staged diff (the pre-commit check)
    python3 privacy_check.py --all        # every tracked file in the working tree
    python3 privacy_check.py --push       # what a push would publish: HEAD, plus added lines in unpushed commits
    python3 privacy_check.py --history    # one-time sweep: added lines in every commit on every local ref
    python3 privacy_check.py FILE...      # named files, full contents

Exit 0 when clean. Exit 1 on any hit, and also when there is nothing to check: no patterns file, zero patterns,
a tracked patterns or allow file, a malformed allow line, or no input. A hit prints its location and the pattern's
line number in .privacy-patterns, never the pattern or the matched text.
"""
import datetime
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PATTERNS = os.path.join(HERE, ".privacy-patterns")
ALLOW = os.path.join(HERE, ".privacy-allow")


def git(*args, check=True):
    r = subprocess.run(["git", "-c", "core.quotepath=off", *args], cwd=HERE, capture_output=True)
    if check and r.returncode != 0:
        raise SystemExit(f"FAIL  git {' '.join(args)}: {r.stderr.decode(errors='replace').strip()}")
    return r


def tracked(path):
    return bool(git("ls-files", "--", os.path.relpath(path, HERE)).stdout.strip())


def load_patterns(errors):
    if not os.path.exists(PATTERNS):
        errors.append("no .privacy-patterns file in the repo root: nothing to check")
        return []
    out = []
    for n, line in enumerate(open(PATTERNS, encoding="utf-8"), 1):
        term = line.strip()
        if term and not term.startswith("#"):
            out.append((n, re.compile(r"(?<![A-Za-z0-9])" + re.escape(term) + r"(?![A-Za-z0-9])", re.I)))
    if not out:
        errors.append(".privacy-patterns has zero patterns: nothing to check")
    return out


def load_allow(errors):
    allow = {}
    if not os.path.exists(ALLOW):
        return allow
    for n, line in enumerate(open(ALLOW, encoding="utf-8"), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        parts = line.rstrip("\n").split("|")
        ok = len(parts) >= 4
        if ok:
            path, text = parts[0].strip(), "|".join(parts[1:-2]).strip()
            date, reason = parts[-2].strip(), parts[-1].strip()
            try:
                datetime.date.fromisoformat(date)
            except ValueError:
                ok = False
            ok = ok and path and text and reason
        if not ok:
            errors.append(f".privacy-allow line {n} is malformed (needs file | exact line text | YYYY-MM-DD | reason)")
            continue
        allow[(path, text)] = reason
    return allow


class Checker:
    def __init__(self, patterns, allow):
        self.patterns, self.allow = patterns, allow
        self.hits = self.allowed = 0
        self.files = set()

    def line(self, where, path, text):
        for n, rx in self.patterns:
            if rx.search(text):
                reason = self.allow.get((path, text.strip()))
                if reason:
                    self.allowed += 1
                    print(f"ALLOWED  {where}  (pattern line {n}): {reason}")
                else:
                    self.hits += 1
                    print(f"HIT  {where}  (pattern line {n})")

    def text(self, path, content, prefix=""):
        self.files.add(prefix + path)
        for i, ln in enumerate(content.splitlines(), 1):
            self.line(f"{prefix}{path}:{i}", path, ln)

    def diff(self, raw, commits=False):
        """Added lines from `git diff -U0` or `git log -p -U0` output."""
        commit, path, n, in_hunk = "", None, 0, False
        for ln in raw.splitlines():
            if commits and ln.startswith("commit ") and len(ln.split()) == 2:
                commit, path, in_hunk = ln.split()[1][:7], None, False
            elif ln.startswith("diff --git "):
                path, in_hunk = None, False
            elif not in_hunk and ln.startswith("+++ "):
                path = None if ln[4:] == "/dev/null" else ln[4:].removeprefix("b/")
                if path:
                    self.files.add((commit + ":" if commit else "") + path)
            elif ln.startswith("@@"):
                m = re.search(r"\+(\d+)", ln)
                n, in_hunk = (int(m.group(1)) if m else 0), True
            elif in_hunk and ln.startswith("+") and path:
                self.line(f"{commit + ':' if commit else ''}{path}:{n}", path, ln[1:])
                n += 1


def main(argv):
    errors = []
    for f in (PATTERNS, ALLOW):
        if os.path.exists(f) and tracked(f):
            errors.append(f"{os.path.basename(f)} is tracked by git: it must be gitignored, never committed")
    patterns = load_patterns(errors)
    allow = load_allow(errors)
    if errors:
        for e in errors:
            print(f"FAIL  {e}")
        return 1

    c = Checker(patterns, allow)
    mode = argv[0] if argv and argv[0].startswith("--") else None

    if mode == "--all":
        for p in git("ls-files", "-z").stdout.decode().split("\0"):
            full = os.path.join(HERE, p)
            if p and os.path.isfile(full):
                data = open(full, "rb").read()
                if b"\0" not in data:
                    c.text(p, data.decode("utf-8", errors="replace"))
    elif mode == "--push":
        if git("rev-parse", "--verify", "-q", "HEAD", check=False).returncode != 0:
            print("FAIL  no commits yet: nothing a push would publish")
            return 1
        for p in git("ls-tree", "-r", "--name-only", "-z", "HEAD").stdout.decode().split("\0"):
            if p:
                c.files.add(p)
        terms = [t.strip() for t in open(PATTERNS, encoding="utf-8") if t.strip() and not t.strip().startswith("#")]
        grep_args = ["grep", "-I", "-n", "-i", "-F", "--null"] + [a for t in terms for a in ("-e", t)] + ["HEAD"]
        for rec in git(*grep_args, check=False).stdout.decode("utf-8", errors="replace").splitlines():
            head, lineno, content = rec.split("\0", 2)
            path = head.split(":", 1)[1]
            c.line(f"{path}:{lineno}", path, content)
        up = git("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}", check=False)
        rng = ["@{upstream}..HEAD"] if up.returncode == 0 else ["HEAD", "--not", "--remotes"]
        c.diff(git("log", "-p", "-U0", "--no-color", "--format=commit %H", *rng).stdout.decode("utf-8", errors="replace"), commits=True)
    elif mode == "--history":
        c.diff(git("log", "-p", "-U0", "--no-color", "--all", "--format=commit %H").stdout.decode("utf-8", errors="replace"), commits=True)
    elif mode:
        print(f"FAIL  unknown option {mode}")
        return 1
    elif argv:
        for p in argv:
            full = os.path.join(HERE, p) if not os.path.isabs(p) else p
            if not os.path.isfile(full):
                print(f"FAIL  no such file: {p}")
                return 1
            c.text(os.path.relpath(full, HERE), open(full, encoding="utf-8", errors="replace").read())
    else:
        staged = [p for p in git("diff", "--cached", "--name-only", "-z").stdout.decode().split("\0") if p]
        if not staged:
            print("FAIL  nothing staged: nothing checked")
            return 1
        c.files.update(staged)
        c.diff(git("diff", "--cached", "-U0", "--no-color").stdout.decode("utf-8", errors="replace"))

    if not c.files:
        print("FAIL  no files matched: nothing checked")
        return 1
    if c.hits:
        print(f"\n{c.hits} hit(s) in {len(c.files)} files checked against {len(patterns)} patterns")
        return 1
    print(f"ok  {len(c.files)} files checked against {len(patterns)} patterns ({c.allowed} allowed)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
