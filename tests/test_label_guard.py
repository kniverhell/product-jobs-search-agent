"""hooks/label_guard.py: the mail connector reads only the labeled alerts. Crafted inputs, fictional data. Tool names and
parameters are the Gmail connector's published ones (checked 2026-11-02, no mail read); the server ID is fictional.
Three configurations: mail_connector set, empty (Gmail route off), and a tool on some other server."""
import json, os, shutil, subprocess, sys, tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
H = os.path.join(REPO, "hooks", "label_guard.py")
fails = 0
def check(name, ok, detail=""):
    global fails
    print(("ok   " if ok else "FAIL ") + name + ("" if ok else f"\n      {str(detail)[:500]}"))
    fails += not ok

T = os.path.realpath(tempfile.mkdtemp())
try:
    proj = os.path.join(T, "proj"); os.makedirs(proj)
    open(os.path.join(proj, ".job-search"), "w").write("format: 1\n")
    SERVER = "0a1b2c3d-1111-2222-3333-444455556666"   # fictional; per-install, so config.md names it
    open(os.path.join(proj, "config.md"), "w").write(f"# Config\nalerts_label: job-alerts\nmail_connector: {SERVER}\n")
    off = os.path.join(T, "off"); os.makedirs(off)           # mail_connector left as the placeholder
    open(os.path.join(off, ".job-search"), "w").write("format: 1\n")
    open(os.path.join(off, "config.md"), "w").write("alerts_label: job-alerts\nmail_connector: [your mail connector's server name; blank = Gmail route off]\n")
    named = os.path.join(T, "named"); os.makedirs(named)     # a server with an ordinary name
    open(os.path.join(named, ".job-search"), "w").write("format: 1\n")
    open(os.path.join(named, "config.md"), "w").write("alerts_label: job-alerts\nmail_connector: claude_ai_Gmail   # my connector\n")
    plain = os.path.join(T, "plain"); os.makedirs(plain)
    nolabel = os.path.join(T, "nolabel"); os.makedirs(nolabel)
    open(os.path.join(nolabel, ".job-search"), "w").write("format: 1\n")
    open(os.path.join(nolabel, "config.md"), "w").write(f"alerts_label: [your label]\nmail_connector: {SERVER}\n")
    SEARCH = f"mcp__{SERVER}__search_threads"
    READ = f"mcp__{SERVER}__get_thread"
    READMSG = f"mcp__{SERVER}__get_message"
    SEARCH_NAMED = "mcp__claude_ai_Gmail__search_threads"

    def hook(tool, args, event="PreToolUse", project=proj, session="s-test-1", response=None, raw=None):
        call = {"hook_event_name": event, "tool_name": tool, "tool_input": args, "cwd": project, "session_id": session}
        if response is not None: call["tool_response"] = response
        if session is None: call.pop("session_id")
        p = subprocess.run([sys.executable, H], capture_output=True, text=True, input=raw if raw is not None else json.dumps(call),
                           env={**os.environ, "CLAUDE_PROJECT_DIR": project})
        return p.returncode, p.stdout + p.stderr
    search = lambda q, **k: hook(k.pop("tool", SEARCH), {"query": q}, **k)

    # searches: allowed
    for q in ["label:job-alerts", "label:job-alerts from:alerts@example.com", "label:job-alerts newer_than:7d is:unread",
              'label:job-alerts subject:"new jobs"', 'label:job-alerts "senior product"', "-from:spam@example.com label:job-alerts",
              "label:Job-Alerts product"]:
        rc, out = search(q); check(f"allowed: {q}", rc == 0 and out == "", out)
    check("allowed on a server with an ordinary name, when config.md names it (any case, trailing comment)",
          search("label:job-alerts", tool=SEARCH_NAMED, project=named)[0] == 0
          and search("label:job-alerts", tool="mcp__CLAUDE_AI_GMAIL__search_threads", project=named)[0] == 0)
    # searches: blocked
    for q in ["", "from:someone@example.com", "label:job-alerts OR in:inbox", "label:job-alerts or label:other", "label:job-alerts | in:anywhere",
              "{label:job-alerts in:sent}", "(label:job-alerts) OR (in:inbox)", "label:other", "-label:job-alerts", "label:job-alerts -label:job-alerts",
              "in:anywhere label:job-alerts", "label:job-alerts category:promotions", "label:job-alerts NOT from:x", "label:job-alerts AROUND 5 x",
              "label:job-alerts rfc822msgid:abc", "label:job-alerts list:x", "label:job-alerts-extra", "label:job-alertsOR in:inbox", "job alerts"]:
        rc, out = search(q); check(f"blocked: {q!r}", rc == 2 and "label_guard" in out, out)
    check("blocked: search with no query parameter at all", hook(SEARCH, {"maxResults": 50})[0] == 2)
    check("blocked: a query under any key but `query` is not accepted", hook(SEARCH, {"q": "label:job-alerts"})[0] == 2)

    # reads by ID: only IDs a label-scoped search returned in this session
    resp = {"threads": [{"id": "18f0aa11bb22cc33", "messageCount": 1, "viewUrl": "x",
                         "messages": [{"id": "18f0aa11bb22cc34", "labelIds": ["Label_1"], "date": "2026-11-02"}]},
                        {"id": "18f0aa11bb22cc44"}]}
    check("blocked: read by an ID no search returned", hook(READ, {"threadId": "18f0aa11bb22cc33"})[0] == 2)
    hook(SEARCH, {"query": "label:job-alerts"}, event="PostToolUse", response=resp)
    check("allowed: read of a thread ID returned by a label-scoped search in the same session", hook(READ, {"threadId": "18f0aa11bb22cc33"})[0] == 0)
    check("allowed: read of a message ID returned inside a thread", hook(READMSG, {"messageId": "18f0aa11bb22cc34", "messageFormat": "PLAIN_TEXT"})[0] == 0)
    check("blocked: read of an ID that was not returned", hook(READ, {"threadId": "ffffffffffffffff"})[0] == 2 and hook(READMSG, {"messageId": "ffffffffffffffff"})[0] == 2)
    check("blocked: ID parameters under other names are not accepted", hook(READ, {"thread_id": "18f0aa11bb22cc33"})[0] == 2 and hook(READ, {"id": "18f0aa11bb22cc33"})[0] == 2)
    check("blocked: another session cannot use them", hook(READ, {"threadId": "18f0aa11bb22cc33"}, session="s-other")[0] == 2)
    hook(SEARCH, {"query": "in:inbox"}, event="PostToolUse", response={"threads": [{"id": "deadbeef12345678"}]})
    check("IDs from an unscoped search are not recorded", hook(READ, {"threadId": "deadbeef12345678"})[0] == 2)
    hook(SEARCH, {"query": "label:job-alerts OR in:inbox"}, event="PostToolUse", response={"threads": [{"id": "0123456789abcdef"}]})
    check("IDs from a widened search are not recorded", hook(READ, {"threadId": "0123456789abcdef"})[0] == 2)
    hook(f"mcp__{SERVER}__list_drafts", {"query": "label:job-alerts"}, event="PostToolUse", response={"drafts": [{"id": "1122334455667788"}]})
    check("IDs from any other tool are not recorded", hook(READ, {"threadId": "1122334455667788"})[0] == 2)
    rc, out = hook(READ, {"threadId": "18f0aa11bb22cc33"}, session=None)
    check("no session ID: reads by ID are blocked (the documented limit)", rc == 2 and "no session ID" in out, out)
    check("blocked: a read with no ID", hook(READ, {})[0] == 2)

    # every other tool on the mail connector is blocked: the connector's full published list (30 tools, 2026-11-02)
    OTHER = ["apply_sensitive_message_label", "apply_sensitive_thread_label", "create_draft", "create_label", "delete_draft",
             "delete_label", "forward", "get_draft", "label_message", "label_thread", "list_drafts", "list_labels",
             "mark_message_spam", "mark_thread_spam", "reply", "send_message", "trash_message", "trash_thread",
             "unlabel_message", "unlabel_thread", "unmark_message_spam", "unmark_thread_spam", "untrash_message",
             "untrash_thread", "update_draft", "update_label", "update_message_labels"]
    res = {t: hook(f"mcp__{SERVER}__{t}", {"query": "label:job-alerts"}) for t in OTHER}
    check("blocked: all 27 other tools on the mail connector, send/forward/trash/label/draft included",
          len(OTHER) == 27 and all(rc == 2 and "label_guard" in out for rc, out in res.values()), {t: r[0] for t, r in res.items() if r[0] != 2})
    check("blocked: a tool name the hook has never seen, on the mail connector", hook(f"mcp__{SERVER}__brand_new_tool", {})[0] == 2)
    check("a failing PostToolUse on an unknown tool never blocks", hook(f"mcp__{SERVER}__brand_new_tool", {}, event="PostToolUse")[0] == 0)

    # case 2: mail_connector empty -> the Gmail route is off
    rc, out = hook(SEARCH, {"query": "label:job-alerts"}, project=off)
    check("mail_connector empty: a mail search is blocked even with the label, and the reason says the Gmail route is off",
          rc == 2 and "Gmail route is off" in out and ".eml" in out, out)
    check("mail_connector empty: mail reads are blocked on any server", hook(READ, {"threadId": "x"}, project=off)[0] == 2
          and hook(SEARCH_NAMED, {"query": "label:job-alerts"}, project=off)[0] == 2 and hook(READMSG, {"messageId": "x"}, project=off)[0] == 2)
    check("mail_connector empty: other tools pass", hook("mcp__x__create_draft", {})[0] == 0 and hook("mcp__x__list_pages", {}, project=off)[0] == 0
          and hook("Bash", {"command": "ls"}, project=off)[0] == 0)

    # case 3: a mail tool on a server config.md does not name (reconnected under a new ID, or renamed)
    rc, out = hook("mcp__ffffffff-0000-0000-0000-000000000000__search_threads", {"query": "label:job-alerts"})
    check("a mail search on a server other than mail_connector is blocked, reason names mail_connector", rc == 2 and "mail_connector" in out, out)
    two = os.path.join(T, "two"); os.makedirs(two)
    open(os.path.join(two, ".job-search"), "w").write("format: 1\n")
    open(os.path.join(two, "config.md"), "w").write(f"alerts_label: job-alerts\nmail_connector: {SERVER}, claude_ai_Gmail\n")
    check("mail_connector takes a comma-separated list: both surfaces' names are guarded, an unlisted one is not allowed",
          hook(SEARCH, {"query": "label:job-alerts"}, project=two)[0] == 0 and search("label:job-alerts", tool=SEARCH_NAMED, project=two)[0] == 0
          and search("in:inbox", tool=SEARCH_NAMED, project=two)[0] == 2 and hook("mcp__claude_ai_Gmail__send_message", {}, project=two)[0] == 2
          and hook("mcp__third__search_threads", {"query": "label:job-alerts"}, project=two)[0] == 2)
    check("a mail read on another server is blocked", hook("mcp__other__get_message", {"messageId": "18f0aa11bb22cc34"})[0] == 2)
    check("a mail tool name that appears on the configured server under a changed tool name is blocked",
          hook(f"mcp__{SERVER}__search_messages", {"query": "label:job-alerts"})[0] == 2)

    # self-checking and fail closed
    check("unmarked folder: everything passes", search("in:inbox", project=plain)[0] == 0 and hook(READ, {"threadId": "x"}, project=plain)[0] == 0
          and hook(f"mcp__{SERVER}__send_message", {}, project=plain)[0] == 0)
    rc, out = search("label:job-alerts", project=nolabel)
    check("marked project with no alerts_label: mail calls are blocked and the reason names config.md", rc == 2 and "alerts_label" in out, out)
    rc, out = hook("", {}, raw="{not json")
    check("unreadable input in a marked project with no tool: passes (nothing to guard)", rc == 0, out)
    rc, out = hook(SEARCH, ["not", "a", "dict"])
    check("a malformed mail call in a marked project is blocked closed, reason given", rc == 2 and "could not check" in out, out)
    check("other tools pass", hook("mcp__x__create_draft", {"to": "a"})[0] == 0 and hook("Bash", {"command": "ls"})[0] == 0)
    check("a failing PostToolUse never blocks", hook(SEARCH, ["bad"], event="PostToolUse")[0] == 0)
    check("writes nothing into the project", sorted(os.listdir(proj)) == [".job-search", "config.md"], os.listdir(proj))
finally:
    shutil.rmtree(T)
    import re
    scratch = f"/private/tmp/claude-{os.getuid()}/" + re.sub(r"[^A-Za-z0-9]", "-", os.path.join(T, "proj"))
    if os.path.isdir(scratch) and os.path.basename(scratch) != "":
        shutil.rmtree(scratch)
print(f"{'FAILED' if fails else 'passed'}: {fails} failure(s)"); sys.exit(1 if fails else 0)
