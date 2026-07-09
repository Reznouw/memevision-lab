from __future__ import annotations

import time
from pathlib import Path

import numpy as np


class MemeAssetCache:
    def __init__(self, base_path: Path | None = None) -> None:
        self.base_path = base_path if base_path is not None else self._discover_default_base_path()
        self._cache: dict[Path, list[np.ndarray]] = {}
        self._missing_cache: dict[str, np.ndarray] = {}

    def frame_for(self, asset_path: str, now: float | None = None) -> np.ndarray | None:
        if not asset_path:
            return self._placeholder_frame("No asset configured")

        path = Path(asset_path)
        if not path.is_absolute():
            path = self.base_path / path
        if not path.exists():
            return self._placeholder_frame(f"Missing asset: {asset_path}")

        frames = self._cache.get(path)
        if frames is None:
            frames = self._load_frames(path)
            self._cache[path] = frames
        if not frames:
            return self._placeholder_frame(f"Unreadable asset: {asset_path}")

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

    def _placeholder_frame(self, message: str) -> np.ndarray:
        cached = self._missing_cache.get(message)
        if cached is not None:
            return cached

        height = 360
        width = 640
        frame = np.zeros((height, width, 4), dtype=np.uint8)
        frame[:, :, :3] = (31, 32, 36)
        frame[:, :, 3] = 255
        frame[24:-24, 24:-24, :3] = (38, 40, 46)
        frame[26:-26, 26:-26, :3] = (31, 32, 36)

        # Small deterministic accent bars make missing assets visually distinct without extra deps.
        accent = (88, 101, 242)
        frame[64:76, 72: width - 72, :3] = accent
        frame[height - 76: height - 64, 72: width - 72, :3] = accent
        self._draw_block_text(frame, "ASSET NOT INCLUDED", 76, 126, scale=5)
        self._draw_block_text(frame, message[:42], 76, 210, scale=3)
        self._missing_cache[message] = frame
        return frame

    def _draw_block_text(self, frame: np.ndarray, text: str, x: int, y: int, scale: int) -> None:
        color = np.array([242, 243, 245, 255], dtype=np.uint8)
        cursor_x = x
        for char in text.upper():
            if char == " ":
                cursor_x += 4 * scale
                continue
            if cursor_x + 3 * scale >= frame.shape[1] - 32:
                break
            self._draw_block_char(frame, char, cursor_x, y, scale, color)
            cursor_x += 4 * scale

    def _draw_block_char(
        self,
        frame: np.ndarray,
        char: str,
        x: int,
        y: int,
        scale: int,
        color: np.ndarray,
    ) -> None:
        glyph = _BLOCK_FONT.get(char, _BLOCK_FONT["?"])
        for row_index, row in enumerate(glyph):
            for col_index, enabled in enumerate(row):
                if enabled != "1":
                    continue
                y0 = y + row_index * scale
                x0 = x + col_index * scale
                frame[y0 : y0 + scale, x0 : x0 + scale] = color

    def _discover_default_base_path(self) -> Path:
        for parent in Path(__file__).resolve().parents:
            if (parent / "plugins").exists() or (parent / "configs").exists():
                return parent
        return Path.cwd()


_BLOCK_FONT = {
    "A": ("010", "101", "111", "101", "101"),
    "B": ("110", "101", "110", "101", "110"),
    "C": ("011", "100", "100", "100", "011"),
    "D": ("110", "101", "101", "101", "110"),
    "E": ("111", "100", "110", "100", "111"),
    "F": ("111", "100", "110", "100", "100"),
    "G": ("011", "100", "101", "101", "011"),
    "H": ("101", "101", "111", "101", "101"),
    "I": ("111", "010", "010", "010", "111"),
    "J": ("001", "001", "001", "101", "010"),
    "K": ("101", "101", "110", "101", "101"),
    "L": ("100", "100", "100", "100", "111"),
    "M": ("101", "111", "111", "101", "101"),
    "N": ("101", "111", "111", "111", "101"),
    "O": ("010", "101", "101", "101", "010"),
    "P": ("110", "101", "110", "100", "100"),
    "Q": ("010", "101", "101", "111", "011"),
    "R": ("110", "101", "110", "101", "101"),
    "S": ("011", "100", "010", "001", "110"),
    "T": ("111", "010", "010", "010", "010"),
    "U": ("101", "101", "101", "101", "111"),
    "V": ("101", "101", "101", "101", "010"),
    "W": ("101", "101", "111", "111", "101"),
    "X": ("101", "101", "010", "101", "101"),
    "Y": ("101", "101", "010", "010", "010"),
    "Z": ("111", "001", "010", "100", "111"),
    "0": ("111", "101", "101", "101", "111"),
    "1": ("010", "110", "010", "010", "111"),
    "2": ("110", "001", "010", "100", "111"),
    "3": ("110", "001", "010", "001", "110"),
    "4": ("101", "101", "111", "001", "001"),
    "5": ("111", "100", "110", "001", "110"),
    "6": ("011", "100", "110", "101", "010"),
    "7": ("111", "001", "010", "010", "010"),
    "8": ("010", "101", "010", "101", "010"),
    "9": ("010", "101", "011", "001", "110"),
    ":": ("000", "010", "000", "010", "000"),
    "-": ("000", "000", "111", "000", "000"),
    "_": ("000", "000", "000", "000", "111"),
    ".": ("000", "000", "000", "000", "010"),
    "/": ("001", "001", "010", "100", "100"),
    "?": ("110", "001", "010", "000", "010"),
}
