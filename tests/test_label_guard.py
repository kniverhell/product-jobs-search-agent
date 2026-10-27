"""hooks/label_guard.py: the mail connector reads only the labeled alerts. Crafted inputs, fictional data. Tool names are
patterns of the names the connector is expected to use (NOT verified on a real install; see the hook's docstring)."""
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
    open(os.path.join(proj, "config.md"), "w").write("# Config\nalerts_label: job-alerts\n")
    plain = os.path.join(T, "plain"); os.makedirs(plain)
    nolabel = os.path.join(T, "nolabel"); os.makedirs(nolabel)
    open(os.path.join(nolabel, ".job-search"), "w").write("format: 1\n")
    open(os.path.join(nolabel, "config.md"), "w").write("alerts_label: [your label]\n")
    SEARCH = "mcp__0a1b2c3d-1111-2222-3333-444455556666__search_threads"   # per-install server ID, suffix is the tool
    READ = "mcp__0a1b2c3d-1111-2222-3333-444455556666__get_thread"
    SEARCH2 = "mcp__claude_ai_Gmail__search_messages"

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
    check("allowed on another install's server ID and on a named server", search("label:job-alerts", tool=SEARCH2)[0] == 0)
    # searches: blocked
    for q in ["", "from:someone@example.com", "label:job-alerts OR in:inbox", "label:job-alerts or label:other", "label:job-alerts | in:anywhere",
              "{label:job-alerts in:sent}", "(label:job-alerts) OR (in:inbox)", "label:other", "-label:job-alerts", "label:job-alerts -label:job-alerts",
              "in:anywhere label:job-alerts", "label:job-alerts category:promotions", "label:job-alerts NOT from:x", "label:job-alerts AROUND 5 x",
              "label:job-alerts rfc822msgid:abc", "label:job-alerts list:x", "label:job-alerts-extra", "label:job-alertsOR in:inbox", "job alerts"]:
        rc, out = search(q); check(f"blocked: {q!r}", rc == 2 and "label_guard" in out, out)
    check("blocked: search with no query parameter at all", hook(SEARCH, {"maxResults": 50})[0] == 2)
    check("blocked: the query under the alternative key q is checked too", hook(SEARCH, {"q": "label:x OR in:inbox"})[0] == 2
          and hook(SEARCH, {"q": "label:job-alerts"})[0] == 0)

    # reads by ID: only IDs a label-scoped search returned in this session
    resp = {"threads": [{"id": "18f0aa11bb22cc33", "snippet": "x"}, {"id": "18f0aa11bb22cc44"}]}
    check("blocked: read by an ID no search returned", hook(READ, {"thread_id": "18f0aa11bb22cc33"})[0] == 2)
    hook(SEARCH, {"query": "label:job-alerts"}, event="PostToolUse", response=resp)
    check("allowed: read of an ID returned by a label-scoped search in the same session", hook(READ, {"thread_id": "18f0aa11bb22cc33"})[0] == 0)
    check("blocked: read of an ID that was not returned", hook(READ, {"thread_id": "ffffffffffffffff"})[0] == 2)
    check("blocked: a list of IDs where one was not returned", hook(READ, {"ids": ["18f0aa11bb22cc33", "ffffffffffffffff"]})[0] == 2)
    check("blocked: another session cannot use them", hook(READ, {"thread_id": "18f0aa11bb22cc33"}, session="s-other")[0] == 2)
    hook(SEARCH, {"query": "in:inbox"}, event="PostToolUse", response={"threads": [{"id": "deadbeef12345678"}]})
    check("IDs from an unscoped search are not recorded", hook(READ, {"thread_id": "deadbeef12345678"})[0] == 2)
    hook(SEARCH, {"query": "label:job-alerts OR in:inbox"}, event="PostToolUse", response={"threads": [{"id": "0123456789abcdef"}]})
    check("IDs from a widened search are not recorded", hook(READ, {"thread_id": "0123456789abcdef"})[0] == 2)
    rc, out = hook(READ, {"thread_id": "18f0aa11bb22cc33"}, session=None)
    check("no session ID: reads by ID are blocked (the documented limit)", rc == 2 and "no session ID" in out, out)
    check("blocked: a read with no ID", hook(READ, {})[0] == 2)

    # self-checking and fail closed
    check("unmarked folder: everything passes", search("in:inbox", project=plain)[0] == 0 and hook(READ, {"thread_id": "x"}, project=plain)[0] == 0)
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
