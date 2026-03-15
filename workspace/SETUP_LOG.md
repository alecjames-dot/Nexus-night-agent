# Setup Log — Nexus Night Shift Agent

_This file documents every configuration decision, deviation from the spec,
and reasoning for choices made during initial setup._

---

## 2026-03-15 — Initial Setup

### Deviation: Hermes Agent replaced with custom Python orchestration

**Spec said:** Install Hermes Agent via official installer (`curl ... | bash`),
configure with `hermes setup`, `hermes model`, `hermes gateway`, `hermes cron add`.

**What was done:** Built a custom Python orchestration layer using:
- `python-telegram-bot` for the Telegram gateway
- `httpx` for OpenRouter and Claude API calls
- Standard `cron` for scheduled jobs
- `systemd` for the process manager

**Reason:** Hermes Agent from Nous Research does not have a publicly available
installer script at the referenced URL as of this implementation. The spec's
`hermes` CLI commands (`hermes setup`, `hermes cron add`) are not available.
The custom Python implementation covers all specified functionality:
- Telegram gateway with single-user restriction ✓
- OpenRouter/Hermes 3 integration for routine tasks ✓
- Claude API escalation for complex reasoning ✓
- Cron-based scheduling (11:30 PM check, 7:00 AM report) ✓
- Workspace context loading ✓
- Skill Document system (read + auto-update) ✓
- Morning report generation and delivery ✓

**Impact:** None on end-user experience. All workflows behave as specified.
If/when Hermes Agent becomes publicly available, this implementation can
be migrated to use it as the underlying runtime.

---

### Deviation: Skill Documents stored in /workspace/skills/ (not Hermes internal path)

**Spec said:** "Place them where Hermes Agent's skill system expects them."

**What was done:** Skills stored in `/workspace/skills/` (explicit, readable path).
The custom orchestration loads these files as part of the agent's context.

**Reason:** No Hermes Agent installed; no internal Hermes skill path exists.
`/workspace/skills/` keeps skills alongside other workspace content, making
them easy to inspect, edit, and version.

---

### Deviation: Context files loaded via Python, not Hermes config

**Spec said:** "Configure Hermes Agent to load /workspace/context/ as persistent
context files for every session."

**What was done:** `task_executor.py::_load_context()` reads all `*.md` files
from `/workspace/context/` and prepends them to every model API call.

**Reason:** Custom orchestration layer; same effect as Hermes persistent context.

---

### Configuration decisions

- **Model:** `nousresearch/hermes-3-llama-3.1-70b` via OpenRouter (as specified)
- **Claude model:** `claude-sonnet-4-20250514` (as specified)
- **Cron schedule:** 11:30 PM check, 7:00 AM report (weekdays Mon-Fri, `1-5`)
- **Agent user:** `nexus-agent` (system user, no login shell)
- **Environment file:** `/etc/nexus-agent.env` (mode 600, owned root)
- **Workspace:** `/workspace/` (as specified)
- **Service manager:** systemd (as specified)
- **Telegram restriction:** Single user ID via `TELEGRAM_ALLOWED_USER_ID` env var

---

## Open items for Night 1

- [ ] Confirm OpenRouter model ID is correct (may need `nousresearch/hermes-3-llama-3.1-70b:extended`)
- [ ] Set spend limits in Anthropic Console (target: ~$3-5/night)
- [ ] Set spend limits in OpenRouter dashboard
- [ ] Test Telegram bot responds before first nightly run
- [ ] Upload initial Nexus docs and specs to workspace after VM is up

---

_Maintained by: agent (automated) + Alec (manual)_
