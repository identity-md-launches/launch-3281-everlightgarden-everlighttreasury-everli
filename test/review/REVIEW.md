# Independent testing contribution

This contribution reviews the accepted application without changing production source, configuration,
dependencies, or earlier tests. The pinned testing reference, wallet-gas helper, constructor/opcode
check, and ownership check were read before adding tests. The network-owned owner-check dependency
and deployment environment are not present here; this report does not claim to have run that protected
harness. The existing local deployment rehearsal remains part of the passing suite.

The review covered candle/payment ordering, reward settlement and dust, owner authority, bridge
authentication and state transitions, exact balance/supply deltas, reentrancy, UTF-8, and indexing.
No additional reproducible implementation defect was found in the tested cases. This is bounded
test evidence, not a proof of all possible executions or an assertion of live bridge operation.

## Added evidence

| File | Properties exercised |
| --- | --- |
| `BridgeCustodyInvariant.t.sol` | Two independent handlers exercise random action sequences. The Ethereum model tracks purchases, claims, withdrawals, donations, queue reservations, failed sends, retries and acknowledgements. Each job's immutable amount, GUID, attempt count and terminal state is checked. The Base model tracks credited tokens, pending/failed burns, actual supply reduction, donations and receipt delivery/replay. |
| `BridgeBoundaries.t.sol` | Source and Base authentication fields, rejected-message rollback, stale/replayed receipts, frozen-route changes, authorization, two-step Base ownership, queue rounding, fee limits, native refund rejection and authorized refund reentry. Wallet-gas comparisons cover dispatch failures and recovery, compose failure, and failed/no-op/successful burn retries. |
| `BridgeDeltaFailures.t.sol` | An actual source debit paired with each malformed receipt must roll back atomically. Duplicate/zero GUIDs, wrong fees and amounts, missing/partial/excess debits are covered. Base sink transfers, compensating mints, incomplete/excess burns and supply reduction from the wrong account cannot count as confirmed burns. Token callbacks cannot retry or acknowledge an unfinished burn. Malformed endpoint receipts preserve retryability and refund the native payment. |
| `GardenMetadataAndUnicode.t.sol` | Exact public wish bytes and indexing events, cumulative claim and fee-destination events, interleaved pagination, empty/terminal/invalid pages, rollback of the last invalid style in a 50-candle purchase, an independent UTF-8 byte-range grammar, and mixed-width scalar strings around the 280-codepoint limit. Old records and reward rights survive a 100-year time advance. |
| `ActivationAndRuntime.t.sol` | Reconfiguration invalidates old readiness, malformed readiness cannot activate purchases, and every checked official route fact must match. Captured Ethereum OFT and Base token/adapter bytecode also run through the supplied wallet-gas helper; Base compose succeeds at its advertised 500,000 gas. |

The source custody invariant independently checks:

- Held IMD equals payments plus donations minus successful sends, claims and bucket withdrawals.
- Queued, reserved, in-transit and confirmed amounts partition the entire 30% burn allocation.
- Failed amounts remain reserved; in-transit/completed jobs cannot be resent.
- Reward claims remain funded while burns, pauses and withdrawals interleave; fractional entitlements
  plus division dust conserve the allocated rewards.
- Every fee bucket and its cumulative withdrawals reconcile to the fixed rates and first-candle fallback.

The Base custody invariant checks that every credited amount is pending or burned exactly once,
failed attempts restore custody, donations do not create deliveries, total supply decreases only by
successful burns, and a receipt cannot acknowledge an unburned delivery or be sent twice. Deterministic
sequences additionally assert nonzero successes, failures and retries so the models cannot pass solely
by exercising empty queues. Each new invariant runs 256 sequences of depth 96 with unexpected reverts
forbidden by the unchanged project configuration. The earlier per-candle reward reference model is
retained and runs alongside them.

## Validation

Foundry 1.8.3 / Solidity 0.8.26, using the assignment seed:

`0x9e56a8a08f479c4debd98dee24655411b47d3a5f10f757d2dd0fcb595fd4d87f`

- Baseline before this contribution: **49 passed, 0 failed, 0 skipped**.
- Final `forge build --offline`: **passed**, with existing production-source lint warnings.
- Final `forge test --offline --summary`: **80 passed, 0 failed, 0 skipped**, across 14 suites.
- Nine added fuzz properties ran 512 cases each. Existing fuzz properties remain enabled.
- Three invariant suites completed **57,344 handler calls, 0 unexpected reverts**: 24,576 calls in each
  new custody model and 8,192 in the existing reward model.

All generated artifacts were directed into disposable `test/scratch/`. Reproduction:

```sh
FOUNDRY_OUT=test/scratch/out \
FOUNDRY_CACHE_PATH=test/scratch/cache \
forge build --offline

FOUNDRY_OUT=test/scratch/out \
FOUNDRY_CACHE_PATH=test/scratch/cache \
FOUNDRY_FUZZ_FAILURE_PERSIST_DIR=test/scratch/fuzz \
FOUNDRY_INVARIANT_FAILURE_PERSIST_DIR=test/scratch/invariant \
FOUNDRY_FUZZ_SEED=0x9e56a8a08f479c4debd98dee24655411b47d3a5f10f757d2dd0fcb595fd4d87f \
forge test --offline --summary
```

## Evidence limits

The fault fixtures and invariant credits are explicitly simulated. Captured deployed bytecode is
tested with local storage and a mocked LayerZero endpoint; it is neither a fork nor a live bridge
test. The existing helper in `test/helpers/WalletGas.sol` is the supplied snapshot/binary-search
helper and is used without changing its assertion semantics.

No network-dependent test, real-fund purchase, broadcast, deployment, source publication or website
work was performed. These tests do not resolve the later Base deployment and live peer, endpoint,
security, liquidity, token-policy and fee verification prerequisites described in
[`docs/deployment.md`](../../docs/deployment.md). Ethereum purchases must remain disabled until the
required authenticated setup is complete. No pending send is reported as a confirmed Base burn.
