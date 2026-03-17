---
name: competitive-research
description: Research competitor protocols and synthesize findings into structured, Nexus-specific recommendations covering the competitive landscape, key findings, and prioritized next steps.
version: 1.0.0
---

# Skill: Competitive Research & Synthesis

## When to Use

When the nightly brief requests research on competitors, protocols,
market patterns, or best practices in the blockchain/DeFi space.

**Trigger keywords:** research, analyze, compare, competitive, look at,
best practices, survey, how do X handle, what are, investigate, landscape

## Quick Reference

| Action | Command |
|--------|---------|
| Synthesize research via Claude | `python3 /workspace/tools/claude_escalate.py synthesize "<topic>" "<raw_research>"` |
| Save raw notes | Write to `/workspace/research/YYYY-MM-DD-<topic>-raw.md` |
| Save synthesis output | Write to `/workspace/output/YYYY-MM-DD/<topic>-analysis.md` |

**Primary reference protocols by topic:**

| Topic | Protocols |
|-------|-----------|
| Perpetuals/Spot Trading | dYdX v4, Hyperliquid, Vertex, GMX v2 |
| L1 Developer Docs | Sui, Aptos, Monad, Berachain, Base |
| Bridge/Interop | Wormhole (Nexus partner), LayerZero, Axelar |
| Explorer/Infrastructure | Blockscout (Nexus partner), Etherscan, Sourcify |

## Procedure

1. Parse the research topic from the brief and identify 3-5 target protocols — no fewer, no more
2. For each target, use web search to gather:
   - Product/protocol overview (what it does, how it works)
   - Relevant features, architecture decisions, or docs relevant to the brief topic
   - User experience and design patterns
   - Published metrics, TVL, or case studies where available
3. Save raw notes to `/workspace/research/YYYY-MM-DD-<topic>-raw.md` — include a source URL for every factual claim before saving
4. Escalate to Claude API for synthesis — Hermes 3 **must not** synthesize directly, as strategic framing for Nexus requires Claude-level reasoning:
   ```
   python3 /workspace/tools/claude_escalate.py synthesize \
     "<topic>" \
     "$(cat /workspace/research/YYYY-MM-DD-<topic>-raw.md)"
   ```
5. Save synthesized output to `/workspace/output/YYYY-MM-DD/<topic>-analysis.md`
6. Log in morning report with a 2-3 bullet summary of key findings

## Pitfalls

1. **Claims written without source URLs in raw notes** — synthesis fails the quality check and the output can't be verified. Write the source URL immediately after each claim while researching; do not batch URL-gathering at the end.
2. **Raw notes file not saved before synthesis** — if Claude is called with inline text and the script fails, all gathered research is lost. Always write raw notes to disk before escalating.
3. **More than 5 protocols** — breadth beyond 5 dilutes the synthesis and inflates token usage. If the brief implies a broad survey, pick the 5 most directly comparable to Nexus Exchange.
4. **Research too shallow (feature names only, no mechanics)** — Claude's synthesis will be generic if the raw notes only list what protocols have rather than how they work. Capture the mechanism, not just the existence of a feature.
5. **Synthesis not framed for Nexus** — always verify the output explicitly connects findings to Nexus Exchange or Nexus chain context. If the output reads as generic blockchain advice, the Claude escalation prompt may need the brief's context passed in.

## Verification

- [ ] 3-5 target protocols covered (not fewer)
- [ ] Every factual claim in raw notes has a source URL
- [ ] Raw notes saved to `/workspace/research/YYYY-MM-DD-<topic>-raw.md` before synthesis
- [ ] Comparison table included in synthesis output where applicable
- [ ] Recommendations are prioritized P0/P1/P2
- [ ] Clear separation between facts and agent analysis
- [ ] Synthesized output explicitly states relevance to Nexus/Nexus Exchange
- [ ] Both raw notes and synthesis output paths logged in morning report
