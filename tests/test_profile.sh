#!/bin/bash
REPO=$(cd "$(dirname "$0")/.." && pwd)
pass=0; fail=0
ok(){ if [ "$1" = 0 ]; then pass=$((pass+1)); echo "ok   $2"; else fail=$((fail+1)); echo "FAIL $2"; fi; }
T=$(mktemp -d); cd "$T"; git init -q; cp "$REPO/application_profile.py" "$REPO/kit_paths.py" .
run(){ python3 application_profile.py "$@" > out.txt 2>&1; echo $? > rc.txt; }
# 1 missing profile
run; ok $([ "$(cat rc.txt)" = 1 ] && grep -q "no application-profile.md" out.txt; echo $?) "missing profile exits 1"
# 2 template parses: everything missing, nothing else
cp "$REPO/templates/application-profile.md" application-profile.md
run; ok $([ "$(cat rc.txt)" = 0 ] && ! grep -q "^FACTUAL |" out.txt && ! grep -q "^KNOCKOUT |" out.txt && [ "$(grep -c '^MISSING |' out.txt)" = 17 ]; echo $?) "template: all 17 keys MISSING, none filled"
# 3 filled fictional profile
cat > application-profile.md <<'P'
# Application Profile
**Format.** One `Field: value` per line.
Email: should-not-parse@example.com
## Factual
Full name: Pat Example
Email: pat@example.com   # work address
Phone: +1 555 0142
LinkedIn: https://www.linkedin.com/in/pat-example
Portfolio: [https://… or leave blank]
GitHub:
  # an indented comment: ignored
## Knockout
Require sponsorship now or in future: No
In-office days per week willing: [e.g. 0 / up to 2]
Passport number: X1234567
Social Security Number: 123-45-6789
Driver's license: D9998887
Date of birth: 1990-01-01
Bank routing: 021000021
Account number: 000123456789
Emergency note: 987-65-4321
## Notes
Ignored key: ignored value
P
run
ok $([ "$(cat rc.txt)" = 0 ]; echo $?) "filled profile exits 0"
ok $(grep -qx "FACTUAL | Full name | Pat Example" out.txt; echo $?) "factual parsed by header"
ok $(grep -qx "FACTUAL | Email | pat@example.com" out.txt; echo $?) "inline comment stripped; pre-header line ignored"
ok $(grep -qx "FACTUAL | LinkedIn | https://www.linkedin.com/in/pat-example" out.txt; echo $?) "URL value keeps its colon"
ok $(grep -qx "KNOCKOUT | Require sponsorship now or in future | No" out.txt; echo $?) "knockout parsed by header"
ok $(grep -q "^MISSING | Portfolio" out.txt && grep -q "^MISSING | GitHub" out.txt && grep -q "^MISSING | In-office days" out.txt; echo $?) "placeholder and blank are MISSING"
ok $(! grep -q "Ignored key" out.txt; echo $?) "unknown section ignored"
ok $([ "$(grep -c '^REFUSED |' out.txt)" = 7 ]; echo $?) "7 denylisted lines REFUSED (incl. SSN-shaped value)"
ok $(! grep -qE "X1234567|123-45-6789|D9998887|1990-01-01|021000021|000123456789|987-65-4321" out.txt; echo $?) "no refused value in output"
ok $(! grep -q "=" out.txt; echo $?) "no key=value in output"
for k in "Passport number" "Social Security Number" "Driver's license" "Date of birth" "Bank routing" "Account number"; do
  run --get "$k"; ok $([ "$(cat rc.txt)" = 1 ] && grep -q "refused" out.txt && ! grep -qE "X1234567|123-45-6789|D9998887|1990-01-01|021000021|000123456789" out.txt; echo $?) "--get '$k' refused, exit 1, value withheld"
done
run --get "email"; ok $([ "$(cat rc.txt)" = 0 ] && [ "$(cat out.txt)" = "pat@example.com" ]; echo $?) "--get is case-insensitive"
run --get "Portfolio"; ok $([ "$(cat rc.txt)" = 1 ] && grep -q "missing" out.txt; echo $?) "--get placeholder exits 1"
run --get "Nope"; ok $([ "$(cat rc.txt)" = 1 ]; echo $?) "--get unknown key exits 1"
# duplicate key
printf '## Factual\nEmail: a@example.com\nemail: b@example.com\n' > dup.md; cp application-profile.md keep.md; cp dup.md application-profile.md
run; ok $([ "$(cat rc.txt)" = 1 ] && grep -q "appears twice" out.txt; echo $?) "duplicate key exits 1"
cp keep.md application-profile.md
# tracked
git add application-profile.md; run; ok $([ "$(cat rc.txt)" = 1 ] && grep -q "tracked by git" out.txt; echo $?) "tracked profile exits 1"
git rm -q --cached application-profile.md
# no fields
printf '# nothing\n' > application-profile.md; run; ok $([ "$(cat rc.txt)" = 1 ]; echo $?) "no fields exits 1"
cd /; rm -rf "$T"
echo "$pass passed, $fail failed"; [ $fail = 0 ]
