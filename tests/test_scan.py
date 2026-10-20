"""scan.py: old (BASELINE, constants in the script) vs new (config read from the project folder) must produce the same
output for the same config and the same recorded API responses. Plus every config error exits 1 with file:line.
Fictional boards and jobs only."""
import contextlib, datetime, importlib.util, io, os, shutil, subprocess, sys, tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASELINE = "3502055"  # last commit where scan.py kept its settings in the script
TODAY = datetime.date(2026, 10, 20)
EXPECTED_DIFFS = {  # the only intended text changes: the two hints that used to say "edit scan.py"
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
finally:
    os.chdir("/"); shutil.rmtree(T)
print(f"{'FAILED' if fails else 'passed'}: {fails} failure(s)"); sys.exit(1 if fails else 0)
