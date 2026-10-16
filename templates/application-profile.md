# Application Profile

The facts an application form asks for, written once. **This file owns them**: `08-application-answers.md`
keeps only prose answers and points here. Fill mode (`modes/fill.md`) reads this file through
`application_profile.py`, never whole.

Copy it to the repo root (`cp -n templates/application-profile.md .`) and fill it in. The root copy is gitignored.

**Format.** One `Field: value` per line. `#` starts a comment. A value left in `[brackets]`, or left blank,
counts as missing, and fill mode leaves that field blank and lists it.

**Never store here:** government ID, SSN, passport, driver's license, date of birth, bank, routing or account
numbers. Forms that ask for these get them from you directly. `application_profile.py` refuses to print any key
that looks like one.

---

## Factual

Filled from here when a form asks. The resume (`00-master-resume.md`, or the role's file in `tailored/`) covers
employers, titles, dates and degrees.

Full name: [First Last]
Preferred name: [what you go by, or leave blank]
Email: [you@example.com]
Phone: [+1 555 0100]
City: [City]
State: [State or region]
Country: [Country]
LinkedIn: [https://www.linkedin.com/in/your-handle]
Portfolio: [https://… or leave blank]
GitHub: [https://github.com/… or leave blank]

---

## Knockout

Answers that can screen you out. Fill mode fills one **only** from an explicit answer here. If the answer is
missing, the field stays blank and is listed for you. Write the answer the way you'd select it on a form.

Authorized to work in the US: [Yes / No]
Require sponsorship now or in future: [Yes / No]
Willing to relocate: [Yes / No / Depends on role]
In-office days per week willing: [e.g. 0 / up to 2 / up to 3 / 5]
Willing to travel: [e.g. up to 25%]
Security clearance: [None / level held]
Over 18: [Yes / No]
