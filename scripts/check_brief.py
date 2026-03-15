"""
Cron job: 11:30 PM weeknights
Checks whether a brief was received today; sends a Telegram reminder if not.
"""

import asyncio
import logging
import os
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


async def main():
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


if __name__ == "__main__":
    asyncio.run(main())
