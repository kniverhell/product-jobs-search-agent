"""modes/interview.md keeps its rules: round first, ledger before resume, labeled unknowns, no LinkedIn lookups. Fictional only."""
import os, re

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
text = re.sub(r"\s+", " ", open(os.path.join(REPO, "modes", "interview.md"), encoding="utf-8").read())
fails = 0
def check(name, ok, detail=""):
    global fails
    print(("ok   " if ok else "FAIL ") + name + ("" if ok else f"\n      {detail}"))
    fails += not ok

check("names the round first, with four rounds", "## 0. Name the round first" in text and all(
    r in text for r in ("Recruiter or coordinator screen", "Hiring manager", "Peer or panel", "Executive or final")))
check("source hierarchy puts the ledger before the resume",
      0 < text.find("proof-point ledger") < text.find("**The resume**") and "**claim**" in text)
check("points at the real ledger and story bank files", "06-proof-points.md" in text and "05-story-bank.md" in text
      and "05-proof-points" not in text)
check("unknowns carry labels and a resolving question", all(l in text for l in ("**Confirmed**", "**Claim**", "**Unknown**"))
      and "resolving question" in text)
check("covers the other side's facts, not only the user's", "team size" in text and "budget" in text)
check("questions to ask resolve open items", "resolves an open item" in text)
check("ledger statuses are used by status", all(s in text for s in ("Solid", "Derived", "Soft", "Confidential", "Designed-only", "Open")))
check("LinkedIn: pasted in, never opened, cites contact.md",
      re.search(r"never opens, searches or reads LinkedIn", text) and "modes/contact.md" in text)
check("does not claim a hook or rule number enforces it", "hook" not in text.lower() and "rule 18" not in text.lower())
check("keeps the story-bank loop", "commit them to the bank" in text and "compounding asset" in text)
print(f"{'FAILED' if fails else 'passed'}: {fails} failure(s)")
raise SystemExit(1 if fails else 0)
