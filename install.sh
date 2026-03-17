#!/usr/bin/env bash
# =============================================================================
# Nexus Night Shift Agent — VM Setup Script
# Target: Ubuntu 22.04+ (Hetzner CPX31 or equivalent)
# Run as the user who will run the agent (NOT root — Hermes installs per-user)
#
# Usage:
#   bash install.sh
#
# What this does:
#   1. Installs Hermes Agent via the official installer
#   2. Creates /workspace/ directory structure
#   3. Seeds context files, skill documents, and tools
#   4. Configures ~/.hermes/ (config.yaml, .env, SOUL.md)
#   5. Installs Telegram gateway as a systemd user service
#   6. Registers cron jobs via Hermes
# =============================================================================
set -euo pipefail

WORKSPACE_ROOT="${WORKSPACE_ROOT:-/workspace}"
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

log()  { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }
info() { echo ""; echo "  ▶ $*"; }
warn() { echo "[WARN] $*" >&2; }
die()  { echo "[ERROR] $*" >&2; exit 1; }

# ---------------------------------------------------------------------------
# 0. Preflight checks
# ---------------------------------------------------------------------------
[[ $EUID -eq 0 ]] && die "Do not run as root. Run as the agent user (e.g. 'ubuntu')."

command -v curl &>/dev/null || die "curl is required. Install with: sudo apt-get install curl"

if [[ ! -f "$REPO_DIR/workspace/context/agent-role.md" ]]; then
    die "Cannot find workspace/context/agent-role.md — run this script from the repo root."
fi

# ---------------------------------------------------------------------------
# 1. Install Hermes Agent
# ---------------------------------------------------------------------------
info "Installing Hermes Agent..."
if command -v hermes &>/dev/null; then
    log "Hermes Agent already installed at $(which hermes). Running update..."
    hermes update || warn "Update failed — continuing with existing version."
else
    log "Installing Hermes Agent via official installer..."
    curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash

    # Reload shell PATH so 'hermes' is available in this script
    # The installer typically adds to ~/.bashrc / ~/.zshrc
    export PATH="$HOME/.local/bin:$HOME/.hermes/bin:$PATH"

    command -v hermes &>/dev/null || {
        # Try common install locations
        for candidate in "$HOME/.local/bin/hermes" "$HOME/.hermes/bin/hermes" "/usr/local/bin/hermes"; do
            [[ -x "$candidate" ]] && { ln -sf "$candidate" "$HOME/.local/bin/hermes" 2>/dev/null || true; break; }
        done
        export PATH="$HOME/.local/bin:$PATH"
    }

    command -v hermes &>/dev/null || die "Hermes Agent installed but 'hermes' not in PATH. Open a new shell and re-run."
fi

log "Hermes version: $(hermes --version 2>/dev/null || echo 'unknown')"

# ---------------------------------------------------------------------------
# 2. Install Python dependencies for Claude escalation utility
# ---------------------------------------------------------------------------
info "Installing Python dependencies..."
if command -v pip3 &>/dev/null; then
    pip3 install --user httpx python-dotenv 2>/dev/null || \
        warn "pip install failed — httpx may already be available or needs manual install."
else
    warn "pip3 not found — install httpx manually: sudo apt-get install python3-pip && pip3 install httpx"
fi

# ---------------------------------------------------------------------------
# 3. Workspace directory structure
# ---------------------------------------------------------------------------
info "Creating workspace at $WORKSPACE_ROOT..."
sudo mkdir -p "$WORKSPACE_ROOT"
sudo chown "$USER:$USER" "$WORKSPACE_ROOT"

for d in exchange-specs nexus-docs research tracking output briefs context tools skills config; do
    mkdir -p "$WORKSPACE_ROOT/$d"
done

log "Workspace directories created at $WORKSPACE_ROOT"

# ---------------------------------------------------------------------------
# 4. Deploy context files, tools, and skill documents
# ---------------------------------------------------------------------------
info "Deploying context files..."
cp -r "$REPO_DIR/workspace/context/."  "$WORKSPACE_ROOT/context/"
cp -r "$REPO_DIR/workspace/tools/."    "$WORKSPACE_ROOT/tools/"
cp -r "$REPO_DIR/workspace/tracking/." "$WORKSPACE_ROOT/tracking/"
cp    "$REPO_DIR/workspace/standing-tasks.md" "$WORKSPACE_ROOT/"

info "Deploying skill documents to ~/.hermes/skills/..."
mkdir -p "$HERMES_HOME/skills"
for skill_file in "$REPO_DIR/workspace/skills/"*.skill.md; do
    skill_name=$(basename "$skill_file" .skill.md)
    skill_dir="$HERMES_HOME/skills/$skill_name"
    mkdir -p "$skill_dir"
    cp "$skill_file" "$skill_dir/SKILL.md"
    log "  Installed skill: $skill_name"
done

# ---------------------------------------------------------------------------
# 5. Configure ~/.hermes/config.yaml
# ---------------------------------------------------------------------------
info "Configuring Hermes Agent..."
mkdir -p "$HERMES_HOME"

HERMES_CONFIG="$HERMES_HOME/config.yaml"
if [[ ! -f "$HERMES_CONFIG" ]]; then
    log "Creating $HERMES_CONFIG from template..."
    cp "$REPO_DIR/workspace/config/hermes-config.yaml" "$HERMES_CONFIG"
else
    log "$HERMES_CONFIG already exists — backing up to ${HERMES_CONFIG}.bak and merging key settings."
    cp "$HERMES_CONFIG" "${HERMES_CONFIG}.bak"
fi

# Apply key model settings via hermes config set
hermes config set model.provider openrouter
hermes config set model.default "nousresearch/hermes-3-llama-3.1-70b"
log "Model configured: OpenRouter → nousresearch/hermes-3-llama-3.1-70b"

# ---------------------------------------------------------------------------
# 6. Configure ~/.hermes/SOUL.md (agent personality + workspace context)
# ---------------------------------------------------------------------------
SOUL_FILE="$HERMES_HOME/SOUL.md"
info "Installing SOUL.md (agent personality)..."
cp "$REPO_DIR/workspace/config/SOUL.md" "$SOUL_FILE"
log "SOUL.md installed at $SOUL_FILE"

# ---------------------------------------------------------------------------
# 7. Configure ~/.hermes/.env (API keys)
# ---------------------------------------------------------------------------
HERMES_ENV="$HERMES_HOME/.env"
if [[ ! -f "$HERMES_ENV" ]]; then
    log "Creating $HERMES_ENV — you MUST fill in your API keys."
    cat > "$HERMES_ENV" <<'EOF'
# Hermes Agent environment — fill in your actual keys
# This file is mode 600; never commit it.

# OpenRouter API key (for Hermes 3 70B — routine tasks)
OPENROUTER_API_KEY=sk-or-REPLACE_ME

# Anthropic API key (for Claude Sonnet — complex reasoning tasks)
ANTHROPIC_API_KEY=sk-ant-REPLACE_ME

# Telegram bot token (from @BotFather)
TELEGRAM_BOT_TOKEN=REPLACE_ME

# Your Telegram chat ID (from @userinfobot — restricts bot to you only)
TELEGRAM_HOME_CHANNEL=REPLACE_ME

# Workspace root
WORKSPACE_ROOT=/workspace
EOF
    chmod 600 "$HERMES_ENV"
else
    log "$HERMES_ENV already exists — not overwriting. Ensure all keys are set."
fi

# ---------------------------------------------------------------------------
# 8. Install Telegram gateway as a systemd user service
# ---------------------------------------------------------------------------
info "Installing Telegram gateway service..."
hermes gateway install --platform telegram 2>/dev/null || {
    warn "hermes gateway install failed — may require manual service setup."
    warn "Run manually: hermes gateway --platform telegram"
}

# ---------------------------------------------------------------------------
# 9. Register cron jobs via Hermes
# ---------------------------------------------------------------------------
info "Registering cron jobs..."

hermes cron add "Every weeknight at 11:30 PM, check whether a nightly brief has been received in Telegram today (look for a file in $WORKSPACE_ROOT/briefs/ with today's date). If no brief file exists and no brief was received in the current Telegram session, send a Telegram message: 'No brief received yet — should I work from the standing task queue at $WORKSPACE_ROOT/standing-tasks.md?'"

hermes cron add "Every weekday morning at 7:00 AM, read the most recent morning report from $WORKSPACE_ROOT/output/ (find the latest dated folder and read report.md), then send the full report as a Telegram message to the home channel. If no report exists, send: 'Good morning! No overnight report was generated. The agent may not have received a brief last night.'"

log "Cron jobs registered."

# ---------------------------------------------------------------------------
# 10. System crontab — Python fallback scripts (separate from Hermes crons)
# ---------------------------------------------------------------------------
info "Configuring system crontab entries..."

PYTHON_BIN="$REPO_DIR/.venv/bin/python"
# Fall back to system python3 if the venv doesn't exist yet
command -v "$PYTHON_BIN" &>/dev/null || PYTHON_BIN="$(command -v python3)"

CRON_REMINDER="30 23 * * 1-5 $PYTHON_BIN $REPO_DIR/scripts/check_brief.py reminder >> /var/log/nexus-agent.log 2>&1"
CRON_FALLBACK=" 5  0 * * 2-6 $PYTHON_BIN $REPO_DIR/scripts/check_brief.py fallback >> /var/log/nexus-agent.log 2>&1"
CRON_REPORT="  0  7 * * 1-5 $PYTHON_BIN $REPO_DIR/scripts/morning_report.py >> /var/log/nexus-agent.log 2>&1"

# Add entries idempotently — strip any existing nexus cron lines, then append
(
  crontab -l 2>/dev/null | grep -v "check_brief\|morning_report\|nexus-agent"
  echo "$CRON_REMINDER"
  echo "$CRON_FALLBACK"
  echo "$CRON_REPORT"
) | crontab -

log "System crontab updated. Current entries:"
crontab -l

# ---------------------------------------------------------------------------
# 11. Smoke test the installation
# ---------------------------------------------------------------------------
info "Running hermes doctor..."
hermes doctor 2>/dev/null || warn "hermes doctor reported issues — review before first run."

# ---------------------------------------------------------------------------
log ""
log "=========================================="
log " Installation complete!"
log "=========================================="
log ""
log " REQUIRED: Fill in your API keys:"
log "   nano $HERMES_ENV"
log ""
log " Keys needed:"
log "   OPENROUTER_API_KEY  — from openrouter.ai"
log "   ANTHROPIC_API_KEY   — from console.anthropic.com"
log "   TELEGRAM_BOT_TOKEN  — from @BotFather on Telegram"
log "   TELEGRAM_HOME_CHANNEL — your Telegram chat ID (from @userinfobot)"
log ""
log " After filling keys, start the gateway:"
log "   hermes gateway --platform telegram"
log ""
log " Verify it works by sending your bot any message."
log ""
log " Night 1 smoke test:"
log "   python3 $REPO_DIR/scripts/smoke_test.py"
log ""
log " Full guide: README.md"
