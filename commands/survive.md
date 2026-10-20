---
description: Company survival scoring
argument-hint: "<company>"
---

Job-search kit, survive mode. Kit root: `${CLAUDE_PLUGIN_ROOT}`. First load the
`job-search-agent:job-search-ops` skill with the Skill tool, then read `${CLAUDE_PLUGIN_ROOT}/modes/survive.md`, and follow them exactly. In those files `<kit>`
means `${CLAUDE_PLUGIN_ROOT}`; every other path is in the current project folder. Never search outside the project
folder and the kit root.

Request: $ARGUMENTS
