#!/usr/bin/env python3
"""Claude Code PreToolUse hook: in a job-search project, keep file tools and Bash inside the project folder and the kit
root. Ships with the plugin, wired in hooks/hooks.json.

Self-checking: active only when the project folder holds the .job-search marker that setup writes. Everywhere else
(other projects, a fresh install before setup) every call passes untouched. Inside a marked project the hook fails
closed: if it cannot check a call, the call is blocked with a message saying so.

Allowed roots: the project folder, the kit root, this project's own scratch folder /private/tmp/claude-<uid>/<slug>/
(slug = the project path with every non-alphanumeric character turned into "-"; another project's scratch is
outside) and this project's own Claude Code folder under ~/.claude/projects/ (saved tool output). Nothing else.

- Read, Glob, Grep, Write, Edit, NotebookEdit: a path (or a Glob pattern's fixed prefix) outside the roots is blocked.
- Bash: every argument of every command that looks like a path (starts with /, ~, $HOME or ., or holds ".." or a
  flag's =value) must resolve inside the roots; so must redirect targets. The command word itself is not checked.
  locate and mdfind are always blocked. Variables other than $HOME are not expanded, and paths built inside
  `python3 -c`, scripts or subshells are not seen: a known gap.

A block exits 2 with the rule and the path, never file contents. ROADMAP item 7.
"""
import json
import os
import re
import shlex
import sys

MARKER = ".job-search"
KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALWAYS_BLOCKED = {"locate", "mdfind"}
HARMLESS = {"/dev/null", "/dev/stdin", "/dev/stdout", "/dev/stderr"}
WRAPPERS = {"sudo", "command", "env", "nohup", "time", "builtin"}
PATH_START = ("/", "~", "$HOME", "${HOME}", "./")
FILE_TOOLS = {"Read": "file_path", "Write": "file_path", "Edit": "file_path", "NotebookEdit": "notebook_path"}


def real(path, base):
    path = os.path.expandvars(os.path.expanduser(path))
    if not os.path.isabs(path):
        path = os.path.join(base, path)
    return os.path.realpath(path)


def inside(path, roots):
    return any(path == r or path.startswith(r.rstrip(os.sep) + os.sep) for r in roots)


def slug(project):
    return re.sub(r"[^A-Za-z0-9]", "-", project)


def roots_for(project):
    roots = {real(project, project), real(KIT, KIT)}
    if os.environ.get("CLAUDE_PLUGIN_ROOT"):
        roots.add(real(os.environ["CLAUDE_PLUGIN_ROOT"], project))
    s = slug(real(project, project))
    roots.add(os.path.realpath(f"/private/tmp/claude-{os.getuid()}/{s}"))
    roots.add(os.path.realpath(os.path.expanduser(os.path.join("~/.claude/projects", s))))
    return roots


def glob_prefix(pattern, base):
    """Fixed part of a glob pattern as a resolved directory: what the pattern can reach at most."""
    full = pattern if os.path.isabs(os.path.expanduser(pattern)) else os.path.join(base, pattern)
    m = re.search(r"[*?\[{]", full)
    prefix = full[:m.start()] if m else full
    if not prefix.endswith(os.sep) and m:
        prefix = os.path.dirname(prefix)
    return real(prefix or base, base)


def segments(command):
    """Split a command at ; & | newlines, parentheses, $( and backticks, but not inside quotes."""
    out, cur, quote, i = [], [], None, 0
    while i < len(command):
        ch = command[i]
        if ch == "\\" and quote != "'" and i + 1 < len(command):
            cur.append(command[i:i + 2]); i += 2; continue
        if quote:
            if ch == quote:
                quote = None
            elif ch in "$`" and quote == '"' and (ch == "`" or command[i + 1:i + 2] == "("):
                out.append("".join(cur)); cur = []  # command substitution still runs inside double quotes
                i += 2 if ch == "$" else 1
                continue
            cur.append(ch)
        elif ch in "'\"":
            quote = ch; cur.append(ch)
        elif ch in ";&|\n()`":
            out.append("".join(cur)); cur = []
        elif ch == "$" and command[i + 1:i + 2] == "(":
            out.append("".join(cur)); cur = []; i += 1
        else:
            cur.append(ch)
        i += 1
    out.append("".join(cur))
    return [s for s in out if s.strip()]


def path_like(tok):
    return tok.startswith(PATH_START) or tok == "." or tok == ".." or tok.startswith("../") or "/../" in tok \
        or tok.endswith("/..")


def check_segment(seg, cwd, roots):
    """Return (rule, path) when the segment breaks the scope, else None."""
    try:
        toks = shlex.split(seg)
    except ValueError:
        toks = seg.split()
    while toks and (re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", toks[0]) or os.path.basename(toks[0]) in WRAPPERS):
        toks = toks[1:]
    if not toks:
        return None
    cmd = os.path.basename(toks[0])
    if cmd in ALWAYS_BLOCKED:
        return (f"{cmd} searches the whole disk", "")
    for t in toks[1:]:
        t = re.sub(r"^\d*[<>]+&?", "", t)  # redirect glued to its target
        if t.startswith("-"):
            if "=" not in t:
                continue
            t = t.split("=", 1)[1]
        elif re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", t):
            t = t.split("=", 1)[1]
        if not t or t in HARMLESS or not path_like(t):
            continue
        if "$" in os.path.expandvars(os.path.expanduser(t)):
            continue  # unresolved variable: cannot tell
        p = real(t, cwd)
        if not inside(p, roots):
            return (f"{cmd}: an argument reaches outside the project and the kit", p)
    return None


def block(rule, path):
    where = f" ({path})" if path else ""
    sys.stderr.write(f"Blocked by scope_guard.py: {rule}{where}. In a job-search project, stay inside the project "
                     "folder and the kit root. If what you need isn't there, say so and ask the user.\n")
    return 2


def marked_project(call):
    candidates = [os.environ.get("CLAUDE_PROJECT_DIR"), (call or {}).get("cwd") if isinstance(call, dict) else None,
                  os.getcwd()]
    return next((c for c in candidates if c and os.path.isfile(os.path.join(c, MARKER))), None)


def main():
    call = None
    try:
        call = json.load(sys.stdin)
        if not isinstance(call, dict):
            raise ValueError("input is not an object")
        project = os.environ.get("CLAUDE_PROJECT_DIR") or call.get("cwd") or os.getcwd()
        if not os.path.isfile(os.path.join(project, MARKER)):
            return 0
        roots = roots_for(project)
        cwd = real(call.get("cwd") or project, project)
        tool = str(call.get("tool_name", ""))
        args = call.get("tool_input") or {}
        if tool in FILE_TOOLS:
            targets = [args.get(FILE_TOOLS[tool])]
        elif tool == "Grep":
            targets = [args.get("path") or cwd]
        elif tool == "Glob":
            base = real(args.get("path") or cwd, cwd)
            targets = [base, glob_prefix(args.get("pattern") or "", base)]
        elif tool == "Bash":
            for seg in segments(str(args.get("command") or "")):
                hit = check_segment(seg, cwd, roots)
                if hit:
                    return block(*hit)
            return 0
        else:
            return 0
        for t in targets:
            if isinstance(t, str) and t:
                p = real(t, cwd)
                if not inside(p, roots):
                    return block(f"{tool} outside the project and the kit", p)
        return 0
    except Exception as e:  # fail closed in a marked project, with the reason
        if marked_project(call) is None:
            return 0
        sys.stderr.write(f"Blocked by scope_guard.py: the hook could not check this call ({type(e).__name__}: {e}). "
                         "Nothing ran. Tell the user the scope guard failed.\n")
        return 2


if __name__ == "__main__":
    sys.exit(main())
