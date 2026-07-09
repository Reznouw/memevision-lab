# MemeVision Lab

MemeVision Lab is a desktop Python computer-vision playground for gesture memes,
anime-style effects, virtual tools, mini-games, and study helpers.

The project is intentionally structured as a platform: users launch mini-projects
from one visual catalog instead of opening separate scripts. Contributors can add
new mini-projects by dropping plugin folders into `plugins/`.

## Current Status

Current alpha status:

- PySide6 desktop shell
- Dark QSS theme
- Home, project catalog, and session console screens
- Dedicated Gesture Recorder screen for landmark sample capture
- Plugin manifest discovery
- Starter `meme_reactions` plugin
- Meme configs organized by trigger under `configs/memes/by_trigger/`
- OpenCV camera worker launched from the catalog
- Separate Camera and Meme Output windows for live sessions
- Screenshot capture from the session console into `captures/`
- Optional MediaPipe hand tracking when the `vision` extra is installed
- Basic hand gesture labels: `peace`, `pointing`, `thumbs_up`, `open_palm`, and `fist`
- Meme reaction engine with cooldowns from trigger configs
- Local image/GIF output in the separate Meme Output window
- Optional local audio playback for meme reactions

Face and motion tracking are available as starter rules; richer per-plugin effects, Gesture Recorder, and profile-driven gesture configs are next phases.

## Install For Development

```bash
cd MemeVisionLab
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -e .
memevision-lab
```

The base install only includes the desktop interface. Install camera support with:

```bash
python -m pip install -e .[camera]
```

Install the full computer-vision dependencies for hand tracking with:

```bash
python -m pip install -e .[vision]
```

Note: if you use Python 3.14 and `mediapipe` has no wheel for your version yet,
use the `camera` extra first or create a Python 3.11/3.12 environment for the
full vision stack. MemeVision Lab keeps the camera live even when MediaPipe is
unavailable.

On macOS/Linux, activate with:

```bash
source .venv/bin/activate
```

## Run Without Installing

```bash
cd MemeVisionLab
python -m pip install -e .
python -m memevision_lab
```

## Launcher Flow

1. Open MemeVision Lab.
2. Go to `Project Catalog`.
3. In the `Meme Reactions` card, pick `Hands only`, `Face only`, `Motion only`, or `Mixed`.
4. Choose up to 5 memes that can appear during the session.
5. Click `Launch Project` on `Meme Reactions`.
6. The app opens VS Code at the plugin folder and starts two runtime windows:
   `MemeVision Camera` and `MemeVision Meme Output`.

`Motion only` supports starter movement triggers such as `head_shake`, `scuba_wave_side`, and `two_hand_palm_bounce`.

## Session Controls

- `Camera Index`: selects which local OpenCV camera device to open before launch.
- `Stop Session`: closes the camera and meme output windows.
- `Screenshot Camera`: saves the current camera frame to `captures/memevision-YYYYMMDD-HHMMSS.png`.
- `Hands`: shows MediaPipe availability and detected hand count.
- `Gesture`: shows the current basic hand gesture when tracking is available.
- `Meme`: shows the latest meme reaction triggered by a configured gesture.

When full vision dependencies are installed, the app can trigger starter meme
reactions from these hand gestures:

- `thumbs_up`: `Thumbs Up Cat`
- `peace`: `Macaco Pointing` fallback
- `pointing`: `Macaco Pointing`
- `fist`: `Tung Sahur`, `Puno`
- `open_palm`: palm-style reactions such as `Absolute Cinema`

## Build A Windows EXE

Use the Python 3.12 environment for the full vision build:

```powershell
cd MemeVisionLab
.\scripts\build_exe.ps1 -InstallDependencies
```

After dependencies are installed once, rebuild with:

```powershell
.\scripts\build_exe.ps1
```

The executable is created at:

```text
dist\MemeVision Lab\MemeVision Lab.exe
```

The build script copies `configs/`, `plugins/`, and `local_assets/` next to the
EXE so VS Code opens readable plugin folders and local meme assets remain easy to
replace during class.

## Local Assets

Put personal meme files in `local_assets/memes/` and sounds in
`local_assets/sounds/`. The app will use them automatically when the paths match
the JSON files under `configs/memes/`; otherwise it falls back to a text overlay.

Meme configs are organized by trigger:

- `configs/memes/by_trigger/thumbs_up.json`
- `configs/memes/by_trigger/open_mouth.json`
- `configs/memes/by_trigger/scuba_wave_side.json`
- `configs/memes/by_trigger/two_hand_palm_bounce.json`

Recommended organization:

- `local_assets/memes/hands/` for hand-triggered GIF/PNG/JPG/WEBP files.
- `local_assets/memes/face/` for face-triggered GIF/PNG/JPG/WEBP files.
- `local_assets/memes/motion/` for movement-triggered GIF/PNG/JPG/WEBP files.
- `local_assets/sounds/hands/` for hand-triggered MP3/WAV/OGG files.
- `local_assets/sounds/face/` for face-triggered MP3/WAV/OGG files.
- `local_assets/sounds/motion/` for movement-triggered MP3/WAV/OGG files.

Contributor guides:

- `docs/CONTRIBUTING_MEMES.md`: add memes safely.
- `docs/TRIGGERS.md`: existing trigger names and meanings.
- `docs/CREATING_PLUGINS.md`: create catalog mini-projects from `templates/plugin/`.
- `docs/CONTRIBUTING_CODE.md`: change detectors, trigger engines, UI, or core behavior.

The `Meme Reactions` card also includes `Add Meme`, which writes a new entry to `configs/memes/by_trigger/<trigger>.json` from inside the app.

The public repository includes a starter set of redistributable meme assets. If a configured asset is missing, the app shows a clear placeholder instead of failing. Add your own files with `Add Meme`; the app copies them into `local_assets/` and keeps configs portable.

## Why PySide6?

MemeVision Lab needs a real desktop UI, video preview, a plugin catalog, styling,
and future packaging as an executable. PySide6 provides Qt widgets, QSS styling,
threads, and a license model that is friendlier for a broad open-source project
than PyQt's GPL/commercial-only model.

## Plugin Concept

Each mini-project lives in `plugins/<plugin_id>/` and declares a `manifest.json`.
The main app discovers plugins automatically and displays them in the catalog.

See `docs/CREATING_PLUGINS.md` for the plugin contract.

Starter files are available in `templates/plugin/`.

## Asset Policy

Do not commit copyrighted meme GIFs, audio, or images directly unless they are
licensed for redistribution. Personal classroom-only assets should stay local.
