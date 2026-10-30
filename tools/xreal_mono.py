#!/usr/bin/env python3
"""Patch XREAL's framebuffer selector to honor its advertised mono capability."""

LIBRARY = "lib/arm64-v8a/libXREALXRPlugin.so"

# DisplayManager::GfxThreadStart seeds stereo from an always-false member even
# when UserDefinedSettings.supportMonoMode says that native mono is supported.
_ORIGINAL = bytes.fromhex("68c241391f010071280080520115881a")
_MONO_CAPABILITY = bytes.fromhex("682a40f908314039490080522101084b")
_GET_FRAMEBUFFER_MODE = bytes.fromhex("1a0100941f080071c0030054e103002a")
_SELECT_MONO_RENDERER = bytes.fromhex("200080521f080071c0030054e103002a")
_STITCH_PATCHES = (
    (0xC6F90, "e1031f2ab3390094081ca04e291ca14e", "c1008052b3390094081ca04e291ca14e", "left center fov"),
    (0xC6FB0, "e1031f2a84390094e00bc03de1c3c23c", "c100805284390094e00bc03de1c3c23c", "left center pose"),
    (0xC6FC0, "02e4006f7f2600b96826052d6a2e062d6282833c6282843c6282853c6142813c", "02e4006f7f2600b9680a052d6a2e062d6282833c6282843c6282853c6142813c", "left half frustum"),
    (0xC6FEC, "21008052350080529b390094081ca04e", "c1008052350080529b390094081ca04e", "right center fov"),
    (0xC7010, "210080526c390094e00bc03de1c3c23c", "c10080526c390094e00bc03de1c3c23c", "right center pose"),
    (0xC7020, "02e4006f7f9e00b96826142d6a2e152d628a05ad6236803d75e600b961c2883c", "02e4006f7f9e00b96226142d6a2e152d628a05ad6236803d75e600b961c2883c", "right half frustum"),
)


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


def patch_xreal_stereo_stitch_renderer(blob: bytes) -> bytes:
    """Render complementary center-camera halves into the required stereo transport."""
    for offset, original, replacement, label in _STITCH_PATCHES:
        blob = _replace_exact(blob, bytes.fromhex(original), bytes.fromhex(replacement), offset, label)
    return blob


def patch_xreal_stereo_transport_mono_renderer(blob: bytes) -> bytes:
    """Keep the visible stereo NRSDK transport while asking Unity for one render view."""
    return _replace_exact(
        blob,
        _GET_FRAMEBUFFER_MODE,
        _SELECT_MONO_RENDERER,
        0xC58A4,
        "framebuffer-mode query",
    )
