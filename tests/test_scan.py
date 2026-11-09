"""scan.py: old (BASELINE, constants in the script) vs new (config read from the project folder) must produce the same
output for the same config and the same recorded API responses, apart from the intended changes listed below. Plus every
config error exits 1 with file:line, and the posting-age window (ROADMAP item 14). Fictional boards and jobs only."""
import contextlib, datetime, hashlib, importlib.util, io, json, os, re, shutil, subprocess, sys, tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASELINE = "3502055"  # last commit where scan.py kept its settings in the script
TODAY = datetime.date(2026, 10, 20)
# Intended changes since BASELINE, each checked explicitly below instead of being ignored:
#  1. two hints that used to say "edit scan.py" (EXPECTED_DIFFS);
#  2. a first run (no earlier read recorded) adds the line AGE_FIRST_RUN and a blank line after it;
#  3. the bold coverage line gains " (dropped by age: 0 · undated kept: 1)" (one undated posting in the fixture).
AGE_FIRST_RUN = "Age window: no limit this run (no earlier read recorded for any board)."
AGE_TAIL = " (dropped by age: 0 · undated kept: 1)"
EXPECTED_DIFFS = {  # the two hints that used to say "edit scan.py"
    ("No comp floor set. Set COMP_FLOOR in scan.py to filter by base salary.",
     "No comp floor set. Set 'comp floor:' in the scan-screen block of 01-target-roles.md to filter by base salary."),
    ("- Lever: only confirmed-slug companies included. Add slugs to LEVER list as discovered.",
     "- Lever: only confirmed-slug companies included. Add slugs to the scan-boards block in 04-queries.md as discovered."),
}
BOARDS = {"greenhouse": [("acme-gh", "Acme"), ("delta-gh", "Delta")], "ashby": [("beta-ash", "Beta")],
          "lever": [("gamma-lev", "Gamma"), ("omega-lev", "Omega")]}
ms = lambda d: int(datetime.datetime(*d, tzinfo=datetime.timezone.utc).timestamp() * 1000)
RESPONSES = {
    "https://boards-api.greenhouse.io/v1/boards/acme-gh/jobs": {"jobs": [
        {"title": "Director, Product Platform", "first_published": "2026-10-01T00:00:00Z", "updated_at": "2026-10-05",
         "location": {"name": "Remote"}, "absolute_url": "https://example.com/a1"},
        {"title": "Senior Software Engineer", "first_published": "2026-10-01", "location": {"name": "NYC"}, "absolute_url": "https://example.com/a2"},
        {"title": "VP Product, Identity", "first_published": "2026-09-05", "location": {"name": "SF"}, "absolute_url": "https://example.com/a3"},
        {"title": "Head of Sales", "first_published": "2026-10-01", "location": {"name": "SF"}, "absolute_url": "https://example.com/a4"},
        {"title": "Principal Product Manager, Fraud", "first_published": "2026-06-01", "location": "Austin", "absolute_url": "https://example.com/a5"},
    ]},
    "https://boards-api.greenhouse.io/v1/boards/delta-gh/jobs": {"_error": "HTTP 404"},
    "https://api.ashbyhq.com/posting-api/job-board/beta-ash?includeCompensation=true": {"jobPostings": [
        {"title": "Director of Product, Trust", "publishedAt": "2026-08-01T00:00:00Z", "location": "Remote", "jobUrl": "https://example.com/b1",
         "compensation": {"summaryComponents": [{"label": "$150,000 – $190,000"}]}},
        {"title": "Head of Product, Onboarding", "publishedAt": "2026-10-10", "location": "", "workplaceType": "Hybrid", "applyUrl": "https://example.com/b2",
         "compensation": {"summaryComponents": [{"label": "$100,000 – $140,000"}]}},
        {"title": "Staff Product Manager, KYC", "publishedAt": None, "location": "London", "jobUrl": "https://example.com/b3"},
        {"title": "Recruiter", "publishedAt": "2026-10-10", "jobUrl": "https://example.com/b4"},
    ]},
    "https://api.lever.co/v0/postings/gamma-lev": [
        {"text": "Senior Director, Product", "createdAt": ms((2026, 9, 1)), "categories": {"location": "Boston"},
         "hostedUrl": "https://example.com/g1", "salaryRange": {"min": 170000, "max": 210000, "currency": "USD"}},
        {"text": "Director, Platform Security", "createdAt": ms((2026, 10, 15)), "categories": {"location": "Denver"},
         "hostedUrl": "https://example.com/g2", "salaryRange": {"min": 120000, "max": 150000, "currency": "USD"}},
    ],
    "https://api.lever.co/v0/postings/omega-lev": {"ok": False, "error": "Document not found"},
}


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def run(mod):
    mod.TODAY = TODAY
    mod.fetch = lambda url, timeout=12: RESPONSES[url]
    with contextlib.redirect_stdout(io.StringIO()):
        mod.main()
    return open(os.path.join(mod.OUTPUT_DIR, f"{TODAY.isoformat()}-scan-candidates.md")).read()


def q(terms):
    return ", ".join(f'"{t}"' for t in terms)


def write_config(proj, floor, old, boards=BOARDS, screen_extra=""):
    open(os.path.join(proj, ".job-search"), "w").write("job-search project folder\nformat: 1\n")
    with open(os.path.join(proj, "01-target-roles.md"), "w") as f:
        f.write(f"# Target roles\n\n```scan-screen\n# fixture\ncomp floor: {floor:,}\nlevel: {q(old.SENIORITY[:6])}\n"
                f"level: {q(old.SENIORITY[6:])}\ninclude: {q(old.DOMAIN)}\nexclude: {q(old.EXCLUDE)}\n{screen_extra}```\n")
    with open(os.path.join(proj, "04-queries.md"), "w") as f:
        f.write("# Queries\n\n```scan-boards\n" + "".join(f"{a} | {s} | {l}\n" for a in boards for s, l in boards[a]) + "```\n")


fails = 0
def check(name, ok, detail=""):
    global fails
    print(("ok   " if ok else "FAIL ") + name + ("" if ok else f"\n      {detail}"))
    fails += not ok


T = tempfile.mkdtemp()
try:
    old_src = subprocess.run(["git", "show", f"{BASELINE}:scan.py"], cwd=REPO, capture_output=True, text=True, check=True).stdout
    open(os.path.join(T, "scan_old.py"), "w").write(old_src)
    old = load(os.path.join(T, "scan_old.py"), "scan_old")
    for floor in (0, 160000):
        o = os.path.join(T, f"old{floor}"); os.makedirs(o)
        old.OUTPUT_DIR, old.COMP_FLOOR = o, floor
        old.GREENHOUSE, old.ASHBY, old.LEVER = BOARDS["greenhouse"], BOARDS["ashby"], BOARDS["lever"]
        old_out = run(old)
        proj = os.path.join(T, f"proj{floor}"); os.makedirs(proj)
        shutil.copy(os.path.join(REPO, "kit_paths.py"), os.path.join(T, "kit_paths.py"))
        shutil.copy(os.path.join(REPO, "scan.py"), os.path.join(T, "scan_new.py"))
        write_config(proj, floor, old)
        os.chdir(proj); sys.path.insert(0, T)
        new = load(os.path.join(T, "scan_new.py"), f"scan_new{floor}")
        new_out = run(new)
        ol, nl = old_out.splitlines(), new_out.splitlines()
        i = nl.index(AGE_FIRST_RUN) if AGE_FIRST_RUN in nl else -1
        check(f"floor {floor:,}: first run says there is no age limit, and why (blank line after)", i > 0 and nl[i + 1] == "")
        if i > 0:
            del nl[i:i + 2]
        check(f"floor {floor:,}: coverage line carries the age counts", any(l.endswith(AGE_TAIL + ".**") for l in nl))
        nl = [l.replace(AGE_TAIL, "") if l.endswith(AGE_TAIL + ".**") else l for l in nl]
        diffs = {(a, b) for a, b in zip(ol, nl) if a != b}
        check(f"floor {floor:,}: same line count ({len(ol)})", len(ol) == len(nl), f"{len(ol)} vs {len(nl)}")
        check(f"floor {floor:,}: only the expected hint lines differ ({len(diffs)})", diffs <= EXPECTED_DIFFS, sorted(diffs - EXPECTED_DIFFS))
        check(f"floor {floor:,}: output written to the project's inbound/", os.path.realpath(new.OUTPUT_DIR) == os.path.realpath(os.path.join(proj, "inbound")))
        check(f"floor {floor:,}: candidates present", "| Acme |" in new_out and "| Gamma |" in new_out, new_out[:300])

    # config errors: each exits 1 with STOP and names the file (and line where there is one)
    def scan_in(proj):
        return subprocess.run([sys.executable, os.path.join(T, "scan_new.py")], cwd=proj, capture_output=True, text=True)
    cases = []
    def case(name, setup, want):
        p = tempfile.mkdtemp(dir=T); write_config(p, 160000, old); setup(p); cases.append((name, p, want))
    def sub(p, fname, a, b):
        f = os.path.join(p, fname); s = open(f).read(); assert a in s, a; open(f, "w").write(s.replace(a, b, 1))
    case("missing 01-target-roles.md", lambda p: os.remove(os.path.join(p, "01-target-roles.md")), "01-target-roles.md not found")
    case("missing 04-queries.md", lambda p: os.remove(os.path.join(p, "04-queries.md")), "04-queries.md not found")
    case("no scan-screen block", lambda p: sub(p, "01-target-roles.md", "```scan-screen", "```text"), "has no ```scan-screen block")
    case("unclosed block", lambda p: open(os.path.join(p, "04-queries.md"), "w").write("```scan-boards\ngreenhouse | a | A\n"), "never closed")
    case("placeholder comp floor", lambda p: sub(p, "01-target-roles.md", "comp floor: 160,000", "comp floor: [your floor]"), "01-target-roles.md:5: placeholder")
    case("non-number comp floor", lambda p: sub(p, "01-target-roles.md", "comp floor: 160,000", "comp floor: lots"), "01-target-roles.md:5: comp floor must be")
    case("unknown key", lambda p: sub(p, "01-target-roles.md", "# fixture", "seniority: \"x\""), "01-target-roles.md:4: expected 'comp floor:'")
    case("unquoted terms", lambda p: sub(p, "01-target-roles.md", 'include: "', 'include: product, "'), "01-target-roles.md:8: expected quoted terms")
    case("placeholder term", lambda p: sub(p, "01-target-roles.md", 'exclude: "', 'exclude: "[your words]", "'), "01-target-roles.md:9: placeholder")
    case("empty list", lambda p: sub(p, "01-target-roles.md", "exclude: ", "# exclude: "), "no terms for 'exclude:'")
    case("no comp floor line", lambda p: sub(p, "01-target-roles.md", "comp floor: 160,000", "# none"), "no 'comp floor:' line")
    case("bad ats name", lambda p: sub(p, "04-queries.md", "greenhouse | acme-gh", "workday | acme-gh"), "04-queries.md:4: expected 'greenhouse | slug | Label'")
    case("two-field board line", lambda p: sub(p, "04-queries.md", "greenhouse | acme-gh | Acme", "greenhouse | acme-gh"), "04-queries.md:4: expected")
    case("placeholder board", lambda p: sub(p, "04-queries.md", "greenhouse | acme-gh | Acme", "greenhouse | [slug] | [Company]"), "04-queries.md:4: placeholder")
    case("no boards", lambda p: open(os.path.join(p, "04-queries.md"), "w").write("```scan-boards\n# none yet\n```\n"), "lists no boards")
    case("lookback days 0", lambda p: sub(p, "01-target-roles.md", "# fixture", "lookback days: 0"), "01-target-roles.md:4: lookback days must be a whole number of at least 1")
    case("lookback days not a number", lambda p: sub(p, "01-target-roles.md", "# fixture", "lookback days: soon"), "01-target-roles.md:4: lookback days must be")
    case("lookback days decimal", lambda p: sub(p, "01-target-roles.md", "# fixture", "lookback days: 2.5"), "01-target-roles.md:4: lookback days must be")
    case("lookback days negative", lambda p: sub(p, "01-target-roles.md", "# fixture", "lookback days: -3"), "01-target-roles.md:4: lookback days must be")
    case("lookback days placeholder", lambda p: sub(p, "01-target-roles.md", "# fixture", "lookback days: [N]"), "01-target-roles.md:4: placeholder")
    case("lookback days twice", lambda p: sub(p, "01-target-roles.md", "# fixture", "lookback days: 5\nlookback days: 6"), "01-target-roles.md:5: 'lookback days:' is given twice")
    for name, p, want in cases:
        r = scan_in(p)
        ok = r.returncode == 1 and r.stdout.startswith("STOP: ") and want in r.stdout and not os.path.exists(os.path.join(p, "inbound"))
        check(f"config error, {name}: exit 1, '{want}'", ok, f"rc={r.returncode} {r.stdout.strip()[:200]}")
    # the template blocks must stop the scan (placeholders only, no defaults)
    p = tempfile.mkdtemp(dir=T)
    open(os.path.join(p, ".job-search"), "w").write("format: 1\n")
    for f in ("01-target-roles.md", "04-queries.md"):
        shutil.copy(os.path.join(REPO, "templates", f), p)
    r = scan_in(p)
    check("untouched templates stop the scan with a placeholder message", r.returncode == 1 and "placeholder" in r.stdout, r.stdout.strip()[:200])

    # ── Posting-age window (ROADMAP item 14) ─────────────────────────────────────
    D = datetime.date
    ONE = {"greenhouse": [("age-gh", "AgeCo")], "ashby": [], "lever": []}
    seq = [0]
    gh = lambda slug: f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"
    def job(jid, posted):
        j = {"title": "Director, Product Platform", "location": {"name": "Remote"}, "absolute_url": f"https://example.com/{jid}"}
        if posted:
            j["first_published"] = posted
        return j
    shown = lambda text: set(re.findall(r"\| https://example\.com/([\w-]+) \|", text))
    def new_project(boards=ONE, extra=""):
        d = tempfile.mkdtemp(dir=T)
        write_config(d, 0, old, boards=boards, screen_extra=extra)
        os.chdir(d); seq[0] += 1
        return d, load(os.path.join(T, "scan_new.py"), f"scan_age{seq[0]}")
    def go(mod, today, responses, **kw):
        mod.TODAY = today
        mod.fetch = lambda url, timeout=12: responses.get(url, {"_error": "HTTP 500"})
        with contextlib.redirect_stdout(io.StringIO()):
            mod.main(**kw)
        return open(os.path.join(mod.OUTPUT_DIR, f"{today.isoformat()}-scan-candidates.md")).read()
    def state_of(d):
        return json.load(open(os.path.join(d, "inbound", "scan-state.json")))["boards"]
    d1, d2 = D(2026, 11, 1), D(2026, 11, 2)
    POSTS = {gh("age-gh"): {"jobs": [job("old60", "2026-09-02"), job("edge8", "2026-10-25"), job("edge9", "2026-10-24"), job("new1", "2026-10-31")]}}

    d, m = new_project()
    t1 = go(m, d1, POSTS)
    check("age: first run has no limit, shows every posting, says why", shown(t1) == {"old60", "edge8", "edge9", "new1"} and AGE_FIRST_RUN in t1, shown(t1))
    check("age: the state file is written under inbound/ after the scan", state_of(d) == {"greenhouse|age-gh": {"last_read": "2026-11-01", "prior_read": None}}, state_of(d))
    t2 = go(m, d2, POSTS)
    check("age: second run at the default 8: 8 days old kept, 9 dropped, older dropped", shown(t2) == {"edge8", "new1"}, shown(t2))
    check("age: the drop count is in the coverage line and the age line names the window",
          "dropped by age: 2" in t2 and "Age window: 8 days (lookback days)." in t2, t2[:600])
    t2b = go(m, d2, POSTS)
    check("age: same-day rerun returns the same list as the first run that day", shown(t2b) == shown(t2) and state_of(d) == {"greenhouse|age-gh": {"last_read": "2026-11-02", "prior_read": "2026-11-01"}}, state_of(d))
    d, m = new_project()
    go(m, d1, POSTS); go(m, d1, POSTS)
    t1b = go(m, d1, POSTS)
    check("age: same-day rerun of a first run still has no limit (the backlog is not lost)", shown(t1b) == {"old60", "edge8", "edge9", "new1"}, shown(t1b))

    d, m = new_project(extra="lookback days: 3\n")
    go(m, d1, POSTS)
    t = go(m, d2, POSTS)
    check("age: lookback days in the screen block sets the window (3: 2 days old kept, 8 dropped)", shown(t) == {"new1"} and "Age window: 3 days (lookback days)." in t, shown(t))

    d, m = new_project()
    go(m, d1, POSTS)
    open(os.path.join(d, "04-queries.md"), "w").write("```scan-boards\ngreenhouse | age-gh | AgeCo\ngreenhouse | late-gh | LateCo\n```\n")
    R = dict(POSTS); R[gh("late-gh")] = {"jobs": [job("late-old", "2026-08-01"), job("late-new", "2026-10-31")]}
    t = go(m, d2, R)
    check("age: a board added after the first run has no limit; the other board still filters",
          shown(t) == {"edge8", "new1", "late-old", "late-new"} and "No limit for LateCo (no earlier read recorded)." in t, shown(t))

    d, m = new_project()
    go(m, d1, POSTS)
    t = go(m, d2, {})
    check("age: a failed board is not recorded: it keeps its old read date", "Failed: 1 (AgeCo" in t and state_of(d)["greenhouse|age-gh"]["last_read"] == "2026-11-01", state_of(d))
    R = {gh("age-gh"): {"jobs": [job("p10", "2026-10-31"), job("p11", "2026-10-30"), job("gap", "2026-11-05")]}}
    t = go(m, D(2026, 11, 10), R)
    check("age: after a failed read the next window covers the gap (9 days + 1 = 10: 10 kept, 11 dropped)",
          shown(t) == {"p10", "gap"} and "longer after a gap or a failed read: AgeCo 10 days" in t, shown(t))

    d, m = new_project()
    go(m, d1, POSTS)
    R = {gh("age-gh"): {"jobs": [job("gap1", "2026-11-02"), job("gap2", "2026-11-20"), job("edge21", "2026-10-31"), job("edge22", "2026-10-30")]}}
    t = go(m, D(2026, 11, 21), R)
    check("age: 20 days between runs: nothing posted in the gap is dropped (window 21)",
          {"gap1", "gap2", "edge21"} <= shown(t) and "edge22" not in shown(t), shown(t))

    d, m = new_project()
    os.makedirs(os.path.join(d, "inbound"))
    for day in ("2026-10-10", "2026-10-20"):
        open(os.path.join(d, "inbound", f"{day}-scan-candidates.md"), "w").write("# earlier scan\n")
    R = {gh("age-gh"): {"jobs": [job("e13", "2026-10-19"), job("e14", "2026-10-18")]}}
    t = go(m, d1, R)
    check("age: no state file but earlier scans: warns and uses the newest earlier date (10-20: window 13)",
          shown(t) == {"e13"} and "using the date of the newest earlier scan (2026-10-20)" in t, shown(t))
    t = go(m, d1, R)
    check("age: that upgrade run's same-day rerun gives the same list", shown(t) == {"e13"}, shown(t))
    check("age: the upgrade run then writes the state file", "greenhouse|age-gh" in state_of(d))

    d, m = new_project()
    R = {gh("age-gh"): {"jobs": [job("dated", "2026-10-31"), job("nodate", None)]}}
    t = go(m, d1, R)
    check("age: first run (no limit) counts the undated posting but does not flag it", "undated kept: 1" in t and "undated, kept" not in t)
    t = go(m, d2, R)
    check("age: a windowed run keeps the undated posting, flags it and counts it",
          shown(t) == {"dated", "nodate"} and "undated, kept" in t and "undated kept: 1" in t, shown(t))

    # one-run overrides
    d, m = new_project()
    go(m, d1, POSTS)
    cfg_hash = lambda: hashlib.sha256(open(os.path.join(d, "01-target-roles.md"), "rb").read()).hexdigest()
    h0 = cfg_hash()
    R = {gh("age-gh"): {"jobs": [job("a2", "2026-11-19"), job("a20", "2026-11-01"), job("a50", "2026-10-02")]}}
    d21 = D(2026, 11, 21)
    t = go(m, d21, R, since=3)
    check("age: --since N applies to every board for that run only", shown(t) == {"a2"} and "3 days on every board this run (--since)" in t, shown(t))
    check("age: a --since run narrower than the board's window does not move its read date", state_of(d)["greenhouse|age-gh"]["last_read"] == "2026-11-01")
    t = go(m, D(2026, 11, 22), R)
    check("age: the next normal run is not affected by the --since run (window covers the gap)", {"a2", "a20"} <= shown(t) and "a50" not in shown(t), shown(t))
    check("age: --since never changes the lookback setting", cfg_hash() == h0)
    d, m = new_project()
    go(m, d1, POSTS)
    t = go(m, d21, R, all_runs=True)
    check("age: --all shows everything for that run and says so", shown(t) == {"a2", "a20", "a50"} and "no limit this run (--all)" in t, shown(t))
    t = go(m, D(2026, 11, 22), R)
    check("age: after an --all run the next normal run filters again (the read was recorded)", shown(t) == {"a2"}, shown(t))
    for args in (["--since"], ["--since", "0"], ["--since", "x"], ["--all", "3"], ["--all", "--since", "2"]):
        r = subprocess.run([sys.executable, os.path.join(T, "scan_new.py"), *args], cwd=d, capture_output=True, text=True)
        check(f"age: bad option {' '.join(args)} exits 2 with usage", r.returncode == 2 and "Usage" in r.stdout, r.stdout[:120])

    # retirement and promotion must not depend on the window
    def board_section(text):
        return re.search(r"## Board status changes and proposals\n(.*?)(?=\n## |\Z)", text, re.S).group(1) if "## Board status changes" in text else ""
    PROB = {"greenhouse": [("prob-gh", "ProbCo")], "ashby": [], "lever": []}
    def prob_run(jobs, state):
        d, m = new_project(PROB)
        open(os.path.join(d, "04-queries.md"), "w").write("```scan-boards\ngreenhouse | prob-gh | ProbCo | probation | alert 2026-09-01\n```\n")
        if state:
            os.makedirs(os.path.join(d, "inbound")); json.dump({"boards": state}, open(os.path.join(d, "inbound", "scan-state.json"), "w"))
        return go(m, d1, {gh("prob-gh"): {"jobs": jobs}})
    stale = {"greenhouse|prob-gh": {"last_read": "2026-10-31", "prior_read": None}}
    a, b = prob_run([job("pold", "2026-10-02")], None), prob_run([job("pold", "2026-10-02")], stale)
    check("age: promotion is the same with and without the window (the old posting is dropped only with it)",
          "Probation to active" in board_section(a) and board_section(a) == board_section(b) and shown(a) == {"pold"} and shown(b) == set(), (board_section(a), board_section(b)))
    a, b = prob_run([], None), prob_run([], stale)
    check("age: retirement is the same with and without the window", "Proposed for retirement" in board_section(a) and board_section(a) == board_section(b), (board_section(a), board_section(b)))
    a, b = prob_run([job("pold", "2026-10-02")], None), prob_run([job("pold", "2026-10-02")], stale)
    check("age: a board whose only postings are dropped by age is not proposed for retirement", "Proposed for retirement" not in board_section(b))
finally:
    os.chdir("/"); shutil.rmtree(T)
print(f"{'FAILED' if fails else 'passed'}: {fails} failure(s)"); sys.exit(1 if fails else 0)
