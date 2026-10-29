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
check("round table says which sections each round gets", "| Sections |" in text and "Produce only the sections listed" in text)
check("pain-to-asset map has its columns and the partial rule",
      "| Company pressure | My evidence (ledger entry + status) | Match: strong / partial / none | Risk if they probe |" in text
      and "Never upgrade a partial match into a strong one." in text)
check("scenarios: five parts, missing metric marked, no invention",
      "situation → choice → what shipped or was killed → metric → why this company cares" in text
      and "never invent one" in text and "Prefer trade-off stories" in text and "fewer stories" in text)
check("persona strategy: names only from pastes, two revealing questions",
      "two questions that reveal their real constraint or success metric" in text and "only from what the user pastes" in text)
check("screening answers: floor from 01-target-roles.md, [UNKNOWN] otherwise",
      "01-target-roles.md" in text and "[UNKNOWN]" in text and "[YOUR FLOOR]" in text)
check("positioning: 60-90 seconds, no passion language, at most five domain bullets labeled",
      "60–90 second" in text and "no passion language" in text and "at most five bullets" in text)
check("checklist for every round: numbers, breaking claims, traps, 48 hours",
      all(k in text for k in ("Numbers to memorize", "break under follow-up", "Trap answers", "Next 48 hours")))
check("practice loop is the closing line, verbatim",
      "End every prep with exactly: \"Practice this out loud. Reply with your version of the elevator pitch and I will cut it.\"" in text
      and "Remove, never add" in text)
check("resume vs Derived ledger figure: flag the resume, offer the Derived figure with arithmetic, do not drop both",
      "flag the resume figure" in text and "offer that figure with its arithmetic, labeled Derived" in text
      and "do not drop both" in text)
check("request-type rule comes before the round table: lookup-only, no round named, round named",
      0 < text.find("First, sort the request") < text.find("| Round | What they decide | Sections |")
      and "A request that includes a lookup" in text and "do not search or fetch anything about the person" in text and "ask the user to paste what they want used" in text and "even if a round was named" in text
      and "A prep request with no round named:** ask which round, and **stop**" in text
      and "A prep request with a round:** produce that round's sections only" in text and text.count("No prep sections") == 2 and "do not add one the table doesn't list" in text)
check("prep goes to chat; a file only when asked, to a path the user names",
      "**Prep output goes to chat.** Write a file only when the user asks, and only to a path the user names." in text)
fill = re.sub(r"\s+", " ", open(os.path.join(REPO, "modes", "fill.md"), encoding="utf-8").read())
check("fill mode: never on linkedin.com, including Easy Apply, stated before the preflight",
      "Never on linkedin.com, including Easy Apply. LinkedIn's terms prohibit automated actions on its site; fill those yourself." in fill
      and 0 < fill.find("Never on linkedin.com") < fill.find("Preflight first"))
print(f"{'FAILED' if fails else 'passed'}: {fails} failure(s)")
raise SystemExit(1 if fails else 0)
