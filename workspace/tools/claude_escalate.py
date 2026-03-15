"""
Claude API escalation utility for Nexus Night Shift Agent.
Called when a task requires stronger reasoning than the base model.

Usage:
    python claude_escalate.py draft-spec "Depth Chart" "context..." "research..."
    python claude_escalate.py draft-doc "Deploy First Contract" "context..."
    python claude_escalate.py synthesize "L1 Onboarding Docs" "raw research..."
"""

import os
import sys
import json
import asyncio
import argparse

import httpx

CLAUDE_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
CLAUDE_MODEL = "claude-sonnet-4-20250514"
CLAUDE_MAX_TOKENS = 8192
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"


async def call_claude(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.3,
) -> str:
    """Send a request to Claude API and return the response text."""
    if not CLAUDE_API_KEY:
        raise EnvironmentError(
            "ANTHROPIC_API_KEY environment variable is not set."
        )

    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(
            ANTHROPIC_API_URL,
            headers={
                "x-api-key": CLAUDE_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": CLAUDE_MODEL,
                "max_tokens": CLAUDE_MAX_TOKENS,
                "temperature": temperature,
                "system": system_prompt,
                "messages": [{"role": "user", "content": user_prompt}],
            },
        )
        response.raise_for_status()
        data = response.json()

        # Log token usage to stderr for cost tracking
        usage = data.get("usage", {})
        print(
            f"[claude_escalate] tokens: in={usage.get('input_tokens', '?')} "
            f"out={usage.get('output_tokens', '?')}",
            file=sys.stderr,
        )

        return "\n".join(
            block["text"]
            for block in data.get("content", [])
            if block.get("type") == "text"
        )


async def draft_spec_section(
    feature_name: str,
    context: str,
    research: str = "",
    conventions_path: str = "/workspace/context/spec-conventions.md",
) -> str:
    """Draft an exchange spec section using Claude."""
    conventions = ""
    if os.path.exists(conventions_path):
        with open(conventions_path, "r") as f:
            conventions = f.read()

    system = f"""You are a senior product manager drafting a feature specification
for the Nexus Exchange, a perpetuals and spot trading platform on the Nexus L1 blockchain.

Follow these conventions exactly:
{conventions}

Be precise, thorough, and include edge cases. Flag open questions explicitly."""

    user = f"""Draft a complete spec section for: {feature_name}

Product context:
{context}

{"Research/competitive analysis:" + chr(10) + research if research else ""}

Output a complete spec section following the conventions provided."""

    return await call_claude(system, user)


async def draft_developer_doc(
    topic: str,
    context: str,
    target_audience: str = "External developers building on Nexus",
) -> str:
    """Draft a developer documentation page using Claude."""
    system = f"""You are a technical writer creating developer documentation
for the Nexus blockchain (EVM-compatible L1, chain ID 3946 mainnet / 3945 testnet).

Target audience: {target_audience}

Write clear, practical documentation with code examples.
Use Solidity/ethers.js/viem for code samples.
Always specify Nexus chain IDs and RPC endpoints explicitly.
Testnet RPC: https://rpc-testnet.nexus.xyz (chain ID 3945)
Mainnet RPC: https://rpc.nexus.xyz (chain ID 3946)"""

    user = f"""Write a developer documentation page for: {topic}

Context:
{context}

Include: prerequisites, step-by-step guide, code examples, common errors, and related links."""

    return await call_claude(system, user)


async def synthesize_research(topic: str, raw_research: str) -> str:
    """Synthesize raw research notes into structured recommendations."""
    system = """You are a product strategist synthesizing research
into actionable recommendations for a blockchain product team.

Structure your output as:
1. Executive Summary (3-4 sentences)
2. Key Findings (grouped by theme)
3. Competitive Landscape (comparison table if applicable)
4. Recommendations (prioritized P0/P1/P2, with rationale)
5. Open Questions

Separate facts from your analysis clearly. Cite sources where provided."""

    user = f"""Synthesize the following research on: {topic}

Raw research:
{raw_research}"""

    return await call_claude(system, user)


def main():
    parser = argparse.ArgumentParser(
        description="Claude API escalation utility for Nexus Night Shift Agent"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # draft-spec
    sp = subparsers.add_parser("draft-spec", help="Draft an exchange spec section")
    sp.add_argument("feature_name", help="Name of the feature")
    sp.add_argument("context", help="Product context string")
    sp.add_argument("research", nargs="?", default="", help="Optional research notes")

    # draft-doc
    dp = subparsers.add_parser("draft-doc", help="Draft a developer documentation page")
    dp.add_argument("topic", help="Documentation topic")
    dp.add_argument("context", help="Context string")
    dp.add_argument("--audience", default="External developers building on Nexus")

    # synthesize
    rp = subparsers.add_parser("synthesize", help="Synthesize raw research")
    rp.add_argument("topic", help="Research topic")
    rp.add_argument("raw_research", help="Raw research notes")

    args = parser.parse_args()

    if args.command == "draft-spec":
        result = asyncio.run(
            draft_spec_section(args.feature_name, args.context, args.research)
        )
    elif args.command == "draft-doc":
        result = asyncio.run(
            draft_developer_doc(args.topic, args.context, args.audience)
        )
    elif args.command == "synthesize":
        result = asyncio.run(synthesize_research(args.topic, args.raw_research))
    else:
        parser.print_help()
        sys.exit(1)

    print(result)


if __name__ == "__main__":
    main()
