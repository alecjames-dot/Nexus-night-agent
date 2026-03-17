---
name: nexus-dev-docs
description: Draft a new developer documentation page for the Nexus blockchain or Nexus Exchange APIs, with correct chain IDs, RPC endpoints, and code examples.
version: 2.0.0
---

# Skill: Nexus Developer Documentation

## When to Use

When the nightly brief requests new or updated developer documentation
for the Nexus blockchain or Nexus Exchange APIs.

**Trigger keywords:** doc, documentation, guide, tutorial, getting started,
how to, developer, devdoc, integration, deploy, contract, rpc, api, sdk

## Quick Reference

| Item | Value |
|------|-------|
| Mainnet chain ID | 3946 — `https://rpc.nexus.xyz` |
| Testnet chain ID | 3945 — `https://rpc-testnet.nexus.xyz` |
| Output path | `/workspace/output/YYYY-MM-DD/<doc-slug>.md` |

## Procedure

1. Identify the documentation topic and target audience (default: external developers building on Nexus)
2. Check `/workspace/nexus-docs/` for any existing docs on this topic to avoid duplication and match style
3. Research comparable documentation from Sui, Aptos, Base, Arbitrum, or Monad — note structure, code example style, and depth of coverage
4. Claude drafts the documentation using the product context and research notes passed in the system prompt.
   The draft must include: Prerequisites, step-by-step guide, code examples with correct chain IDs and
   RPC endpoints, and a Common Errors section (minimum 3 items).
5. After receiving the draft, verify all code examples against the templates below before saving
6. Save to `/workspace/output/YYYY-MM-DD/<doc-slug>.md`
7. Log in morning report

## Code Templates

**ethers.js**
```javascript
const { ethers } = require("ethers");

// Nexus Testnet (chain ID 3945)
const provider = new ethers.JsonRpcProvider("https://rpc-testnet.nexus.xyz");

// Nexus Mainnet (chain ID 3946)
// const provider = new ethers.JsonRpcProvider("https://rpc.nexus.xyz");
```

**viem**
```typescript
import { createPublicClient, http } from 'viem';

const nexusTestnet = {
  id: 3945,
  name: 'Nexus Testnet',
  network: 'nexus-testnet',
  rpcUrls: { default: { http: ['https://rpc-testnet.nexus.xyz'] } },
} as const;

const client = createPublicClient({
  chain: nexusTestnet,
  transport: http(),
});
```

## Pitfalls

1. **Wrong chain ID in code examples** — Claude may default to common IDs (1, 1337, 8453). Verify every numeric chain ID is 3946 (mainnet) or 3945 (testnet).
2. **Placeholder RPC URLs** — every RPC URL must be `https://rpc.nexus.xyz` or `https://rpc-testnet.nexus.xyz`.
3. **Missing Prerequisites section** — without it, external developers can't follow the guide. Append if omitted.
4. **Fewer than 3 common errors** — the Common Errors section is what developers search when things break. Request additional errors if the draft has fewer than 3.
5. **Nexus docs directory not checked first** — always read `/workspace/nexus-docs/` before drafting to avoid duplicate or contradictory content.

## Verification

- [ ] Title and one-line description present
- [ ] Prerequisites section complete
- [ ] Step-by-step guide with code examples
- [ ] Code examples use correct chain IDs: mainnet=3946, testnet=3945
- [ ] RPC endpoints: mainnet=`https://rpc.nexus.xyz`, testnet=`https://rpc-testnet.nexus.xyz`
- [ ] Common Errors section has at least 3 items
- [ ] Links to related docs included
- [ ] Code examples are syntactically valid Solidity/ethers.js/viem
- [ ] Output path logged in morning report
