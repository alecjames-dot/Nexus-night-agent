#!/usr/bin/env bash
# =============================================================================
# Nexus Night Shift Agent — VM Setup Script
# Target: Ubuntu 22.04+ (Hetzner CPX31 or equivalent)
# Run as root: bash install.sh
# =============================================================================
set -euo pipefail

WORKSPACE_ROOT="${WORKSPACE_ROOT:-/workspace}"
AGENT_USER="${AGENT_USER:-nexus-agent}"
REPO_DIR="/opt/nexus-night-agent"
VENV_DIR="$REPO_DIR/.venv"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }
die() { log "ERROR: $*" >&2; exit 1; }

# ---------------------------------------------------------------------------
# 1. System dependencies
# ---------------------------------------------------------------------------
log "Installing system dependencies..."
apt-get update -qq
apt-get install -y --no-install-recommends \
    python3.11 python3.11-venv python3-pip \
    curl wget git cron jq \
    ca-certificates tzdata

# ---------------------------------------------------------------------------
# 2. Create agent user (non-root, no login shell)
# ---------------------------------------------------------------------------
if ! id "$AGENT_USER" &>/dev/null; then
    log "Creating agent user: $AGENT_USER"
    useradd --system --no-create-home --shell /usr/sbin/nologin "$AGENT_USER"
fi

# ---------------------------------------------------------------------------
# 3. Clone / copy repo to /opt
# ---------------------------------------------------------------------------
log "Setting up agent code at $REPO_DIR..."
if [[ -d "$REPO_DIR/.git" ]]; then
    git -C "$REPO_DIR" pull --ff-only
else
    # If running from a local copy, rsync it in
    if [[ -f "$(dirname "$0")/agent_main.py" || -d "$(dirname "$0")/scripts" ]]; then
        rsync -a --exclude='.git' "$(dirname "$0")/" "$REPO_DIR/"
    else
        die "Cannot locate agent source. Run this script from the repo root."
    fi
fi
chown -R "$AGENT_USER:$AGENT_USER" "$REPO_DIR"

# ---------------------------------------------------------------------------
# 4. Python virtual environment + dependencies
# ---------------------------------------------------------------------------
log "Creating Python virtual environment..."
python3.11 -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install --upgrade pip -q
"$VENV_DIR/bin/pip" install -q \
    httpx \
    python-telegram-bot \
    python-dotenv \
    pyyaml \
    aiofiles \
    aiohttp

# ---------------------------------------------------------------------------
# 5. Workspace directory structure
# ---------------------------------------------------------------------------
log "Creating workspace at $WORKSPACE_ROOT..."
for d in \
    exchange-specs nexus-docs research tracking \
    output briefs context tools skills; do
    mkdir -p "$WORKSPACE_ROOT/$d"
done

# Seed placeholder .gitkeep files so dirs are tracked if workspace is versioned
for d in exchange-specs nexus-docs research tracking output briefs; do
    touch "$WORKSPACE_ROOT/$d/.gitkeep"
done

chown -R "$AGENT_USER:$AGENT_USER" "$WORKSPACE_ROOT"

# ---------------------------------------------------------------------------
# 6. Copy workspace seed files (context, tools, skills)
# ---------------------------------------------------------------------------
log "Deploying context and skill documents..."
cp -r "$REPO_DIR/workspace/context/." "$WORKSPACE_ROOT/context/"
cp -r "$REPO_DIR/workspace/tools/."   "$WORKSPACE_ROOT/tools/"
cp -r "$REPO_DIR/workspace/skills/."  "$WORKSPACE_ROOT/skills/"
cp    "$REPO_DIR/workspace/standing-tasks.md" "$WORKSPACE_ROOT/"
chown -R "$AGENT_USER:$AGENT_USER" "$WORKSPACE_ROOT"

# ---------------------------------------------------------------------------
# 7. Environment file
# ---------------------------------------------------------------------------
ENV_FILE="/etc/nexus-agent.env"
if [[ ! -f "$ENV_FILE" ]]; then
    log "Creating environment file template at $ENV_FILE"
    cat > "$ENV_FILE" <<'EOF'
# Nexus Night Shift Agent — Environment Configuration
# Fill in actual values, then: systemctl restart nexus-agent
ANTHROPIC_API_KEY=sk-ant-REPLACE_ME
OPENROUTER_API_KEY=sk-or-REPLACE_ME
TELEGRAM_BOT_TOKEN=REPLACE_ME
TELEGRAM_ALLOWED_USER_ID=REPLACE_ME
WORKSPACE_ROOT=/workspace
LOG_LEVEL=INFO
EOF
    chmod 600 "$ENV_FILE"
    log "⚠  Edit $ENV_FILE with your actual API keys before starting the service."
else
    log "Environment file already exists at $ENV_FILE — skipping."
fi

# ---------------------------------------------------------------------------
# 8. Systemd service
# ---------------------------------------------------------------------------
log "Installing systemd service..."
cp "$REPO_DIR/services/nexus-agent.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable nexus-agent.service
log "Service installed. Start with: systemctl start nexus-agent"

# ---------------------------------------------------------------------------
# 9. Cron jobs
# ---------------------------------------------------------------------------
log "Installing cron jobs..."
CRON_FILE="/etc/cron.d/nexus-agent"
cat > "$CRON_FILE" <<EOF
# Nexus Night Shift Agent — Cron Schedule
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin

# 11:30 PM — Check for nightly brief; remind if missing
30 23 * * 1-5 $AGENT_USER $VENV_DIR/bin/python $REPO_DIR/scripts/check_brief.py >> /var/log/nexus-agent-cron.log 2>&1

# 7:00 AM — Send morning report via Telegram
0  7  * * 1-5 $AGENT_USER $VENV_DIR/bin/python $REPO_DIR/scripts/morning_report.py >> /var/log/nexus-agent-cron.log 2>&1
EOF
chmod 644 "$CRON_FILE"

# ---------------------------------------------------------------------------
# 10. Log file
# ---------------------------------------------------------------------------
touch /var/log/nexus-agent.log /var/log/nexus-agent-cron.log
chown "$AGENT_USER:$AGENT_USER" /var/log/nexus-agent.log /var/log/nexus-agent-cron.log

# ---------------------------------------------------------------------------
log "Installation complete."
log ""
log "Next steps:"
log "  1. Edit /etc/nexus-agent.env with your API keys"
log "  2. systemctl start nexus-agent"
log "  3. Verify Telegram bot responds: send it any message"
log "  4. Check logs: journalctl -u nexus-agent -f"
