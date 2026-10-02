#!/usr/bin/env bash
# after_update.sh - v49, v50: the checks every library update runs before it is committed. Called by the RUN.sh of an
# update zip:   bash pipeline/repo/after_update.sh v49
# If a check fails the script stops, RUN.sh fails, and the workflow ends before the commit: a broken update does not
# reach the repo (delete the uploaded zip and try again). Everything here uses Python's standard library only.
set -euo pipefail
origin="${1:?usage: after_update.sh <version, e.g. v49>}"
echo "== 1. sijill validator"
python3 pipeline/sijill/sijill.py --repo . all
echo "== 2. authentication tests"
python3 pipeline/hadith/test_authenticate.py
echo "== 3. Jalasa stress test (docs/jalasa/STRESS_TEST.md): a failed must stops the update; the scorecard is committed"
python3 pipeline/jalasa/stress_test.py
echo "== 4. no stray archives in the tree"
stray=$(git ls-files --cached --others --exclude-standard | grep -Ei '\.(zip|rar|7z)$' | grep -v '^library-update-' || true)
if [ -n "$stray" ]; then echo "stray archives: $stray"; exit 1; fi
echo "== 5. manifest"
python3 pipeline/repo/update_manifest.py --origin "$origin"
echo "== all checks passed for $origin"
