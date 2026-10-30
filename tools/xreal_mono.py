#!/usr/bin/env python3
"""Patch XREAL's framebuffer selector to honor its advertised mono capability."""

LIBRARY = "lib/arm64-v8a/libXREALXRPlugin.so"

# DisplayManager::GfxThreadStart seeds stereo from an always-false member even
# when UserDefinedSettings.supportMonoMode says that native mono is supported.
_ORIGINAL = bytes.fromhex("68c241391f010071280080520115881a")
_MONO_CAPABILITY = bytes.fromhex("682a40f908314039490080522101084b")


def patch_xreal_mono(blob: bytes) -> bytes:
    matches = []
    start = 0
    while True:
        found = blob.find(_ORIGINAL, start)
        if found < 0:
            break
        matches.append(found)
        start = found + 1
    if matches != [0xC5854]:
        raise ValueError(
            f"expected XREAL framebuffer selector once at 0xc5854, found {matches}"
        )
    return blob[:matches[0]] + _MONO_CAPABILITY + blob[matches[0] + len(_ORIGINAL):]
