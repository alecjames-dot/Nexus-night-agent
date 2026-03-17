---
name: competitive-research
description: Research competitor protocols and synthesize findings into structured, Nexus-specific recommendations covering the competitive landscape, key findings, and prioritized next steps.
version: 2.0.0
---

# Skill: Competitive Research & Synthesis

## When to Use

When the nightly brief requests research on competitors, protocols,
market patterns, or best practices in the blockchain/DeFi space.

**Trigger keywords:** research, analyze, compare, competitive, look at,
best practices, survey, how do X handle, what are, investigate, landscape

**Primary reference protocols by topic:**

| Topic | Protocols |
|-------|-----------|
| Perpetuals/Spot Trading | dYdX v4, Hyperliquid, Vertex, GMX v2 |
| L1 Developer Docs | Sui, Aptos, Monad, Berachain, Base |
| Bridge/Interop | Wormhole (Nexus partner), LayerZero, Axelar |
| Explorer/Infrastructure | Blockscout (Nexus partner), Etherscan, Sourcify |

## Procedure

1. Parse the research topic from the brief and identify 3-5 target protocols — no fewer, no more
2. For each target, gather:
   - Product/protocol overview (what it does, how it works)
   - Features, architecture decisions, or docs relevant to the brief topic
   - User experience and design patterns
   - Published metrics, TVL, or case studies where available
3. Save raw notes to `/workspace/research/YYYY-MM-DD-<topic>-raw.md` — include a source URL for every factual claim before saving
4. Claude synthesizes the raw research into structured recommendations. The task_executor passes
   the full raw notes and context to Claude with instructions to produce a comparison table,
   key findings, and P0/P1/P2 next steps framed for Nexus.
5. Save synthesized output to `/workspace/output/YYYY-MM-DD/<topic>-analysis.md`
6. Log in morning report with a 2-3 bullet summary of key findings

## Pitfalls

1. **Claims without source URLs** — synthesis can't be verified. Write the source URL immediately after each claim while researching.
2. **Raw notes not saved before task completes** — always write raw notes to disk at `/workspace/research/` first.
3. **More than 5 protocols** — breadth beyond 5 dilutes the synthesis and inflates token usage. Pick the 5 most directly comparable to Nexus Exchange.
4. **Research too shallow (feature names only, no mechanics)** — capture how protocols work, not just what they have.
5. **Synthesis not framed for Nexus** — verify the output explicitly connects findings to Nexus Exchange or Nexus chain context.

## Verification

- [ ] 3-5 target protocols covered (not fewer)
- [ ] Every factual claim in raw notes has a source URL
- [ ] Raw notes saved to `/workspace/research/YYYY-MM-DD-<topic>-raw.md`
- [ ] Comparison table included in synthesis output where applicable
- [ ] Recommendations are prioritized P0/P1/P2
- [ ] Clear separation between facts and agent analysis
- [ ] Synthesized output explicitly states relevance to Nexus/Nexus Exchange
- [ ] Both raw notes and synthesis output paths logged in morning report
