"""
Task Executor — routes tasks to the appropriate model and writes output.

Routing logic:
  spec-draft, doc-write  → Claude API (via claude_escalate.py)
  research               → OpenRouter/Hermes 3 + optional Claude synthesis
  organize, track-update → OpenRouter/Hermes 3
  general                → OpenRouter/Hermes 3
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
import time
from datetime import date, datetime
from pathlib import Path
from typing import Optional

import httpx

log = logging.getLogger(__name__)

WORKSPACE_ROOT = Path(os.environ.get("WORKSPACE_ROOT", "/workspace"))
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
OPENROUTER_MODEL = "nousresearch/hermes-3-llama-3.1-70b"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
TOOLS_DIR = WORKSPACE_ROOT / "tools"

# Cost tracking (approximate, per 1M tokens)
HERMES_COST_PER_1M = {"input": 0.90, "output": 0.90}   # approx OpenRouter pricing
CLAUDE_COST_PER_1M = {"input": 3.00, "output": 15.00}  # claude-sonnet-4 pricing


class ExecutionStats:
    def __init__(self):
        self.hermes_input_tokens = 0
        self.hermes_output_tokens = 0
        self.claude_input_tokens = 0
        self.claude_output_tokens = 0
        self.tasks_completed: list[dict] = []
        self.decisions: list[str] = []
        self.blocked: list[str] = []
        self.skills_created: list[str] = []

    def hermes_cost(self) -> float:
        return (
            self.hermes_input_tokens / 1_000_000 * HERMES_COST_PER_1M["input"]
            + self.hermes_output_tokens / 1_000_000 * HERMES_COST_PER_1M["output"]
        )

    def claude_cost(self) -> float:
        return (
            self.claude_input_tokens / 1_000_000 * CLAUDE_COST_PER_1M["input"]
            + self.claude_output_tokens / 1_000_000 * CLAUDE_COST_PER_1M["output"]
        )

    def total_cost(self) -> float:
        return self.hermes_cost() + self.claude_cost()


class TaskExecutor:
    def __init__(self, workspace_root: Path):
        self.workspace = workspace_root
        self.stats = ExecutionStats()
        self._current_task: Optional[str] = None
        self._status: str = "idle"
        self.fallback_mode: bool = False  # Set True when running standing task queue

    def get_status(self) -> str:
        if self._status == "idle":
            return "Agent is idle — no active execution."
        return f"Status: {self._status}\nCurrent task: {self._current_task or 'none'}"

    async def execute_all(self, tasks, telegram_update=None) -> None:
        """Execute all tasks from the brief, write output, generate report."""
        today = date.today().isoformat()
        output_dir = self.workspace / "output" / today
        output_dir.mkdir(parents=True, exist_ok=True)
        self.stats = ExecutionStats()
        self._status = "running"

        context = self._load_context()

        for task in tasks:
            self._current_task = task.slug
            log.info("Executing task %d [%s]: %s", task.number, task.task_type, task.raw[:60])

            try:
                result = await self._execute_task(task, context, output_dir)
                self.stats.tasks_completed.append(result)
                if telegram_update:
                    await telegram_update.message.reply_text(
                        f"✅ Task {task.number} complete: {result['output_path']}"
                    )
            except Exception as exc:
                log.exception("Task %d failed: %s", task.number, exc)
                self.stats.blocked.append(
                    f"Task {task.number} ({task.slug}): {exc}"
                )
                if telegram_update:
                    await telegram_update.message.reply_text(
                        f"⚠️ Task {task.number} blocked: {exc}"
                    )

        # Generate and save morning report
        report = self._generate_report(today)
        report_path = output_dir / "report.md"
        report_path.write_text(report, encoding="utf-8")
        log.info("Morning report written to %s", report_path)

        self._status = "idle"
        self._current_task = None

    async def _execute_task(self, task, context: str, output_dir: Path) -> dict:
        """Route and execute a single task."""
        task_dir = output_dir / task.slug
        task_dir.mkdir(parents=True, exist_ok=True)

        if task.task_type in ("spec-draft", "doc-write"):
            result_text = await self._run_claude_escalation(task, context)
            model_used = "claude"
        elif task.task_type == "research":
            # First gather with Hermes, then synthesize with Claude
            raw = await self._run_hermes(
                task,
                context,
                instruction="Gather and organize relevant information. Include source URLs.",
            )
            result_text = await self._run_claude_synthesis(task.raw, raw)
            model_used = "hermes+claude"
        else:
            result_text = await self._run_hermes(task, context)
            model_used = "hermes"

        # Write output file
        output_file = task_dir / f"{task.slug}.md"
        output_file.write_text(result_text, encoding="utf-8")
        log.info("Output written to %s", output_file)

        # Check if this task generated a reusable skill pattern
        skill_note = self._maybe_create_skill(task, result_text)
        if skill_note:
            self.stats.skills_created.append(skill_note)

        # Extract a brief notes snippet from the first non-empty line of output
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
            "model_used": model_used,
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
                parts.append(f"=== {md_file.name} ===\n{md_file.read_text(encoding='utf-8')}")
            except Exception as e:
                log.warning("Could not read context file %s: %s", md_file, e)
        return "\n\n".join(parts)

    async def _run_hermes(
        self, task, context: str, instruction: str = ""
    ) -> str:
        """Call Hermes 3 via OpenRouter."""
        if not OPENROUTER_API_KEY:
            raise EnvironmentError("OPENROUTER_API_KEY not set")

        system = (
            "You are the Nexus Night Shift PM agent. "
            "Execute the following task using the provided context.\n\n"
            f"CONTEXT:\n{context}"
        )
        user = f"TASK:\n{task.raw}\n\n{instruction}".strip()

        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                OPENROUTER_URL,
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "HTTP-Referer": "https://nexus.xyz",
                    "Content-Type": "application/json",
                },
                json={
                    "model": OPENROUTER_MODEL,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "max_tokens": 4096,
                    "temperature": 0.3,
                },
            )
            resp.raise_for_status()
            data = resp.json()

        usage = data.get("usage", {})
        self.stats.hermes_input_tokens += usage.get("prompt_tokens", 0)
        self.stats.hermes_output_tokens += usage.get("completion_tokens", 0)

        return data["choices"][0]["message"]["content"]

    async def _run_claude_escalation(self, task, context: str) -> str:
        """Run claude_escalate.py for spec drafting or doc writing."""
        tool_path = TOOLS_DIR / "claude_escalate.py"
        python = sys.executable

        if task.task_type == "spec-draft":
            cmd = [python, str(tool_path), "draft-spec", task.raw, context]
        else:  # doc-write
            cmd = [python, str(tool_path), "draft-doc", task.raw, context]

        env = {**os.environ}
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            raise RuntimeError(
                f"claude_escalate.py failed (code {proc.returncode}): "
                f"{stderr.decode()[:500]}"
            )

        # Parse token usage from stderr
        for line in stderr.decode().splitlines():
            if "[claude_escalate] tokens:" in line:
                try:
                    parts = line.split()
                    for p in parts:
                        if p.startswith("in="):
                            self.stats.claude_input_tokens += int(p[3:])
                        elif p.startswith("out="):
                            self.stats.claude_output_tokens += int(p[4:])
                except (ValueError, IndexError):
                    pass

        return stdout.decode("utf-8")

    async def _run_claude_synthesis(self, topic: str, raw_research: str) -> str:
        """Run claude_escalate.py synthesize for research tasks."""
        tool_path = TOOLS_DIR / "claude_escalate.py"
        python = sys.executable

        cmd = [python, str(tool_path), "synthesize", topic, raw_research]
        env = {**os.environ}
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            raise RuntimeError(
                f"claude_escalate.py synthesize failed: {stderr.decode()[:500]}"
            )

        for line in stderr.decode().splitlines():
            if "[claude_escalate] tokens:" in line:
                try:
                    parts = line.split()
                    for p in parts:
                        if p.startswith("in="):
                            self.stats.claude_input_tokens += int(p[3:])
                        elif p.startswith("out="):
                            self.stats.claude_output_tokens += int(p[4:])
                except (ValueError, IndexError):
                    pass

        return stdout.decode("utf-8")

    def _maybe_create_skill(self, task, result_text: str) -> Optional[str]:
        """
        If the task produced high-quality output, create or update a Skill Document.
        Returns a description string if a skill was created, else None.
        """
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
            return None  # Seeded skills should already exist

        # Append a learned example to the skill doc
        example_note = (
            f"\n\n## Learned Example — {date.today().isoformat()}\n"
            f"**Task:** {task.raw[:120]}...\n"
            f"**Pattern used:** {task.task_type}\n"
            f"_Auto-appended by agent after successful completion._\n"
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
            model_summary = {t["model_used"] for t in completed}
            lines.append(
                f"Completed {n} task(s) overnight: {task_names}. "
                f"Models used: {', '.join(sorted(model_summary))}. "
                f"{len(blocked)} item(s) blocked or needing input."
            )

        lines += ["", "## Tasks Completed"]
        for i, t in enumerate(completed, 1):
            lines += [
                f"### {i}. {t['slug']}",
                f"- **Output:** {t['output_path']}",
                f"- **Status:** {t['status']}",
                f"- **Model:** {t['model_used']}",
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
            f"- **Hermes 3 (OpenRouter):** "
            f"~{self.stats.hermes_input_tokens + self.stats.hermes_output_tokens:,} tokens, "
            f"~${self.stats.hermes_cost():.2f}",
            f"- **Claude API (Sonnet):** "
            f"~{self.stats.claude_input_tokens + self.stats.claude_output_tokens:,} tokens, "
            f"~${self.stats.claude_cost():.2f}",
            f"- **Total:** ~${self.stats.total_cost():.2f}",
        ]

        return "\n".join(lines)
