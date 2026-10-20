#!/bin/bash
SRC=$(cd "$(dirname "$0")/.." && pwd)
T=$(mktemp -d); cd "$T"; PASS=0; FAILN=0
export GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@t GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@t
check() { local name="$1" want="$2"; shift 2; out=$("$@" 2>&1); got=$?; if [ "$got" = "$want" ]; then PASS=$((PASS+1)); echo "ok   [$got] $name"; else FAILN=$((FAILN+1)); echo "FAIL [$got want $want] $name"; echo "$out" | sed 's/^/      /'; fi; LAST="$out"; }
noleak() { if echo "$LAST" | grep -qi -e zorblax -e "quuxing" -e "731-555"; then FAILN=$((FAILN+1)); echo "FAIL leaked pattern/line text: $1"; else PASS=$((PASS+1)); echo "ok   no pattern/line text in output: $1"; fi; }
git init -q --bare remote.git; git init -q repo; cd repo
cp $SRC/privacy_check.py $SRC/kit_paths.py .; mkdir -p hooks; cp $SRC/hooks/privacy_before_push.py hooks/
printf '/.privacy-patterns\n/.privacy-allow\n/hooks/\n' > .gitignore
printf '# test patterns\nzorblax\nquux\n731\nexamplecorp\n' > .privacy-patterns
printf 'hello\n' > a.txt; printf '    ("examplecorp", "ExampleCorp"),\nother\n' > scan.py
printf 'scan.py | ("examplecorp", "ExampleCorp"), | 2026-10-15 | kept per owner decision\n' > .privacy-allow
git add .gitignore privacy_check.py kit_paths.py a.txt scan.py; git commit -qm base; git remote add origin ../remote.git; git push -q -u origin HEAD:main 2>/dev/null; git branch -q -u origin/main 2>/dev/null
P="python3 privacy_check.py"
echo "== staged scope"
check "nothing staged fails" 1 $P
echo "fine" >> a.txt; git add a.txt; check "clean staged diff passes" 0 $P; echo "$LAST" | grep -q "files checked against 4 patterns" && echo "     counts shown: $LAST"
printf 'x Zorblax y\n' >> a.txt; git add a.txt; check "planted staged hit fails" 1 $P; echo "$LAST" | grep -q "a.txt:3  (pattern line 2)" && echo "     location+pattern line shown: $(echo "$LAST" | head -1)"; noleak "staged hit"
git reset -q --hard; git rm -q --cached scan.py; check "deletion-only staged diff passes" 0 $P; git reset -q --hard
echo "== patterns file"
mv .privacy-patterns pp.bak; check "missing patterns fails" 1 $P --all; : > .privacy-patterns; check "empty patterns fails" 1 $P --all; printf '# only comments\n\n' > .privacy-patterns; check "comments-only fails" 1 $P --all; mv pp.bak .privacy-patterns
git add -f .privacy-patterns; check "tracked patterns file fails" 1 $P --all; git rm -q --cached .privacy-patterns
git add -f .privacy-allow; check "tracked allow file fails" 1 $P --all; git rm -q --cached .privacy-allow
echo "== boundaries (named files)"
printf 'quuxing notes\n' > b1.txt; check "quuxing does not hit quux" 0 $P b1.txt
printf 'id 47319 here\n' > b2.txt; check "47319 does not hit 731" 0 $P b2.txt
printf 'call 731-555-0100\n' > b3.txt; check "731-555-0100 hits 731" 1 $P b3.txt; noleak "number hit"; rm b1.txt b2.txt b3.txt
echo "== allow-list"
check "--all passes with ExampleCorp line ALLOWED" 0 $P --all; echo "$LAST" | grep -q "ALLOWED  scan.py:1  (pattern line 5): kept per owner decision" && echo "     $(echo "$LAST" | grep ALLOWED)"
printf '    ("examplecorp2", "ExampleCorp"),\n' >> scan.py; check "second ExampleCorp line fails" 1 $P --all; git checkout -q scan.py
sed -i '' 's/"ExampleCorp"),/"ExampleCorp"),  # edited/' scan.py; check "edited allowed line fails" 1 $P --all; git checkout -q scan.py
cp .privacy-allow al.bak; printf 'scan.py | only two fields\n' >> .privacy-allow; check "malformed allow line fails" 1 $P --all; mv al.bak .privacy-allow
echo "== --push (HEAD, not working tree)"
printf 'zorblax uncommitted\n' >> a.txt; check "uncommitted hit: --push passes" 0 $P --push; check "uncommitted hit: --all fails" 1 $P --all; git checkout -q a.txt
printf 'zorblax committed\n' >> a.txt; git commit -qam hit; check "committed hit in HEAD fails --push" 1 $P --push; git reset -q --hard HEAD~1
printf 'zorblax temp\n' > t.txt; git add t.txt; git commit -qm add; git rm -q t.txt; git commit -qm remove; check "added-then-removed in unpushed commits fails --push" 1 $P --push; echo "     $(echo "$LAST" | grep HIT)"; git reset -q --hard origin/main
printf 'zorblax old\n' > h.txt; git add h.txt; git commit -qm old; git rm -q h.txt; git commit -qm gone; git push -q origin HEAD:main 2>/dev/null
check "hit only in pushed history: --push passes" 0 $P --push
check "--history catches it" 1 $P --history; echo "     $(echo "$LAST" | grep HIT | head -1)"
git checkout -q -b nouptream; printf 'zorblax local\n' > n.txt; git add n.txt; git commit -qm local; check "no upstream: falls back to HEAD --not --remotes (hit caught)" 1 $P --push; git checkout -q -; git branch -q -D nouptream
echo "== Claude Code push hook (hooks/privacy_before_push.py)"
H="hooks/privacy_before_push.py"; export CLAUDE_PROJECT_DIR="$PWD"
hook_hit() { printf 'zorblax hh\n' >> a.txt; git commit -qam hh; printf '{"tool_name":"Bash","tool_input":{"command":"%s"}}' "$1" | python3 $H; local rc=$?; git reset -q --hard HEAD~1; return $rc; }
hook() { printf '{"tool_name":"Bash","tool_input":{"command":"%s"}}' "$1" | python3 $H; }
printf 'zorblax head\n' >> a.txt; git commit -qam headhit
check "git push with HEAD hit blocked" 2 hook "git push"; echo "$LAST" | grep -q "Blocked by privacy_check.py" && echo "     reason shown"
check "gh pr create --fill with hit blocked" 2 hook "gh pr create --fill"
check "gh repo sync with hit blocked" 2 hook "gh repo sync"
check "cd x && git push origin main checked" 2 hook "cd x && git push origin main"
git reset -q --hard HEAD~1; check "clean git push allowed" 0 hook "git push"
mv .privacy-patterns pp.bak; check "git status untouched (checker not run: would fail with no patterns)" 0 hook "git status"; mv pp.bak .privacy-patterns
mv .privacy-patterns pp.bak
check "path .git/privacy-push.log does not trigger" 0 hook "tail -2 .git/privacy-push.log"
check "git stash push does not trigger" 0 hook "git stash push -m x"
check "echo git push (quoted text) does not trigger" 0 hook "echo 'git push'"
mv pp.bak .privacy-patterns
check "/usr/bin/git -C repo push triggers" 2 hook_hit "/usr/bin/git -C . push"
check "gh repo sync (no hit) passes with JSON pass message" 0 hook "gh repo sync"; echo "$LAST" | grep -q '"systemMessage": "privacy check passed' && echo "     pass message: $LAST"
echo "== pre-commit hook"
printf '#!/bin/sh\nexec python3 "$(git rev-parse --show-toplevel)/privacy_check.py"\n' > .git/hooks/pre-commit; chmod +x .git/hooks/pre-commit
printf 'zorblax precommit\n' >> a.txt; git add a.txt; check "pre-commit blocks staged hit" 1 git commit -qm blocked; git reset -q --hard
echo "clean" >> a.txt; git add a.txt; check "pre-commit allows clean commit" 0 git commit -qm clean
echo; echo "RESULT: $PASS passed, $FAILN failed"; cd /; rm -rf "$T"
