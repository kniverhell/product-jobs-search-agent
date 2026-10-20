"""Scripts find data in the project folder (cwd, or $JOB_SEARCH_DIR), never next to themselves. Fictional data only."""
import csv, os, shutil, subprocess, sys, tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails = 0
def check(name, ok, detail=""):
    global fails
    print(("ok   " if ok else "FAIL ") + name + ("" if ok else f"\n      {detail}"))
    fails += not ok

T = tempfile.mkdtemp()
try:
    kit = os.path.join(T, "kit")          # stands in for a plugin install: code only, no data
    os.makedirs(kit)
    for f in ("kit_paths.py", "tracker_io.py", "triage.py", "application_profile.py", "privacy_check.py", "scan.py"):
        shutil.copy(os.path.join(REPO, f), kit)
    proj = os.path.join(T, "proj")
    os.makedirs(proj)
    # without the .job-search marker every data script stops
    for script, args in (("tracker_io.py", []), ("triage.py", ["x"]), ("application_profile.py", []), ("scan.py", [])):
        r = subprocess.run([sys.executable, os.path.join(kit, script)] + args, cwd=proj, capture_output=True, text=True)
        check(f"no marker: {script} exits 1 with 'not a job-search folder'", r.returncode == 1 and "not a job-search folder" in r.stdout, r.stdout + r.stderr)
    code = f"import sys; sys.path.insert(0, {kit!r}); from tracker_io import read_tracker; read_tracker()"
    r = subprocess.run([sys.executable, "-c", code], cwd=proj, capture_output=True, text=True)
    check("no marker: read_tracker() from Python stops too", r.returncode == 1 and "not a job-search folder" in r.stdout, r.stdout + r.stderr)
    open(os.path.join(proj, ".job-search"), "w").write("job-search project folder\nformat: 1\ncreated: 2026-10-20\n")
    fields = open(os.path.join(REPO, "templates", "02-tracker.csv")).readline().strip().split(",")
    def row(**kw):
        return {f: kw.get(f, "") for f in fields}
    rows = [row(date_found="2026-10-01", company="Acme", title="Director, Product", url="https://example.com/1", score="4.2", status="Interviewing"),
            row(date_found="2026-10-02", company="Beta", title="Head of Product", url="https://example.com/2", score="4.4", status="Evaluated"),
            row(date_found="2026-10-03", company="Gamma", title="VP Product", url="https://example.com/3", score="3.6", status="New",
                next_action="Application deadline", next_action_due="2026-10-22")]
    with open(os.path.join(proj, "02-tracker.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, quoting=csv.QUOTE_ALL); w.writeheader(); w.writerows(rows)
    open(os.path.join(proj, "07-network.md"), "w").write("# Network\n\n## Beta\n- Sam Example, former colleague\n")
    run = lambda args, cwd, env=None: subprocess.run([sys.executable] + args, cwd=cwd, capture_output=True, text=True,
                                                      env={**os.environ, **(env or {})})

    r = run([os.path.join(kit, "tracker_io.py")], proj)
    check("tracker_io validates the project's tracker (3 rows)", r.returncode == 0 and "3 rows" in r.stdout, r.stdout + r.stderr)
    r = run([os.path.join(kit, "tracker_io.py")], kit)
    check("tracker_io run from the kit folder finds no tracker there (exit 1)", r.returncode == 1, r.stdout + r.stderr)
    r = run([os.path.join(kit, "tracker_io.py")], T, {"JOB_SEARCH_DIR": proj})
    check("$JOB_SEARCH_DIR overrides cwd", r.returncode == 0 and "3 rows" in r.stdout, r.stdout + r.stderr)
    r = run([os.path.join(kit, "triage.py"), "Acme Director", "--today", "2026-10-20"], proj)
    check("triage reads tracker and network from the project", r.returncode == 0 and "Beta" in r.stdout and "possible warm path" in r.stdout
          and r.stdout.index("DEADLINES") < r.stdout.index("BENCHMARK") and "Gamma" in r.stdout.split("BENCHMARK")[0], r.stdout + r.stderr)
    # a write through tracker_io lands in the project, with its archive there too
    code = (f"import sys; sys.path.insert(0, {kit!r}); from tracker_io import read_tracker, write_tracker; "
            "rows, f = read_tracker(); rows[0]['notes'] = 'x'; write_tracker(rows, f)")
    r = run(["-c", code], proj)
    check("write_tracker writes the project's tracker and archive/", r.returncode == 0 and os.path.isdir(os.path.join(proj, "archive"))
          and not os.path.exists(os.path.join(kit, "archive")) and not os.path.exists(os.path.join(kit, "02-tracker.csv")), r.stderr)
    open(os.path.join(proj, "application-profile.md"), "w").write("## Factual\nEmail: pat@example.com\n")
    r = run([os.path.join(kit, "application_profile.py"), "--get", "Email"], proj)
    check("application_profile reads the project's profile (non-git folder counts as untracked)", r.returncode == 0 and r.stdout.strip() == "pat@example.com", r.stdout + r.stderr)
    check("nothing was written into the kit folder", sorted(os.listdir(kit)) == sorted(
        ["kit_paths.py", "tracker_io.py", "triage.py", "application_profile.py", "privacy_check.py", "scan.py", "__pycache__"]) or
        sorted(os.listdir(kit)) == sorted(["kit_paths.py", "tracker_io.py", "triage.py", "application_profile.py", "privacy_check.py", "scan.py"]),
        os.listdir(kit))
finally:
    shutil.rmtree(T)
print(f"{'FAILED' if fails else 'passed'}: {fails} failure(s)"); sys.exit(1 if fails else 0)
