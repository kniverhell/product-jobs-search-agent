#!/usr/bin/env python3
"""Claude Code SessionStart hook: in a job-search folder, tell the session where the kit is and where it may look.

Self-checking: it adds context only when the project folder holds the .job-search marker that setup writes. In any
other folder (other projects, or before setup) it prints nothing, so it never adds noise elsewhere.

The kit root comes from CLAUDE_PLUGIN_ROOT (or this file's location) and lives only in the session's context; it is
never written to any file.
"""
import json
import os
import sys

MARKER = ".job-search"


def main():
    try:
        call = json.load(sys.stdin)
    except ValueError:
        call = {}
    project = os.environ.get("CLAUDE_PROJECT_DIR") or call.get("cwd") or os.getcwd()
    if not os.path.isfile(os.path.join(project, MARKER)):
        return 0
    kit = os.environ.get("CLAUDE_PLUGIN_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    context = (
        f"This folder is a job-search project (it has the {MARKER} marker). For any request here, use the "
        f"job-search-agent:job-search-ops skill and its modes; the /job-search-agent:<mode> commands load them directly.\n"
        f"Kit root (scripts, modes, templates): {kit}. Mode files write it as <kit>. Run kit scripts by full path, e.g. "
        f"python3 \"{kit}/triage.py\", from this project folder.\n"
        f"Never search outside this project folder and the kit root: no find or recursive listing of the home folder or "
        f"other folders, and never read another job-search folder or another copy of the kit. If something isn't in "
        f"those two places, say so and ask."
    )
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": context}}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
