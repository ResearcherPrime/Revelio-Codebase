#!/usr/bin/env bash

set -e
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

source "$REPO_ROOT/venv/bin/activate"

MODE="${1:-full}"

# --------------------------------------------------
# Configuration
# --------------------------------------------------

SESSION="scraping_session"
WEBHOOK_URL=""

TMPDIR="$SCRIPT_DIR/logs/temp"

ASNS_DIR="$SCRIPT_DIR/asns"
PREFIX_DIR="$SCRIPT_DIR/prefixes"

EXEC_LOG="$SCRIPT_DIR/logs/exec"
TIME_LOG="$SCRIPT_DIR/logs/time"

# --------------------------------------------------
# Mode-specific configuration
# --------------------------------------------------

if [[ "$MODE" == "fast" ]]; then
    USE_TMUX=0
    ENABLE_WEBHOOKS=0
    
    ASNS_CMD="python3 $SCRIPT_DIR/asns_scrapper.py \"United Arab Emirates\""

    PREFIX_CMD="python3 $SCRIPT_DIR/prefix_scrapper.py $ASNS_DIR/United_Arab_Emirates United_Arab_Emirates 0 fast"

else
    USE_TMUX=1
    ENABLE_WEBHOOKS=1

    ASNS_CMD=(
        "python3 $SCRIPT_DIR/asns_scrapper.py"
    )

    PREFIX_CMDS=(
        "bash $SCRIPT_DIR/batch_prefix_scrapper.sh $SCRIPT_DIR/target_not_free.csv 0"
        "bash $SCRIPT_DIR/batch_prefix_scrapper.sh $SCRIPT_DIR/target_partly_free.csv 2"
        "bash $SCRIPT_DIR/batch_prefix_scrapper.sh $SCRIPT_DIR/target_free.csv 4"
        "bash $SCRIPT_DIR/batch_prefix_scrapper.sh $SCRIPT_DIR/target_middle_east.csv 6"
    )
fi

# --------------------------------------------------
# Notification helper
# --------------------------------------------------

send_notification() {

    local payload="$1"

    if [[ "$ENABLE_WEBHOOKS" -eq 0 ]]; then
        return
    fi

    if [[ -z "$WEBHOOK_URL" ]]; then
        echo "[INFO] WEBHOOK_URL not configured"
        return
    fi

    if ! curl -s \
        -H 'Content-Type: application/json' \
        -d "$payload" \
        "$WEBHOOK_URL" > /dev/null 2>&1; then

        echo "[ERROR] Webhook notification failed"
    fi
}

# --------------------------------------------------
# Cleanup previous outputs
# --------------------------------------------------

rm -rf \
    "$ASNS_DIR" \
    "$PREFIX_DIR" \
    "$EXEC_LOG" \
    "$TIME_LOG" \
    "$TMPDIR"

mkdir -p \
    "$ASNS_DIR" \
    "$PREFIX_DIR" \
    "$EXEC_LOG" \
    "$TIME_LOG" \
    "$TMPDIR"

# --------------------------------------------------
# Fast mode
# --------------------------------------------------

if [[ "$MODE" == "fast" ]]; then

    echo "[INFO] Running scraping module in FAST mode"

    echo "[INFO] Fetching UAE ASN list"

    eval $ASNS_CMD

    echo "[INFO] Fetching UAE prefixes"

    eval $PREFIX_CMD

    echo "[INFO] Fast scraping completed"

    exit 0
fi

# --------------------------------------------------
# Full mode
# --------------------------------------------------

echo "[INFO] Running scraping module in FULL mode"

payload=$(printf '{"content":"ℹ️ ASN & Prefix Scraping started"}')
send_notification "$payload"

# Remove old tmux session if present
if tmux has-session -t "$SESSION" 2>/dev/null; then
    tmux kill-session -t "$SESSION"
fi

tmux new-session -d -s "$SESSION"

echo "[INFO] ASN scraping started in tmux"

codefile="$TMPDIR/asns.code"

tmux send-keys -t "$SESSION:0.0" \
    "source $REPO_ROOT/venv/bin/activate && ${ASNS_CMD[*]}; echo \$? > \"$codefile\"; tmux wait-for -S done_asns" C-m

tmux wait-for done_asns

code=$(< "$codefile")

if [[ "$code" -ne 0 ]]; then
    echo "[ERROR] ASN scraping failed"
    exit 1
fi

echo "[INFO] Prefix scraping started in tmux"

for i in "${!PREFIX_CMDS[@]}"; do

    if [[ "$i" -gt 0 ]]; then
        tmux split-window -v -t "$SESSION"
        tmux select-layout -t "$SESSION" tiled
    fi

    codefile="$TMPDIR/prefix_$i.code"

    tmux send-keys -t "$SESSION:0.$i" \
        "source $REPO_ROOT/venv/bin/activate && ${PREFIX_CMDS[i]}; echo \$? > \"$codefile\"; tmux wait-for -S done_$i" C-m

done

for i in "${!PREFIX_CMDS[@]}"; do

    tmux wait-for done_$i

    codefile="$TMPDIR/prefix_$i.code"
    code=$(< "$codefile")

    if [[ "$code" -ne 0 ]]; then
        echo "[ERROR] Prefix scraping failed in pane $i"
        exit 1
    fi
done

payload=$(printf '{"content":"ℹ️ ASN & Prefix Scraping completed"}')
send_notification "$payload"

echo "[INFO] Full scraping completed"
