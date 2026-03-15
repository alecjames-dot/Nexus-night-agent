# Setup Log — Nexus Night Shift Agent

_Documents all configuration decisions, deviations from the spec, and reasoning.
Updated during setup and as configuration evolves._

---

## 2026-03-15 — Initial Setup

### Hermes Agent installation

Hermes Agent is installed via the official Nous Research installer:
```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
```

Repository: https://github.com/NousResearch/hermes-agent

The installer handles Python, Node.js, and all dependencies. After install,
`hermes` is available in `~/.local/bin` or `~/.hermes/bin`.

---

### Configuration decisions

| Setting | Value | Reason |
|---------|-------|--------|
| Primary model | `nousresearch/hermes-3-llama-3.1-70b` | Spec recommendation; good balance of cost/quality for routine PM tasks |
| Model provider | `openrouter` | OpenRouter supports 200+ models with no lock-in |
| Claude model | `claude-sonnet-4-20250514` | Best reasoning for spec drafting and synthesis |
| Gateway platform | Telegram | As specified; single-user restriction via `TELEGRAM_HOME_CHANNEL` |
| Skill location | `~/.hermes/skills/<skill-name>/SKILL.md` | Hermes Agent's standard skill directory |
| Workspace root | `/workspace/` | As specified |
| Session reset | Daily at 4 AM | Clears context between overnight sessions without disrupting the 7 AM report |
| Memory | Enabled, 4000 char limit | Allows agent to accumulate product knowledge over weeks |
| Auto skill creation | Enabled | Core spec requirement — agent improves over time |
| Context load | Via `SOUL.md` instructions | SOUL.md instructs agent to read `/workspace/context/` at session start |

---

### Deviation: Skill documents use `SKILL.md` filename inside subdirectory

**Spec said:** Skill Documents with `.skill.md` extension.

**What was done:** Each skill is a directory inside `~/.hermes/skills/` containing
a `SKILL.md` file, matching Hermes Agent's actual skill structure. The source
files in the repo use the `.skill.md` convention and are copied by `install.sh`.

**Example:**
- Source: `workspace/skills/exchange-spec-drafting.skill.md`
- Installed to: `~/.hermes/skills/exchange-spec-drafting/SKILL.md`

---

### Deviation: `hermes gateway setup` replaced with `hermes gateway install --platform telegram`

**Spec said:** `hermes gateway setup` → select Telegram → enter token.

**What was done:** Token and chat ID are set via `~/.hermes/.env` (environment
variables `TELEGRAM_BOT_TOKEN` and `TELEGRAM_HOME_CHANNEL`). Gateway is installed
as a service via `hermes gateway install --platform telegram`.

**Reason:** Hermes Agent reads gateway credentials from environment variables,
not an interactive setup wizard. This is more compatible with automated deployment.

---

### Deviation: User ID restriction via `TELEGRAM_HOME_CHANNEL`

**Spec said:** "Restrict the Telegram bot to a single user ID."

**What was done:** `TELEGRAM_HOME_CHANNEL` in `~/.hermes/.env` is set to the
owner's Telegram chat ID. The Hermes gateway only delivers messages to/from
the configured home channel.

**Security note:** The Hermes gateway also supports DM pairing for additional
access control. For extra security, consider enabling `hermes gateway pairing`
which requires new users to be explicitly approved.

---

### Standalone Python scripts (scripts/ directory)

The `scripts/` directory contains a full Python implementation of the workflow
using `python-telegram-bot`. These were built before confirming Hermes Agent's
availability and now serve as:

1. **Fallback** — if Hermes Agent is unavailable for any reason, the Python
   scripts can run the gateway, brief parsing, and report delivery independently
2. **Reference** — the Claude escalation logic in `task_executor.py` documents
   the routing decision making
3. **Claude utility** — `claude_escalate.py` is actively used by both the Hermes
   workflow (called via Hermes's code execution tool) and the standalone scripts

The standalone scripts require `TELEGRAM_ALLOWED_USER_ID` (not `TELEGRAM_HOME_CHANNEL`)
when run outside of Hermes.

---

## Open items for Night 1

- [ ] Confirm Hermes 3 70B model ID on OpenRouter (may need `:extended` suffix)
- [ ] Set spend limits in Anthropic Console (~$60-80/mo)
- [ ] Set spend limits in OpenRouter dashboard
- [ ] Test Telegram bot responds before first nightly run (`hermes doctor`)
- [ ] Upload initial exchange specs to `/workspace/exchange-specs/`
- [ ] Upload initial Nexus dev docs to `/workspace/nexus-docs/`
- [ ] Update `/workspace/context/nexus-product-context.md` with current milestone status

---

_Maintained by: Alec (manual updates) + agent (automated additions)_
_Last updated: 2026-03-15_
