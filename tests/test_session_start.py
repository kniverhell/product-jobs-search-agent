"""hooks/session_start.py: context only in a marked job-search folder; nothing elsewhere."""
import json, os, subprocess, sys, tempfile, shutil
H = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "hooks", "session_start.py")
fails = 0
def check(name, ok, detail=""):
    global fails; print(("ok   " if ok else "FAIL ") + name + ("" if ok else f"\n      {detail}")); fails += not ok
T = tempfile.mkdtemp()
try:
    plain = os.path.join(T, "plain"); os.makedirs(plain)
    marked = os.path.join(T, "marked"); os.makedirs(marked); open(os.path.join(marked, ".job-search"), "w").write("format: 1\n")
    run = lambda proj, env=None: subprocess.run([sys.executable, H], input=json.dumps({"hook_event_name": "SessionStart", "cwd": proj}),
                                                capture_output=True, text=True, env={**os.environ, "CLAUDE_PROJECT_DIR": proj, **(env or {})})
    r = run(plain)
    check("unmarked folder: no output, exit 0", r.returncode == 0 and r.stdout == "", r.stdout)
    r = run(marked, {"CLAUDE_PLUGIN_ROOT": "/fake/kit/root"})
    ctx = json.loads(r.stdout)["hookSpecificOutput"]["additionalContext"] if r.stdout else ""
    check("marked folder: SessionStart additionalContext", r.returncode == 0 and json.loads(r.stdout)["hookSpecificOutput"]["hookEventName"] == "SessionStart", r.stdout)
    check("names the kit root from CLAUDE_PLUGIN_ROOT", "Kit root (scripts, modes, templates): /fake/kit/root." in ctx, ctx)
    check("says never search outside the project and kit root", "Never search outside this project folder and the kit root" in ctx, ctx)
    check("points at the skill and commands", "job-search-agent:job-search-ops" in ctx and "/job-search-agent:<mode>" in ctx, ctx)
    check("writes nothing into the project", sorted(os.listdir(marked)) == [".job-search"], os.listdir(marked))
    r = subprocess.run([sys.executable, H], input="not json", capture_output=True, text=True, env={**os.environ, "CLAUDE_PROJECT_DIR": plain})
    check("unreadable input: exit 0", r.returncode == 0, r.stderr)
finally:
    shutil.rmtree(T)
print(f"{'FAILED' if fails else 'passed'}: {fails} failure(s)"); sys.exit(1 if fails else 0)
