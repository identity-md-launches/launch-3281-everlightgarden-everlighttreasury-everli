#!/usr/bin/env python3
"""Build an unsigned EIP-1559 Base deployment request for the owner's wallet. No network, keys or signing."""
import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OWNER = "0x48E4E74fE1d0c14404cEB57B9fec5b21329C6ec9"

def address_word(value):
    if not re.fullmatch(r"0x[0-9a-fA-F]{40}", value) or int(value, 16) == 0:
        raise ValueError("a nonzero, service-confirmed Ethereum garden address is required")
    return value[2:].lower().rjust(64, "0")

def build(garden, nonce, gas, max_fee, priority_fee):
    if nonce < 0 or gas <= 0 or max_fee <= 0 or priority_fee < 0 or priority_fee > max_fee:
        raise ValueError("invalid transaction gas, fee or nonce")
    package = json.loads((ROOT / "docs/base/deployment-package.json").read_text())
    for relative, expected in package["sourceSHA256"].items():
        path = ROOT / relative
        if not relative.startswith("src/") or ".." in Path(relative).parts:
            raise ValueError("invalid source path in Base package")
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError("stale Base package; rebuild and rerun scripts/export-abis.py")
    code = package["creationBytecode"].removeprefix("0x")
    return {"type": "0x2", "chainId": hex(8453), "from": OWNER,
            "nonce": hex(nonce), "gas": hex(gas), "maxFeePerGas": hex(max_fee),
            "maxPriorityFeePerGas": hex(priority_fee), "value": "0x0",
            "data": "0x" + code + address_word(OWNER) + address_word(garden), "accessList": []}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ethereum-garden", required=True)
    parser.add_argument("--nonce", type=int, required=True)
    parser.add_argument("--gas", type=int, required=True, help="Base node-estimated deployment gas plus margin")
    parser.add_argument("--max-fee-per-gas", type=int, required=True, help="wei")
    parser.add_argument("--max-priority-fee-per-gas", type=int, required=True, help="wei")
    args = parser.parse_args()
    try:
        tx = build(args.ethereum_garden, args.nonce, args.gas, args.max_fee_per_gas, args.max_priority_fee_per_gas)
    except ValueError as exc:
        parser.error(str(exc))
    print(json.dumps(tx, indent=2))
