#!/usr/bin/env python3
"""Claude Code PreToolUse hook (Bash): check what a push would publish before `git push`, `gh pr create` or
`gh repo sync` runs. Ships with the plugin, wired in hooks/hooks.json.

Self-checking, so it never blocks a fresh install:
- Only those three commands are looked at, matched on whole command words (`.git/privacy-push.log` and
  `git stash push` never trigger). Every other command passes untouched.
- If the project folder has no .privacy-patterns, or the file has no terms yet, the command is allowed with a
  visible message saying the check isn't configured.
- Otherwise it runs privacy_check.py --push in the project folder and blocks (exit 2) if that fails.
- The exact command `echo job-search-agent-hook-probe` is always blocked with "hooks are live": setup uses it to
  prove the plugin's hooks are loaded.

A pass, a skip and a block are all visible (a systemMessage or the block reason), and each check is logged to
.git/privacy-push.log in the project when that folder is a git repo.
"""
import datetime
import json
import os
import re
import shlex
import subprocess
import sys

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROBE = "echo job-search-agent-hook-probe"


def is_trigger(segment):
    """True for `git ... push` (not `git stash push`), `gh pr create` and `gh repo sync`, on whole command words."""
    try:
        toks = shlex.split(segment)
    except ValueError:
        toks = segment.split()
    names = [os.path.basename(t) for t in toks]
    for i, n in enumerate(names):
        if n == "git" and "push" in toks[i + 1:] and "stash" not in toks[i + 1:]:
            return True
        if n == "gh" and toks[i + 1:i + 3] in (["pr", "create"], ["repo", "sync"]):
            return True
    return False


def terms(path):
    if not os.path.exists(path):
        return 0
    return sum(1 for line in open(path, encoding="utf-8") if line.strip() and not line.strip().startswith("#"))


def log(project, cmd, verdict, summary):
    if not os.path.isdir(os.path.join(project, ".git")):
        return
    try:
        with open(os.path.join(project, ".git", "privacy-push.log"), "a", encoding="utf-8") as f:
            stamp = datetime.datetime.now().isoformat(timespec="seconds")
            f.write(f"{stamp}\t{verdict}\t{cmd.strip()[:120]}\t{summary}\n")
    except OSError:
        pass


def main():
    try:
        call = json.load(sys.stdin)
        cmd = (call.get("tool_input") or {}).get("command", "") or ""
    except (ValueError, AttributeError):
        return 0  # not a Bash call we can read; this hook only ever adds checks, it never invents blocks
    if cmd.strip() == PROBE:
        sys.stderr.write("job-search-agent hooks are live (this probe is blocked on purpose).\n")
        return 2
    if not any(is_trigger(s) for s in re.split(r"&&|\|\||;|\||\n", cmd)):
        return 0
    project = os.environ.get("CLAUDE_PROJECT_DIR") or call.get("cwd") or os.getcwd()
    if not terms(os.path.join(project, ".privacy-patterns")):
        msg = "privacy check not configured: add terms to .privacy-patterns (push allowed unchecked)"
        log(project, cmd, "SKIPPED", msg)
        print(json.dumps({"systemMessage": msg}))
        return 0
    r = subprocess.run([sys.executable, os.path.join(KIT, "privacy_check.py"), "--push"], cwd=project,
                       capture_output=True, text=True, env={**os.environ, "JOB_SEARCH_DIR": project})
    summary = (r.stdout.strip().splitlines() or [r.stderr.strip() or "no output"])[-1]
    log(project, cmd, "BLOCKED" if r.returncode else "PASSED", summary)
    if r.returncode != 0:
        sys.stderr.write("Blocked by privacy_check.py --push:\n" + r.stdout + r.stderr)
        return 2
    print(json.dumps({"systemMessage": f"privacy check passed: {summary}"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
