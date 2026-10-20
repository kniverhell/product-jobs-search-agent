#!/usr/bin/env python3
"""Where your data lives: the project folder, never the kit's own folder.

The kit's code (scripts, modes, templates) can sit anywhere, for example in a Claude Code plugin install. Your files
(the tracker, the profile, the network file, reports) live in the project folder you run Claude Code in. Scripts find
it here: `$JOB_SEARCH_DIR` if set, else the current working directory.
"""
import os


def project_dir():
    return os.path.abspath(os.environ.get("JOB_SEARCH_DIR") or os.getcwd())
