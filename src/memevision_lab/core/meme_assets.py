from __future__ import annotations

import time
from pathlib import Path

import numpy as np


class MemeAssetCache:
    def __init__(self, base_path: Path | None = None) -> None:
        self.base_path = base_path if base_path is not None else self._discover_default_base_path()
        self._cache: dict[Path, list[np.ndarray]] = {}

    def frame_for(self, asset_path: str, now: float | None = None) -> np.ndarray | None:
        if not asset_path:
            return None

        path = Path(asset_path)
        if not path.is_absolute():
            path = self.base_path / path
        if not path.exists():
            return None

        frames = self._cache.get(path)
        if frames is None:
            frames = self._load_frames(path)
            self._cache[path] = frames
        if not frames:
            return None

        now = now if now is not None else time.monotonic()
        return frames[int(now * 10) % len(frames)]

    def _load_frames(self, path: Path) -> list[np.ndarray]:
        suffix = path.suffix.lower()
        try:
            if suffix == ".gif":
                import imageio.v3 as iio

                frames = iio.imread(path, index=None)
                return [self._ensure_rgba(frame) for frame in frames]

            import cv2

            image = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
            if image is None:
                return []
            if image.ndim == 3 and image.shape[2] >= 3:
                image = cv2.cvtColor(image, cv2.COLOR_BGRA2RGBA if image.shape[2] == 4 else cv2.COLOR_BGR2RGB)
            return [self._ensure_rgba(image)]
        except Exception:
            return []

    def _ensure_rgba(self, image: np.ndarray) -> np.ndarray:
        if image.ndim == 2:
            rgb = np.stack([image, image, image], axis=-1)
            alpha = np.full(image.shape, 255, dtype=np.uint8)
            return np.dstack([rgb, alpha])
        if image.shape[2] == 4:
            return image.astype(np.uint8)
        alpha = np.full(image.shape[:2], 255, dtype=np.uint8)
        return np.dstack([image[:, :, :3], alpha]).astype(np.uint8)

    def _discover_default_base_path(self) -> Path:
        for parent in Path(__file__).resolve().parents:
            if (parent / "plugins").exists() or (parent / "configs").exists():
                return parent
        return Path.cwd()
