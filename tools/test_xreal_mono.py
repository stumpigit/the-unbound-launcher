#!/usr/bin/env python3
import hashlib
import unittest
import zipfile
from pathlib import Path

from xreal_mono import LIBRARY, patch_xreal_mono

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "artifacts/unbound-launcher-help/the-unbound-launcher.apk"


class XrealMonoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with zipfile.ZipFile(BASE) as archive:
            cls.original = archive.read(LIBRARY)

    def test_mono_capability_selects_mono_framebuffer(self):
        patched = patch_xreal_mono(self.original)
        self.assertNotEqual(patched, self.original)
        changed = [i for i, (old, new) in enumerate(zip(self.original, patched)) if old != new]
        self.assertTrue(changed)
        self.assertGreaterEqual(min(changed), 0xC5854)
        self.assertLess(max(changed), 0xC5864)
        self.assertEqual(
            patched[0xC5854:0xC5864].hex(),
            "682a40f908314039490080522101084b",
        )

    def test_rejects_unknown_or_already_patched_library(self):
        patched = patch_xreal_mono(self.original)
        with self.assertRaisesRegex(ValueError, "expected XREAL framebuffer selector"):
            patch_xreal_mono(patched)
        damaged = bytearray(self.original)
        damaged[0xC5854] ^= 1
        with self.assertRaisesRegex(ValueError, "expected XREAL framebuffer selector"):
            patch_xreal_mono(bytes(damaged))

    def test_preserves_library_size_and_unrelated_bytes(self):
        patched = patch_xreal_mono(self.original)
        self.assertEqual(len(patched), len(self.original))
        self.assertEqual(
            hashlib.sha256(patched[:0xC5854] + patched[0xC5864:]).digest(),
            hashlib.sha256(self.original[:0xC5854] + self.original[0xC5864:]).digest(),
        )


if __name__ == "__main__":
    unittest.main()
