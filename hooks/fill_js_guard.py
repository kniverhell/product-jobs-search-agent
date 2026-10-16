#!/usr/bin/env python3
"""Claude Code PreToolUse hook for fill mode: block every browser javascript_tool call except the approved read-only
snippets in hooks/fill_read/ (page-1.js … page-8.js, generated from source.js by make_pages.py).

The script text in the call is hashed (sha256, after stripping leading and trailing whitespace and turning CRLF into
LF) and compared with APPROVED_SHA256 below, one hash per page. Anything else, including a page plus one extra
statement, is blocked with exit 2. A malformed call is blocked too: this hook fails closed.

APPROVED_SHA256 is pinned here on purpose. Editing source.js changes every page's hash, so a changed snippet is
blocked until this list is updated from make_pages.py's output, and that update is a guardrail change that needs its
own approval (SKILL.md rule 12).

Wire it in .claude/settings.local.json (see SETUP.md, "Filling applications"):
    {"matcher": "mcp__.*javascript_tool", "hooks": [{"type": "command",
     "command": "python3 \\"$CLAUDE_PROJECT_DIR/hooks/fill_js_guard.py\\""}]}
"""
import hashlib
import json
import sys

APPROVED_SHA256 = {
    "334434a2f3d4d26b5081cd5ca27d6d642f835960c2a0a37d47a8455ddb547b10",  # page-1.js
    "34b1779c44ee556dd9c1fafe28874b1650d34c66f7cfd5a9287a4249552d300c",  # page-2.js
    "d422d03fc7295560f78879764deba7906736d0f55a943272e9c840ac86b4a7e4",  # page-3.js
    "b237abcf82b1014cc9af99f716bf35e20483f8625860a3318926a4bed08f3818",  # page-4.js
    "85536bb08c1f309bdcd55a01698751a1ca518c52d86d5adb84e23e77ad564dee",  # page-5.js
    "3f5555369ee0923225401076d6e0b74bed0e8640dc4754004950b119d562257e",  # page-6.js
    "3d1f79b08186bcbdfb61730ea5fa4dbb5a495a9b5f4b6922874903c652ff787d",  # page-7.js
    "924754174b9db44a0acdcf72c7d423ff302d8a246bc8e2efec4f84c14ca8dc5f",  # page-8.js
}


def digest(text):
    return hashlib.sha256(text.replace("\r\n", "\n").strip().encode("utf-8")).hexdigest()


def block(reason):
    sys.stderr.write(f"Blocked by fill_js_guard.py: {reason}. The only scripts allowed are the exact text of "
                     "hooks/fill_read/page-N.js (read-only field values). Clicks, keys and other scripts are never "
                     "allowed in fill mode.\n")
    return 2


def main():
    try:
        call = json.load(sys.stdin)
    except ValueError:
        return block("unreadable hook input")
    if not isinstance(call, dict):
        return block("unreadable hook input")
    if not str(call.get("tool_name", "")).endswith("javascript_tool"):
        return 0  # the matcher should never send other tools here; don't interfere if it does
    text = (call.get("tool_input") or {}).get("text")
    if not isinstance(text, str) or not text.strip():
        return block("no script text")
    if digest(text) not in APPROVED_SHA256:
        return block("script is not one of the approved read-only snippets")
    print(json.dumps({"systemMessage": "fill_js_guard: approved read-only snippet allowed"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
