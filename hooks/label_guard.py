#!/usr/bin/env python3
"""Claude Code hook (PreToolUse and PostToolUse): in a job-search project, the mail connector may read only the
labeled alerts. Ships with the plugin, wired in hooks/hooks.json. ROADMAP: discover mode (1.4.0).

Self-checking: active only in a project folder that holds the .job-search marker. In a marked project the hook fails
closed: a mail tool call it cannot check is blocked, with the reason.

Which server is the mail connector: the `mail_connector` field in config.md names it, exactly as it appears in the
tool names (`mcp__<server>__<tool>`). The hook does not guess a server name. The same connector can have a different
server name in each Claude surface (observed 2026-11-02: a UUID in the desktop app, `claude_ai_Gmail` in the CLI), so
the field takes a comma-separated list.
- Field set: every tool on that server is guarded. search_threads (parameter `query`) and get_thread / get_message
  (parameters `threadId` / `messageId`) are checked as below; every other tool on that server, including send, draft,
  reply, forward, trash and label tools, is blocked.
- Field empty or still the placeholder: the Gmail route is off (use .eml files). A tool named like a mail search or
  read tool on any server is blocked. Tools of an unidentified mail server that have other names cannot be recognised.
- A search or read tool name that appears on a server other than the configured one is blocked: if the connector is
  reconnected under a new server ID, or its tool names change, the hook blocks until config.md is updated.

TOOL NAMES: checked against the Gmail connector's published tool list and parameter schemas on 2026-11-02 (30 tools),
then tested live in a command-line session: an unlabeled search and a read of an unreturned ID were blocked, a labeled
search and a read of one of its results were allowed. A search response is `{"threads": [{"id", "messageCount",
"messages": [{"id", "threadId", "sender", "subject", "toRecipients"}]}]}`: no label IDs, so a message's labels cannot be
checked from it. If the shape ever changes so that no IDs are found, no IDs are recorded and every read by ID is
blocked (fails closed). Not tested in the desktop app.

Searches: the query must AND `label:<alerts_label>` (alerts_label is a field in config.md) with the rest. Allowed
besides the label: plain words and quoted phrases, and from: to: subject: after: before: newer_than: older_than: is:
has: (each may be negated with "-"). Blocked: OR, "|", { }, ( ), NOT, in:, category:, another label:, a negated label:,
and any other operator. Anything not on the allow-list is blocked rather than guessed.

Reads by message or thread ID: a PostToolUse call records the IDs a label-scoped search returned, in this session; a
read is allowed only for a recorded ID. State is a small file in the project's own scratch folder keyed by session ID.
If the hook has no session ID, or cannot write its state, it cannot remember IDs, so every read by ID is blocked: that
is the documented limit (README). Gmail matches a search by thread: a thread with one labeled message and other
unlabeled ones is returned whole, so a recorded ID can lead to an unlabeled message in a mixed thread (README).
"""
import json
import os
import re
import sys
import tempfile

MARKER = ".job-search"
SEARCH_TOOLS = {"search_threads"}
READ_TOOLS = {"get_thread", "get_message"}
QUERY_KEYS = ("query",)
ID_KEYS = ("threadId", "messageId")
OK_OPERATORS = {"from", "to", "subject", "after", "before", "newer_than", "older_than", "is", "has"}


def split_tool(name):
    """mcp__<server>__<tool> -> (server, tool), lowercased; a non-MCP tool has server None."""
    name = name or ""
    if not name.startswith("mcp__"):
        return None, name.lower()
    server, sep, tool = name[5:].rpartition("__")
    return (server.lower(), tool.lower()) if sep else (name[5:].lower(), "")


def norm_server(text):
    text = text.strip().strip("`\"'").lower()
    if text.startswith("mcp__"):
        text = text[5:]
    return text.rstrip("_") if text.endswith("__") else text


def config_value(project, key):
    try:
        for line in open(os.path.join(project, "config.md"), encoding="utf-8"):
            m = re.match(rf"\s*{key}\s*:\s*(.+?)\s*(?:#.*)?$", line, re.I)
            if m and "[" not in m.group(1) and m.group(1).strip():
                return m.group(1).strip()
    except OSError:
        pass
    return None


def tool_kind(name, project):
    """search | read | mail-other (a tool on the configured mail server that is neither) | stray (a mail search or read
    tool name on some other server, or with no connector configured) | None (not a mail tool this hook can see)."""
    server, tool = split_tool(name)
    mail = config_value(project, "mail_connector")
    names = {norm_server(n) for n in re.split(r"[,\s]+", mail or "") if n}
    if server is not None and server in names:
        return "search" if tool in SEARCH_TOOLS else "read" if tool in READ_TOOLS else "mail-other"
    if server is not None and tool in SEARCH_TOOLS | READ_TOOLS:
        return "stray"
    return None


def norm_label(text):
    return re.sub(r"[\s_]+", "-", text.strip().strip('"').lower())


def alerts_label(project):
    v = config_value(project, "alerts_label")
    return norm_label(v) if v else None


def tokens(query):
    """Split on spaces, keeping "quoted phrases" and operator:"quoted values" whole. Brackets are their own tokens."""
    return re.findall(r'[{}()|]|(?:[^\s"{}()|]*"[^"]*")+[^\s"{}()|]*|[^\s"{}()|]+', query)


def check_query(query, label):
    """Return None when the query is allowed, else the reason it is blocked."""
    if not isinstance(query, str) or not query.strip():
        return "no query: a search without a query reads the whole mailbox"
    has_label = False
    for tok in tokens(query):
        if tok in "{}()|" or tok.upper() in ("OR", "NOT", "AROUND"):
            return f"'{tok}' can widen the search"
        neg = tok.startswith("-")
        body = tok[1:] if neg else tok
        if ":" in body and not body.startswith('"'):
            op, _, val = body.partition(":")
            op = op.lower()
            if op == "label":
                if neg or norm_label(val) != label:
                    return "a label other than the alerts label, or a negated label"
                has_label = True
            elif op not in OK_OPERATORS:
                return f"operator '{op}:' is not allowed"
        elif neg and not body:
            return "a bare '-'"
    return None if has_label else f"the query is not restricted to label:{label}"


def state_file(project, session):
    slug = re.sub(r"[^A-Za-z0-9]", "-", os.path.realpath(project))
    base = os.path.join(f"/private/tmp/claude-{os.getuid()}" if os.path.isdir("/private/tmp") else tempfile.gettempdir(), slug)
    return os.path.join(base, f"label-guard-{re.sub(r'[^A-Za-z0-9_-]', '', session)}.json")


def load_ids(path):
    try:
        return set(json.load(open(path)))
    except (OSError, ValueError):
        return set()


def ids_in(value):
    out = []
    if isinstance(value, str):
        out.append(value)
    elif isinstance(value, (list, tuple)):
        for v in value:
            out += ids_in(v)
    return out


def returned_ids(response):
    text = json.dumps(response) if not isinstance(response, str) else response
    return set(re.findall(r'"(?:id|threadId|thread_id|messageId|message_id)"\s*:\s*"([A-Za-z0-9_-]{6,})"', text.replace('\\"', '"')))


def block(reason):
    sys.stderr.write(f"Blocked by label_guard.py: {reason}. In a job-search project the mail connector reads only the "
                     "labeled alerts (alerts_label in config.md). If you need more, say so and ask the user.\n")
    return 2


def main():
    call = None
    try:
        call = json.load(sys.stdin)
        if not isinstance(call, dict):
            raise ValueError("input is not an object")
        project = os.environ.get("CLAUDE_PROJECT_DIR") or call.get("cwd") or os.getcwd()
        if not os.path.isfile(os.path.join(project, MARKER)):
            return 0
        kind = tool_kind(str(call.get("tool_name", "")), project)
        if kind is None:
            return 0
        args = call.get("tool_input") or {}
        if not isinstance(args, dict):
            raise ValueError("tool_input is not an object")
        session = str(call.get("session_id") or "")
        label = alerts_label(project)
        if call.get("hook_event_name") == "PostToolUse":
            if kind == "search" and label and check_query(next((args[k] for k in QUERY_KEYS if k in args), None), label) is None \
                    and session:
                path = state_file(project, session)
                os.makedirs(os.path.dirname(path), exist_ok=True)
                json.dump(sorted(load_ids(path) | returned_ids(call.get("tool_response"))), open(path, "w"))
            return 0
        if kind == "stray":
            if not config_value(project, "mail_connector"):
                return block("mail_connector is not set in config.md, so the Gmail route is off (use .eml files in inbound/alerts/)")
            return block(f"{call.get('tool_name')} is not on the mail_connector server named in config.md; if the connector "
                         "was reconnected or renamed, the user updates mail_connector first")
        if kind == "mail-other":
            return block(f"{call.get('tool_name')} is not a labeled-alert search or read; only search_threads, get_thread and "
                         "get_message are allowed on the mail connector")
        if not label:
            return block("alerts_label is not set in config.md, so the labeled alerts cannot be told apart from the rest of the inbox")
        if kind == "search":
            why = check_query(next((args[k] for k in QUERY_KEYS if k in args), None), label)
            return block(why) if why else 0
        wanted = [i for k in ID_KEYS for i in ids_in(args.get(k))]
        if not wanted:
            return block("a read with no message or thread ID")
        if not session:
            return block("no session ID, so the hook cannot tell which IDs a label-scoped search returned (reads by ID are blocked)")
        known = load_ids(state_file(project, session))
        missing = [i for i in wanted if i not in known]
        return block("that ID was not returned by a label-scoped search in this session") if missing else 0
    except Exception as e:  # fail closed in a marked project, with the reason
        try:
            project = os.environ.get("CLAUDE_PROJECT_DIR") or (call or {}).get("cwd") or os.getcwd()
            marked = os.path.isfile(os.path.join(project, MARKER))
            kind = tool_kind(str((call or {}).get("tool_name", "")), project)
        except Exception:
            marked, kind = True, "?"
        if not marked or kind is None or (call or {}).get("hook_event_name") == "PostToolUse":
            return 0
        sys.stderr.write(f"Blocked by label_guard.py: the hook could not check this call ({type(e).__name__}: {e}). "
                         "Nothing ran. Tell the user the label guard failed.\n")
        return 2


if __name__ == "__main__":
    sys.exit(main())
