---
name: exchange-spec-drafting
description: Draft a new feature specification section for the Nexus Exchange PRD, including competitive research, F-XXX assignment, and feature registry update.
version: 2.0.0
---

# Skill: Exchange Spec Drafting

## When to Use

When the nightly brief requests a new spec section or feature specification
for the Nexus Exchange (perpetuals/spot trading platform).

**Trigger keywords:** spec, prd, feature, requirement, order type, depth chart,
order book, draft spec, write spec, product requirement

## Procedure

1. Read `/workspace/tracking/feature-registry.md` → note the next available Feature ID (F-XXX) and REQ number (REQ-XXX)
2. Read `/workspace/context/spec-conventions.md` for the required structure and spec section header template
3. Read any related existing spec sections from `/workspace/exchange-specs/` for context and alignment
4. If the feature has competitive precedent, research 2-3 of the primary references below:
   - Order/trading features: dYdX v4, Vertex, GMX v2, Hyperliquid
5. Claude drafts the spec section using the conventions and research context passed in the system prompt.
   The output must include: Feature ID, User Story, Requirements (using 'must'), Edge Cases (min 3),
   Acceptance Criteria (Given/When/Then), Open Questions.
6. Save output to `/workspace/output/YYYY-MM-DD/<feature-slug>.md`
7. Update `/workspace/tracking/feature-registry.md`: add a row for the new Feature ID, name, milestone, status "Draft", and output file path
8. Log output path, decisions made, and open questions in the morning report

## Pitfalls

1. **Feature registry not read before assigning IDs** — results in duplicate Feature IDs. Always read the registry first; never guess the next ID.
2. **Conventions file missing** — verify `/workspace/context/spec-conventions.md` exists and is loaded before drafting.
3. **Competitor research skipped for complex features** — spec will miss established UX patterns. If the feature exists at dYdX or Hyperliquid, spend time researching before drafting.
4. **Open Questions section omitted** — blocking product decisions reach review invisibly. The spec must always include Open Questions; add manually if Claude omits it.
5. **Output saved to wrong directory** — all output goes to `/workspace/output/YYYY-MM-DD/`, never to `/workspace/exchange-specs/` directly.

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
