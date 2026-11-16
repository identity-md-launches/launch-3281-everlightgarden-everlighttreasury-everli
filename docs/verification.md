# Official IMD bridge verification and evidence limits

The route is derived from the supplied token addresses, verified deployed source and read-only chain calls, not guessed selectors or arbitrary router calldata. The application does not import or deploy any token implementation.

## Observed contracts

[bridge-dependencies.json](evidence/bridge-dependencies.json) records the source verification identifiers, hashes, live requests/responses and observation times. Calls use independent `latest` reads, **not a pinned-block fork or one atomic snapshot**. All three deployed runtimes matched the stored Sourcify onchain bytecode when fetched during this contribution.

| Role | Chain/address | Verified source/runtime |
| --- | --- | --- |
| Ethereum IMD OFT | 1, `0xd34a99bc0f67ae1bbd63c660e6d0b0dd03e263b7` | [BridgedFP and inherited OFT source](https://sourcify.dev/server/v2/contract/1/0xd34a99bc0f67ae1bbd63c660e6d0b0dd03e263b7?fields=all), runtime hash `0x79a1ae149d27d4aae006d4dd75cb834222c9623799bbf34359428aaf66fec3bf` |
| Base official peer/adapter | 8453, `0xab152db8aac047b6757ffcf495ffe88d7712690a` | [FrenPetOFTAdapter source](https://sourcify.dev/server/v2/contract/8453/0xab152db8aac047b6757ffcf495ffe88d7712690a?fields=all), runtime hash `0x1ad0c62178c048836ae25bc3c56a69579ae1ac8498209281c36acd344063e4da` |
| Supplied Base IMD token | 8453, `0xFF0C532FDB8Cd566Ae169C1CB157ff2Bdc83E105` | [FrenPetToken and ERC20Burnable source](https://sourcify.dev/server/v2/contract/8453/0xFF0C532FDB8Cd566Ae169C1CB157ff2Bdc83E105?fields=all), runtime hash `0x15021fda4613ae853a7e3199f62df75e6f547ca11d32df53c0b1616f4a80ef4f` |

Ethereum `peers(30184)` returned the Base adapter. Base adapter `peers(30101)` returned the Ethereum token, and `token()` returned the exact supplied Base address. Both OFTs report the endpoint `0x1a44076050125825900e736c501f859c50fE728c` and a `10^12` decimal conversion rate. Base endpoint `eid()` returned 30184. Ethereum IMD's verified `approvalRequired()` returns false: it burns from the caller in `_debit`, so there must be no allowance. The Base adapter's `_credit` unlocks existing Base collateral to the destination; it does not mint a replacement token.

The Base token is 18 decimals but its live symbol is **Fren Pet**. Its supplied address remains authoritative for this assignment; no substitute was selected. Live reads showed migration phase false, trading active true, transfer limits enabled, blacklist power not renounced, and the adapter not blacklisted at observation. A receiver has not yet been deployed, so its live status cannot be certified. These token controls and collateral availability are explicit pre-activation checks and continuing external liveness risks. The token's burn uses inherited ERC20Burnable and reduces the caller's balance and totalSupply. Ethereum's token exposes no public `burn`/`burnFrom`; its source-chain bridge debit alone is not a permanent global burn claim.

## Interface and message provenance

`src/bridge/IMDBridge.sol` declares only the ABI subset used by the application, with unchanged tuple layouts from verified `IOFT.sol` and `ILayerZeroEndpointV2.sol`: `SendParam`, `MessagingFee`, `MessagingReceipt`, `OFTReceipt`, `MessagingParams`, and `Origin`. No dynamic arbitrary target/call bytes are accepted by the garden. The application constructs its fixed official send internally. Payload is only a job ID; OFT automatically inserts the source sender.

Verified `OFTMsgCodec` packs destination address (32 bytes), shared-decimal amount (8), compose sender (32), then job ID (32). The Base adapter uses verified `OFTComposeMsgCodec`: nonce (8), source EID (4), local-decimal amount (32), compose sender (32), job ID (32). The receiver demands exactly 108 bytes and the correct authenticated source.

Execution options follow LayerZero's [OptionsBuilder](https://github.com/LayerZero-Labs/devtools/blob/main/packages/oapp-evm/contracts/oapp/libs/OptionsBuilder.sol) and [ExecutorOptions definitions](https://github.com/LayerZero-Labs/LayerZero-v2/blob/main/packages/layerzero-v2/evm/messagelib/contracts/libs/ExecutorOptions.sol): Type 3, executor worker 1, receive type 1 with 16-byte gas, compose type 3 with index 0 plus 16-byte gas. Encoded option sizes include the option-type byte (17 and 19). No native-drop, arbitrary options or LZ-token payment is supported. The [official OFT integration guide](https://docs.layerzero.network/v2/developers/evm/oft/quickstart) explains separate credit/compose transactions and retry behavior.

Readiness and burn acknowledgements are application messages sent through the official endpoint's `quote`/`send`, using the fixed Ethereum garden destination, fixed receive options and native fees. Ethereum implements `allowInitializePath`, `nextNonce` (unordered delivery) and the official `lzReceive` signature, with strict endpoint/peer checks and application GUID/job replay protection. This is a separate return channel whose deployment-specific defaults still require review.

## What was actually exercised

- **Live read-only:** token/adapter source retrieval, runtime comparison, decimals, peers, endpoints, conversion rate, approval requirement, Base metadata and token policy reads. No live `send`, token transfer, purchase, burn, deployment or signature.
- **Verified bytecode with local storage:** Ethereum payment and actual OFT send, actual Base adapter credit/compose format, actual Base token supply-reducing burn. The endpoint is replaced by a test double, balances/peers are locally seeded, and there is no mainnet fork. This does not certify current DVN, executor, liquidity, wallet-limit, fee, or finality behavior.
- **Fault injection/mock:** bad transfers, no-return transfers, reentrancy, send failure, invalid OFT receipts, burn failure/no-op, message forgery/replay/order, gas starvation, pause, and recovery. Test doubles are only in `test/`.
- **Not verified live:** production Ethereum/Base application addresses; Base receiver source verification; complete endpoint security/default-library configuration for both channels; real end-to-end delivery/burn/ack; current production fee estimates. These remain [activation blockers](deployment.md), not claims of a working live burn service.

The earlier [Ethereum dependency snapshot](evidence/ethereum-dependencies.json) is retained as historical imported evidence only; it is not the launch's bridge approval. All newly generated artifacts build offline from ordinary repository files and existing dependencies.
