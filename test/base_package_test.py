"""Offline checks for the unsigned Base package helper; no signing, networking or deployment."""
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location("base_transaction", ROOT / "scripts/build-base-transaction.py")
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)


class BasePackageTest(unittest.TestCase):
    # Only a static encoding fixture. Never written into the delivered deployment package or broadcast.
    fixture_address = "0xD34a99Bc0f67aE1bbd63C660e6d0b0dd03E263B7"

    def test_unsigned_constructor_encoding_and_fixed_chain_owner(self):
        tx = helper.build(self.fixture_address, 7, 3_000_000, 1_000_000_000, 1_000_000)
        self.assertEqual(tx["chainId"], hex(8453))
        self.assertEqual(tx["from"], helper.OWNER)
        self.assertEqual(tx["value"], "0x0")
        # Deterministic deployment: the call goes to the canonical deployer, salt first, then init code.
        self.assertEqual(tx["to"], helper.CREATE2_DEPLOYER)
        package = json.loads((ROOT / "docs/base/deployment-package.json").read_text())
        encoded = subprocess.check_output(
            ["cast", "abi-encode", "constructor(address,address)", helper.OWNER, self.fixture_address], text=True
        ).strip()
        init_code = package["creationBytecode"].removeprefix("0x") + encoded[2:]
        self.assertEqual(tx["data"], "0x" + package["create2Salt"][2:] + init_code)
        cast_keccak = lambda value: subprocess.check_output(["cast", "keccak", value], text=True).strip()
        self.assertEqual(package["create2Salt"], cast_keccak(package["create2SaltPreimage"]))
        # The same derivation WishGarden's constructor performs for pinnedBaseReceiver().
        preimage = "0xff" + helper.CREATE2_DEPLOYER[2:] + package["create2Salt"][2:] + cast_keccak("0x" + init_code)[2:]
        self.assertEqual(tx["expectedReceiver"], "0x" + cast_keccak(preimage)[-40:])

    def test_keccak_known_answers(self):
        self.assertEqual(
            helper.keccak256(b"").hex(), "c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470"
        )
        for size in (1, 135, 136, 137, 272, 1000):
            data = bytes(i % 251 for i in range(size))
            expected = subprocess.check_output(["cast", "keccak", "0x" + data.hex()], text=True).strip()
            self.assertEqual("0x" + helper.keccak256(data).hex(), expected)

    def test_rejects_missing_invalid_addresses_and_transaction_fields(self):
        for address in ("", "bad", "0x" + "0" * 40):
            with self.assertRaises(ValueError):
                helper.build(address, 0, 1, 1, 0)
        for fields in ((-1, 1, 1, 0), (0, 0, 1, 0), (0, 1, 0, 0), (0, 1, 1, 2), (0, 1, 1, -1)):
            with self.assertRaises(ValueError):
                helper.build(self.fixture_address, *fields)
        result = subprocess.run([sys.executable, str(ROOT / "scripts/build-base-transaction.py")], capture_output=True)
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
