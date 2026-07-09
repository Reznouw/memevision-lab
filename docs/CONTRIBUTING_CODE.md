# Contributing Code

Use this guide when a change needs Python code instead of only JSON/assets.

## Code Areas

- `src/memevision_lab/core/gesture_engine.py`: static hand gesture rules.
- `src/memevision_lab/core/face_tracker.py`: face landmarks and expression rules.
- `src/memevision_lab/core/motion_gesture_engine.py`: movement gestures over time.
- `src/memevision_lab/core/meme_reactions.py`: trigger-to-meme matching.
- `src/memevision_lab/ui/main_window.py`: launcher UI and runtime windows.
- `plugins/`: catalog mini-projects.

## Before Touching Code

Try these no-code paths first:

- Add a meme to an existing trigger: `docs/CONTRIBUTING_MEMES.md`.
- Create a catalog mini-project: `docs/CREATING_PLUGINS.md`.
- Reuse an existing trigger: `docs/TRIGGERS.md`.

Touch Python only when the current trigger/profile/plugin contract cannot express the behavior.

## Adding A New Trigger In Code

1. Decide the trigger name, for example `finger_snap`.
2. Implement detection in the right engine.
3. Add or update `configs/memes/by_trigger/finger_snap.json`.
4. Add a small test or smoke script if possible.
5. Run verification:

```powershell
.\.venv312\Scripts\python.exe -m compileall "src" "plugins" "scripts"
.\.venv312\Scripts\python.exe -m pytest -q
.\.venv312\Scripts\python.exe -m ruff check "src" "tests"
```

## Motion Gesture Guidance

For motion triggers, prefer rules based on landmarks and short histories instead of video frames:

- track palm center, nose point, or face center
- compare horizontal and vertical ranges
- detect direction changes
- require one hand vs two hands when that matters
- avoid using a generic motion trigger for different gestures

Example distinction:

```text
scuba_wave_side        = one anchored hand near face + other hand waves sideways
two_hand_palm_bounce   = two hands move vertically, together or alternating
head_shake             = nose moves left-right-left
```

## Future Gesture Recorder

The no-code gesture recorder stores landmarks, not video:

```text
configs/gestures/motion/<gesture_id>.json
```

The first slice records one 1-second motion sample after a `3 2 1` countdown. Later slices should capture several samples and derive simple features such as movement axis, hand count, range, speed, and direction changes.

To record a motion sample:

1. Launch `Meme Reactions` in `Motion only` or `Mixed`.
2. Open `Session Console`.
3. Enter a lowercase snake_case gesture id.
4. Click `Record Motion Sample`.
5. Perform the gesture after the countdown.

## Rules

- Keep changes minimal and focused.
- Do not block the camera frame loop.
- Do not commit private/copyrighted media. Only commit media with redistribution rights.
- Keep user-editable behavior in JSON where practical.
- Add or update tests when changing a detector, trigger matcher, loader, or UI helper.
