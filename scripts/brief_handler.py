"""
Brief Handler — saves, parses, and retrieves nightly briefs.
"""

import re
import logging
from datetime import date, datetime
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)


class Task:
    """A single parsed task from the nightly brief."""

    TASK_TYPES = {
        "spec-draft": [
            "spec", "prd", "feature", "requirement", "draft spec",
            "write spec", "order book", "depth chart", "order type",
        ],
        "doc-write": [
            "doc", "documentation", "guide", "tutorial", "getting started",
            "how to", "developer", "devdoc",
        ],
        "research": [
            "research", "analyze", "compare", "competitive", "look at",
            "what are best practices", "how do", "survey",
        ],
        "track-update": [
            "update", "tracker", "tracking", "mark", "checklist", "status",
            "add row", "launch tracker", "feature registry",
        ],
        "organize": [
            "organize", "restructure", "reformat", "consolidate", "clean",
            "deduplicate",
        ],
    }

    def __init__(self, number: int, raw: str):
        self.number = number
        self.raw = raw.strip()
        self.task_type = self._classify()
        self.slug = self._make_slug()

    def _classify(self) -> str:
        text = self.raw.lower()
        for task_type, keywords in self.TASK_TYPES.items():
            for kw in keywords:
                if kw in text:
                    return task_type
        return "general"

    def _make_slug(self) -> str:
        # First ~50 chars of the task, lowercased, spaces→dashes, stripped
        first_line = self.raw.split("\n")[0][:60]
        slug = re.sub(r"[^a-z0-9\s-]", "", first_line.lower())
        slug = re.sub(r"\s+", "-", slug.strip())
        slug = re.sub(r"-{2,}", "-", slug)
        return slug[:40].rstrip("-") or f"task-{self.number}"

    def __repr__(self) -> str:
        return f"Task({self.number}, type={self.task_type}, slug={self.slug!r})"


class BriefHandler:
    def __init__(self, workspace_root: Path):
        self.workspace = workspace_root
        self.briefs_dir = workspace_root / "briefs"
        self.briefs_dir.mkdir(parents=True, exist_ok=True)

    def save_brief(self, text: str) -> Path:
        """Save raw brief text to /workspace/briefs/YYYY-MM-DD.md."""
        today = date.today().isoformat()
        path = self.briefs_dir / f"{today}.md"

        content = f"# Nightly Brief — {today}\n\n"
        content += f"_Received: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_\n\n"
        content += text

        path.write_text(content, encoding="utf-8")
        log.info("Brief saved to %s", path)
        return path

    def parse_tasks(self, text: str) -> list[Task]:
        """
        Parse numbered tasks from brief text.
        Supports formats:
          1. Task description
          1) Task description
        """
        tasks = []
        # Match numbered items: "1. ..." or "1) ..."
        pattern = re.compile(r"(?:^|\n)\s*(\d+)[.)]\s+(.+?)(?=\n\s*\d+[.)]|\Z)", re.DOTALL)
        matches = pattern.findall(text)

        if matches:
            for num_str, body in matches:
                tasks.append(Task(int(num_str), body.strip()))
        else:
            # Fallback: treat entire message as one task
            tasks.append(Task(1, text.strip()))

        log.info("Parsed %d tasks: %s", len(tasks), tasks)
        return tasks

    def get_todays_brief(self) -> Optional[str]:
        today = date.today().isoformat()
        path = self.briefs_dir / f"{today}.md"
        if path.exists():
            return path.read_text(encoding="utf-8")
        return None

    def brief_received_today(self) -> bool:
        return (self.briefs_dir / f"{date.today().isoformat()}.md").exists()

    @staticmethod
    def get_latest_report(workspace_root: Path) -> Optional[str]:
        output_root = workspace_root / "output"
        if not output_root.exists():
            return None
        # Find the most recent dated output directory
        dated_dirs = sorted(
            [d for d in output_root.iterdir() if d.is_dir()],
            reverse=True,
        )
        for d in dated_dirs:
            report = d / "report.md"
            if report.exists():
                return report.read_text(encoding="utf-8")
        return None
