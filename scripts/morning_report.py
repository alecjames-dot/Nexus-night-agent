"""
Cron job: 7:00 AM weekday mornings
Reads the latest morning report from /workspace/output/ and sends it via Telegram.
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
log = logging.getLogger("morning-report")

sys.path.insert(0, str(Path(__file__).parent))
from brief_handler import BriefHandler

# Telegram message limit
TELEGRAM_MAX_CHARS = 4096


def split_message(text: str, limit: int = TELEGRAM_MAX_CHARS) -> list[str]:
    """Split long messages into chunks at paragraph boundaries."""
    if len(text) <= limit:
        return [text]

    chunks = []
    current = ""
    for para in text.split("\n\n"):
        candidate = current + ("\n\n" if current else "") + para
        if len(candidate) <= limit:
            current = candidate
        else:
            if current:
                chunks.append(current)
            current = para
    if current:
        chunks.append(current)
    return chunks or [text[:limit]]


async def main():
    report = BriefHandler.get_latest_report(WORKSPACE_ROOT)

    if not report:
        log.warning("No morning report found to send.")
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        await bot.send_message(
            chat_id=TELEGRAM_ALLOWED_USER_ID,
            text=(
                "⚠️ Good morning! No morning report was generated overnight. "
                "Check /var/log/nexus-agent.log for details."
            ),
        )
        return

    log.info("Sending morning report (%d chars)...", len(report))
    bot = Bot(token=TELEGRAM_BOT_TOKEN)

    chunks = split_message(report)
    for i, chunk in enumerate(chunks):
        prefix = f"📋 Morning Report (part {i+1}/{len(chunks)})\n\n" if len(chunks) > 1 else "📋 "
        await bot.send_message(
            chat_id=TELEGRAM_ALLOWED_USER_ID,
            text=prefix + chunk,
            parse_mode="Markdown",
        )
        if len(chunks) > 1:
            await asyncio.sleep(0.5)

    log.info("Morning report delivered (%d message(s)).", len(chunks))


if __name__ == "__main__":
    asyncio.run(main())
