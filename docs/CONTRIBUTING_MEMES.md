# Contributing Memes

Use this guide when you want to add a meme reaction without changing Python code.

## Fast Path: Use The App

1. Open MemeVision Lab.
2. Go to `Project Catalog`.
3. Find `Meme Reactions`.
4. Click `Add Meme`.
5. Choose an existing trigger or type a new trigger name.
6. Choose `Hand`, `Face`, or `Motion`.
7. Pick a GIF/image file and optional audio file with `Browse`.
8. Click `Save Meme`.

The app copies files into `local_assets/` and writes the JSON entry under:

```text
configs/memes/by_trigger/<trigger>.json
```

## Manual Path

Use the manual path when reviewing a pull request, fixing a typo, or adding many memes at once.

1. Put the media file in the matching folder.
2. Add one JSON object to the trigger file.
3. Run the validation command below.

Recommended folders:

```text
local_assets/memes/hands/    hand-triggered GIF/PNG/JPG/WEBP
local_assets/memes/face/     face-triggered GIF/PNG/JPG/WEBP
local_assets/memes/motion/   motion-triggered GIF/PNG/JPG/WEBP
local_assets/sounds/hands/   optional MP3/WAV/OGG
local_assets/sounds/face/    optional MP3/WAV/OGG
local_assets/sounds/motion/  optional MP3/WAV/OGG
```

Example:

```json
{
  "id": "the_rock_stop",
  "name": "The Rock Stop",
  "asset": "local_assets/memes/hands/the_rock_stop.gif",
  "sound": "local_assets/sounds/hands/the_rock_stop.mp3",
  "input_type": "hand",
  "cooldown_seconds": 1.0,
  "category": "reaction"
}
```

## Trigger Files

The file name is the trigger. For example:

```text
configs/memes/by_trigger/open_palm.json
```

Entries in that file respond to `open_palm` even if the entry does not include a `triggers` field.

Only add `triggers` when a meme should respond to aliases too:

```json
"triggers": ["open_palm", "both_palms"]
```

## Pull Request Checklist

- Media files are yours, public domain, or licensed for redistribution.
- File names are lowercase snake_case where possible.
- JSON `id` is unique.
- `input_type` matches the trigger family: `hand`, `face`, or `motion`.
- Asset paths are relative, not absolute Windows paths.
- Optional sound paths exist if provided.
- Validation reports no missing assets.

## Validation

Run this before committing:

```powershell
.\.venv312\Scripts\python.exe -c "import json; from pathlib import Path; files=sorted(Path('configs/memes').rglob('*.json')); data=[]; [data.extend(json.loads(p.read_text(encoding='utf-8'))) for p in files]; missing=[item.get('asset') for item in data if item.get('asset') and not Path(item['asset']).exists()]; missing_sound=[item.get('sound') for item in data if item.get('sound') and not Path(item['sound']).exists()]; print('memes', len(data)); print('missing_assets', len(missing)); print('missing_sounds', len(missing_sound))"
```

Expected output for a clean repo:

```text
missing_assets 0
missing_sounds 0
```

## When Code Is Needed

You need Python changes only when the trigger itself does not exist yet and cannot be represented by an existing trigger. See `docs/CONTRIBUTING_CODE.md`.
