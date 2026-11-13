#!/bin/zsh
cd "$(dirname "$0")" || exit 1
printf '\nParallel Computing Lab - FULL RUN - Student ID 230103344\n\n'
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
if [[ -f .checkpoint_230103344_full.json ]]; then
  echo 'Found saved checkpoint: resuming finished stages.'
  extra=(--resume)
fi
if command -v caffeinate >/dev/null 2>&1; then
  caffeinate -i "$PY" parallel_lab.py --profile full --id 230103344 "${extra[@]}"
else
  "$PY" parallel_lab.py --profile full --id 230103344 "${extra[@]}"
fi
status=$?
echo ''
if [[ $status -eq 0 ]]; then
  echo 'FULL RUN FINISHED: lab_report_230103344.md'
  echo 'Raw telemetry: run_230103344_full.log'
else
  echo "Run stopped (code $status). Log and last completed stages are saved."
  echo 'Open START_FULL.command again to resume the full run.'
  echo 'If there is an error, attach run_230103344_full.log.'
fi
echo 'Press Enter to close this window.'
read -r _
exit $status
