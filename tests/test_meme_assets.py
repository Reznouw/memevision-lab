from __future__ import annotations

from memevision_lab.core.meme_assets import MemeAssetCache


def test_missing_asset_returns_placeholder_frame(tmp_path):
    cache = MemeAssetCache(base_path=tmp_path)

    frame = cache.frame_for("local_assets/memes/hands/missing.gif", now=1.0)

    assert frame is not None
    assert frame.shape == (360, 640, 4)
    assert frame.dtype.name == "uint8"
    assert frame[:, :, 3].max() == 255


def test_missing_asset_placeholder_is_cached(tmp_path):
    cache = MemeAssetCache(base_path=tmp_path)

    first = cache.frame_for("missing.gif", now=1.0)
    second = cache.frame_for("missing.gif", now=2.0)

    assert first is second
