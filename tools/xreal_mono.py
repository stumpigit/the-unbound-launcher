#!/usr/bin/env python3
"""Patch XREAL's framebuffer selector to honor its advertised mono capability."""

LIBRARY = "lib/arm64-v8a/libXREALXRPlugin.so"

# DisplayManager::GfxThreadStart seeds stereo from an always-false member even
# when UserDefinedSettings.supportMonoMode says that native mono is supported.
_ORIGINAL = bytes.fromhex("68c241391f010071280080520115881a")
_MONO_CAPABILITY = bytes.fromhex("682a40f908314039490080522101084b")
_GET_FRAMEBUFFER_MODE = bytes.fromhex("1a0100941f080071c0030054e103002a")
_SELECT_MONO_RENDERER = bytes.fromhex("200080521f080071c0030054e103002a")


def _replace_exact(blob: bytes, original: bytes, replacement: bytes, offset: int, label: str) -> bytes:
    matches = []
    start = 0
    while True:
        found = blob.find(original, start)
        if found < 0:
            break
        matches.append(found)
        start = found + 1
    if matches != [offset]:
        raise ValueError(f"expected XREAL {label} once at {offset:#x}, found {matches}")
    return blob[:offset] + replacement + blob[offset + len(original):]


def patch_xreal_mono(blob: bytes) -> bytes:
    return _replace_exact(blob, _ORIGINAL, _MONO_CAPABILITY, 0xC5854, "framebuffer selector")


def patch_xreal_stereo_transport_mono_renderer(blob: bytes) -> bytes:
    """Keep the visible stereo NRSDK transport while asking Unity for one render view."""
    return _replace_exact(
        blob,
        _GET_FRAMEBUFFER_MODE,
        _SELECT_MONO_RENDERER,
        0xC58A4,
        "framebuffer-mode query",
    )
