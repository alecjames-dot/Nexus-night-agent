# Spec Writing Conventions

## Exchange PRD Structure
Every spec section must include:

- **Feature ID**: F-XXX (check /workspace/tracking/feature-registry.md for next available)
- **Milestone**: M1.1, M1.2, etc.
- **User Story**: "As a [user type], I want [action] so that [outcome]"
- **Requirements**: Numbered list (REQ-XXX)
- **Edge Cases**: Explicit section, minimum 3 per feature
- **Acceptance Criteria**: Testable statements
- **Open Questions**: Items needing human decision, flagged for morning review

### Spec section header template

Use this exact structure for every new spec section:

```markdown
## F-XXX: [Feature Name]

**Milestone:** M1.X
**Status:** Draft
**Feature ID:** F-XXX
**Last Updated:** YYYY-MM-DD

### User Story
As a [user type], I want [action] so that [outcome].

### Requirements
- **REQ-XXX:** [Requirement text — use "must", never "should"]
- **REQ-XXX:** ...

### Edge Cases
1. **[Category]:** [Description of edge case and expected behavior]
2. **[Category]:** ...
3. **[Category]:** ...

### Acceptance Criteria
- Given [context], When [action], Then [expected outcome]
- ...

### Open Questions
- [ ] **OQ-001**: [Question text] — Owner: [name], Priority: P[0/1/2]
```

## Developer Docs Structure
- Title and one-line description
- Prerequisites
- Step-by-step guide with code examples
- Common errors and troubleshooting
- Links to related docs
- Target audience: external developers building on Nexus

## Language Conventions
- Use precise language. Avoid "should" — use "must" for requirements.
- Reference chain IDs explicitly (3946 mainnet, 3945 testnet)
- Include gas cost context where relevant (reference /workspace/context/gas-model.md if present)
- All monetary values in USD unless specified

## Requirement Numbering
- Requirements: REQ-001, REQ-002, ... (sequential, globally unique)
- Check /workspace/tracking/feature-registry.md for last used REQ number
- Feature IDs: F-001, F-002, ... (sequential, globally unique)

## Edge Case Categories
Every feature spec should address edge cases in at least these categories:
1. Input validation / malformed data
2. Network failure / timeout scenarios
3. Concurrent/race conditions
4. Boundary values (min/max quantities, zero values)
5. Authorization / access control edge cases

## Acceptance Criteria Format
Use the Given/When/Then format where possible:
- Given [context], When [action], Then [expected outcome]
- Criteria must be unambiguously testable by QA

## Open Questions Format
```
### Open Questions
- [ ] **OQ-001**: [Question text] — Owner: [name], Priority: P[0/1/2]
```
