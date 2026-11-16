# EVERLIGHT GARDEN on IMD — contracts only

Permanent paid candle records and public wishes on Ethereum. Deploy **only `WishGarden(address owner_)`**, with owner `0x48E4E74fE1d0c14404cEB57B9fec5b21329C6ec9`. Purchases start **disabled**. Its treasury and restricted bridge queue are internal components, with no external binding or initializer. A separate Base burn receiver must be deployed and verified before activation.

This contribution supplies source, offline Foundry tests, ABIs, a manifest handoff, and an unsigned Base deployment package. Source publication, the source commit identifier, the Ethereum launch manifest and confirmed deployment address belong to the subsequent network steps. No contract was deployed, transaction broadcast, real-fund purchase made, or website built here.

## Paid candles

- Existing Ethereum IMD: `0xD34a99Bc0f67aE1bbd63C660e6d0b0dd03E263B7`, 18 decimals. Exactly **1 IMD** buys each candle, **1–50** per transaction. No 10,000 cap or expiry.
- `buyCandles(uint8[] styles, string[] wishes)` accepts one style and optional wish per candle. Empty strings represent no wish. Each wish is strict UTF-8, at most **280 Unicode scalar values/codepoints and 1,120 bytes**. Text is public forever, stored and emitted unchanged. There is no encryption, private wish facility, deletion or admin rewrite.
- Purchaser and beneficiary are always the paying caller. Sequential IDs start at 1; positions are ID minus 1. Timestamps, beneficiaries, styles and wishes are immutable. These records and rewards are nontransferable and are **not NFTs**.
- Cosmetic styles 0–6: Purity, Hope, Love, Success, Health, Wealth, Happiness. Styles change no price, weight or entitlement.
- No free claims, lottery, random winner, retrospective rewards, legacy import or NFT entitlement. NFT ownership grants **nothing**.

## Fixed economics per candle

| Allocation | IMD | Treatment |
| --- | ---: | --- |
| Real-burn queue | 0.30 | Restricted official bridge route, then Base `burn(uint256)` |
| Earlier paid candles | 0.30 | Equal weight across all prior IDs; first candle only falls back to ecosystem |
| Ecosystem | 0.30 | Owner-withdrawable bucket |
| Operations | 0.05 | Separate owner-withdrawable bucket |
| Founder | 0.05 | Separate owner-withdrawable bucket |

**Rewards come ONLY from later candle purchases. They are not yield from an external business. No later purchases means no new rewards, and there is no guaranteed return.** Ecosystem investments give candle holders no financial rights. Purchases by the same wallet generate a partial self-share of its own payment; that is not profit.

Actual canonical transaction execution and array order determine priority. Each share is allocated before the new candle joins; earlier candles in the same batch earn from later ones. Claims are beneficiary-initiated, paid only to that beneficiary, available at any time, including while purchases pause. Owner withdrawals cannot consume reward liabilities or burn funds. See [integration and rounding](docs/abi/README.md).

## Real burn and activation

Ethereum IMD is the official LayerZero V2 OFT and has no public burn. Its Base peer is `0xab152db8aaC047b6757fFCF495FfE88d7712690A`, an OFT adapter for the supplied Base token `0xFF0C532FDB8Cd566Ae169C1CB157ff2Bdc83E105`. The application burns only after authenticated Base delivery and confirms back to Ethereum via LayerZero. Bridging, locking, pending transfers and sink transfers are never reported as confirmed supply reduction.

The Base token currently reports **“Fren Pet”** in its live symbol field; its exact supplied address and bridge pairing were verified. It has an administrator and transfer restrictions. [Verification evidence](docs/verification.md) distinguishes verified source/runtime, live reads, offline fixtures and unverified live operation. [Deployment](docs/deployment.md) lists activation blockers, including Base deployment, endpoint security/default-library review, token transfer conditions, liquidity, fees and receiver verification. Purchases remain disabled until the owner completes setup and Ethereum receives authenticated Base readiness.

The legacy garden `0xaabd6a747359f5478803efa7b51e929e62ec4ca2` and treasury `0x929a062e0ab6266534f1ce573ba34ca7980207aa` remain separate and untouched. No function reads, sweeps or migrates their balances.

## Build and handoff

```sh
forge build
FOUNDRY_FUZZ_SEED=0x9e56a8a08f479c4debd98dee24655411b47d3a5f10f757d2dd0fcb595fd4d87f forge test
python3 scripts/export-abis.py --check
```

No dependency/configuration changes or network access are needed to build/test. [ADAPTATION.md](ADAPTATION.md) maps changes and imported findings to evidence. [Validation/review](docs/validation.md) states coverage and review limits. [Ethereum handoff](docs/deployment/manifest-handoff.json) identifies the sole launch contract; [Base package](docs/base/README.md) is outside that manifest.

Named engineering limits: page size 100, reward precision `10^27`, bridge shared-unit conversion `10^12`, source send subcall gas 1,000,000, Base burn subcall gas 150,000, receiver gas option 200,000, compose gas option 650,000, and maximum native message fee 0.05 ETH per message. These constants cannot be changed by the owner. The Base burn destination is not owner-settable: `pinnedBaseReceiver()` is fixed at construction as the CREATE2 address of this repository's receiver (canonical deployer `0x4e59b44847b379578588920cA78FbF26c0B4956C`, salt `keccak256("EVERLIGHT GARDEN Base burn receiver v1")`, arguments initial owner and garden).

The 1–50 candle limit and the 1120-byte wish limit hold separately, not together: one Ethereum transaction carries at most 16,777,216 gas, and a safe bound is `300,000 + 170,000 × candles + 1,300 × total wish bytes`. Fifty candles fit with about 122 wish bytes each; full-length wishes fit 10 per transaction; 50 full-length wishes (about 71.7M gas) can never be mined and must be split. See [integration guide, Batch gas](docs/abi/README.md#batch-gas).
