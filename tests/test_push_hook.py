"""hooks/privacy_before_push.py (shipped with the plugin): self-checking, never blocks a fresh install. Fictional only."""
import json, os, shutil, subprocess, sys, tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
H = os.path.join(REPO, "hooks", "privacy_before_push.py")
fails = 0
def check(name, ok, detail=""):
    global fails
    print(("ok   " if ok else "FAIL ") + name + ("" if ok else f"\n      {str(detail)[:500]}"))
    fails += not ok

def hook(cmd, project, raw=None):
    p = subprocess.run([sys.executable, H], capture_output=True, text=True,
                       input=raw if raw is not None else json.dumps({"tool_name": "Bash", "tool_input": {"command": cmd}}),
                       env={**os.environ, "CLAUDE_PROJECT_DIR": project})
    return p.returncode, p.stdout + p.stderr

T = os.path.realpath(tempfile.mkdtemp())
env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
git = lambda *a, cwd: subprocess.run(["git", *a], cwd=cwd, capture_output=True, text=True, env=env)
try:
    empty = os.path.join(T, "empty"); os.makedirs(empty)
    rc, out = hook("echo job-search-agent-hook-probe", empty)
    check("probe is blocked with 'hooks are live' (any folder)", rc == 2 and "hooks are live" in out, out)
    rc, out = hook("echo job-search-agent-hook-probe && ls", empty)
    check("probe text inside another command is not the probe", rc == 0, out)
    rc, out = hook("ls -la", empty)
    check("ordinary command passes silently", rc == 0 and out == "", out)
    rc, out = hook("git push origin main", empty)
    check("fresh folder, no .privacy-patterns: push allowed, 'not configured' shown", rc == 0 and "not configured" in out, out)
    open(os.path.join(empty, ".privacy-patterns"), "w").write(open(os.path.join(REPO, "templates", "privacy-patterns")).read())
    rc, out = hook("gh pr create --fill", empty)
    check("comments-only patterns (as setup writes them): allowed, 'not configured'", rc == 0 and "not configured" in out, out)
    rc, out = hook("", empty, raw="{not json")
    check("unreadable input: passes (adds checks, never invents blocks)", rc == 0, out)

    remote = os.path.join(T, "remote.git"); git("init", "-q", "--bare", remote, cwd=T)
    proj = os.path.join(T, "proj"); os.makedirs(proj); git("init", "-q", cwd=proj)
    open(os.path.join(proj, ".gitignore"), "w").write("/.privacy-patterns\n")
    open(os.path.join(proj, ".privacy-patterns"), "w").write("# terms\nzorblax\n")
    open(os.path.join(proj, "a.txt"), "w").write("hello\n")
    git("add", ".gitignore", "a.txt", cwd=proj); git("commit", "-qm", "base", cwd=proj)
    git("remote", "add", "origin", remote, cwd=proj); git("push", "-q", "-u", "origin", "HEAD:main", cwd=proj)
    rc, out = hook("git push", proj)
    check("configured, clean: push passes with 'privacy check passed'", rc == 0 and "privacy check passed" in out, out)
    open(os.path.join(proj, "a.txt"), "a").write("Zorblax here\n"); git("commit", "-qam", "hit", cwd=proj)
    rc, out = hook("git push", proj)
    check("configured, committed hit: push blocked (exit 2), reason shown", rc == 2 and "Blocked by privacy_check.py" in out, out)
    check("block output never prints the term", "zorblax" not in out.lower(), out)
    for cmd in ("gh repo sync", "cd x && git push origin main", "/usr/bin/git -C . push"):
        rc, out = hook(cmd, proj)
        check(f"'{cmd}' is checked (blocked)", rc == 2, out)
    for cmd in ("git stash push -m x", "tail -2 .git/privacy-push.log", "echo 'git push'"):
        rc, out = hook(cmd, proj)
        check(f"'{cmd}' does not trigger", rc == 0 and out == "", out)
    log = open(os.path.join(proj, ".git", "privacy-push.log")).read()
    check("checks are logged to .git/privacy-push.log", "PASSED" in log and "BLOCKED" in log, log)
    check("no log written in a non-git folder", not os.path.exists(os.path.join(empty, ".git")))
    rc, out = subprocess.run([sys.executable, H], capture_output=True, text=True, cwd=proj,
                             input=json.dumps({"tool_name": "Bash", "cwd": proj, "tool_input": {"command": "git push"}}),
                             env={k: v for k, v in env.items() if k != "CLAUDE_PROJECT_DIR"}).returncode, ""
    check("hook input cwd is used when CLAUDE_PROJECT_DIR is unset (hit blocked)", rc == 2)
finally:
    shutil.rmtree(T)
print(f"{'FAILED' if fails else 'passed'}: {fails} failure(s)"); sys.exit(1 if fails else 0)
