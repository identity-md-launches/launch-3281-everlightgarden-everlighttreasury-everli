#!/usr/bin/env python3
"""Export checked Ethereum ABI and a separate, reproducible Base artifact. Never signs or broadcasts."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def export(check=False):
    for name in ("WishGarden", "EverlightBurnReceiver"):
        source = ROOT / "out" / f"{name}.sol" / f"{name}.json"
        if not source.is_file():
            raise SystemExit(f"Missing {source.relative_to(ROOT)}; run forge build first")
        artifact = json.loads(source.read_text())
        if "__" in artifact["bytecode"]["object"] or artifact["bytecode"].get("linkReferences"):
            raise SystemExit(f"{name}: external library linkage is forbidden")
        outputs = {ROOT / "docs" / ("abi" if name == "WishGarden" else "base") / f"{name}.json": artifact["abi"]}
        if name == "EverlightBurnReceiver":
            sources = {}
            for path in sorted((ROOT / "src").rglob("*.sol")):
                sources[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
            outputs[ROOT / "docs/base/deployment-package.json"] = {
                "chainId": 8453,
                "contract": name,
                "excludedFromEthereumManifest": True,
                "owner": "0x48E4E74fE1d0c14404cEB57B9fec5b21329C6ec9",
                "constructorTypes": ["address", "address"],
                "constructorFields": ["owner", "service-confirmed Ethereum WishGarden address"],
                "compiler": "0.8.26", "evmVersion": "cancun", "optimizerRuns": 200,
                "bytecodeHash": "none", "creationBytecode": artifact["bytecode"]["object"],
                "sourceSHA256": sources,
                "status": "unsigned; Base deployment and activation are later owner steps"
            }
        for path, value in outputs.items():
            encoded = json.dumps(value, indent=2) + "\n"
            if check:
                if not path.is_file() or path.read_text() != encoded:
                    raise SystemExit(f"Artifact differs: {path.relative_to(ROOT)}")
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(encoded)
            print(f"{'Checked' if check else 'Exported'} {path.relative_to(ROOT)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    export(parser.parse_args().check)
