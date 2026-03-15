"""
Standing Tasks Executor
Called when no nightly brief is received — works from the prioritized backlog.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv("/etc/nexus-agent.env")

WORKSPACE_ROOT = Path(os.environ.get("WORKSPACE_ROOT", "/workspace"))

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("standing-tasks")

sys.path.insert(0, str(Path(__file__).parent))
from brief_handler import Task
from task_executor import TaskExecutor

STANDING_TASKS_PATH = WORKSPACE_ROOT / "standing-tasks.md"


def load_standing_tasks() -> list[Task]:
    """Parse the P0 standing tasks from standing-tasks.md."""
    if not STANDING_TASKS_PATH.exists():
        log.warning("standing-tasks.md not found at %s", STANDING_TASKS_PATH)
        return []

    content = STANDING_TASKS_PATH.read_text(encoding="utf-8")

    # Extract P0 tasks (lines under "### P0")
    p0_tasks = []
    in_p0 = False
    task_num = 1

    for line in content.splitlines():
        if line.startswith("### P0"):
            in_p0 = True
            continue
        if line.startswith("### P1") or line.startswith("### P2"):
            in_p0 = False
        if in_p0 and line.strip().startswith("-"):
            task_text = line.strip().lstrip("- ").strip()
            if task_text:
                p0_tasks.append(Task(task_num, task_text))
                task_num += 1

    log.info("Loaded %d P0 standing tasks.", len(p0_tasks))
    return p0_tasks


async def main():
    tasks = load_standing_tasks()
    if not tasks:
        log.info("No standing tasks to execute.")
        return

    executor = TaskExecutor(WORKSPACE_ROOT)
    log.info("Running %d standing tasks...", len(tasks))
    await executor.execute_all(tasks)
    log.info("Standing tasks complete.")


if __name__ == "__main__":
    asyncio.run(main())
