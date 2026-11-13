#!/bin/zsh
cd "$(dirname "$0")" || exit 1
printf '\nParallel Computing Lab - SHORT HEALTH CHECK - Student ID 230103344\n\n'
if [[ -x /usr/local/bin/python3 ]]; then
  PY=/usr/local/bin/python3
elif [[ -x /opt/homebrew/bin/python3 ]]; then
  PY=/opt/homebrew/bin/python3
elif command -v python3 >/dev/null 2>&1; then
  PY=$(command -v python3)
else
  echo 'Python 3 not found. Install Python 3.10 or newer, then retry.'
  read -r '?Press Enter to close...'
  exit 1
fi
"$PY" --version
extra=()
if [[ -f .checkpoint_230103344_pilot.json ]]; then
  echo 'Found pilot checkpoint: resuming.'
  extra=(--resume)
fi
"$PY" parallel_lab.py --profile pilot --id 230103344 "${extra[@]}"
status=$?
echo ''
if [[ $status -eq 0 ]]; then
  echo 'TEST PASSED: lab_report_230103344_PILOT.md'
  echo 'This is NOT the full required lab. Run START_FULL.command next.'
else
  echo "Test stopped (code $status). Try START_TEST.command again to resume."
  echo 'If the error persists, attach run_230103344_pilot.log.'
fi
echo 'Press Enter to close this window.'
read -r _
exit $status
