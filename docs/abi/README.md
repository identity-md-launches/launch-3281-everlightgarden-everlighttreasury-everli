# Integration contract

Ethereum application ABI: [WishGarden.json](WishGarden.json). Base-only ABI: [EverlightBurnReceiver.json](../base/EverlightBurnReceiver.json). Regenerate both with `forge build` and `python3 scripts/export-abis.py`. All IMD amounts are integers in 18-decimal base units. Use only service-confirmed deployment addresses; this contribution does not supply a deployed address.

## Required disclosures

**Rewards come ONLY from later candle purchases. They are not yield from an external business. No later purchases means no new rewards; there is no guaranteed return.** A wallet's additional purchases can return a partial self-share of its own payment, not profit. Ecosystem spending or investments confer no financial rights on candle holders. There is no lottery, NFT right, free candle, external yield, legacy reward or automatic distribution.

Wishes are **public forever**, in Ethereum storage, transaction inputs and logs. They are immutable, never encrypted or private; the owner cannot edit or delete them. Do not collect sensitive text under a privacy promise. A wish is optional by supplying an empty string. Unicode length counts scalar values/codepoints, including combining marks separately; it does not count grapheme clusters, UTF-16 code units, or visible glyphs. The contract preserves original valid UTF-8 bytes without normalization. A renderer must escape untrusted text, not interpret it as HTML, script or markup.

## Purchasing and indexing

1. Confirm chain 1, the accepted `WishGarden` address, `activated() == true` and `purchasesPaused() == false`. A pending bridge or deployment is not an active garden.
2. Build equally sized `styles` and `wishes` arrays with 1–50 entries. Each style is 0–6; each wish is strict UTF-8, <=280 codepoints **and** <=1120 bytes. Approve exactly `styles.length * 10^18` IMD to the garden. The caller pays and is each candle's immutable beneficiary; there is no arbitrary payer or gift destination.
3. Simulate `buyCandles(styles, wishes)` with zero ETH from the purchaser, estimate gas for the actual text, then submit. Maximum-count batches with long wishes can exceed the chain's gas ceiling; split them before submission. Separate transactions may partially succeed; each transaction is atomic. Do not treat a rejected signature, reverted call or pending transaction as a candle.
4. Index `CandleCreated(candleId, purchaser, beneficiary, position, style, createdAt, wish)` and `CandlesPurchased`. Obtain IDs from confirmed receipt logs. Deduplicate logs by chain/transaction/log index and records by candle ID. Handle reorganizations by removing orphaned records and rereading canonical state. A new paid transaction intentionally buys new candles; there is no client idempotency nonce.

`getCandle(id)` returns purchaser, beneficiary, Unix timestamp, style, zero-based position, and wish. IDs begin at 1 and position equals ID minus 1. `getCandles(firstId, limit)` returns records and the next ID; begin at 1. `candleIdsOf(purchaser, offset, limit)` returns IDs and next offset; begin at 0. Both page limits are 1–100. An end cursor returns an empty array; a cursor beyond the end reverts. Use a common block tag when paginating a snapshot. `totalCandles`, `paidCandles()` and `candleCountOf` count paid candles only. No operation loops over all historical records.

Canonical mined execution, including array order within a batch, determines reward priority. Validators may reorder or censor submitted transactions; submission time does not reserve priority. Timestamps do not select beneficiaries. Cosmetic names: 0 Purity, 1 Hope, 2 Love, 3 Success, 4 Health, 5 Wealth, 6 Happiness.

## Rewards, precision and custody

For each new candle, let `n` be the number of prior candles, `R = 3*10^17` and `Q = 10^27`.

- If `n == 0`, move that candle's entire `R` to ecosystem. There is no reward liability for the first candle's allocation.
- Otherwise add `floor(R*Q/n)` to the global reward-per-candle accumulator **before** adding the new weight. Book the full `R` as restricted reward liability, and add `(R*Q) mod n` to `rewardDustScaled`.
- Settle the purchaser's existing weight using its accumulator checkpoint, retaining scaled fractions. Then increase its weight and set its checkpoint at the current accumulator. New candles cannot receive earlier allocations; earlier candles in the same batch earn normally.
- Lifetime `earned` is the floor of accumulated scaled entitlement divided by `Q`. `claimable = earned - claimed`. `claimRewards()` settles once and pays the caller's full claimable amount only to the caller. It reverts if nothing is due. There is no expiry, lock, admin confiscation, third-party claim or destination override.

`rewardState(account)` returns `(candles, earned, claimed, claimable, fractionScaled)`. `claimableRewards(account)` is a convenience view. Earned is cumulative and does not decrease on claims; claimed increases only after a successful exact payment. Purchases and claims are O(batch <=50) and O(1), respectively, apart from validating each bounded wish. No automatic transfer is made to earlier users during purchases.

Global division dust is never recycled: recycling it after adding a weight could give a later candle earlier rewards. It remains restricted in the garden forever and is not revenue. Account fractions remain attached to their original account across claims and can accumulate into claimable wei from later purchases. At any state:

```
sum(account lifetime earnedScaled) + rewardDustScaled = totalRewardsAllocated * Q
rewardLiability = totalRewardsAllocated - totalRewardsClaimed
accountedBalance = ecosystemBalance + operationsBalance + founderBalance
                 + rewardLiability + burnQueued + burnReserved
held Ethereum IMD >= accountedBalance
```

The reward liability includes both eventual claimable fractions and permanently undistributed division dust. It is deliberately conservative: sum of currently claimable amounts never exceeds it. Claimable IMD must be backed by **held Ethereum IMD**, not burn assets in transit, ecosystem promises or a displayed APY. `unallocatedBalance` shows donations/excess that cannot be swept or relabeled as revenue. No new entrant receives old rewards via dust rounding.

Examples: Alice buying two candles pays 2 IMD, earns 0.3 IMD, leaves 0.6 IMD in the burn queue and 1.1 IMD in owner buckets. If Alice buys one, Bob buys one, then Bob buys one more, Alice earns 0.45 IMD and Bob earns 0.15 IMD. Bob's 0.15 IMD is a partial self-share of Bob's later payment.

## Fee buckets and privileges

Use `withdrawBucket(bucket, destination, amount)` as the **current owner**, with bucket 0 ecosystem, 1 operations, 2 founder. The default operational destination is the owner; the caller explicitly supplies it. Each bucket is independent and partial withdrawals are allowed. `BucketWithdrawn` records bucket, caller, destination and amount. Track each current balance and `totalEcosystemWithdrawn`, `totalOperationsWithdrawn`, `totalFounderWithdrawn`. The first candle's fallback is part of ecosystem.

Ownership transfers require `transferOwnership` then the proposed owner's `acceptOwnership`; all three fee powers follow the accepted owner. Renouncing ownership is disabled. The owner can pause/resume **purchases only**, prepare bridge configuration before activation, activate after readiness, and queue/dispatch restricted burns. It cannot change prices/rates, candle or wish data, entitlements, the official bridge/token, destination after activation, or withdraw rewards/burn funds. There is no proxy or arbitrary admin execution.

## Bridge state and events

`totalBurnAllocated` is cumulative purchase allocation, not confirmed burn. The custody identity is:

```
totalBurnAllocated = burnQueued + burnReserved + burnInTransit + confirmedBurn
```

`queueBurn(maximumAmount)` reserves up to the requested available amount, rounded down to `10^12` base units. `bridgeDust()` is the remaining queue modulo that unit. Ordinary 0.3 IMD candle shares are divisible by it. Each immutable job amount has a stable sequential ID. `BurnQueued` announces the ID and amount.

`quoteBurn(id)` quotes the fixed destination, exact send/receive amount, official options and compose payload. `dispatchBurn(id)` requires the owner and the exact separately funded native fee, capped at 0.05 ETH. Ethereum IMD's OFT requires **no approval**: it debits the sending garden directly. The allowance is zero, not unlimited. Source balance reduction and both OFT receipt amounts must equal the job amount. IMD gas or rewards are never used for fees.

Source status values: 0 None, 1 Queued, 2 Failed, 3 InTransit, 4 Completed. A failed attempted source send returns `false`, emits `BurnSendFailed`, keeps its IMD reserved and refunds attached native ETH. A retry uses the same ID. `failedBurnAmount` is a **subset of burnReserved**, not an extra liability. `totalSendFailures`, `totalSendRetries` and job attempts are cumulative counts. Quote/config/fee/low-gas precondition failures revert without an attempt. A success emits `BurnDispatched` and cannot be sent again. Dispatch remains available during a purchase pause.

Base receives the official authenticated compose message, checks endpoint, adapter, Ethereum source EID, compose sender, GUID, job uniqueness and sufficient custody. Tokens are transferred by the official adapter before compose executes, possibly in another transaction; this is **not** an atomic callback balance-delta measurement. Correct amount attribution relies on the verified adapter's lossless credit and Base token transfer behavior. The contract separately verifies the exact balance and `totalSupply` reductions caused by its burn. It never burns all of its balance or counts donations.

Base `deliveries(guid)` tracks received amount, job ID, attempts, status and acknowledgement. Status 0 None, 1 Received, 2 Failed, 3 Burned. A failed/no-op/inexact burn is atomically undone and recorded as failed, with custody retained. Anyone may pay transaction gas for `retryBurn(guid)`; funds cannot be redirected. `pendingBurn` includes failed burns; `failedBurn` is a subset, and `totalReceived = pendingBurn + totalBurned`.

A successful Base burn emits `SupplyBurned`. Anyone may fund `sendBurnReceipt(guid)` with the exact quoted native fee. A reverted receipt send leaves it retryable; after a successful send, retry delivery of that same LayerZero packet instead of sending again. Only an authenticated receipt matching source job ID, GUID, amount and configuration changes Ethereum's `confirmedBurn` and emits `BurnConfirmed`. Receiving a duplicate or conflicting receipt cannot count twice. Show Base-burned-but-unacknowledged amounts separately; do not add them again to Ethereum confirmed burn.

A source-chain OFT debit is bridge accounting, not an application-confirmed permanent global supply burn. Do not count it and the Base burn twice. Out-of-order deliveries are supported. Never rebridge an in-transit job because of a timeout. See [recovery instructions](../deployment.md).
