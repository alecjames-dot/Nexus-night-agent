# Nexus Night Shift Agent

Autonomous overnight PM agent for the Nexus blockchain product team. Send it
tonight's priorities via Telegram. Wake up to a morning report with completed
drafts, research, and tracking updates.

Built on [Hermes Agent](https://github.com/NousResearch/hermes-agent) by Nous Research,
with a hybrid inference model: Hermes 3 70B via OpenRouter for routine tasks,
Claude Sonnet 4 for spec drafting, doc writing, and research synthesis.

---

## Table of contents

1. [How it works](#1-how-it-works)
2. [Prerequisites](#2-prerequisites)
3. [VM setup](#3-vm-setup)
4. [Installation](#4-installation)
5. [Configuration](#5-configuration)
6. [First run](#6-first-run)
7. [Daily interaction](#7-daily-interaction)
8. [Workspace layout](#8-workspace-layout)
9. [Model routing](#9-model-routing)
10. [Cron schedule](#10-cron-schedule)
11. [Skill documents](#11-skill-documents)
12. [Cost management](#12-cost-management)
13. [Monitoring and logs](#13-monitoring-and-logs)
14. [Troubleshooting](#14-troubleshooting)

---

## 1. How it works

```
You (Telegram)          VM                            APIs
     │                   │                              │
     │  Tonight's brief  │                              │
     ├──────────────────►│                              │
     │                   │  Parse tasks                 │
     │                   │  Load workspace context      │
     │                   │                              │
     │                   │  Routine tasks               │
     │                   ├─────────────────────────────►│ OpenRouter
     │                   │                     Hermes 3 │ (nousresearch/hermes-3-llama-3.1-70b)
     │                   │◄─────────────────────────────│
     │                   │                              │
     │                   │  Spec drafting / docs /      │
     │                   │  research synthesis          │
     │                   ├─────────────────────────────►│ Anthropic
     │                   │              Claude Sonnet 4 │ (claude-sonnet-4-20250514)
     │                   │◄─────────────────────────────│
     │                   │                              │
     │                   │  Write output files          │
     │                   │  /workspace/output/YYYY-MM-DD/
     │                   │                              │
     │  Morning report   │                              │
     │◄──────────────────│  (7:00 AM cron)              │
```

**Every night the agent:**
1. Receives your brief via Telegram, saves it to `/workspace/briefs/YYYY-MM-DD.md`
2. Classifies each task and routes it to the right model
3. Writes all output to `/workspace/output/YYYY-MM-DD/`
4. Generates a morning report and sends it to you at 7 AM
5. Auto-creates Skill Documents from successful complex tasks (Hermes built-in)

---

## 2. Prerequisites

Before starting you'll need:

| Item | Where to get it |
|------|----------------|
| Ubuntu 22.04+ VM (4 vCPU, 8 GB RAM recommended) | Hetzner CPX31 ~$16/mo |
| SSH access to the VM | — |
| Telegram bot token | [@BotFather](https://t.me/BotFather) on Telegram |
| Your Telegram chat ID | [@userinfobot](https://t.me/userinfobot) on Telegram |
| OpenRouter API key | [openrouter.ai/keys](https://openrouter.ai/keys) |
| Anthropic API key | [console.anthropic.com](https://console.anthropic.com) |

> **Cost:** OpenRouter for Hermes 3 70B is ~$0.90/1M tokens. Claude Sonnet 4 is
> ~$3/1M input, $15/1M output. Estimated nightly cost: **$2.50–$4.55**.
> Set spend limits in both consoles before going live.

---

## 3. VM setup

```bash
# SSH into your VM
ssh ubuntu@<vm-ip>

# Install git and curl (if not present)
sudo apt-get update && sudo apt-get install -y git curl

# Clone this repo
git clone https://github.com/nexus-xyz/nexus-night-agent.git
cd nexus-night-agent
```

---

## 4. Installation

Run the installer as your regular user (not root):

```bash
bash install.sh
```

The installer:
- Downloads and installs Hermes Agent via the official installer
- Creates `/workspace/` with all required directories
- Copies context files, skill documents, and tools to the workspace
- Installs skill documents to `~/.hermes/skills/`
- Writes a starter `~/.hermes/config.yaml` (configured for OpenRouter + Hermes 3)
- Installs `~/.hermes/SOUL.md` (the agent's personality and operating instructions)
- Installs the Telegram gateway as a systemd service
- Registers the 11:30 PM brief check and 7:00 AM report cron jobs

After the installer finishes, your shell needs to pick up the new `hermes` command:

```bash
source ~/.bashrc   # or ~/.zshrc if you use zsh
hermes --version   # should print a version number
```

---

## 5. Configuration

### 5.1 Set your API keys

Open `~/.hermes/.env` and fill in all four values:

```bash
nano ~/.hermes/.env
```

```bash
OPENROUTER_API_KEY=sk-or-...        # OpenRouter key
ANTHROPIC_API_KEY=sk-ant-...        # Anthropic / Claude key
TELEGRAM_BOT_TOKEN=123456:ABC...    # From @BotFather
TELEGRAM_HOME_CHANNEL=123456789     # Your Telegram chat ID (from @userinfobot)
WORKSPACE_ROOT=/workspace
```

Save and close (`Ctrl+O`, `Enter`, `Ctrl+X` in nano).

> The file is mode 600 (owner read/write only). Never commit it or share it.

### 5.2 Verify the config

```bash
hermes config          # Print current configuration
hermes doctor          # Check for missing keys or broken setup
```

### 5.3 Optional: tune the model

To switch the primary model:

```bash
hermes model
# Interactive selector — choose OpenRouter → nousresearch/hermes-3-llama-3.1-70b
```

Or set it directly:

```bash
hermes config set model.provider openrouter
hermes config set model.default "nousresearch/hermes-3-llama-3.1-70b"
```

### 5.4 Review SOUL.md

`~/.hermes/SOUL.md` is the agent's permanent system prompt. It encodes:
- The nightly workflow (parse brief → classify → route → write output → report)
- Model routing rules (what goes to Claude vs. Hermes)
- Workspace paths and conventions
- Nexus product facts (chain IDs, partners, current milestone)

You can edit it directly:

```bash
nano ~/.hermes/SOUL.md
```

Keep product context current (current milestone, launch phase, key decisions).
Also update `/workspace/context/nexus-product-context.md` — both are read by the agent.

---

## 6. First run

### 6.1 Start the Telegram gateway

```bash
hermes gateway --platform telegram
```

You should see:
```
[gateway] Connecting to Telegram...
[gateway] Telegram adapter connected ✓
[gateway] Listening for messages...
```

> To run the gateway persistently, use the systemd service installed by the
> installer: `systemctl --user start hermes-gateway` (see Section 13).

### 6.2 Test the connection

Open Telegram and send your bot:

```
/start
```

You should get a response from the agent. If not, see [Troubleshooting](#14-troubleshooting).

### 6.3 Night 1 smoke test

Send this message to the bot:

```
Tonight's priorities:

1. Summarize the contents of /workspace/ and confirm you can access all context files. Draft a 1-paragraph test spec for a 'Hello World' feature.
```

Verify:
- [ ] Brief saved to `/workspace/briefs/YYYY-MM-DD.md`
- [ ] Output written to `/workspace/output/YYYY-MM-DD/`
- [ ] Morning report generated in `/workspace/output/YYYY-MM-DD/report.md`
- [ ] Report sent to Telegram at 7 AM

You can also trigger the smoke test script directly:

```bash
python3 scripts/smoke_test.py
```

---

## 7. Daily interaction

### Sending the nightly brief

Each evening, send your bot a message with numbered priorities. You can send it
any time — the agent processes it immediately and works through the night.

**Message format:**

```
Tonight's priorities:

1. [Task description with context]
   Context: [any relevant details, source files, references]

2. [Task description]
   Research: [what to look at]

3. [Task description]
```

**Real example:**

```
Tonight's priorities:

1. Draft the depth chart spec section for the exchange PRD.
   Context: Should cover order book visualization, bid/ask spread display,
   configurable depth levels (5/10/20/50). Look at how dYdX and Vertex
   handle this for reference.

2. Research: What are best practices for developer onboarding docs
   for new L1 chains? Look at Sui, Aptos, Monad, and Berachain docs.

3. Update the launch tracker — mark Blockscout integration as complete,
   add a row for "Gas fee estimation API" as a new P1 item.
```

### Telegram commands

| Command | What it does |
|---------|-------------|
| `/start` | Shows welcome message and command list |
| `/new` or `/reset` | Clears the current session context |
| Any text message | Sent as a task or conversation to the agent |

### What to expect overnight

- **11:30 PM:** If no brief was received, the bot sends a reminder asking whether
  to use the standing task queue.
- **During the night:** The agent works through each task, writing files to
  `/workspace/output/YYYY-MM-DD/`.
- **7:00 AM:** The morning report is sent to your Telegram. It includes:
  - Summary of what was done
  - Links to output files (as workspace paths)
  - Decisions made that need your review
  - Any blocked items
  - Token usage and estimated cost

### Reading the morning report

The report is sent to Telegram and saved to `/workspace/output/YYYY-MM-DD/report.md`.
To read it on the VM:

```bash
# Find the latest report
ls -lt /workspace/output/ | head -5

# Read it
cat /workspace/output/$(date +%Y-%m-%d)/report.md
```

### Reviewing output files

All output is in `/workspace/output/YYYY-MM-DD/<task-slug>/`:

```bash
# List all output from last night
ls /workspace/output/$(date +%Y-%m-%d)/

# Read a specific output
cat /workspace/output/2026-03-15/depth-chart-spec/depth-chart-spec.md
```

### No brief tonight?

If you don't send a brief, the agent will:
1. Send a reminder at 11:30 PM
2. If no brief by midnight, automatically work from the standing task queue
   (`/workspace/standing-tasks.md`), starting with P0 items

To explicitly trigger the standing tasks:

```
use standing tasks
```

---

## 8. Workspace layout

```
/workspace/
├── briefs/              ← Nightly briefs (YYYY-MM-DD.md)
│   └── 2026-03-15.md
├── output/              ← Agent's nightly output
│   └── 2026-03-15/
│       ├── report.md           ← Morning report
│       ├── depth-chart-spec/
│       │   └── depth-chart-spec.md
│       └── l1-onboarding-research/
│           └── l1-onboarding-research.md
├── exchange-specs/      ← Exchange PRD sections (source — read only)
├── nexus-docs/          ← Developer docs (source — read only)
├── research/            ← Research library
├── tracking/
│   ├── feature-registry.md    ← F-XXX and REQ-XXX ID tracking
│   └── launch-phases.md       ← Phase entry/exit criteria
├── context/             ← Persistent context (loaded every session)
│   ├── nexus-product-context.md
│   ├── agent-role.md
│   └── spec-conventions.md
├── tools/
│   ├── claude_escalate.py     ← Claude API escalation utility
│   └── notion_sync.py         ← Notion sync (Phase 2 stub)
├── skills/              ← Working copies of skill docs (also in ~/.hermes/skills/)
│   ├── exchange-spec-drafting.skill.md
│   ├── nexus-dev-docs.skill.md
│   └── competitive-research.skill.md
├── config/              ← Config templates (for reference)
│   ├── hermes-config.yaml
│   └── SOUL.md
├── standing-tasks.md    ← Backlog for no-brief nights
└── SETUP_LOG.md         ← Configuration decisions and deviations
```

### Uploading source documents

When you have Nexus docs or specs to feed the agent, copy them to the
appropriate directory:

```bash
# From your local machine
scp ~/notion-exports/m1.1-spec.md ubuntu@<vm-ip>:/workspace/exchange-specs/
scp ~/notion-exports/nexus-docs/*.md ubuntu@<vm-ip>:/workspace/nexus-docs/

# Or directly on the VM
cp ~/downloads/feature-registry.md /workspace/tracking/
```

---

## 9. Model routing

The agent self-routes based on task type. You don't need to specify — it decides.

| Task type | Trigger keywords | Model used |
|-----------|-----------------|------------|
| `spec-draft` | spec, prd, feature, requirement, draft spec | Claude Sonnet 4 |
| `doc-write` | doc, documentation, guide, tutorial, developer | Claude Sonnet 4 |
| `research` | research, analyze, compare, competitive, best practices | Hermes 3 gather → Claude synthesize |
| `track-update` | update, tracker, mark, checklist, feature registry | Hermes 3 |
| `organize` | organize, restructure, reformat, consolidate | Hermes 3 |

**Claude escalation** happens via `/workspace/tools/claude_escalate.py`:

```bash
# Test each function manually
python3 /workspace/tools/claude_escalate.py draft-spec "Depth Chart" "context..." "research..."
python3 /workspace/tools/claude_escalate.py draft-doc "Deploy First Contract" "context..."
python3 /workspace/tools/claude_escalate.py synthesize "L1 Onboarding" "raw research..."
```

---

## 10. Cron schedule

Cron jobs are registered via `hermes cron add` during install. To view them:

```bash
hermes cron list
```

| Time | Job |
|------|-----|
| 11:30 PM weeknights | Check for brief; send Telegram reminder if missing |
| 7:00 AM weekdays | Read morning report from `/workspace/output/` and send to Telegram |

To add or modify cron jobs in natural language:

```bash
hermes cron add "Every Sunday at 10 PM, run a standing tasks session from /workspace/standing-tasks.md and send results to Telegram"
```

To remove a job:

```bash
hermes cron list           # find the job ID
hermes cron remove <id>
```

---

## 11. Skill documents

Skill documents are reusable procedures that make the agent faster and more
consistent. They live in `~/.hermes/skills/` and are loaded when the agent
encounters a matching task.

Three skills are pre-seeded:

| Skill | File | Used for |
|-------|------|---------|
| `exchange-spec-drafting` | `~/.hermes/skills/exchange-spec-drafting/SKILL.md` | Exchange PRD sections |
| `nexus-dev-docs` | `~/.hermes/skills/nexus-dev-docs/SKILL.md` | Developer documentation |
| `competitive-research` | `~/.hermes/skills/competitive-research/SKILL.md` | Research and analysis |

### Viewing skills

```bash
hermes skills browse           # Interactive skill browser
ls ~/.hermes/skills/           # List installed skills
cat ~/.hermes/skills/exchange-spec-drafting/SKILL.md
```

### Auto-created skills

Hermes Agent automatically creates new skills after it completes complex tasks
successfully. Over time the agent builds a library of Nexus-specific patterns.
Check what it has learned:

```bash
ls ~/.hermes/skills/
```

### Editing a skill

If the agent is producing suboptimal output for a recurring task type, edit the
relevant skill document:

```bash
nano ~/.hermes/skills/exchange-spec-drafting/SKILL.md
```

---

## 12. Cost management

### Set spend limits (do this before Night 1)

**Anthropic Console:**
1. Go to [console.anthropic.com](https://console.anthropic.com) → Settings → Limits
2. Set a monthly spend limit (recommend: $60-80/mo to start)
3. Enable email alerts at 80% of limit

**OpenRouter Dashboard:**
1. Go to [openrouter.ai](https://openrouter.ai) → Account → Limits
2. Set a monthly credit limit

### Estimated costs

| Model | Est. nightly tokens | Est. cost |
|-------|-------------------|-----------|
| Hermes 3 70B (OpenRouter) | ~2M input+output | ~$1.00–1.80 |
| Claude Sonnet 4 (Anthropic) | ~500K input+output | ~$1.50–2.75 |
| **Nightly total** | | **~$2.50–4.55** |
| **Monthly (22 nights)** | | **~$55–100** |

The morning report includes actual token usage and cost so you can track spend
night by night.

### Reducing costs

To shift more tasks to Hermes 3 (cheaper) and less to Claude:
- Make the brief tasks more routine (organize, update, restructure)
- Reserve Claude escalation for new spec drafts and complex doc writing
- Review the morning report's cost breakdown — if Claude is doing work Hermes
  could handle, adjust the task descriptions

---

## 13. Monitoring and logs

### Service status

```bash
# Check if the gateway is running
systemctl --user status hermes-gateway

# Start / stop / restart
systemctl --user start hermes-gateway
systemctl --user stop hermes-gateway
systemctl --user restart hermes-gateway
```

### Logs

```bash
# Gateway logs (live)
journalctl --user -u hermes-gateway -f

# Session logs (all conversations)
ls ~/.hermes/sessions/
cat ~/.hermes/sessions/<latest>.json

# Cron job logs
ls ~/.hermes/cron/

# Agent output
ls /workspace/output/
```

### Check what the agent is doing

```bash
# See the latest session
hermes            # Start an interactive session, ask "what did you do last night?"

# Or just read the report
cat /workspace/output/$(date +%Y-%m-%d)/report.md
```

---

## 14. Troubleshooting

### Bot not responding on Telegram

1. Check the gateway is running: `systemctl --user status hermes-gateway`
2. Check `TELEGRAM_BOT_TOKEN` is set: `grep BOT_TOKEN ~/.hermes/.env`
3. Check `TELEGRAM_HOME_CHANNEL` is your correct chat ID
4. Restart the gateway: `systemctl --user restart hermes-gateway`
5. Run `hermes doctor` for diagnostics

### "ANTHROPIC_API_KEY not set" error

```bash
# Verify it's in the env file
grep ANTHROPIC ~/.hermes/.env

# Test Claude escalation directly
ANTHROPIC_API_KEY=sk-ant-... python3 /workspace/tools/claude_escalate.py \
    draft-doc "test" "test context"
```

### OpenRouter / Hermes 3 errors

```bash
# Check your OpenRouter key
grep OPENROUTER ~/.hermes/.env

# Test a basic hermes session
hermes
> Hello, can you confirm which model you're using?
```

### Morning report not sent

1. Check cron jobs: `hermes cron list`
2. Check cron logs: `ls ~/.hermes/cron/`
3. Verify the output directory exists: `ls /workspace/output/$(date +%Y-%m-%d)/`
4. Manually trigger: `hermes "Read the morning report from /workspace/output/ and send it to Telegram"`

### Agent not finding context files

Ensure context files are in place:

```bash
ls /workspace/context/
cat /workspace/context/nexus-product-context.md
```

The agent loads these at the start of each session via the SOUL.md instructions.
If content is outdated, update the files directly:

```bash
nano /workspace/context/nexus-product-context.md
```

### Hermes command not found after install

```bash
source ~/.bashrc
# If still not found:
export PATH="$HOME/.local/bin:$HOME/.hermes/bin:$PATH"
hermes --version
# Then add the export to ~/.bashrc permanently
```

### Run hermes doctor

```bash
hermes doctor
```

This checks for missing API keys, broken config, outdated versions, and other
common issues.

---

## Repository layout

```
├── install.sh                    # VM setup script (run as agent user)
├── .env.example                  # Template for environment variables
├── requirements.txt              # Python deps for claude_escalate.py
├── services/
│   └── nexus-agent.service       # Systemd service reference (for manual setup)
├── scripts/
│   ├── agent_main.py             # Standalone Telegram gateway (Hermes fallback)
│   ├── brief_handler.py          # Brief parsing utility
│   ├── task_executor.py          # Task routing and execution
│   ├── check_brief.py            # Standalone 11:30 PM brief check
│   ├── morning_report.py         # Standalone 7:00 AM report sender
│   ├── standing_tasks.py         # Standalone standing task executor
│   └── smoke_test.py             # Night 1 verification
└── workspace/
    ├── context/                  # Persistent product context
    │   ├── nexus-product-context.md
    │   ├── agent-role.md
    │   └── spec-conventions.md
    ├── config/
    │   ├── hermes-config.yaml    # ~/.hermes/config.yaml template
    │   └── SOUL.md               # ~/.hermes/SOUL.md (agent personality)
    ├── tools/
    │   ├── claude_escalate.py    # Claude API escalation utility
    │   └── notion_sync.py        # Notion sync stub (Phase 2)
    ├── skills/                   # Skill document source files
    │   ├── exchange-spec-drafting.skill.md
    │   ├── nexus-dev-docs.skill.md
    │   └── competitive-research.skill.md
    ├── tracking/
    │   ├── feature-registry.md
    │   └── launch-phases.md
    ├── standing-tasks.md
    └── SETUP_LOG.md              # Config decisions and deviations
```

> **Note on the `scripts/` directory:** These are standalone Python utilities that
> implement the full workflow without Hermes Agent. They serve as a fallback
> implementation and as reference code. When Hermes Agent is installed and running,
> the Hermes gateway + cron system handles the same functions natively.
