#!/bin/bash
# Run every kit test. Fictional data only; each test works in its own temp folder and cleans up.
cd "$(dirname "$0")"
fail=0
out=$(bash test_privacy.sh 2>&1 | tail -1); echo "privacy:         $out"; [[ $out == *" 0 failed"* ]] || fail=1
out=$(bash test_profile.sh | tail -1);      echo "profile:         $out"; [[ $out == *" 0 failed"* ]] || fail=1
for t in test_*.py; do
  out=$(python3 "$t" | tail -1); printf "%-17s%s\n" "${t%.py}:" "$out"
  [[ $out == *"0 failed"* || $out == "passed: 0 failure(s)" ]] || fail=1
done
exit $fail
