"""setup.py: creates a project folder from templates, never overwrites, refuses home, / and the kit. Fictional only."""
import hashlib, os, shutil, subprocess, sys, tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails = 0
def check(name, ok, detail=""):
    global fails
    print(("ok   " if ok else "FAIL ") + name + ("" if ok else f"\n      {str(detail)[:600]}"))
    fails += not ok

def snapshot(folder):
    out = {}
    for root, dirs, files in os.walk(folder):
        for f in files:
            p = os.path.join(root, f)
            out[os.path.relpath(p, folder)] = hashlib.sha256(open(p, "rb").read()).hexdigest()
        for d in dirs:
            out[os.path.relpath(os.path.join(root, d), folder) + "/"] = "dir"
    return out

T = os.path.realpath(tempfile.mkdtemp())
try:
    kit = os.path.join(T, "kit")                      # a copy of the kit, as a plugin install would hold it
    os.makedirs(kit)
    for f in ("setup.py", "kit_paths.py"):
        shutil.copy(os.path.join(REPO, f), kit)
    shutil.copytree(os.path.join(REPO, "templates"), os.path.join(kit, "templates"))
    shutil.copytree(os.path.join(REPO, ".claude-plugin"), os.path.join(kit, ".claude-plugin"))
    home = os.path.join(T, "home"); os.makedirs(home)
    def setup(cwd, env=None):
        return subprocess.run([sys.executable, os.path.join(kit, "setup.py")], cwd=cwd, capture_output=True, text=True,
                              env={**os.environ, "HOME": home, **(env or {})})
    templates = sorted(f for f in os.listdir(os.path.join(kit, "templates")) if f not in ("privacy-patterns", "gitignore"))

    proj = os.path.join(home, "job-search"); os.makedirs(proj)
    r = setup(proj)
    check("empty folder: exit 0", r.returncode == 0, r.stdout + r.stderr)
    for f in templates + [".privacy-patterns", ".gitignore", ".job-search"]:
        check(f"created {f}", os.path.isfile(os.path.join(proj, f)) and f"created  {f}" in r.stdout, r.stdout)
    for d in ("inbound", "reports", "tailored", "sent", "archive"):
        check(f"created {d}/", os.path.isdir(os.path.join(proj, d)))
    for f in templates:
        check(f"{f} is byte-identical to its template", open(os.path.join(proj, f), "rb").read() ==
              open(os.path.join(kit, "templates", f), "rb").read())
    first = r.stdout.split("FILL IN FIRST")[1].split("STILL TEMPLATES")[0]
    check("FILL IN FIRST lists config, target roles, resume, proof points",
          all(f in first for f in ("config.md", "01-target-roles.md", "00-master-resume.md", "06-proof-points.md")), first)
    check("hooks: fill guard active, privacy check not configured",
          "fill guard: active here" in r.stdout and "privacy push check: not configured" in r.stdout, r.stdout)
    marker = open(os.path.join(proj, ".job-search")).read()
    check("marker holds no path", "/" not in marker and "format: 1" in marker, marker)
    leaked = [p for p in snapshot(proj) if not p.endswith("/") and (kit.encode() in open(os.path.join(proj, p), "rb").read()
                                                                   or T.encode() in open(os.path.join(proj, p), "rb").read())]
    check("no created file contains the kit path or any temp path", not leaked, leaked)

    before = snapshot(proj)
    open(os.path.join(proj, "config.md"), "a").write("\nedited by the user\n")
    edited = hashlib.sha256(open(os.path.join(proj, "config.md"), "rb").read()).hexdigest()
    r = setup(proj)
    after = snapshot(proj)
    check("rerun: exit 0, every file kept", r.returncode == 0 and "created" not in r.stdout, r.stdout)
    check("rerun: the user's edit survives", after["config.md"] == edited)
    check("rerun: nothing else changed", {k: v for k, v in after.items() if k != "config.md"} ==
          {k: v for k, v in before.items() if k != "config.md"})
    check("rerun: an edited file leaves FILL IN FIRST", "config.md" not in r.stdout.split("FILL IN FIRST")[1].split("STILL")[0], r.stdout)

    open(os.path.join(proj, ".privacy-patterns"), "a").write("zorblax\n")
    r = setup(proj)
    check("patterns with a term: privacy check configured (1 terms)", "configured (1 terms)" in r.stdout, r.stdout)

    p2 = os.path.join(home, "two"); os.makedirs(p2)
    open(os.path.join(p2, ".gitignore"), "w").write("node_modules/\n/config.md\n")
    r = setup(p2)
    check("existing .gitignore is not changed", open(os.path.join(p2, ".gitignore")).read() == "node_modules/\n/config.md\n")
    check("missing .gitignore entries are listed", ".gitignore is missing: /02-tracker.csv" in r.stdout
          and ".gitignore is missing: /config.md" not in r.stdout, r.stdout)

    p3 = os.path.join(T, "elsewhere"); os.makedirs(p3)
    r = setup(T, {"JOB_SEARCH_DIR": p3})
    check("$JOB_SEARCH_DIR picks the project folder", r.returncode == 0 and os.path.isfile(os.path.join(p3, ".job-search")), r.stdout)

    for name, cwd in (("home folder", home), ("filesystem root", "/"), ("the kit folder", kit),
                      ("inside the kit", os.path.join(kit, "templates")), ("a folder containing the kit", T)):
        b = snapshot(cwd) if cwd not in ("/",) else None
        r = setup(cwd)
        check(f"refuses {name}: exit 1, nothing written", r.returncode == 1 and "setup refused" in r.stdout
              and (b is None or snapshot(cwd) == b), r.stdout)
    r = subprocess.run([sys.executable, os.path.join(REPO, "setup.py")], cwd=REPO, capture_output=True, text=True)
    check("refuses the real kit repo", r.returncode == 1 and "kit's own folder" in r.stdout and not os.path.exists(os.path.join(REPO, ".job-search")), r.stdout)
finally:
    shutil.rmtree(T)
print(f"{'FAILED' if fails else 'passed'}: {fails} failure(s)"); sys.exit(1 if fails else 0)
