# Skill: Nexus Developer Documentation

## When to use
When the nightly brief requests new or updated developer documentation
for the Nexus blockchain or Nexus Exchange APIs.

## Trigger keywords
doc, documentation, guide, tutorial, getting started, how to, developer,
devdoc, integration, deploy, contract, rpc, api, sdk

## Procedure
1. Identify topic and target audience (default: external devs building on Nexus)
2. Research: check existing Nexus docs in `/workspace/nexus-docs/`
3. Web research: find comparable docs from Sui, Aptos, Base, Arbitrum, Monad
   — note structure, code example style, depth of coverage
4. Escalate to Claude API using `draft_developer_doc()` from `claude_escalate.py`
   - Pass: topic, context (existing docs + research), target_audience
5. Ensure all code examples compile and use correct chain IDs (3946/3945)
6. Verify RPC endpoint references are current (check `/workspace/context/nexus-product-context.md`)
7. Save to `/workspace/output/YYYY-MM-DD/<doc-slug>.md`
8. Log in morning report

## Quality checklist
- [ ] Title and one-line description present
- [ ] Prerequisites section complete
- [ ] Step-by-step guide with code examples
- [ ] Code examples use correct chain IDs: mainnet=3946, testnet=3945
- [ ] RPC endpoints: mainnet=https://rpc.nexus.xyz, testnet=https://rpc-testnet.nexus.xyz
- [ ] Common errors section has at least 3 items
- [ ] Links to related docs included
- [ ] Code examples are syntactically valid Solidity/ethers.js/viem

## Code example template (ethers.js)
```javascript
const { ethers } = require("ethers");

// Nexus Testnet (chain ID 3945)
const provider = new ethers.JsonRpcProvider("https://rpc-testnet.nexus.xyz");

// Nexus Mainnet (chain ID 3946)
// const provider = new ethers.JsonRpcProvider("https://rpc.nexus.xyz");
```

## Code example template (viem)
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
