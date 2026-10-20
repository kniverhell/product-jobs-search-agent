#!/usr/bin/env python3
"""Where your data lives: the project folder, never the kit's own folder.

The kit's code (scripts, modes, templates) can sit anywhere, for example in a Claude Code plugin install. Your files
(the tracker, the profile, the network file, reports) live in the project folder you run Claude Code in. Scripts find
it here: `$JOB_SEARCH_DIR` if set, else the current working directory.
"""
import os


def project_dir():
    return os.path.abspath(os.environ.get("JOB_SEARCH_DIR") or os.getcwd())


MARKER = ".job-search"


def require_project():
    """Return the project folder, or stop (exit 1) if it hasn't been set up: data scripts only work in a folder
    that holds the .job-search marker, which `setup.py` writes. This keeps data out of $HOME, out of the kit's own
    folder, and out of folders that were never meant for it."""
    folder = project_dir()
    if not os.path.isfile(os.path.join(folder, MARKER)):
        print(f"STOP: not a job-search folder: {folder} has no {MARKER} marker. Run setup in your project folder first.")
        raise SystemExit(1)
    return folder
