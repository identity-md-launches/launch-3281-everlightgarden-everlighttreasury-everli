# Specification-derived adversarial evidence

This directory replaces the imported NFT/sink-specific independent suites, whose required behavior conflicts with the new launch brief. It contains a separately implemented **reference model**, not an independently signed external audit. Tests and this review were produced within the implementation contribution; network review of the final source/manifest is still required.

`RewardModelInvariant.t.sol` distributes each candle's reward to **every earlier individual candle**, tracking scaled entitlements, accounts, claims, withdrawals and donations from its input actions. It never copies production reward state into expected values. Production instead uses a global accumulator and per-account checkpoints. Equality after every action checks ordering, no self-allocation/new-entrant retroactivity, persistent fractions, liability backing, the first-candle fallback, three fee buckets and zero reward overpayment. The configured run is 128 sequences of depth 64, 8,192 handler actions, with unexpected reverts forbidden.

`BridgeAdversarial.t.sol` adds hostile delivery ordering and replay, immutable amount/GUID accounting, repeated source failures/refunds, permissionless fixed-destination Base retries, unallocated donations, no token rescue/approval, and supplied/lowest-successful gas tests. Source and Base retry counters represent actual attempts; low outer gas must revert rather than record skipped work as success. There is no timeout-based resend of an in-transit job.

Other delivered tests cover token return/fee/no-op/surcharge failures, same/cross-function reentry (including an authorized owner), Unicode, unsupported/free/NFT entrypoints, unauthorized claims and bucket withdrawals, pause, ownership rotation, actual verified token/adapter bytecode, empty-chain constructors and forbidden opcodes.

All test beneficiaries and fault doubles are local fixtures, not deployment arguments. These tests do not establish live LayerZero security, remote execution, liquidity, fees, token administrative status, deployment or signature. No fork or real-fund purchase is used. See `docs/validation.md` for recorded results and `docs/deployment.md` for setup blockers.

Revision note: `../RevisionFindings.t.sol` answers the later independent review (pinned Base destination, third-party OFT option/peer changes, credited compose after re-peering, executor compose gas through an endpoint-style forwarder, joint batch/wish gas bound). Those tests are mocked as well; see `docs/validation.md`, "Revision after independent review".
