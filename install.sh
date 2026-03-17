#!/usr/bin/env bash
# =============================================================================
# Nexus Night Shift Agent — VM Setup Script
# Target: Ubuntu 22.04+
# Run as the user who will run the agent (NOT root)
#
# Usage:
#   bash install.sh
#
# What this does:
#   1. Creates Python virtual environment and installs dependencies
#   2. Creates /workspace/ directory structure
#   3. Seeds context files, skill documents, and tracking files
#   4. Creates /etc/nexus-agent.env (secrets — fill in before starting)
#   5. Installs Telegram gateway as a systemd service
#   6. Registers cron jobs via system crontab
# =============================================================================
set -euo pipefail

WORKSPACE_ROOT="${WORKSPACE_ROOT:-/workspace}"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$REPO_DIR/.venv"
PYTHON_BIN="$VENV_DIR/bin/python"
NEXUS_LOG="/var/log/nexus-agent.log"

log()  { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }
info() { echo ""; echo "  ▶ $*"; }
warn() { echo "[WARN] $*" >&2; }
die()  { echo "[ERROR] $*" >&2; exit 1; }

# ---------------------------------------------------------------------------
# 0. Preflight checks
# ---------------------------------------------------------------------------
[[ $EUID -eq 0 ]] && die "Do not run as root. Run as the agent user (e.g. 'ubuntu')."

command -v python3 &>/dev/null  || die "python3 required: sudo apt-get install python3 python3-venv"
command -v python3 -m venv --help &>/dev/null 2>&1 || \
  python3 -c "import venv" 2>/dev/null || \
  die "python3-venv required: sudo apt-get install python3-venv"

if [[ ! -f "$REPO_DIR/workspace/context/agent-role.md" ]]; then
    die "Cannot find workspace/context/agent-role.md — run this script from the repo root."
fi

# ---------------------------------------------------------------------------
# 1. Python virtual environment
# ---------------------------------------------------------------------------
info "Setting up Python virtual environment..."
if [[ ! -d "$VENV_DIR" ]]; then
    python3 -m venv "$VENV_DIR"
    log "Created venv at $VENV_DIR"
else
    log "Venv already exists at $VENV_DIR"
fi

"$VENV_DIR/bin/pip" install --quiet --upgrade pip
"$VENV_DIR/bin/pip" install --quiet -r "$REPO_DIR/requirements.txt"
log "Python dependencies installed."

# ---------------------------------------------------------------------------
# 2. Workspace directory structure
# ---------------------------------------------------------------------------
info "Creating workspace at $WORKSPACE_ROOT..."
sudo mkdir -p "$WORKSPACE_ROOT"
sudo chown "$USER:$USER" "$WORKSPACE_ROOT"

for d in exchange-specs nexus-docs research tracking output briefs context tools skills; do
    mkdir -p "$WORKSPACE_ROOT/$d"
done

touch "$WORKSPACE_ROOT/output/.gitkeep" "$WORKSPACE_ROOT/briefs/.gitkeep"
log "Workspace directories created at $WORKSPACE_ROOT"

# ---------------------------------------------------------------------------
# 3. Deploy context files, skill documents, and tracking files
# ---------------------------------------------------------------------------
info "Deploying context files..."
cp -r "$REPO_DIR/workspace/context/."  "$WORKSPACE_ROOT/context/"
cp -r "$REPO_DIR/workspace/tracking/." "$WORKSPACE_ROOT/tracking/"
cp    "$REPO_DIR/workspace/standing-tasks.md" "$WORKSPACE_ROOT/"

info "Deploying skill documents to $WORKSPACE_ROOT/skills/..."
cp -r "$REPO_DIR/workspace/skills/." "$WORKSPACE_ROOT/skills/"
log "Skills deployed."

# ---------------------------------------------------------------------------
# 4. Create /etc/nexus-agent.env (secrets file for systemd + cron)
# ---------------------------------------------------------------------------
SYSTEM_ENV="/etc/nexus-agent.env"
if [[ ! -f "$SYSTEM_ENV" ]]; then
    info "Creating $SYSTEM_ENV (requires sudo) — fill in API keys before starting the service."
    sudo tee "$SYSTEM_ENV" > /dev/null <<'ENVEOF'
# /etc/nexus-agent.env — Nexus Night Shift Agent secrets
# Loaded by nexus-agent.service and all cron scripts.
# Permissions: 640 — NEVER commit this file or expose it.

# OpenRouter API key (routes to Claude Sonnet — all task execution)
OPENROUTER_API_KEY=sk-or-REPLACE_ME

# Telegram bot token (from @BotFather)
TELEGRAM_BOT_TOKEN=REPLACE_ME

# Your Telegram user ID (from @userinfobot — restricts bot to you only)
TELEGRAM_ALLOWED_USER_ID=REPLACE_ME

# Workspace root
WORKSPACE_ROOT=/workspace

# Spend ceilings (USD) — agent stops starting new tasks if cumulative night
# spend exceeds NIGHT_SPEND_CEILING_USD; warns if a single task exceeds TASK_SPEND_CEILING_USD
NIGHT_SPEND_CEILING_USD=5.00
TASK_SPEND_CEILING_USD=3.00

# Log level
LOG_LEVEL=INFO
ENVEOF
    sudo chmod 640 "$SYSTEM_ENV"
    sudo chown root:"$USER" "$SYSTEM_ENV"
    log "$SYSTEM_ENV created. Fill in all REPLACE_ME values before starting the service."
else
    log "$SYSTEM_ENV already exists — not overwriting. Verify all values are set."
fi

# ---------------------------------------------------------------------------
# 5. Create log file
# ---------------------------------------------------------------------------
if [[ ! -f "$NEXUS_LOG" ]]; then
    sudo touch "$NEXUS_LOG"
    sudo chown "$USER:$USER" "$NEXUS_LOG"
    sudo chmod 644 "$NEXUS_LOG"
    log "Created $NEXUS_LOG"
fi

# ---------------------------------------------------------------------------
# 6. Install systemd service
# ---------------------------------------------------------------------------
info "Installing systemd service..."
SERVICE_SRC="$REPO_DIR/services/nexus-agent.service"
SERVICE_DST="/etc/systemd/system/nexus-agent.service"

if [[ -f "$SERVICE_SRC" ]]; then
    sudo cp "$SERVICE_SRC" "$SERVICE_DST"
    # Patch ExecStart and WorkingDirectory to match this install location
    sudo sed -i "s|ExecStart=.*|ExecStart=$PYTHON_BIN $REPO_DIR/scripts/agent_main.py|" "$SERVICE_DST"
    sudo sed -i "s|WorkingDirectory=.*|WorkingDirectory=$REPO_DIR|" "$SERVICE_DST"
    sudo systemctl daemon-reload
    sudo systemctl enable nexus-agent.service
    log "Service installed and enabled."
else
    warn "services/nexus-agent.service not found — service not installed."
fi

# ---------------------------------------------------------------------------
# 7. System crontab
# ---------------------------------------------------------------------------
info "Configuring system crontab..."

CRON_REMINDER="30 23 * * 1-5 $PYTHON_BIN $REPO_DIR/scripts/check_brief.py reminder >> $NEXUS_LOG 2>&1"
CRON_FALLBACK=" 5  0 * * 2-6 $PYTHON_BIN $REPO_DIR/scripts/check_brief.py fallback >> $NEXUS_LOG 2>&1"
CRON_REPORT="   0  7 * * 1-5 $PYTHON_BIN $REPO_DIR/scripts/morning_report.py >> $NEXUS_LOG 2>&1"

(
  crontab -l 2>/dev/null | grep -v "check_brief\|morning_report\|nexus-agent"
  echo "$CRON_REMINDER"
  echo "$CRON_FALLBACK"
  echo "$CRON_REPORT"
) | crontab -

log "System crontab updated:"
crontab -l

# ---------------------------------------------------------------------------
log ""
log "=========================================="
log " Installation complete!"
log "=========================================="
log ""
log " REQUIRED: Fill in your API keys:"
log "   sudo nano $SYSTEM_ENV"
log ""
log " Keys needed:"
log "   OPENROUTER_API_KEY       — from openrouter.ai"
log "   TELEGRAM_BOT_TOKEN       — from @BotFather on Telegram"
log "   TELEGRAM_ALLOWED_USER_ID — your Telegram user ID (@userinfobot)"
log ""
log " Start the agent:"
log "   sudo systemctl start nexus-agent"
log "   sudo systemctl status nexus-agent"
log ""
log " View logs:"
log "   tail -f $NEXUS_LOG"
log "   sudo journalctl -u nexus-agent -f"
log ""
log " Night 1 smoke test:"
log "   $PYTHON_BIN $REPO_DIR/scripts/smoke_test.py"
log ""
