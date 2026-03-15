# Skill: Competitive Research & Synthesis

## When to use
When the nightly brief requests research on competitors, protocols,
market patterns, or best practices in the blockchain/DeFi space.

## Trigger keywords
research, analyze, compare, competitive, look at, best practices,
survey, how do X handle, what are, investigate, landscape

## Procedure
1. Parse research topic and identify 3-5 target protocols/products to examine
2. Use web search to gather data on each target:
   - Product/protocol overview
   - Relevant features, architecture, or docs
   - User experience and design decisions
   - Any published metrics or case studies
3. Save raw notes to `/workspace/research/YYYY-MM-DD-<topic>-raw.md`
   - Include source URLs for every claim
4. Escalate to Claude API using `synthesize_research()` from `claude_escalate.py`
   - Pass: topic, raw_research_notes
5. Save synthesized output to `/workspace/output/YYYY-MM-DD/<topic>-analysis.md`
6. Log in morning report with key findings summary (2-3 bullet points)

## Quality checklist
- [ ] 3-5 target protocols covered (not fewer)
- [ ] Every factual claim has a source URL
- [ ] Comparison table included where applicable
- [ ] Recommendations are prioritized P0/P1/P2
- [ ] Clear separation between facts and agent analysis
- [ ] Raw notes saved separately from synthesized output
- [ ] Relevance to Nexus/Nexus Exchange stated explicitly

## Primary reference protocols by topic

### Perpetuals/Spot Trading
- dYdX v4 (orderbook perps, cosmos-based)
- Hyperliquid (high-performance L1 perps)
- Vertex (spot + perps, Arbitrum)
- GMX v2 (AMM perps, multi-chain)

### L1 Developer Docs
- Sui (Move-based, strong DX focus)
- Aptos (Move-based, comprehensive docs)
- Monad (EVM-compatible, high TPS)
- Berachain (EVM + PoL mechanism)
- Base (Coinbase L2, excellent onboarding)

### Bridge/Interop
- Wormhole (Nexus's bridge partner)
- LayerZero
- Axelar

### Explorer/Infrastructure
- Blockscout (Nexus's explorer)
- Etherscan
- Sourcify (Nexus's contract verification)
