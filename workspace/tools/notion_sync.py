"""
Notion API sync utility — Phase 2 (Week 3+)
Pulls target Notion pages into the local workspace as markdown.

This is a stub. Implement once Notion OAuth is configured.
"""

import os
import sys

NOTION_API_KEY = os.environ.get("NOTION_API_KEY")
WORKSPACE_ROOT = os.environ.get("WORKSPACE_ROOT", "/workspace")

# Map Notion page IDs to local workspace paths
SYNC_TARGETS = {
    # "notion-page-id": "local/relative/path.md",
    # Example:
    # "abc123def456": "exchange-specs/m1.1-full-order-suite.md",
}


def sync():
    if not NOTION_API_KEY:
        print(
            "[notion_sync] NOTION_API_KEY not set — skipping sync.",
            file=sys.stderr,
        )
        return

    if not SYNC_TARGETS:
        print("[notion_sync] No sync targets configured — nothing to do.", file=sys.stderr)
        return

    # TODO (Phase 2):
    # 1. Import notion-client
    # 2. For each target, fetch page blocks and convert to markdown
    # 3. Write to WORKSPACE_ROOT / local_path
    # 4. Log conflicts (remote newer vs local modifications)
    raise NotImplementedError(
        "Notion sync not yet implemented. Configure SYNC_TARGETS and implement "
        "the Notion → markdown conversion in Phase 2."
    )


if __name__ == "__main__":
    sync()
