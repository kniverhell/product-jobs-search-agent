import hashlib, json, os, re, subprocess, sys
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
H = R + "/hooks/fill_js_guard.py"
D = R + "/hooks/fill_read"
pages = [open(f"{D}/page-{n}.js").read() for n in range(1, 9)]
src = open(D + "/source.js").read()
CH = "mcp__claude-in-chrome__javascript_tool"
import tempfile
FILL = tempfile.mkdtemp(); open(os.path.join(FILL, "application-profile.md"), "w").write("## Factual\n")
PLAIN = tempfile.mkdtemp()
def run(raw, project=FILL):
    p = subprocess.run([sys.executable, H], input=raw, capture_output=True, text=True,
                       env={**os.environ, "CLAUDE_PROJECT_DIR": project}); return p.returncode, p.stdout + p.stderr
def call(text, tool=CH, project=FILL):
    return run(json.dumps({"tool_name": tool, "tool_input": {"action": "javascript_exec", "text": text, "tabId": 1}}), project)
p1 = pages[0]
def run_no_env(cwd):
    p = subprocess.run([sys.executable, H], capture_output=True, text=True,
                       input=json.dumps({"tool_name": CH, "cwd": cwd, "tool_input": {"text": "document.title"}}),
                       env={k: v for k, v in os.environ.items() if k != "CLAUDE_PROJECT_DIR"})
    return p.returncode, p.stdout + p.stderr
cases = [(f"page-{n} exact allowed", call(t), 0) for n, t in enumerate(pages, 1)] + [
 ("page-1 stripped ends allowed", call(p1.strip()), 0),
 ("page-1 CRLF allowed", call(p1.replace("\n", "\r\n")), 0),
 ("page-1 via in-app browser tool allowed", call(p1, tool="mcp__Claude_Browser__javascript_tool"), 0),
 ("page-1 + one extra statement blocked", call(p1.rstrip() + ";\ndocument.getElementById('submit').click()"), 2),
 ("extra statement before page-1 blocked", call("document.forms[0].submit();\n" + p1), 2),
 ("page-1 with one inner char changed blocked", call(p1.replace("BUDGET = 750", "BUDGET = 751")), 2),
 ("page-1 with inner whitespace changed blocked", call(p1.replace("  const text", "    const text")), 2),
 ("unlisted page 9 blocked", call(src.replace("__PAGE__", "9")), 2),
 ("source.js template itself blocked", call(src), 2),
 ("arbitrary script blocked", call("document.querySelector('button[type=submit]').click()"), 2),
 ("read-only-looking other script blocked", call("document.title"), 2),
 ("empty text blocked", call(""), 2),
 ("missing text blocked", run(json.dumps({"tool_name": CH, "tool_input": {"action": "javascript_exec"}})), 2),
 ("non-string text blocked", run(json.dumps({"tool_name": CH, "tool_input": {"text": ["x"]}})), 2),
 ("malformed JSON blocked", run("{not json"), 2),
 ("JSON array input blocked", run("[]"), 2),
 ("self-check: folder without application-profile.md passes any script", call("document.title", project=PLAIN), 0),
 ("self-check: folder without profile passes a click script too", call("document.querySelector('button').click()", project=PLAIN), 0),
 ("self-check: hook input cwd used when CLAUDE_PROJECT_DIR is unset", run_no_env(FILL), 2),
 ("other tool passes through", run(json.dumps({"tool_name": "mcp__claude-in-chrome__read_page", "tool_input": {}})), 0),
]
fails = 0
for name, (rc, out), want in cases:
    ok = rc == want and ("Blocked by fill_js_guard.py" in out if want == 2 else True) and ("snippet allowed" in out if want == 0 and "other tool" not in name and not name.startswith("self-check") else True)
    print(("ok   " if ok else "FAIL ") + name + ("" if ok else f" (rc={rc}) {out[:200]}")); fails += not ok
# drift: page files are exactly source.js with PAGE set, and the hook pins exactly their hashes
pinned = set(re.findall(r'"([0-9a-f]{64})"', open(H).read()))
gen = {hashlib.sha256(src.replace("__PAGE__", str(n)).strip().encode()).hexdigest() for n in range(1, 9)}
files = {hashlib.sha256(t.strip().encode()).hexdigest() for t in pages}
for name, ok in [("page files match source.js", files == gen), ("hook pins exactly the 8 page hashes", pinned == gen)]:
    print(("ok   " if ok else "FAIL ") + name); fails += not ok
total = len(cases) + 2
print(f"{total-fails} passed, {fails} failed"); sys.exit(1 if fails else 0)
