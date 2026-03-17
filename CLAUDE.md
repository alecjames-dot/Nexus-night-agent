<project>
  <overview>
    This repo is the Nexus Night Shift Agent — an autonomous overnight PM agent
    that runs on a DigitalOcean Droplet (Ubuntu 24.04, SFO2). It takes a nightly
    briefing via Telegram, executes product work (spec drafting, developer docs,
    research, document organization) against a local markdown workspace using
    Claude Sonnet (Anthropic API) as the primary model, and delivers a structured
    morning report.

    The agent serves Alec, a Product Manager at Nexus, working across the Nexus EVM L1
    blockchain (chain ID 3946 mainnet, 3945 testnet) and Nexus Exchange (perpetual
    futures DEX). The public mainnet launch target is April 21, 2026.
  </overview>

  <architecture>
    The system has two layers:

    1. TELEGRAM GATEWAY (scripts/agent_main.py)
       - Pure Python implementation via python-telegram-bot
       - Restricted to a single authorized Telegram user ID
       - Runs as a systemd service (nexus-agent.service)
       - Receives nightly briefs, routes to TaskExecutor, sends morning report

    2. TASK EXECUTOR (scripts/task_executor.py)
       - All tasks execute via Claude Sonnet 4.6 (Anthropic API, direct)
       - No model routing — Claude handles spec drafting, docs, research, and general tasks
       - Spend ceilings enforced per-night ($5.00) and per-task ($3.00)
       - Token usage logged to /workspace/tracking/token-usage.log
       - Output always written to /workspace/output/YYYY-MM-DD/<task-slug>/

    Note: This architecture is intentionally simple for Week 1 testing.
    Optimization (caching, batching, model routing) can be added later.
  </architecture>

  <repo_structure>
    /opt/nexus-night-agent/
    ├── workspace/
    │   ├── exchange-specs/        — PRD sections, M1.1 spec, feature registry
    │   ├── nexus-docs/            — Developer documentation drafts
    │   ├── research/              — Competitor analysis, protocol research
    │   ├── tracking/              — Status trackers, token-usage.log
    │   ├── output/
    │   │   └── YYYY-MM-DD/       — Nightly output directories
    │   ├── briefs/
    │   │   └── YYYY-MM-DD.md     — Nightly briefs from Telegram
    │   ├── context/               — Product context loaded as system prompt
    │   │   ├── agent-role.md
    │   │   ├── nexus-product-context.md
    │   │   └── spec-conventions.md
    │   ├── config/
    │   │   └── SOUL.md            — Agent persona (injected into system prompt)
    │   ├── skills/                — Reusable task patterns
    │   │   ├── competitive-research.skill.md
    │   │   ├── exchange-spec-drafting.skill.md
    │   │   └── nexus-dev-docs.skill.md
    │   ├── standing-tasks.md      — Fallback task queue for no-brief nights
    │   └── tools/
    │       └── notion_sync.py     — Notion sync (Phase 2 placeholder)
    ├── scripts/
    │   ├── agent_main.py          — Telegram gateway (systemd service entry point)
    │   ├── brief_handler.py       — Brief parsing and task classification
    │   ├── check_brief.py         — Cron: 11:30 PM reminder + midnight fallback
    │   ├── morning_report.py      — Cron: 7 AM report delivery
    │   ├── smoke_test.py          — Night 1 verification script
    │   ├── standing_tasks.py      — Standing task queue executor
    │   └── task_executor.py       — Core execution engine (Claude Sonnet API)
    ├── services/
    │   └── nexus-agent.service    — systemd service definition
    ├── .venv/                     — Python virtual environment (created by install.sh)
    ├── requirements.txt
    └── install.sh                 — VM setup script
  </repo_structure>

  <environment>
    - VM: DigitalOcean Basic Premium Droplet, 2 vCPU / 4GB RAM, Ubuntu 24.04
    - User: deploy (not root)
    - Python: 3.11+ in .venv
    - Model: claude-sonnet-4-6 via OpenRouter API (anthropic/claude-sonnet-4-6)

    Environment variables (in /etc/nexus-agent.env):
    - OPENROUTER_API_KEY
    - TELEGRAM_BOT_TOKEN
    - TELEGRAM_ALLOWED_USER_ID
    - WORKSPACE_ROOT (default: /workspace)
    - NIGHT_SPEND_CEILING_USD (default: 5.00)
    - TASK_SPEND_CEILING_USD (default: 3.00)
    - LOG_LEVEL (default: INFO)

    Crontab (system crontab, America/Los_Angeles):
    30 23 * * 1-5  .venv/bin/python3 scripts/check_brief.py reminder
    5  0  * * 2-6  .venv/bin/python3 scripts/check_brief.py fallback
    0  7  * * 2-6  .venv/bin/python3 scripts/morning_report.py
  </environment>

  <coding_conventions>
    - Python scripts use async/await; task_executor uses anthropic.AsyncAnthropic
    - All API keys read from environment variables, NEVER hardcoded
    - Agent output always written to /workspace/output/YYYY-MM-DD/, never overwriting source files
    - Date format: YYYY-MM-DD everywhere (directory names, brief filenames, report filenames)
    - Markdown is the universal file format — no JSON configs for content, no databases
    - Error handling: always try/except API calls, log failures, never silently swallow errors
    - Scripts called from cron must use absolute paths or be run from the repo root
    - Cron scripts must use the .venv Python: /opt/nexus-night-agent/.venv/bin/python3
  </coding_conventions>

  <nexus_context>
    Nexus is an EVM-compatible L1 blockchain.
    - Chain IDs: 3946 (mainnet), 3945 (testnet)
    - Native token: $NEX
    - Gas mechanism: EIP-1559
    - Key partners: Wormhole (bridge), Blockscout (explorer), Sourcify (verification),
      dTeam + Cloudflare (RPC), Halliday (onramp), Anchorage (custody)

    Nexus Exchange is a perpetual futures DEX on the Nexus chain.
    - Current milestone: M1.1 (Full Order Suite)
    - Order types: market, limit, stop, TP/SL, position exits
    - Margin asset: USDX

    Spec conventions:
    - Feature IDs: F-XXX
    - Requirements: REQ-XXX, use "must" not "should"
    - Every spec needs: Feature ID, User Story, Requirements, Edge Cases (min 3),
      Acceptance Criteria (testable), Open Questions
    - Dev docs target external developers building on Nexus
    - All code examples use Solidity/ethers.js/viem with correct chain IDs
  </nexus_context>

  <critical_rules>
    - NEVER hardcode API keys or secrets in any file
    - NEVER overwrite source files in workspace — always write to /output/
    - NEVER leave the Telegram bot unrestricted — always enforce TELEGRAM_ALLOWED_USER_ID
    - All cron scripts must handle the case where they're called but have nothing to do
    - Morning reports must always include token usage and cost estimates
    - When modifying scripts called by cron, verify paths are absolute or cwd-relative to repo root
  </critical_rules>

  <current_status>
    - Architecture: Claude Sonnet 4.6 as sole model (Week 1 testing phase)
    - Telegram gateway: systemd service (nexus-agent.service)
    - All tasks execute via httpx in task_executor.py (OpenRouter OpenAI-compatible endpoint)
    - Skill documents in /workspace/skills/ guide Claude's task execution
    - Context files in /workspace/context/ loaded as system prompt for every task
  </current_status>

  <common_tasks>
    When asked to make changes, the most common tasks will be:

    1. Skill document refinement — updating /workspace/skills/*.skill.md based on evaluation findings
    2. Script fixes — bugs in check_brief.py, morning_report.py, or task_executor.py
    3. System prompt tuning — adjusting context files or task-specific instructions in task_executor.py
    4. Cost optimization — reducing token usage through better prompts or context trimming
    5. Adding new task types — extending task_instructions in TaskExecutor._call_claude()
    6. Context file updates — keeping /workspace/context/ accurate as the product evolves
  </common_tasks>
</project>
