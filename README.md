# Nexus Night Shift Agent

An autonomous overnight PM agent for the Nexus blockchain and Nexus Exchange products.

## What It Does

The agent:
1. Listens for task briefs via Telegram
2. Executes all tasks via Claude Sonnet (Anthropic API, direct)
3. Writes all output to `/workspace/output/<date>/`
4. Delivers a morning report with completed work and cost tracking

## Requirements

- Ubuntu 22.04+ VM (2 vCPU, 4 GB RAM minimum)
- Python 3.11+
- API keys: Anthropic, Telegram
- Estimated cost: $2–$5/night (Claude Sonnet, depends on task volume)

## Quick Start

1. Clone this repository
2. Run `bash install.sh`
3. Edit `/etc/nexus-agent.env` with your API credentials
4. Start the service: `sudo systemctl start nexus-agent`
5. Send a test brief via Telegram

## Architecture

- **Gateway:** Telegram (python-telegram-bot)
- **Model:** Claude Sonnet 4.6 (Anthropic API, direct) — all task types
- **Workflow:** Brief → Parse → Execute → Report
- **Skill documents:** Reusable task patterns in `/workspace/skills/`

## Key Files

- `scripts/agent_main.py` — Telegram gateway and message routing
- `scripts/task_executor.py` — Task execution via Claude Sonnet API
- `workspace/context/` — Product context, spec conventions, agent role
- `workspace/skills/` — Reusable task patterns (spec, docs, research)
- `workspace/standing-tasks.md` — Fallback queue for brief-less nights

See CLAUDE.md for full technical overview.
