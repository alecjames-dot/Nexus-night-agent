# Nexus Night Shift Agent

Autonomous overnight PM agent for the Nexus blockchain product team.
Takes a nightly briefing via Telegram, executes product work (spec drafting,
developer docs, research, document organization), and delivers a structured
morning report.

## Architecture

```
Telegram brief (11 PM)
      │
      ▼
agent_main.py (systemd service)
      │
      ├── BriefHandler: saves brief to /workspace/briefs/YYYY-MM-DD.md
      │
      └── TaskExecutor: routes tasks to appropriate model
              │
              ├── Routine tasks (organize, track-update, research-gather)
              │     └── OpenRouter → nousresearch/hermes-3-llama-3.1-70b
              │
              └── Complex tasks (spec-draft, doc-write, research-synthesize)
                    └── Claude API → claude-sonnet-4 (via claude_escalate.py)

Cron: 11:30 PM → check_brief.py (sends Telegram reminder if no brief)
Cron: 7:00 AM  → morning_report.py (sends report.md via Telegram)
```

## Repository layout

```
├── install.sh                    # Full VM setup script (run as root)
├── .env.example                  # Environment variable template
├── services/
│   └── nexus-agent.service       # systemd service definition
├── scripts/
│   ├── agent_main.py             # Telegram gateway + main loop
│   ├── brief_handler.py          # Brief saving and task parsing
│   ├── task_executor.py          # Task routing and execution
│   ├── check_brief.py            # 11:30 PM cron: remind if no brief
│   ├── morning_report.py         # 7:00 AM cron: send report
│   ├── standing_tasks.py         # Fallback tasks when no brief
│   └── smoke_test.py             # Night 1 verification script
└── workspace/
    ├── context/                  # Persistent agent context (loaded every session)
    │   ├── nexus-product-context.md
    │   ├── agent-role.md
    │   └── spec-conventions.md
    ├── tools/
    │   ├── claude_escalate.py    # Claude API escalation utility
    │   └── notion_sync.py        # Notion sync (Phase 2 stub)
    ├── skills/                   # Skill Documents
    │   ├── exchange-spec-drafting.skill.md
    │   ├── nexus-dev-docs.skill.md
    │   └── competitive-research.skill.md
    ├── tracking/
    │   ├── feature-registry.md
    │   └── launch-phases.md
    ├── standing-tasks.md         # Backlog for no-brief nights
    └── SETUP_LOG.md              # Configuration decisions and deviations
```

## Installation

### Prerequisites
- Ubuntu 22.04+ VM (Hetzner CPX31 recommended: 4 vCPU, 8GB RAM)
- SSH access as root
- Telegram bot token from @BotFather
- Your Telegram user ID (get via @userinfobot)
- OpenRouter API key (openrouter.ai)
- Anthropic API key (console.anthropic.com)

### Steps

```bash
# 1. Clone repo to VM
git clone <repo-url> /opt/nexus-night-agent
cd /opt/nexus-night-agent

# 2. Run installer
bash install.sh

# 3. Set API keys and credentials
nano /etc/nexus-agent.env

# 4. Start the service
systemctl start nexus-agent
systemctl status nexus-agent

# 5. Run Night 1 smoke test
source /etc/nexus-agent.env
python /opt/nexus-night-agent/scripts/smoke_test.py
```

### Environment variables

| Variable | Description |
|---|---|
| `ANTHROPIC_API_KEY` | Claude API key |
| `OPENROUTER_API_KEY` | OpenRouter API key |
| `TELEGRAM_BOT_TOKEN` | Bot token from @BotFather |
| `TELEGRAM_ALLOWED_USER_ID` | Your Telegram user ID (restricts access) |
| `WORKSPACE_ROOT` | Workspace path (default: `/workspace`) |
| `LOG_LEVEL` | Logging verbosity (default: `INFO`) |

## Usage

Send a Telegram message to your bot with tonight's priorities:

```
Tonight's priorities:

1. Draft the depth chart spec section for the exchange PRD.
   Context: bid/ask spread display, configurable depth levels (5/10/20/50).
   Research dYdX and Vertex for reference.

2. Research best practices for developer onboarding docs for new L1 chains.
   Look at Sui, Aptos, Monad, and Berachain.

3. Update the launch tracker — mark Blockscout integration as complete.
```

The agent will:
1. Save the brief to `/workspace/briefs/YYYY-MM-DD.md`
2. Execute each task overnight
3. Write output to `/workspace/output/YYYY-MM-DD/`
4. Send a morning report via Telegram at 7 AM

## Commands

| Command | Description |
|---|---|
| `/start` | Show welcome message and command list |
| `/status` | Current execution status |
| `/report` | Resend the latest morning report |
| `/brief` | Show today's brief |

## Cost model

| Model | Est. nightly tokens | Est. cost |
|---|---|---|
| Hermes 3 70B (OpenRouter) | ~2M | ~$1.00–1.80 |
| Claude Sonnet 4 | ~500K | ~$1.50–2.75 |
| **Total** | | **~$2.50–4.55** |

Set spend limits in your Anthropic Console and OpenRouter dashboard.

## Security

- Telegram bot restricted to a single user ID via `TELEGRAM_ALLOWED_USER_ID`
- API keys stored in `/etc/nexus-agent.env` (mode 600)
- Agent runs as unprivileged `nexus-agent` system user
- No write access to production systems — local markdown files only
- SSH access via key only (disable password auth: `PasswordAuthentication no` in sshd_config)

## Logs

```bash
# Service logs
journalctl -u nexus-agent -f

# Cron job logs
tail -f /var/log/nexus-agent-cron.log

# Agent runtime log
tail -f /var/log/nexus-agent.log
```

## Development notes

See `workspace/SETUP_LOG.md` for a record of all configuration decisions
and deviations from the original spec.

The primary deviation: Hermes Agent (Nous Research) was not publicly available
as an installable package, so the orchestration layer was implemented directly
in Python. All spec-defined behaviors are preserved.
