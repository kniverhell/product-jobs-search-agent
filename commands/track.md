---
description: Add or update a role in 02-tracker.csv through the kit's tracker writer
argument-hint: "<company, title, URL, status>"
---

Job-search kit, tracker mode. Kit root: `${CLAUDE_PLUGIN_ROOT}`. First load the
`job-search-agent:job-search-ops` skill with the Skill tool, then follow its rule 10 and *Canonical statuses* exactly. In those files `<kit>`
means `${CLAUDE_PLUGIN_ROOT}`; every other path is in the current project folder. Never search outside the project
folder and the kit root.

Request: $ARGUMENTS
