"""hooks/scope_guard.py: inside a marked project only, file tools and Bash stay in the project and the kit. Fictional only."""
import json, os, shutil, subprocess, sys, tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
H = os.path.join(REPO, "hooks", "scope_guard.py")
fails = 0
def check(name, ok, detail=""):
    global fails
    print(("ok   " if ok else "FAIL ") + name + ("" if ok else f"\n      {str(detail)[:500]}"))
    fails += not ok

T = os.path.realpath(tempfile.mkdtemp())
try:
    proj = os.path.join(T, "proj"); os.makedirs(os.path.join(proj, "reports"))
    open(os.path.join(proj, ".job-search"), "w").write("format: 1\n")
    plain = os.path.join(T, "plain"); os.makedirs(plain)
    other = os.path.join(T, "other-job-search"); os.makedirs(other); open(os.path.join(other, "secret.txt"), "w").write("x")
    home = os.path.expanduser("~")
    kit = os.path.join(T, "kit"); os.makedirs(kit); open(os.path.join(kit, "scan.py"), "w").write("")

    def hook(tool, args, project=proj, cwd=None, raw=None):
        call = {"tool_name": tool, "tool_input": args, "cwd": cwd or project}
        p = subprocess.run([sys.executable, H], capture_output=True, text=True, input=raw if raw is not None else json.dumps(call),
                           env={**os.environ, "CLAUDE_PROJECT_DIR": project, "CLAUDE_PLUGIN_ROOT": kit})
        return p.returncode, p.stdout + p.stderr
    bash = lambda c, **k: hook("Bash", {"command": c}, **k)

    # Read / Glob / Grep
    rc, out = hook("Read", {"file_path": os.path.join(other, "secret.txt")})
    check("Read outside both roots: blocked, path named, no contents", rc == 2 and "secret.txt" in out and "scope_guard" in out, out)
    check("Read in the project: allowed", hook("Read", {"file_path": os.path.join(proj, "02-tracker.csv")})[0] == 0)
    check("Read a relative path in the project: allowed", hook("Read", {"file_path": "reports/a.md"})[0] == 0)
    check("Read in the kit root: allowed", hook("Read", {"file_path": os.path.join(kit, "scan.py")})[0] == 0)
    check("Read via .. escape: blocked", hook("Read", {"file_path": os.path.join(proj, "..", "other-job-search", "secret.txt")})[0] == 2)
    check("Read ~ path: blocked", hook("Read", {"file_path": "~/job-search/scan.py"})[0] == 2)
    os.symlink(other, os.path.join(proj, "link"))
    check("Read through a symlink out of the project: blocked", hook("Read", {"file_path": os.path.join(proj, "link", "secret.txt")})[0] == 2)
    check("Grep with no path (project): allowed", hook("Grep", {"pattern": "x"})[0] == 0)
    check("Grep outside: blocked", hook("Grep", {"pattern": "x", "path": other})[0] == 2)
    check("Glob in the project: allowed", hook("Glob", {"pattern": "reports/*.md"})[0] == 0)
    check("Glob with an absolute outside pattern: blocked", hook("Glob", {"pattern": home + "/*"})[0] == 2)
    check("Glob with .. in the pattern: blocked", hook("Glob", {"pattern": "../*"})[0] == 2)
    check("Glob with an outside path: blocked", hook("Glob", {"pattern": "*.py", "path": other})[0] == 2)
    import re as _re
    mine = f"/private/tmp/claude-{os.getuid()}/" + _re.sub(r"[^A-Za-z0-9]", "-", proj)
    theirs = f"/private/tmp/claude-{os.getuid()}/" + _re.sub(r"[^A-Za-z0-9]", "-", other)
    check("Read this project's own scratch: allowed", hook("Read", {"file_path": mine + "/s/scratchpad/a.txt"})[0] == 0)
    rc, out = hook("Read", {"file_path": theirs + "/s/scratchpad/a.txt"})
    check("Read another project's scratch: blocked", rc == 2 and "scope_guard" in out, out)
    check("Read plain /tmp: blocked", hook("Read", {"file_path": "/tmp/scratch.txt"})[0] == 2)
    check("Write to own scratch: allowed", hook("Write", {"file_path": mine + "/s/scratchpad/n.txt", "content": "x"})[0] == 0)
    check("Write to another project's scratch: blocked", hook("Write", {"file_path": theirs + "/n.txt", "content": "x"})[0] == 2)
    check("Bash redirect into own scratch: allowed", bash(f"echo hi > {mine}/s/out.txt")[0] == 0)
    check("Bash redirect into /tmp: blocked", bash("echo hi > /tmp/out.txt")[0] == 2)
    # Write / Edit / NotebookEdit
    check("Write in the project: allowed", hook("Write", {"file_path": os.path.join(proj, "n.md"), "content": "x"})[0] == 0)
    check("Write outside: blocked", hook("Write", {"file_path": os.path.join(other, "n.md"), "content": "x"})[0] == 2)
    check("Edit outside: blocked", hook("Edit", {"file_path": os.path.join(other, "secret.txt"), "old_string": "a", "new_string": "b"})[0] == 2)
    check("Edit in the kit: allowed", hook("Edit", {"file_path": os.path.join(kit, "scan.py"), "old_string": "a", "new_string": "b"})[0] == 0)
    check("NotebookEdit outside: blocked", hook("NotebookEdit", {"notebook_path": os.path.join(other, "n.ipynb")})[0] == 2)
    check("NotebookEdit in the project: allowed", hook("NotebookEdit", {"notebook_path": os.path.join(proj, "n.ipynb")})[0] == 0)

    # Bash: blocked
    for cmd in ["find ~ -name scan.py", "find / -name '*.py'", f"find {other} -type f", "ls -R ~", "ls ~", "tree /opt",
                f"cat {other}/secret.txt", f"cd {other} && ls", "cd ~/job-search; ls -la", "grep -r token ~", f"rg token {other}",
                "mdfind scan.py", "locate scan.py", "du -sh ~", "ls ..", "cat ../other-job-search/secret.txt", "echo hi | tail ~/x",
                "FOO=1 find ~", "echo x > /etc/x", "python3 /etc/passwd", "git -C ~ status", "python3 x.py --out=/etc/y", "cat ~/x", "echo hi >/etc/z", "wc -l ../other-job-search/secret.txt", "cp 02-tracker.csv /tmp/t.csv", "cat $HOME/x", "zzzfake /etc/hosts", "sudo find /", "echo $(find ~ -name x)", f"ls {os.path.join(proj, 'link')}/"]:
        rc, out = bash(cmd)
        check(f"Bash blocked: {cmd}", rc == 2 and "scope_guard" in out, out)
    # Bash: allowed
    for cmd in ["ls", "ls -la reports", "find . -name '*.md'", "find", f"find {proj} -type f", f"cat {kit}/scan.py",
                f"python3 \"{kit}/triage.py\" --help", "git status", "git push --dry-run origin main", "grep -n foo 02-tracker.csv",
                "cat 02-tracker.csv 2>/dev/null", "ls /dev/null", "head -n 5 reports/a.md", "echo hello", 
                "wc -l *.md", "echo /dev/null", "git log --oneline -3", "sed s/a/b/ 02-tracker.csv", "python3 - </dev/null", "echo https://example.com/a/b", "git commit -m fix", "date +%s", "grep -rn x --include=*.md .", "find . -type f ! -name '*.md'", "python3 -c 'print(1)'"]:
        rc, out = bash(cmd)
        check(f"Bash allowed: {cmd}", rc == 0 and out == "", out)
    rc, out = bash("python3 -c 'print(1)' > /opt/x/escape.txt")
    check("quoted parentheses don't split the command; the block names python3", rc == 2 and "python3:" in out and "': " not in out, out)
    rc, out = bash("echo \"$(cat /etc/hosts)\"")
    check("command substitution inside double quotes is still checked", rc == 2 and "cat:" in out, out)
    check("a quoted ; or | is not a separator", bash("grep 'a;b|c' 02-tracker.csv")[0] == 0)
    check("Bash with a cwd outside the roots: relative find is blocked", bash("find . -name x", cwd=other)[0] == 2)

    # Self-checking
    check("unmarked folder: Read outside is untouched", hook("Read", {"file_path": os.path.join(other, "secret.txt")}, project=plain)[0] == 0)
    check("unmarked folder: find ~ is untouched", bash("find ~ -name x", project=plain)[0] == 0)
    rc, out = hook("", {}, raw="{not json")
    check("unreadable input in a marked project: blocked closed, reason given", rc == 2 and "could not check" in out, out)
    rc, out = hook("", {}, raw="{not json", project=plain)
    check("unreadable input in an unmarked folder: allowed", rc == 0, out)
    rc, out = hook("Read", ["not", "a", "dict"])
    check("internal error in a marked project: blocked closed, reason given", rc == 2 and "could not check" in out, out)
    check("other tools pass", hook("WebFetch", {"url": "https://example.com"})[0] == 0)
    check("writes nothing into the project", sorted(os.listdir(proj)) == [".job-search", "link", "reports"], os.listdir(proj))
finally:
    shutil.rmtree(T)
print(f"{'FAILED' if fails else 'passed'}: {fails} failure(s)"); sys.exit(1 if fails else 0)
