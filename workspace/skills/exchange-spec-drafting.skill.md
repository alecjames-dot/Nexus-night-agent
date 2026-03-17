---
name: exchange-spec-drafting
description: Draft a new feature specification section for the Nexus Exchange PRD, including competitive research, F-XXX assignment, and feature registry update.
version: 1.0.0
---

# Skill: Exchange Spec Drafting

## When to Use

When the nightly brief requests a new spec section or feature specification
for the Nexus Exchange (perpetuals/spot trading platform).

**Trigger keywords:** spec, prd, feature, requirement, order type, depth chart,
order book, draft spec, write spec, product requirement

## Quick Reference

| Action | Command |
|--------|---------|
| Draft spec via Claude | `python3 /workspace/tools/claude_escalate.py draft-spec "<feature>" "$(cat /workspace/context/nexus-product-context.md)" "<research>"` |
| Check next Feature ID | Read `/workspace/tracking/feature-registry.md` → "Last assigned" section |
| Load conventions | Read `/workspace/context/spec-conventions.md` |
| Load related specs | Read `/workspace/exchange-specs/` directory |
| Save output | Write to `/workspace/output/YYYY-MM-DD/<feature-slug>.md` |

## Procedure

1. Read `/workspace/tracking/feature-registry.md` → note the next available Feature ID (F-XXX) and REQ number (REQ-XXX)
2. Read `/workspace/context/spec-conventions.md` for the required structure and the spec section header template
3. Read any related existing spec sections from `/workspace/exchange-specs/` for context and conventions alignment
4. If the feature has competitive precedent, use web search to analyze 2-3 of the primary references below:
   - Order/trading features: dYdX v4, Vertex, GMX v2, Hyperliquid
5. Escalate to Claude API — handle with Hermes 3 is **not appropriate** for initial spec drafting:
   ```
   python3 /workspace/tools/claude_escalate.py draft-spec \
     "<feature_name>" \
     "$(cat /workspace/context/nexus-product-context.md)" \
     "<research_notes>"
   ```
6. Save output to `/workspace/output/YYYY-MM-DD/<feature-slug>.md`
7. Update `/workspace/tracking/feature-registry.md`: add a row for the new Feature ID, name, milestone, status "Draft", and output file path
8. Log output path, decisions made, and open questions in `/workspace/output/YYYY-MM-DD/report.md`
9. If this task revealed a reusable spec pattern, update this skill document

## Pitfalls

1. **Feature registry not read before assigning IDs** — results in duplicate Feature IDs across nights. Always read the registry first; never guess the next ID.
2. **Conventions file path wrong or missing** — `claude_escalate.py` warns to stderr if not found; the spec will be drafted without the F-XXX template. Verify `/workspace/context/spec-conventions.md` exists before escalating.
3. **Competitor research skipped for complex features** — spec will miss established UX patterns (e.g. depth chart levels, TP/SL trigger types). If the feature exists at dYdX or Hyperliquid, spend 5 minutes researching before escalating.
4. **Open Questions section omitted** — blocking product decisions reach review invisibly. Claude must always produce an Open Questions section; if the output lacks one, append it manually before saving.
5. **Output saved to wrong directory** — writing to `/workspace/exchange-specs/` directly violates the no-overwrite rule. All output must go to `/workspace/output/YYYY-MM-DD/`.

## Verification

- [ ] Feature ID (F-XXX) assigned and registered in `/workspace/tracking/feature-registry.md`
- [ ] Milestone (M1.1, M1.2, etc.) specified
- [ ] User story in correct format: "As a [user type], I want [action] so that [outcome]"
- [ ] All requirements use "must" not "should"
- [ ] Minimum 3 edge cases documented in explicit Edge Cases section
- [ ] Acceptance criteria use Given/When/Then format and are unambiguously testable
- [ ] Open Questions section present with at least one item flagged for human review
- [ ] Chain IDs referenced correctly (3946 mainnet, 3945 testnet) where relevant
- [ ] Output path logged in morning report
