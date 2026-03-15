# Skill: Exchange Spec Drafting

## When to use
When the nightly brief requests a new spec section or feature specification
for the Nexus Exchange (perpetuals/spot trading platform).

## Trigger keywords
spec, prd, feature, requirement, order type, depth chart, order book,
draft spec, write spec, product requirement

## Procedure
1. Check `/workspace/tracking/feature-registry.md` for next available Feature ID
2. Load `/workspace/context/spec-conventions.md` for structure and conventions
3. Load any related existing spec sections from `/workspace/exchange-specs/`
4. If competitive research is needed, use web search to analyze 2-3 competitors
   (dYdX, Vertex, GMX, Hyperliquid are primary references for order/trading features)
5. Escalate to Claude API using `draft_spec_section()` from `claude_escalate.py`
   - Pass: feature_name, product_context, research_notes
6. Save output to `/workspace/output/YYYY-MM-DD/<feature-slug>.md`
7. Update feature registry with new Feature ID and status "Draft"
8. Log output path, decisions, and open questions in morning report

## Quality checklist
- [ ] Feature ID (F-XXX) assigned and registered
- [ ] Milestone (M1.1, M1.2, etc.) specified
- [ ] User story in correct format
- [ ] All requirements use "must" not "should"
- [ ] Minimum 3 edge cases documented in explicit Edge Cases section
- [ ] Acceptance criteria are testable (Given/When/Then format)
- [ ] Open questions section present and flagged for human review
- [ ] Chain IDs referenced correctly (3946 mainnet, 3945 testnet) where relevant

## Escalation notes
Always escalate to Claude for initial spec drafts — Hermes 3 can do reformatting
and table updates, but spec drafting requires precise technical reasoning.

## Reference examples
- `/workspace/exchange-specs/m1.1-full-order-suite.md` (when available)
