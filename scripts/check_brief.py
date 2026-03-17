"""
Cron jobs for nightly brief checking.

Run modes (pass as first argument):
  reminder  — 11:30 PM: send Telegram reminder if no brief received yet
  fallback  — 00:05 AM: run standing tasks if still no brief by midnight

Crontab:
  30 23 * * 1-5  python3 /opt/nexus-night-agent/scripts/check_brief.py reminder
  5  0  * * 2-6  python3 /opt/nexus-night-agent/scripts/check_brief.py fallback
"""

import asyncio
import logging
import os
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv
from telegram import Bot

load_dotenv("/etc/nexus-agent.env")

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_ALLOWED_USER_ID = int(os.environ["TELEGRAM_ALLOWED_USER_ID"])
WORKSPACE_ROOT = Path(os.environ.get("WORKSPACE_ROOT", "/workspace"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("check-brief")

sys.path.insert(0, str(Path(__file__).parent))
from brief_handler import BriefHandler


async def send_reminder():
    """11:30 PM: send Telegram reminder if no brief received."""
    handler = BriefHandler(WORKSPACE_ROOT)

    if handler.brief_received_today():
        log.info("Brief already received for today — no reminder needed.")
        return

    log.info("No brief received yet. Sending Telegram reminder.")
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    await bot.send_message(
        chat_id=TELEGRAM_ALLOWED_USER_ID,
        text=(
            "👋 No brief received yet for tonight.\n\n"
            "Send me tonight's priorities, or I'll work from the standing task queue. "
            "Replying with 'use standing tasks' will start the queue automatically."
        ),
    )
    log.info("Reminder sent.")


async def run_fallback():
    """00:05 AM: if still no brief, run standing tasks automatically."""
    handler = BriefHandler(WORKSPACE_ROOT)

    if handler.brief_received_today():
        log.info("Brief received before midnight — no fallback needed.")
        return

    log.info("No brief received by midnight. Starting standing task queue.")
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    await bot.send_message(
        chat_id=TELEGRAM_ALLOWED_USER_ID,
        text=(
            "🌙 No brief received by midnight. "
            "Starting the standing task queue automatically (P0 tasks)."
        ),
    )

    scripts_dir = Path(__file__).parent
    proc = subprocess.Popen(
        [sys.executable, str(scripts_dir / "standing_tasks.py")],
        stdout=open("/var/log/nexus-agent.log", "a"),
        stderr=subprocess.STDOUT,
    )
    log.info("Standing tasks started (PID %d).", proc.pid)


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "reminder"
    if mode == "fallback":
        asyncio.run(run_fallback())
    else:
        asyncio.run(send_reminder())
