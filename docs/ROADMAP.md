# Roadmap

## Phase 1: Desktop Shell

- Create package structure with `pyproject.toml`.
- Build PySide6 main window.
- Add QSS theme.
- Add Home, Catalog, and Live screens.
- Discover plugin manifests.

## Phase 2: Camera Core

- Add OpenCV camera service. Done.
- Run camera capture outside the UI thread. Done.
- Render frames inside the Live screen. Done.
- Add FPS and camera status indicators. Done.
- Add screenshot capture. Done.

## Phase 3: Vision Tracking

- Add MediaPipe Hands tracker. In progress.
- Add MediaPipe Face tracker.
- Define shared tracking result objects. In progress.
- Add debug landmark overlays. In progress for hands.

## Phase 4: Gesture Engine

- Detect thumbs up, peace, fist, open palm, and pointing. In progress.
- Detect thumbs down, pinch, smile, open mouth, closed eyes, and serious face.
- Add confidence and cooldown handling. In progress for meme reactions.

## Phase 5: Meme Reactions MVP

- Load meme mappings from JSON. Done.
- Render placeholder meme overlays over the camera frame. Done.
- Render images and GIFs over the camera frame.
- Play optional sounds.
- Ship at least 12 configured placeholders.

## Phase 6: Reference-Informed UX Upgrade

- Add split Live Studio mode: camera feed plus dedicated meme output panel. Done.
- Add in-app gesture guide with asset status. Done.
- Add debug landmarks toggle for hand skeletons. Done.
- Add reaction mode selection for hand/face/mixed. Done.
- Add explicit gesture priority and conflict handling.
- Add camera index selection. Done.

## Phase 7: Meme Effects

- Add deep-fried filter effect as an optional meme reaction.
- Add face-positioned sticker overlays.
- Add screenshot/clip export presets.

## Phase 8: Community Plugin System

- Harden plugin validation.
- Add plugin settings schema.
- Add plugin template.
- Document contribution rules.

## Phase 9: Viral Mini-Projects

- Anime Portal.
- Air Drawing.
- Virtual Piano.
- Brick Breaker.
- Study Guardian.
