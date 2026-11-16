# Local validation and adversarial review

These results are implementation/model evidence, **not independent network approval**. The final independent reviewer must assess the accepted source, manifest, privileged arguments and activation evidence before deployment/activation. No source publication, contract deployment, signing or real-fund purchase was performed here.

## Reproduction

Pinned project configuration is unchanged: Solidity 0.8.26, Cancun, optimizer enabled/200 runs, bytecode metadata hash none; existing OpenZeppelin/forge-std only. Local Foundry is 1.8.3. Tests use no environment settings, filesystem permissions, fork, external service or downloaded runtime dependency. The assignment seed is:

```
0x9e56a8a08f479c4debd98dee24655411b47d3a5f10f757d2dd0fcb595fd4d87f
```

Run:

```sh
forge build
FOUNDRY_FUZZ_SEED=0x9e56a8a08f479c4debd98dee24655411b47d3a5f10f757d2dd0fcb595fd4d87f forge test
python3 scripts/export-abis.py --check
```

Final command results are recorded after the final source build. Parameterized tests use 512 cases. The specification model uses 128 sequences, depth 64 (8,192 actions), with fail-on-revert enabled. A 10,001-candle test disables test-harness gas metering while performing many **bounded** purchases; it is not evidence that one transaction can create 10,001 candles. Wallet-gas helpers separately compare results/logs at the lowest successful call gas against calls with spare gas.

## Recorded final results

- `forge build --sizes`: passed, with no external library link references.
- `forge test --summary` with the exact assignment seed: **60 passed, 0 failed, 0 skipped**, across nine suites. Eight fuzz properties ran 512 cases each; the invariant model completed **128 runs / 8,192 calls / 0 reverts**.
- `python3 scripts/export-abis.py --check`: passed for the Ethereum ABI, separate Base ABI and reproducible Base package.
- `python3 test/base_package_test.py`: three offline helper tests passed, including constructor encoding comparison with `cast abi-encode`, the deterministic-deployer calldata and predicted receiver address against `cast keccak`, Keccak known answers, required inputs, fixed chain/owner/value, and invalid parameter rejection. No test transaction was written to the deployment package or broadcast.

| Application | Runtime bytes | Initcode bytes before arguments |
| --- | ---: | ---: |
| WishGarden (Ethereum) | 18,291 | 27,794 (includes the Base receiver creation code, hashed once in the constructor to pin the destination; it is not part of the runtime) |
| EverlightBurnReceiver (separate Base package) | 8,456 | 8,848 |

Both are below EIP-170/EIP-3860 limits. Foundry lint warnings on exact balance comparisons, bounded loop validation, bridge-unit truncation, guarded calls/events and restoration after failed external subcalls were reviewed against behavior; their relevant failure modes are exercised by the tests. Exact comparisons and queue rounding are deliberate requirements, not relaxed to suppress warnings.

## Review of custody and privileges

| Attack / requirement | Evidence and conclusion |
| --- | --- |
| Owner drains earlier-candle rewards | Two-candle regression produces 0.3 IMD claimable and exactly 1.1 IMD owner buckets; all buckets exhausted still leave reward and burn custody. Owner has no reward/dust/burn sweep. |
| New weight earns old rewards | Batch vs sequential fuzz and independent per-candle model agree. Allocation precedes weight addition, dust is not recycled, fractions survive repeated claims. |
| Account split/rounding overpayment | Model checks sum of lifetime scaled entitlements plus division dust exactly equals funded reward allocation times precision. Claims floor only accumulated account entitlement. |
| Reentry / partial transfer | Guarded purchase/claim/withdraw/bridge/composer paths; caller-only SafeERC20 pull and both-side exact transfer checks. Faults and callbacks revert/settle exactly once. |
| Wish/NFT manipulation | All free/NFT/bind/recordPayment selectors reject. Record/text immutability is structural; strict UTF-8 tests include scalar bounds, overlongs, surrogates, truncation and full batch rollback. |
| Forged burn or arbitrary destination | No arbitrary target, call payload, token rescue or owner-completion method. Exact fixed OFT receipt and source debit; endpoint/peer/config/job/GUID/amount authenticated acknowledgements. |
| Duplicate, delayed or reordered burn delivery | GUID and job replay guards, immutable job amounts, out-of-order three-job tests and return receipt replay. In-transit jobs cannot be resent on Ethereum. |
| Bridge/burn failure hides lost custody | Source self-call isolates external send and receipt checks atomically; failures preserve reservation/refund native fee. Base self-call isolates exact burn checks; failed burns retain funded pending amounts. |
| Gas starvation appears to succeed without trying | Explicit EIP-150 headroom plus completion margin; source dispatch and Base compose tested at wallet-minimum gas, Base compose through an endpoint-style forwarder (queue clear, 63/64 forwarding) at 80% of the advertised 650,000 gas with cold accounts, underfunded compose reverts. |
| Fake sink burn | Actual deployed Base token runtime reduces both balance and totalSupply locally. Actual deployed Ethereum OFT debit remains unconfirmed until Base receipt. Mock results are identified separately. |
| Factory traps ownership / deployment fails on empty chain | Explicit constructor owner, no dependency calls; empty-code factory rehearsal, ABI static arguments, bounded runtime/initcode, no linked external library and protected-style reachable-opcode scan. |

All application source was reviewed: GardenEconomy, WishGarden, WishGardenTreasury, Utf8Wish, IMDBridge ABI/options, EverlightBridgeQueue and EverlightBurnReceiver. The original imported audit was assessed and its corrected/qualified findings are listed in ADAPTATION.md. The final local review identified and fixed an unnecessary recovery dependency: already authenticated, funded Base deliveries now remain burn-retryable after a later bridge peer change, since only the fixed token is needed. A regression exercises the peer change, retry and acknowledgement. It also verified checks-effects-interactions around isolated send/burn subcalls, with failed-subcall custody restored before returning. No additional reproduced unauthorized-withdrawal, old-reward leakage, double-burn or replay defect remained in the tested model.

## Evidence boundaries and unresolved operational risk

The Base bytecode tests have fresh local storage and a mocked endpoint; the Ethereum bytecode test also uses a mocked endpoint. Separate live evidence establishes deployed token/adapter runtime hashes and selected reads, not a live cross-chain execution. No fork, live purchase, live burn, broadcast or independent signed audit was performed. Slither/Mythril were not available/run; vendored OpenZeppelin, forge-std, IMD internals and LayerZero are trusted external dependencies, not audited by this contribution.

The remote receiver is pinned, not chosen: the garden accepts only the CREATE2 address of this repository's receiver bytecode for this garden and initial owner, so the owner cannot route burn funds to a wallet or author confirmations. The owner's evidence hash remains an unverified document pointer. The receipt channel relies on the official endpoint's current defaults/security and availability; the token bridge relies on IMD administrators, peers, adapter collateral and token policy. These external administrators can change behavior or deny service even though application configuration is immutable. A fixed gas or native fee ceiling can become inadequate in future. There is deliberately no arbitrary withdrawal/upgrade fallback that could release burn funds.

Base compose occurs after adapter credit, potentially in another transaction. It validates the official message and sufficient pending custody, not a same-transaction before/after transfer delta. Its attribution assumes the source-verified adapter's lossless transfer and the token's verified ordinary-transfer behavior; the owner must verify receiver policy/limits before activation. The burn itself enforces exact balance/supply deltas. Concurrent prefunded/out-of-order messages and donations are covered without treating donations as confirmed burn.

The owner can stop **new purchases**, choose fee destinations, rotate ownership through acceptance, and dispatch fixed-route burns; claims remain callable. IMD token transfer failures can still make a particular claim transaction revert without consuming entitlement. Public text can contain hostile content and is immutable; later renderers must escape it. The 50-candle and 1120-byte limits hold separately, not together: one Ethereum transaction carries at most 16,777,216 gas, and the measured joint bound is documented in the integration guide ("Batch gas").

The protected constructor/opcode requirements are reproduced locally. The pinned Owners test imports a network-owned `floor/OwnerChecks.sol` that is absent here; it is not claimed as executed. Local tests explicitly verify named ownership and no factory privilege. Final protected/service verification remains the network's responsibility.

## Revision after independent review

An independent reviewer reopened the first accepted round with five findings. Each was reproduced on the starting tree before any change. `test/RevisionFindings.t.sol` (11 **mocked** tests, one of them fuzzed) holds the regressions; `test/Bridge.t.sol::test_configurationChangeFailsClosedForDispatchOnlyAndClaimsStayAvailable` replaces the test that encoded the old fail-closed purchase behaviour.

| Finding | Result on the starting tree | After the change |
| --- | --- | --- |
| `e1e37d73` owner-chosen Base destination | Reviewer proof failed: 3 IMD sent to an owner wallet and reported as burned | `configureBridge` rejects every address but `pinnedBaseReceiver()`; proof passes; fuzzed over arbitrary addresses |
| `3a1155f9` purchases/dispatch tied to third-party OFT options | Both proof tests failed with `InvalidBridgeConfiguration` | Purchases need only the IMD token; dispatch ignores enforced options, still fails closed on peer/endpoint/code changes and resumes when restored. The reviewer's proof file itself can no longer run: its `setUp` configures the arbitrary receiver `0xB0B0`, which the first finding requires the garden to reject. The same two scenarios run in-tree with the pinned receiver and pass |
| `14107f84` credited compose stranded by adapter re-peer | Proof failed: no record, no retry | `lzCompose` needs activation, unchanged token code and the authenticated endpoint/adapter message; proof passes; `announceReady` stays gated by the full route check |
| `29960a92` 50 candles x 1120 bytes cannot be mined | Measured 71.7M gas | Joint bound documented and pinned by a test against the 16,777,216 per-transaction limit |
| `772340d3` compose gas margin | Minimum 466,467 gas for a first delivery through an endpoint-style forwarder, cold accounts, captured Base runtimes, against 500,000 advertised | `COMPOSE_GAS` is 650,000; the test requires success at 80% of it and a revert, not a skipped burn, at 300,000 |

Live, read-only (two public-endpoint calls, recorded under `revisionReads` in the bridge evidence): the canonical deterministic deployer has code on Base, and Ethereum IMD's `quoteSend` accepts the final options with a native fee of about 0.00089 ETH. Nothing was sent, purchased, bridged or burned; there is still no fork or live end-to-end burn result, and Slither/Mythril were not run.

Residual trust after this revision: the IMD team can still stop **burn dispatch** (never purchases, claims or bucket withdrawals) by re-peering its OFT, and burn IMD then waits in the garden with no withdrawal path. The owner's evidence hash is an unverified document pointer. Anyone may deploy the pinned receiver; only the named owner can activate it.
