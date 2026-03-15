"""
Nexus Night Shift Agent — Main Entry Point
Runs the Telegram gateway, listens for nightly briefs, and orchestrates the
task execution loop.

Start via systemd: nexus-agent.service
"""

import asyncio
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from brief_handler import BriefHandler
from task_executor import TaskExecutor

load_dotenv("/etc/nexus-agent.env")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_ALLOWED_USER_ID = int(os.environ["TELEGRAM_ALLOWED_USER_ID"])
WORKSPACE_ROOT = Path(os.environ.get("WORKSPACE_ROOT", "/workspace"))
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("nexus-agent")

brief_handler = BriefHandler(WORKSPACE_ROOT)
task_executor = TaskExecutor(WORKSPACE_ROOT)


# ---------------------------------------------------------------------------
# Telegram handlers
# ---------------------------------------------------------------------------

def _authorized(update: Update) -> bool:
    """Return True only if the message is from the allowed user."""
    return update.effective_user.id == TELEGRAM_ALLOWED_USER_ID


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _authorized(update):
        log.warning(
            "Unauthorized message from user %s — ignoring.",
            update.effective_user.id,
        )
        return

    text = update.message.text.strip()
    log.info("Received message from authorized user: %r", text[:80])

    # Save as tonight's brief and confirm
    brief_path = brief_handler.save_brief(text)
    await update.message.reply_text(
        f"Brief received and saved to {brief_path.relative_to(WORKSPACE_ROOT)}.\n"
        "I'll begin working on your tasks now and send a morning report by 7 AM. 🌙"
    )

    # Start executing tasks in the background
    asyncio.create_task(_run_tasks(update, text))


async def _run_tasks(update: Update, brief_text: str) -> None:
    """Parse the brief and execute all tasks, reporting status."""
    try:
        tasks = brief_handler.parse_tasks(brief_text)
        log.info("Parsed %d tasks from brief.", len(tasks))
        await update.message.reply_text(
            f"Parsed {len(tasks)} task(s). Starting execution..."
        )
        await task_executor.execute_all(tasks, update)
    except Exception as exc:
        log.exception("Task execution failed: %s", exc)
        await update.message.reply_text(
            f"⚠️ Error during task execution: {exc}\n"
            "Check /var/log/nexus-agent.log for details."
        )


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _authorized(update):
        return
    await update.message.reply_text(
        "Nexus Night Shift Agent online.\n\n"
        "Send me tonight's priorities and I'll get to work.\n"
        "Commands:\n"
        "  /status — current execution status\n"
        "  /report — resend the latest morning report\n"
        "  /brief  — show tonight's brief\n"
    )


async def handle_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _authorized(update):
        return
    status = task_executor.get_status()
    await update.message.reply_text(status)


async def handle_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _authorized(update):
        return
    report = brief_handler.get_latest_report(WORKSPACE_ROOT)
    if report:
        await update.message.reply_text(report[:4096])
    else:
        await update.message.reply_text("No report found yet.")


async def handle_brief(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _authorized(update):
        return
    brief = brief_handler.get_todays_brief()
    if brief:
        await update.message.reply_text(brief[:4096])
    else:
        await update.message.reply_text("No brief found for today.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    log.info("Starting Nexus Night Shift Agent...")
    log.info("Workspace: %s", WORKSPACE_ROOT)
    log.info("Allowed Telegram user ID: %d", TELEGRAM_ALLOWED_USER_ID)

    app = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .build()
    )

    app.add_handler(CommandHandler("start", handle_start))
    app.add_handler(CommandHandler("status", handle_status))
    app.add_handler(CommandHandler("report", handle_report))
    app.add_handler(CommandHandler("brief", handle_brief))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    log.info("Telegram gateway active. Waiting for messages...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
