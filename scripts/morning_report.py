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


def get_task_output_files(workspace_root: Path) -> list[Path]:
    """Return all task output .md files from the latest output directory, sorted by name."""
    output_root = workspace_root / "output"
    if not output_root.exists():
        return []
    dated_dirs = sorted([d for d in output_root.iterdir() if d.is_dir()], reverse=True)
    for dated_dir in dated_dirs:
        if not (dated_dir / "report.md").exists():
            continue
        files = sorted(
            f for f in dated_dir.rglob("*.md") if f.name != "report.md"
        )
        return files
    return []


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

    bot = Bot(token=TELEGRAM_BOT_TOKEN)

    # Send report summary
    log.info("Sending morning report (%d chars)...", len(report))
    chunks = split_message(report)
    for i, chunk in enumerate(chunks):
        prefix = f"📋 Morning Report (part {i+1}/{len(chunks)})\n\n" if len(chunks) > 1 else "📋 "
        await bot.send_message(
            chat_id=TELEGRAM_ALLOWED_USER_ID,
            text=prefix + chunk,
        )
        if len(chunks) > 1:
            await asyncio.sleep(0.5)
    log.info("Morning report delivered (%d message(s)).", len(chunks))

    # Send task output files as documents
    output_files = get_task_output_files(WORKSPACE_ROOT)
    if output_files:
        await bot.send_message(
            chat_id=TELEGRAM_ALLOWED_USER_ID,
            text=f"📎 Attaching {len(output_files)} task output file(s):",
        )
        for output_file in output_files:
            with open(output_file, "rb") as f:
                await bot.send_document(
                    chat_id=TELEGRAM_ALLOWED_USER_ID,
                    document=f,
                    filename=output_file.name,
                )
            log.info("Sent file: %s", output_file.name)
            await asyncio.sleep(0.3)


if __name__ == "__main__":
    asyncio.run(main())
