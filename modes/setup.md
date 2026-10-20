# Mode: Setup — make this folder a job-search folder

Trigger: "run setup" or `/job-search-agent:setup`. Run it in an empty folder made for your job search, or rerun it
any time: it never overwrites a file.

`<kit>` below is the kit root that `SKILL.md` names.

## Steps

1. Run `python3 "<kit>/setup.py"` from the project folder. If it prints `STOP: setup refused`, show the reason and
   stop. It refuses your home folder, `/`, and the kit's own folder: your files never live with the code.
2. **Check that the hooks loaded.** Run exactly `echo job-search-agent-hook-probe` with Bash.
   - Blocked, with "job-search-agent hooks are live": the plugin's hooks are loaded.
   - It just prints the text: the hooks did not load. Say "hooks not loaded: check `/plugin` (is job-search-agent
     enabled?) and start a new session".
3. Report, in this order:
   - **Created / kept:** one line, with counts. List created files only if fewer than five.
   - **Fill in first:** the files under FILL IN FIRST, each with one line on what goes in it:
     - `config.md`: facts about you (background, comp floors, home metro);
     - `01-target-roles.md`: your scoring rules, plus the `scan-screen` block if you'll use `scan.py`;
     - `00-master-resume.md`: your full resume;
     - `06-proof-points.md`: every number you can defend, with its source.
   - **Fill in when you need them:** the STILL TEMPLATES list, by name only. Mention `application-profile.md` for
     fill mode and `07-network.md` for outreach.
   - **Hooks:** live or not loaded (step 2); the fill guard and the privacy push check, as setup printed them.
   - Any `.gitignore is missing:` lines, unchanged.
4. Stop. One next step: "Fill in `config.md` and `01-target-roles.md`, then paste a job posting or say 'run the
   scout'."

Setup writes only into the project folder: the `.job-search` marker (a format number and a date, no paths), the
templates, `.privacy-patterns`, a `.gitignore` if there was none, and empty output folders. It never writes the
kit's location anywhere.
