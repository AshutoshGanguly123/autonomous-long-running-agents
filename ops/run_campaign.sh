#!/bin/bash
# Resume the same campaign until runs/<campaign>/STOP exists.
# HTTP failures and process exits restart from the durable ledger.
# This does not launch GPUs. Serving stays on the existing two-card endpoint.
set -u
cd ${REPO_ROOT}
export PYTHONUNBUFFERED=1
CAMPAIGN="${1:-runs/campaign-v0}"
LOG=ops/campaign-v0.log
mkdir -p ops "$(dirname "$CAMPAIGN")"
echo "supervisor start $(date -Is) host=$(hostname) pid=$$ campaign=$CAMPAIGN" >> "$LOG"
while [[ ! -e "$CAMPAIGN/STOP" ]]; do
  .venv/bin/python -m tree_ai_scientist run --campaign "$CAMPAIGN" >> "$LOG" 2>&1
  code=$?
  if [[ -e "$CAMPAIGN/STOP" ]]; then
    echo "stop file present after exit $code $(date -Is)" >> "$LOG"
    exit 0
  fi
  echo "process exit $code $(date -Is); resuming from the ledger" >> "$LOG"
  sleep 20
done
echo "stop file present before launch $(date -Is)" >> "$LOG"
