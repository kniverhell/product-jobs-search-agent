# Job search agent: fallback pointer

This folder is the kit's code. The preferred install is the plugin (see README): your files then live in a separate
project folder and the skill loads by itself.

Fallback, only if you opened Claude Code in a clone without installing: read `skills/job-search-ops/SKILL.md` and
follow it. In that file and in `modes/`, `${CLAUDE_PLUGIN_ROOT}` and `<kit>` both mean this folder. Your own files
still go in a separate project folder (run `python3 <this folder>/setup.py` from inside it); setup refuses to put them
here, and the scripts stop in any folder without the `.job-search` marker setup writes.
