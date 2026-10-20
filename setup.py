#!/usr/bin/env python3
"""Set up a job-search project folder from the kit's templates. Never overwrites a file that exists.

Usage (from the folder that will hold your job-search files):
    python3 <kit>/setup.py

Refuses to run in your home folder, in /, or in or around the kit's own folder: your data never lives with the
code. Then it writes the .job-search marker (format and date only, never a path), copies every template that is
missing (placeholders only), creates .privacy-patterns (comments only) and a .gitignore if there is none, and makes
the output folders. It prints one plain line per item, what's still a template, and whether the hooks are ready.

Exit codes: 0 ok · 1 refused (wrong folder) or a file couldn't be written.
"""
import datetime
import filecmp
import os
import shutil
import sys

from kit_paths import MARKER, project_dir

KIT = os.path.dirname(os.path.realpath(__file__))
TEMPLATES = os.path.join(KIT, "templates")
FOLDERS = ("inbound", "reports", "tailored", "sent", "archive")
FILL_FIRST = ("config.md", "01-target-roles.md", "00-master-resume.md", "06-proof-points.md")
SPECIAL = {"privacy-patterns": ".privacy-patterns", "gitignore": ".gitignore"}


def refusal(project):
    real = os.path.realpath(project)
    home = os.path.realpath(os.path.expanduser("~"))
    if real == os.path.realpath(os.sep):
        return "this is the filesystem root"
    if real == home:
        return "this is your home folder; make a folder for your job search and run setup there"
    if real == KIT or real.startswith(KIT + os.sep):
        return "this is the kit's own folder; your files go in a separate project folder"
    if KIT.startswith(real + os.sep):
        return "this folder contains the kit; use a separate project folder for your files"
    return None


def terms(path):
    if not os.path.exists(path):
        return 0
    return sum(1 for line in open(path, encoding="utf-8") if line.strip() and not line.strip().startswith("#"))


def main():
    project = project_dir()
    why = refusal(project)
    if why:
        print(f"STOP: setup refused in {project}: {why}.")
        return 1
    print(f"SETUP {project}")

    marker = os.path.join(project, MARKER)
    if os.path.exists(marker):
        print(f"kept     {MARKER}")
    else:
        with open(marker, "x", encoding="utf-8") as f:
            f.write(f"job-search project folder\nformat: 1\ncreated: {datetime.date.today().isoformat()}\n")
        print(f"created  {MARKER}")

    still_template = []
    for name in sorted(os.listdir(TEMPLATES)):
        src = os.path.join(TEMPLATES, name)
        if not os.path.isfile(src):
            continue
        dest_name = SPECIAL.get(name, name)
        dest = os.path.join(project, dest_name)
        if os.path.exists(dest):
            print(f"kept     {dest_name}")
            if name == "gitignore":
                have = {l.strip() for l in open(dest, encoding="utf-8")}
                missing = [l.strip() for l in open(src, encoding="utf-8")
                           if l.strip() and not l.startswith("#") and l.strip() not in have]
                for entry in missing:
                    print(f"         .gitignore is missing: {entry}")
                if missing:
                    print("         (your .gitignore was not changed; add these lines if this folder is a git repo)")
        else:
            with open(src, "rb") as s, open(dest, "xb") as d:  # "x": never overwrite, even in a race
                shutil.copyfileobj(s, d)
            print(f"created  {dest_name}")
        if name not in SPECIAL and filecmp.cmp(src, dest, shallow=False):
            still_template.append(dest_name)

    for folder in FOLDERS:
        path = os.path.join(project, folder)
        if os.path.isdir(path):
            print(f"kept     {folder}/")
        else:
            os.makedirs(path)
            print(f"created  {folder}/")

    print()
    first = [f for f in FILL_FIRST if f in still_template]
    rest = [f for f in still_template if f not in FILL_FIRST]
    print("FILL IN FIRST (still the template)")
    print("\n".join(f"  {f}" for f in first) or "  (none)")
    print("STILL TEMPLATES (fill in when you need them)")
    print("\n".join(f"  {f}" for f in rest) or "  (none)")

    print()
    print("HOOKS (ready in this folder)")
    profile = os.path.exists(os.path.join(project, "application-profile.md"))
    print("  fill guard: " + ("active here (application-profile.md present)" if profile
                              else "inactive here (no application-profile.md)"))
    n = terms(os.path.join(project, ".privacy-patterns"))
    print("  privacy push check: " + (f"configured ({n} terms)" if n
                                      else "not configured: add terms to .privacy-patterns; pushes are not checked until then"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
