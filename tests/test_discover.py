"""scan.py discover features: status/source on scan-boards lines, paused boards scanned and labeled, probation promotion,
board detection that confirms the company (at most 3 slug tries), alert parsing without bodies or URLs, and the
rejection answer (keep / pause / remove). Fictional boards, jobs and alerts only."""
import contextlib, datetime, importlib.util, io, os, shutil, subprocess, sys, tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TODAY = datetime.date(2026, 10, 27)
fails = 0
def check(name, ok, detail=""):
    global fails
    print(("ok   " if ok else "FAIL ") + name + ("" if ok else f"\n      {str(detail)[:500]}"))
    fails += not ok

GH_JOBS = lambda *titles: {"jobs": [{"title": t, "first_published": "2026-10-20", "location": {"name": "Remote"},
                                      "absolute_url": f"https://example.com/{i}"} for i, t in enumerate(titles)]}
RESP = {
    "https://boards-api.greenhouse.io/v1/boards/acme/jobs": GH_JOBS("Director, Product Platform"),
    "https://boards-api.greenhouse.io/v1/boards/oldco/jobs": GH_JOBS("Director, Product Identity"),
    "https://boards-api.greenhouse.io/v1/boards/newco/jobs": GH_JOBS("Director, Product Growth"),
    "https://boards-api.greenhouse.io/v1/boards/staleco/jobs": GH_JOBS("Recruiter"),
    "https://boards-api.greenhouse.io/v1/boards/northwindfreight/jobs": GH_JOBS("Director, Product Platform", "Recruiter"),
    "https://boards-api.greenhouse.io/v1/boards/northwindfreight": {"name": "Northwind Freight"},
    "https://boards-api.greenhouse.io/v1/boards/brightloom/jobs": GH_JOBS("Director, Product Platform"),  # another company's board
    "https://boards-api.greenhouse.io/v1/boards/brightloom": {"name": "Brightloom Logistics"},
}
CALLS = []
def fake_fetch(url, timeout=12):
    CALLS.append(url)
    return RESP.get(url, {"_error": "HTTP 404"})

def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec); sys.modules[name] = mod; spec.loader.exec_module(mod)
    return mod

T = tempfile.mkdtemp()
try:
    shutil.copy(os.path.join(REPO, "kit_paths.py"), T); shutil.copy(os.path.join(REPO, "scan.py"), T)
    SCREEN = ("# Target roles\n\n```scan-screen\ncomp floor: 0\nlevel: \"director\", \"senior\", \"staff\"\n"
              "include: \"product\"\nexclude: \"engineer\", \"recruiter\"\n```\n\n## No-go list\n\n| Employer | Reason (optional) |\n"
              "|---|---|\n| Blockco | |\n\n---\n")
    PORTALS = "# Registry\n\n## Watchlist — priority employers\n\n| Employer | ATS | Slug / URL | Watching | Last checked |\n|---|---|---|---|---|\n\n---\n"

    def project(boards):
        p = tempfile.mkdtemp(dir=T)
        open(os.path.join(p, ".job-search"), "w").write("format: 1\n")
        open(os.path.join(p, "01-target-roles.md"), "w").write(SCREEN)
        open(os.path.join(p, "03-portals.md"), "w").write(PORTALS)
        open(os.path.join(p, "04-queries.md"), "w").write("# Queries\n\n```scan-boards\n" + boards + "```\n")
        return p

    def mod_in(p, name):
        os.chdir(p); sys.path.insert(0, T)
        m = load(os.path.join(T, "scan.py"), name)
        m.TODAY = TODAY; m.fetch = fake_fetch
        return m

    def run_main(m):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            m.main()
        return open(os.path.join(m.OUTPUT_DIR, f"{TODAY.isoformat()}-scan-candidates.md")).read()

    def read(p, f): return open(os.path.join(p, f)).read()

    # status and source parsing
    p = project("greenhouse | acme | Acme\ngreenhouse | oldco | OldCo | paused | paused 2026-10-20 rejected\n"
                "greenhouse | newco | NewCo | probation | alert 2026-10-26\n")
    m = mod_in(p, "d1")
    out = run_main(m)
    check("old 3-field line scans as active; 5-field lines parse", m.BOARD_META[("greenhouse", "acme")][0] == "active"
          and m.BOARD_META[("greenhouse", "oldco")] == ("paused", "paused 2026-10-20 rejected")
          and m.BOARD_META[("greenhouse", "newco")] == ("probation", "alert 2026-10-26"))
    check("a paused board is still scanned", "OldCo" in out and "| Director, Product Identity |" in out, out)
    check("its roles are labeled paused: rejected <date>", "OldCo (paused: rejected 2026-10-20)" in out, out)
    check("coverage counts boards by status", "Boards by status: 1 active · 1 probation · 1 paused (scanned, labeled)" in out, out)
    check("a probation board that returned real listings becomes active (source kept)",
          "greenhouse | newco | NewCo | active | alert 2026-10-26" in read(p, "04-queries.md"), read(p, "04-queries.md"))
    check("the report lists the promotion", "Probation to active (real listings read): NewCo" in out, out)
    check("an unlabeled active role carries no label", "| Acme |" in out and "Acme (paused" not in out)

    # retirement proposal and 90-day review
    p = project("greenhouse | staleco | StaleCo | probation | alert 2026-09-01\ngreenhouse | oldco | OldCo | paused | paused 2026-07-01 rejected\n")
    out = run_main(mod_in(p, "d2"))
    check("30+ days on alert with no passing role: proposed for retirement, not removed",
          "Proposed for retirement" in out and "StaleCo" in out and "StaleCo" in read(p, "04-queries.md"), out)
    check("paused 90+ days: the review asks whether to clear the label", "Paused 90+ days: keep the label or clear it? OldCo" in out, out)

    # bad status
    p = project("greenhouse | acme | Acme | sleeping\n")
    r = subprocess.run([sys.executable, os.path.join(T, "scan.py")], cwd=p, capture_output=True, text=True)
    check("an unknown status stops the scan with file:line", r.returncode == 1 and "04-queries.md:4: status must be" in r.stdout, r.stdout)

    # detection
    p = project("greenhouse | acme | Acme\n")
    m = mod_in(p, "d3")
    CALLS.clear()
    ats, slug, how, tries, tf = m.detect_board("Northwind Freight", "Director, Product Platform")
    check("detection confirms by the board's own name", (ats, slug) == ("greenhouse", "northwindfreight") and how == "board name matches", (ats, slug, how))
    CALLS.clear()
    ats, slug, how, tries, tf = m.detect_board("Brightloom Freight", "Senior Product Manager, Onboarding")
    slugs = {u.split("/boards/")[1].split("/")[0] for u in CALLS if "greenhouse" in u} | \
            {u.rsplit("/", 1)[1].split("?")[0] for u in CALLS if "ashby" in u or "lever" in u}
    check("a slug that returns another company's listings is rejected (name differs, no title match)", ats is None, (ats, slug, how))
    check("at most 3 slug candidates are tried, no retry loops", tries <= 3 and len(slugs) <= 3 and len(CALLS) <= 12, (tries, slugs, len(CALLS)))
    ats, slug, how, tries, tf = m.detect_board("Brightloom Freight", "Director, Product Platform")
    check("a board that states another company's name is a miss even when a title matches", ats is None, (ats, slug, how))
    RESP["https://api.lever.co/v0/postings/unnamedco"] = [{"text": "Director, Product Growth"}]
    ats, slug, how, tries, tf = m.detect_board("UnnamedCo", "Director, Product Growth")
    check("where the board states no name, a posting matching the alert title confirms", ats == "lever" and tf, (ats, slug, how))

    # alerts: parse the fixture, then discover
    p = project("greenhouse | acme | Acme\n")
    os.makedirs(os.path.join(p, "inbound", "alerts"))
    shutil.copy(os.path.join(REPO, "tests", "fixtures", "sample-alert.eml"), os.path.join(p, "inbound", "alerts"))
    shutil.copy(os.path.join(REPO, "tests", "fixtures", "unreadable-alert.eml"), os.path.join(p, "inbound", "alerts"))
    m = mod_in(p, "d4")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        m.cmd_parse_alerts()
    csv_text = read(p, "inbound/alerts-2026-10-27.csv")
    check("parse-alerts writes fields only: company, title, location, date", "Northwind Freight,Director, Product Platform" in csv_text.replace('"', "")
          and "Remote" in csv_text and "2026-10-27" in csv_text, csv_text)
    check("no linkedin.com or lnkd.in URL and no email body in the CSV", "linkedin" not in csv_text.lower() and "lnkd" not in csv_text.lower()
          and "http" not in csv_text and "Unsubscribe" not in csv_text and "View job" not in csv_text, csv_text)
    check("an alert the parser can't read is named, not guessed", "unreadable-alert.eml" in buf.getvalue(), buf.getvalue())
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        m.cmd_alerts()
    o = buf.getvalue()
    q = read(p, "04-queries.md")
    check("a confirmed board is appended as probation with source alert <date>", "greenhouse | northwindfreight | Northwind Freight | probation | alert 2026-10-27" in q, q)
    check("an unconfirmed company goes to the alerts-only watchlist, not dropped",
          "| Brightloom Freight | alerts-only |" in read(p, "03-portals.md") and "alerts-only watchlist" in o, o)
    check("a title that fails the filter is ignored (engineer role)", "Staff Software Engineer" not in q and "Northwind" in q)
    check("the first report line counts reads, verified and boards added", "Alerts: 3 read, 1 verified on employer sites, 0 unreadable · Boards added: 1" in o, o)
    # no-go and dedup
    open(os.path.join(p, "inbound", "alerts-2026-10-28.csv"), "w").write(
        "company,title,location,alert_date,parsed_by\nBlockco,Director Product,Remote,2026-10-28,code\nAcme,Director Product,Remote,2026-10-28,code\n"
        "Northwind Freight,Director Product,Remote,2026-10-28,code\n,,,2026-10-28,unreadable\n")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        m.cmd_alerts(os.path.join(p, "inbound", "alerts-2026-10-28.csv"))
    o = buf.getvalue()
    check("no-go and already-listed companies are skipped in code; empty rows count as unreadable",
          "Blockco: on the no-go list" in o and "Acme: already on the board list" in o and "1 unreadable" in o
          and read(p, "04-queries.md").count("northwindfreight") == 1, o)

    # the rejection answer
    p = project("greenhouse | oldco | OldCo\ngreenhouse | acme | Acme\n")
    m = mod_in(p, "d5")
    before = (read(p, "04-queries.md"), read(p, "01-target-roles.md"))
    with contextlib.redirect_stdout(io.StringIO()):
        m.cmd_decide("OldCo", "keep")
    check("Keep changes nothing", (read(p, "04-queries.md"), read(p, "01-target-roles.md")) == before)
    with contextlib.redirect_stdout(io.StringIO()):
        m.cmd_decide("OldCo", "pause")
    check("Pause sets status paused with source 'paused <date> rejected'", "greenhouse | oldco | OldCo | paused | paused 2026-10-27 rejected" in read(p, "04-queries.md"), read(p, "04-queries.md"))
    check("Pause does not touch the no-go list", read(p, "01-target-roles.md") == before[1])
    m = mod_in(p, "d6")
    out = run_main(m)
    check("a paused company is still scanned and labeled", "OldCo (paused: rejected 2026-10-27)" in out, out)
    with contextlib.redirect_stdout(io.StringIO()):
        m.cmd_decide("OldCo", "remove")
    check("Remove adds the company to the no-go list in 01-target-roles.md", "| OldCo | rejected 2026-10-27 |" in read(p, "01-target-roles.md"), read(p, "01-target-roles.md"))
    m = mod_in(p, "d7")
    out = run_main(m)
    check("Remove stops scanning it", "OldCo" not in out.split("## Candidates")[1].split("## Notes")[0] and "skipped (no-go list)" in out, out)
    # bad choice
    r = subprocess.run([sys.executable, os.path.join(T, "scan.py"), "decide", "OldCo", "maybe"], cwd=p, capture_output=True, text=True)
    check("an unknown answer changes nothing and exits 1", r.returncode == 1)
finally:
    os.chdir("/"); shutil.rmtree(T)
print(f"{'FAILED' if fails else 'passed'}: {fails} failure(s)"); sys.exit(1 if fails else 0)
