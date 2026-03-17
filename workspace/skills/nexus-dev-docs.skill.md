---
name: nexus-dev-docs
description: Draft a new developer documentation page for the Nexus blockchain or Nexus Exchange APIs, with correct chain IDs, RPC endpoints, and code examples.
version: 1.0.0
---

# Skill: Nexus Developer Documentation

## When to Use

When the nightly brief requests new or updated developer documentation
for the Nexus blockchain or Nexus Exchange APIs.

**Trigger keywords:** doc, documentation, guide, tutorial, getting started,
how to, developer, devdoc, integration, deploy, contract, rpc, api, sdk

## Quick Reference

| Action | Command |
|--------|---------|
| Draft doc via Claude | `python3 /workspace/tools/claude_escalate.py draft-doc "<topic>" "$(cat /workspace/context/nexus-product-context.md)"` |
| Draft doc with custom audience | `python3 /workspace/tools/claude_escalate.py draft-doc "<topic>" "<context>" --audience "<audience>"` |
| Check existing docs | Read `/workspace/nexus-docs/` directory |
| Mainnet chain ID | 3946 — `https://rpc.nexus.xyz` |
| Testnet chain ID | 3945 — `https://rpc-testnet.nexus.xyz` |
| Save output | Write to `/workspace/output/YYYY-MM-DD/<doc-slug>.md` |

## Procedure

1. Identify the documentation topic and target audience (default: external developers building on Nexus)
2. Check `/workspace/nexus-docs/` for any existing docs on this topic to avoid duplication and match style
3. Web research: find comparable documentation from Sui, Aptos, Base, Arbitrum, or Monad — note structure, code example style, and depth of coverage
4. Escalate to Claude API — Hermes 3 **must not** write developer docs directly due to chain ID / RPC accuracy requirements:
   ```
   python3 /workspace/tools/claude_escalate.py draft-doc \
     "<topic>" \
     "$(cat /workspace/context/nexus-product-context.md)" \
     --audience "External developers building on Nexus"
   ```
5. After receiving the draft, verify all code examples against the templates below:
   - **ethers.js**: `new ethers.JsonRpcProvider("https://rpc-testnet.nexus.xyz")` with chain ID 3945
   - **viem**: chain object with `id: 3945` and `rpcUrls: { default: { http: ['https://rpc-testnet.nexus.xyz'] } }`
6. Verify RPC endpoint references match current values in `/workspace/context/nexus-product-context.md`
7. Save to `/workspace/output/YYYY-MM-DD/<doc-slug>.md`
8. Log in morning report

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

1. **Wrong chain ID in code examples** — Claude may default to common IDs (1 for mainnet, 1337 for local, 8453 for Base). Always verify every numeric chain ID in the output is 3946 (mainnet) or 3945 (testnet).
2. **Placeholder RPC URLs** — Claude occasionally uses `https://rpc.example.com` or similar placeholders. Every RPC URL must be `https://rpc.nexus.xyz` or `https://rpc-testnet.nexus.xyz`.
3. **Missing Prerequisites section** — without it, external developers can't follow the guide. If Claude's output omits prerequisites, add them before saving.
4. **Fewer than 3 common errors** — the Common Errors section is what developers search for when things break. If Claude only lists 1-2, request additional errors before saving.
5. **Nexus docs directory not checked first** — if a doc on this topic already exists, Claude may produce a duplicate or contradictory version. Always read `/workspace/nexus-docs/` before escalating.

## Verification

- [ ] Title and one-line description present
- [ ] Prerequisites section complete
- [ ] Step-by-step guide with code examples
- [ ] Code examples use correct chain IDs: mainnet=3946, testnet=3945
- [ ] RPC endpoints: mainnet=`https://rpc.nexus.xyz`, testnet=`https://rpc-testnet.nexus.xyz`
- [ ] Common errors section has at least 3 items
- [ ] Links to related docs included
- [ ] Code examples are syntactically valid Solidity/ethers.js/viem
- [ ] Output path logged in morning report
