#!/usr/bin/env python3
"""Claude Code hook (PreToolUse and PostToolUse): in a job-search project, the Gmail connector may read only the
labeled alerts. Ships with the plugin, wired in hooks/hooks.json. ROADMAP: discover mode (1.4.0).

Self-checking: active only in a project folder that holds the .job-search marker. In a marked project the hook fails
closed: a mail tool call it cannot check is blocked, with the reason.

TOOL NAMES, NOT VERIFIED ON A REAL INSTALL. The connector's server ID differs per install (a UUID), so tools are matched
by the tool-name suffix, not the server. SEARCH_TOOLS and READ_TOOLS below are the names the Gmail connector is expected
to use; QUERY_KEYS and ID_KEYS are the parameter names. They were written without a Gmail connector attached to the
build session. Before relying on this hook, list the connector's real tool names and parameters and fix these four sets;
a name that is missing here is not guarded (the hook cannot block a tool it does not recognise).

Searches: the query must AND `label:<alerts_label>` (alerts_label is a field in config.md) with the rest. Allowed
besides the label: plain words and quoted phrases, and from: to: subject: after: before: newer_than: older_than: is:
has: (each may be negated with "-"). Blocked: OR, "|", { }, ( ), NOT, in:, category:, another label:, a negated label:,
and any other operator. Anything not on the allow-list is blocked rather than guessed.

Reads by message or thread ID: a PostToolUse call records the IDs a label-scoped search returned, in this session; a
read is allowed only for a recorded ID. State is a small file in the project's own scratch folder keyed by session ID.
If the hook has no session ID, or cannot write its state, it cannot remember IDs, so every read by ID is blocked: that
is the documented limit (README).
"""
import json
import os
import re
import sys
import tempfile

MARKER = ".job-search"
SEARCH_TOOLS = {"search_threads", "search_messages", "search_emails", "list_threads", "list_messages", "list_emails",
                "gmail_search_messages", "gmail_search_threads"}
READ_TOOLS = {"get_thread", "get_message", "read_thread", "read_message", "read_email", "get_email",
              "gmail_read_message", "gmail_read_thread", "get_threads", "get_messages"}
QUERY_KEYS = ("query", "q", "search", "search_query")
ID_KEYS = ("thread_id", "threadId", "message_id", "messageId", "id", "ids", "thread_ids", "message_ids")
OK_OPERATORS = {"from", "to", "subject", "after", "before", "newer_than", "older_than", "is", "has"}


def tool_kind(name):
    base = re.sub(r"^mcp__[^_]+(?:_[^_]+)*?__", "", name or "")
    base = base.split("__")[-1].lower()
    if base in SEARCH_TOOLS:
        return "search"
    if base in READ_TOOLS:
        return "read"
    return None


def norm_label(text):
    return re.sub(r"[\s_]+", "-", text.strip().strip('"').lower())


def alerts_label(project):
    try:
        for line in open(os.path.join(project, "config.md"), encoding="utf-8"):
            m = re.match(r"\s*alerts_label\s*:\s*(.+?)\s*(?:#.*)?$", line, re.I)
            if m and "[" not in m.group(1) and m.group(1).strip():
                return norm_label(m.group(1))
    except OSError:
        pass
    return None


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
        kind = tool_kind(str(call.get("tool_name", "")))
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
            kind = tool_kind(str((call or {}).get("tool_name", "")))
        except Exception:
            marked, kind = True, "?"
        if not marked or kind is None or (call or {}).get("hook_event_name") == "PostToolUse":
            return 0
        sys.stderr.write(f"Blocked by label_guard.py: the hook could not check this call ({type(e).__name__}: {e}). "
                         "Nothing ran. Tell the user the label guard failed.\n")
        return 2


if __name__ == "__main__":
    sys.exit(main())
