"""
Night 1 Smoke Test
Sends the test brief via Telegram and verifies the agent responds.
Run manually after installation: python smoke_test.py
"""

import asyncio
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from telegram import Bot

load_dotenv("/etc/nexus-agent.env")

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_ALLOWED_USER_ID = int(os.environ["TELEGRAM_ALLOWED_USER_ID"])

TEST_BRIEF = """Tonight's priorities:

1. Summarize the contents of /workspace/ and confirm you can access all context files. Draft a 1-paragraph test spec for a 'Hello World' feature.
"""

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("smoke-test")


async def main():
    log.info("Sending Night 1 smoke test brief to Telegram bot...")
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    await bot.send_message(
        chat_id=TELEGRAM_ALLOWED_USER_ID,
        text=TEST_BRIEF,
    )
    log.info("Test brief sent. Check Telegram for the agent's response.")
    log.info("Verify:")
    log.info("  1. Brief saved to /workspace/briefs/YYYY-MM-DD.md")
    log.info("  2. Output written to /workspace/output/YYYY-MM-DD/")
    log.info("  3. Morning report generated and sent at 7 AM")


if __name__ == "__main__":
    asyncio.run(main())
