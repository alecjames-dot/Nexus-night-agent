"""
Task Executor — executes all tasks via Claude Sonnet (Anthropic API).

All task types route directly to claude-sonnet-4-6.
"""

import asyncio
import logging
import os
from datetime import date
from pathlib import Path
from typing import Optional

import anthropic

log = logging.getLogger(__name__)

WORKSPACE_ROOT = Path(os.environ.get("WORKSPACE_ROOT", "/workspace"))
CLAUDE_MODEL = "claude-sonnet-4-6"

# Cost per 1M tokens (claude-sonnet-4-6, as of 2025)
CLAUDE_COST_PER_1M = {"input": 3.00, "output": 15.00}

# Spend ceilings — configurable via environment variables
NIGHT_SPEND_CEILING_USD = float(os.environ.get("NIGHT_SPEND_CEILING_USD", "5.00"))
TASK_SPEND_CEILING_USD = float(os.environ.get("TASK_SPEND_CEILING_USD", "3.00"))

TOKEN_USAGE_LOG = WORKSPACE_ROOT / "tracking" / "token-usage.log"
TOKEN_LOG_HEADER = "# date       | model             | input_tok | output_tok |  cost_usd
"


class ExecutionStats:
    def __init__(self):
        self.input_tokens = 0
        self.output_tokens = 0
        self.tasks_completed: list[dict] = []
        self.decisions: list[str] = []
        self.blocked: list[str] = []
        self.skills_created: list[str] = []

    def total_cost(self) -> float:
        return (
            self.input_tokens / 1_000_000 * CLAUDE_COST_PER_1M["input"]
            + self.output_tokens / 1_000_000 * CLAUDE_COST_PER_1M["output"]
        )


class TaskExecutor:
    def __init__(self, workspace_root: Path):
        self.workspace = workspace_root
        self.stats = ExecutionStats()
        self._current_task: Optional[str] = None
        self._status: str = "idle"
        self.fallback_mode: bool = False
        self._client = anthropic.AsyncAnthropic(
            api_key=os.environ.get("ANTHROPIC_API_KEY")
        )

    def get_status(self) -> str:
        if self._status == "idle":
            return "Agent is idle — no active execution."
        return f"Status: {self._status}
Current task: {self._current_task or 'none'}"

    async def execute_all(self, tasks, telegram_update=None) -> None:
        """Execute all tasks from the brief, write output, generate report."""
        today = date.today().isoformat()
        output_dir = self.workspace / "output" / today
        output_dir.mkdir(parents=True, exist_ok=True)
        self.stats = ExecutionStats()
        self._status = "running"

        context = self._load_context()

        for task in tasks:
            current_spend = self.stats.total_cost()
            if current_spend >= NIGHT_SPEND_CEILING_USD:
                msg = (
                    f"Task {task.number} ({task.slug}) not started — "
                    f"night spend ceiling ${NIGHT_SPEND_CEILING_USD:.2f} reached "
                    f"(spent so far: ${current_spend:.2f})"
                )
                log.warning(msg)
                self.stats.blocked.append(msg)
                if telegram_update:
                    await telegram_update.message.reply_text(f"🛑 {msg}")
                break

            self._current_task = task.slug
            log.info("Executing task %d [%s]: %s", task.number, task.task_type, task.raw[:60])
            cost_before_task = self.stats.total_cost()

            try:
                result = await self._execute_task(task, context, output_dir)

                task_cost = self.stats.total_cost() - cost_before_task
                if task_cost > TASK_SPEND_CEILING_USD:
                    warn_msg = (
                        f"[COST WARNING: task spent ${task_cost:.2f}, "
                        f"ceiling is ${TASK_SPEND_CEILING_USD:.2f}] "
                    )
                    log.warning("Task %d exceeded per-task ceiling: $%.2f", task.number, task_cost)
                    result["notes"] = warn_msg + result.get("notes", "")
                result["cost_usd"] = round(task_cost, 4)

                self.stats.tasks_completed.append(result)
            except Exception as exc:
                log.exception("Task %d failed: %s", task.number, exc)
                self.stats.blocked.append(f"Task {task.number} ({task.slug}): {exc}")
                if telegram_update:
                    await telegram_update.message.reply_text(
                        f"⚠️ Task {task.number} blocked: {exc}"
                    )

        report = self._generate_report(today)
        report_path = output_dir / "report.md"
        report_path.write_text(report, encoding="utf-8")
        log.info("Morning report written to %s", report_path)

        self._log_token_usage(today)

        self._status = "idle"
        self._current_task = None

    async def _execute_task(self, task, context: str, output_dir: Path) -> dict:
        """Execute a single task via Claude Sonnet."""
        task_dir = output_dir / task.slug
        task_dir.mkdir(parents=True, exist_ok=True)

        result_text = await self._call_claude(task, context)

        output_file = task_dir / f"{task.slug}.md"
        output_file.write_text(result_text, encoding="utf-8")
        log.info("Output written to %s", output_file)

        skill_note = self._maybe_create_skill(task, result_text)
        if skill_note:
            self.stats.skills_created.append(skill_note)

        notes = ""
        for line in result_text.splitlines():
            line = line.strip().lstrip("#").strip()
            if line and not line.startswith("---"):
                notes = line[:200]
                break

        return {
            "task_number": task.number,
            "task_type": task.task_type,
            "slug": task.slug,
            "model_used": CLAUDE_MODEL,
            "output_path": str(output_file.relative_to(self.workspace)),
            "status": "complete",
            "notes": notes,
        }

    def _load_context(self) -> str:
        """Load all persistent context files."""
        context_dir = self.workspace / "context"
        parts = []
        for md_file in sorted(context_dir.glob("*.md")):
            try:
                parts.append(f"=== {md_file.name} ===
{md_file.read_text(encoding='utf-8')}")
            except Exception as e:
                log.warning("Could not read context file %s: %s", md_file, e)
        return "

".join(parts)

    async def _call_claude(self, task, context: str) -> str:
        """Call Claude Sonnet directly with task and full context."""
        system = (
            "You are the Nexus Night Shift PM agent — an autonomous product management assistant "
            "working overnight for the Nexus blockchain and Nexus Exchange products. "
            "Execute the following task with precision and depth. Write production-ready output.

"
            f"CONTEXT:
{context}"
        )

        task_instructions = {
            "spec-draft": (
                "Draft a complete feature specification section following the conventions "
                "in spec-conventions.md. Include Feature ID, User Story, Requirements (use 'must' "
                "not 'should'), Edge Cases (minimum 3), Acceptance Criteria (Given/When/Then format), "
                "and Open Questions."
            ),
            "doc-write": (
                "Write complete developer documentation. Include a Prerequisites section, "
                "step-by-step guide, code examples using the correct chain IDs "
                "(mainnet=3946, testnet=3945) and RPC endpoints "
                "(mainnet=https://rpc.nexus.xyz, testnet=https://rpc-testnet.nexus.xyz), "
                "and a Common Errors section with at least 3 items."
            ),
            "research": (
                "Research the topic thoroughly and synthesize findings into structured "
                "recommendations. Include a comparison table, key findings, and prioritized "
                "P0/P1/P2 next steps explicitly framed for Nexus Exchange or Nexus chain context. "
                "Cite source URLs for all factual claims."
            ),
        }
        instruction = task_instructions.get(
            task.task_type,
            "Execute the following task and write the output as a well-structured markdown document.",
        )

        user_message = f"TASK:
{task.raw}

INSTRUCTION:
{instruction}"

        response = await self._client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=8192,
            temperature=0.3,
            system=system,
            messages=[{"role": "user", "content": user_message}],
        )

        usage = response.usage
        self.stats.input_tokens += usage.input_tokens
        self.stats.output_tokens += usage.output_tokens

        log.info(
            "Claude usage — in: %d, out: %d, cost: $%.4f",
            usage.input_tokens,
            usage.output_tokens,
            self.stats.total_cost(),
        )

        return response.content[0].text

    def _maybe_create_skill(self, task, result_text: str) -> Optional[str]:
        """Append a learned example to the matching skill document, if it exists."""
        skills_dir = self.workspace / "skills"
        skills_dir.mkdir(parents=True, exist_ok=True)

        skill_map = {
            "spec-draft": "exchange-spec-drafting",
            "doc-write": "nexus-dev-docs",
            "research": "competitive-research",
        }

        skill_name = skill_map.get(task.task_type)
        if not skill_name:
            return None

        skill_path = skills_dir / f"{skill_name}.skill.md"
        if not skill_path.exists():
            return None

        example_note = (
            f"

## Learned Example — {date.today().isoformat()}
"
            f"**Task:** {task.raw[:120]}...
"
            f"**Pattern used:** {task.task_type}
"
            f"_Auto-appended by agent after successful completion._
"
        )
        with open(skill_path, "a", encoding="utf-8") as f:
            f.write(example_note)

        return f"Updated skill: {skill_name}"

    def _generate_report(self, today: str) -> str:
        """Generate the morning report markdown."""
        lines = [
            f"# Morning Report — {today}",
            "",
            "## Summary",
        ]

        completed = self.stats.tasks_completed
        n = len(completed)
        blocked = self.stats.blocked

        if self.fallback_mode:
            lines.append(
                "**Mode: FALLBACK** — No brief was received; "
                "the standing task queue (P0 tasks) was executed automatically."
            )
            lines.append("")

        if n == 0 and not blocked:
            lines.append("No tasks were completed this session.")
        else:
            task_names = ", ".join(t["slug"].replace("-", " ") for t in completed)
            lines.append(
                f"Completed {n} task(s) overnight: {task_names}. "
                f"Model: {CLAUDE_MODEL}. "
                f"{len(blocked)} item(s) blocked or needing input."
            )

        lines += ["", "## Tasks Completed"]
        for i, t in enumerate(completed, 1):
            lines += [
                f"### {i}. {t['slug']}",
                f"- **Output:** {t['output_path']}",
                f"- **Status:** {t['status']}",
                f"- **Cost:** ~${t.get('cost_usd', 0):.4f}",
                f"- **Notes:** {t['notes'] or 'None'}",
                "",
            ]

        lines += ["## Decisions Made (Review Needed)"]
        if self.stats.decisions:
            for d in self.stats.decisions:
                lines.append(f"- {d}")
        else:
            lines.append("- No decisions requiring review.")

        lines += ["", "## Blocked / Needs Input"]
        if blocked:
            for b in blocked:
                lines.append(f"- {b}")
        else:
            lines.append("- None.")

        lines += ["", "## Skill Documents Created/Updated"]
        if self.stats.skills_created:
            for s in self.stats.skills_created:
                lines.append(f"- {s}")
        else:
            lines.append("- None this session.")

        lines += [
            "",
            "## Token Usage & Cost",
            f"- **Model:** {CLAUDE_MODEL}",
            f"- **Input tokens:** {self.stats.input_tokens:,}",
            f"- **Output tokens:** {self.stats.output_tokens:,}",
            f"- **Total cost:** ~${self.stats.total_cost():.4f}",
        ]

        return "
".join(lines)

    def _log_token_usage(self, today: str) -> None:
        """Append this session's token usage to the persistent log."""
        log_path = TOKEN_USAGE_LOG
        log_path.parent.mkdir(parents=True, exist_ok=True)

        write_header = not log_path.exists() or log_path.stat().st_size == 0

        with open(log_path, "a", encoding="utf-8") as f:
            if write_header:
                f.write(TOKEN_LOG_HEADER)
            f.write(
                f"{today} | {CLAUDE_MODEL:<17} | {self.stats.input_tokens:>9,} | "
                f"{self.stats.output_tokens:>10,} | ${self.stats.total_cost():>8.4f}
"
            )

        log.info("Token usage logged to %s", log_path)
