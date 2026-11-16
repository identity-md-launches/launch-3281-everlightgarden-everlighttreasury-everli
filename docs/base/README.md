# Separate Base owner deployment package

This directory is **outside the Ethereum launch manifest**. It deploys only `src/base/EverlightBurnReceiver.sol:EverlightBurnReceiver` on Base chain ID 8453. It does not deploy a token. Its owner is `0x48E4E74fE1d0c14404cEB57B9fec5b21329C6ec9`; its second constructor argument is the network-confirmed Ethereum `WishGarden` address, available only after that launch.

[deployment-package.json](deployment-package.json) contains reproducible creation bytecode, constructor types/order, compiler settings and SHA-256 hashes of application sources. [EverlightBurnReceiver.json](EverlightBurnReceiver.json) is the ABI. Regenerate and validate with:

```sh
forge build
python3 scripts/export-abis.py
python3 scripts/export-abis.py --check
```

Use the existing pinned configuration/dependencies. The constructor is nonpayable, makes no external calls and leaves activation disabled. It accepts `(owner, ethereumGarden)` in that order, both nonzero. The package intentionally contains no guessed Ethereum deployment address, nonce, signature or Base deployment receipt.

For the owner to prepare a signature, `scripts/build-base-transaction.py` accepts the actual garden address, owner's current **Base** nonce, current native fee settings (wei) and node-estimated deployment gas with margin. All five CLI fields are required:

```
python3 scripts/build-base-transaction.py --ethereum-garden ADDRESS --nonce NONCE --gas GAS \
  --max-fee-per-gas MAX_FEE_WEI --max-priority-fee-per-gas PRIORITY_FEE_WEI
```

The uppercase argument names describe required owner-supplied values; they are not runnable stand-ins. The script emits an unsigned EIP-1559 contract-creation transaction request with chain 8453, the named owner as `from`, zero native deployment value, the checked creation bytecode and two ABI-encoded address arguments. It never reads keys, accounts, environment configuration or RPC; it neither signs nor broadcasts. A contract-creation request has no `to` field. Review and sign it in the owner's own wallet tooling, broadcast on Base, then archive the actual hash, deployed address and receipt. If the owner is a smart account, use its ordinary contract-creation workflow with the same initcode and named constructor owner.

Validate the source hashes and creation bytecode against the accepted source commit before signing. Verify the actual deployed runtime and constructor arguments on the explorer. Check `owner()`, `ethereumGarden()`, chain ID and `activated()==false`. The endpoint, token, adapter and chain IDs are fixed in source. **Do not add this contract to Ethereum's manifest.** Complete every [activation step and blocker](../deployment.md), including shared evidence hash, Base activation, authenticated readiness and Ethereum activation. Live burns are not claimed by this package.
