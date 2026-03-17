<project>
  <overview>
    This repo is the Nexus Night Shift Agent — an autonomous overnight PM agent
    that runs on a DigitalOcean Droplet (Ubuntu 24.04, SFO2) powered by Hermes Agent
    (Nous Research). It takes a nightly briefing via Telegram, executes product work
    (spec drafting, developer docs, research, document organization) against a local
    markdown workspace, escalates complex reasoning to the Claude API, and delivers
    a structured morning report.

    The agent serves Alec, a Product Manager at Nexus, working across the Nexus EVM L1
    blockchain (chain ID 3946 mainnet, 3945 testnet) and Nexus Exchange (perpetual
    futures DEX). The public mainnet launch target is April 21, 2026.
  </overview>

  <architecture>
    The system has three layers:

    1. HERMES AGENT (core runtime)
       - Model: anthropic/claude-sonnet-4.6 via Anthropic API (direct, not OpenRouter)
       - Terminal backend: local
       - Gateway: Telegram (restricted to single user ID)
       - Memory + Skills: Hermes built-in system (~/.hermes/memories/, ~/.hermes/skills/)
       - Context: AGENTS.md files discovered automatically by Hermes at every directory level
       - Cron: system crontab, NOT Hermes native cron

    2. WORKSPACE (/opt/nexus-night-agent/workspace/)
       - exchange-specs/    — PRD sections, M1.1 spec, feature registry
       - nexus-docs/        — Developer documentation drafts
       - research/          — Competitor analysis, protocol research
       - tracking/          — Status trackers, launch checklist, partner matrix
       - output/            — Agent's nightly output (new drafts, diffs, reports)
       - briefs/            — Nightly brief files (input from Alec via Telegram)
       - context/           — Legacy context files (being migrated to AGENTS.md)
       - tools/             — Python utilities (Claude escalation, Notion sync)

    3. CLAUDE ESCALATION (workspace/tools/claude_escalate.py)
       - Called via Hermes execute_code tool for complex reasoning tasks
       - Three functions: draft_spec_section(), draft_developer_doc(), synthesize_research()
       - Uses Claude Sonnet 4.6 directly via Anthropic API
       - API key from environment variable ANTHROPIC_API_KEY
  </architecture>

  <repo_structure>
    /opt/nexus-night-agent/
    ├── workspace/
    │   ├── AGENTS.md                    # Root-level agent instructions (CRITICAL FILE)
    │   ├── exchange-specs/
    │   │   ├── AGENTS.md                # PRD-specific conventions
    │   │   └── *.md
    │   ├── nexus-docs/
    │   │   ├── AGENTS.md                # Doc-writing conventions
    │   │   └── *.md
    │   ├── research/
    │   ├── tracking/
    │   │   └── standing-tasks.md        # Fallback task queue for no-brief nights
    │   ├── output/
    │   │   └── YYYY-MM-DD/             # Nightly output directories
    │   ├── briefs/
    │   │   └── YYYY-MM-DD.md           # Nightly briefs from Telegram
    │   ├── context/                     # Legacy context files
    │   │   ├── agent-role.md
    │   │   ├── nexus-product-context.md
    │   │   └── spec-conventions.md
    │   └── tools/
    │       └── claude_escalate.py       # Claude API escalation utility
    ├── scripts/
    │   ├── check_brief.py              # Cron: reminder + fallback modes
    │   └── send_morning_report.py      # Cron: morning report to Telegram
    ├── .venv/                           # Python virtual environment
    ├── requirements.txt
    ├── SETUP_LOG.md                     # Deviations from original spec
    └── STATUS.md                        # Post-setup status report
  </repo_structure>

  <environment>
    - VM: DigitalOcean Basic Premium Droplet, 2 vCPU / 4GB RAM, Ubuntu 24.04
    - User: deploy (not root)
    - Python: 3.11+ in .venv
    - Hermes Agent: installed at ~/.local/bin/hermes
    - Hermes config: ~/.hermes/config.yaml
    - Hermes skills: ~/.hermes/skills/
    - Hermes memory: ~/.hermes/memories/

    Environment variables (in ~/.bashrc and /etc/environment.d/nightshift.conf):
    - ANTHROPIC_API_KEY
    - OPENROUTER_API_KEY
    - TELEGRAM_BOT_TOKEN
    - TELEGRAM_USER_ID

    Crontab (deploy user, America/Los_Angeles):
    30 23 * * 1-5  .venv/bin/python3 scripts/check_brief.py reminder
    5  0  * * 2-6  .venv/bin/python3 scripts/check_brief.py fallback
    0  7  * * 2-6  .venv/bin/python3 scripts/send_morning_report.py
  </environment>

  <coding_conventions>
    - Python scripts use async/await with httpx for API calls
    - All API keys read from environment variables, NEVER hardcoded
    - Agent output always written to /workspace/output/YYYY-MM-DD/, never overwriting source files
    - Date format: YYYY-MM-DD everywhere (directory names, brief filenames, report filenames)
    - Markdown is the universal file format — no JSON configs for content, no databases
    - Error handling: always try/catch API calls, log failures, never silently swallow errors
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
    - NEVER connect to production systems, GitHub repos, or databases from the agent
    - NEVER leave the Telegram bot unrestricted — always enforce TELEGRAM_ALLOWED_USERS
    - All cron scripts must handle the case where they're called but have nothing to do
    - Morning reports must always include token usage and cost estimates
    - Test changes locally with `hermes` CLI before assuming they work via Telegram gateway
    - When modifying scripts called by cron, verify paths are absolute or cwd-relative to repo root
  </critical_rules>

  <current_status>
    - Hermes Agent installed and running on DigitalOcean Droplet
    - Model: anthropic/claude-sonnet-4.6 (direct Anthropic API, not OpenRouter)
    - Telegram gateway: installed as systemd user service
    - Firecrawl and Honcho enabled for web search and persistent user modeling
    - AGENTS.md files need content migration from legacy /context/ files
    - Currently in evaluation phase (Nights 1-3 testing)
  </current_status>

  <common_tasks>
    When asked to make changes, the most common tasks will be:

    1. AGENTS.md refinement — updating agent instructions based on evaluation findings
    2. Script fixes — bugs in check_brief.py, send_morning_report.py, or claude_escalate.py
    3. Skill document creation — writing or editing files in ~/.hermes/skills/
    4. Workflow tuning — adjusting the task parsing, model routing, or report template logic
    5. Cost optimization — reducing token usage through better prompts or smarter routing
    6. Adding new task types — extending the agent to handle new categories of overnight work
  </common_tasks>
</project>
