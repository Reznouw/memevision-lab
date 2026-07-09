# Adding Memes

MemeVision Lab lets contributors add memes without touching Python code.

For the full pull request checklist, see `docs/CONTRIBUTING_MEMES.md`.

## Add From The App

The easiest path is inside the launcher:

1. Open `Project Catalog`.
2. Find `Meme Reactions`.
3. Click `Add Meme`.
4. Fill in name, trigger, type, asset path, optional sound, category, and cooldown.
5. Click `Save Meme`.

The app writes the entry into:

```text
configs/memes/by_trigger/<trigger>.json
```

It then refreshes the selection list without restarting.

If the asset or sound is outside the project folder, the app copies it into `local_assets/` automatically and stores a relative path. This keeps local configs portable without exposing private absolute paths.

## Pick A Trigger

Memes are grouped by trigger name:

```text
configs/memes/by_trigger/
  thumbs_up.json
  peace.json
  pointing.json
  open_palm.json
  neutral_face.json
  head_shake.json
  scuba_wave_side.json
  two_hand_palm_bounce.json
```

If the trigger file already exists, add your meme to that JSON array. If it does not exist yet, create a new `<trigger>.json` file.

## Add The Asset

When using `Add Meme`, files are copied here automatically. When editing JSON manually, put local files here:

```text
local_assets/memes/hands/    static hand gesture GIF/PNG/JPG/WEBP
local_assets/memes/face/     static face expression GIF/PNG/JPG/WEBP
local_assets/memes/motion/   movement GIF/PNG/JPG/WEBP
local_assets/sounds/hands/   optional hand sounds
local_assets/sounds/face/    optional face sounds
local_assets/sounds/motion/  optional motion sounds
```

## Add JSON

You can also edit JSON manually.

Example for `configs/memes/by_trigger/thumbs_up.json`:

```json
{
  "id": "thumbs_up_cat",
  "name": "Thumbs Up Cat",
  "asset": "local_assets/memes/hands/thumbs_up_cat.gif",
  "sound": "local_assets/sounds/hands/thumbs_up_cat.mp3",
  "input_type": "hand",
  "cooldown_seconds": 0.8,
  "category": "reaction"
}
```

The trigger is inferred from the file name. Only add `triggers` manually when a meme should respond to aliases too, such as `peace` and `two_fingers`.

## Input Types

Use one of:

- `hand`: static hand gesture.
- `face`: static face expression.
- `motion`: movement sequence.

## Current Trigger Examples

- Hands: `thumbs_up`, `peace`, `pointing`, `open_palm`, `fist`.
- Face: `neutral_face`, `open_mouth`, `look_side`, `closed_eyes`, `serious_face`.
- Motion: `head_shake`, `scuba_wave_side`, `two_hand_palm_bounce`.

See `docs/TRIGGERS.md` for the full trigger reference.

## Asset Policy

Do not add copyrighted GIFs or sounds to the public repository unless their license allows redistribution. For personal/classroom use, keep assets in `local_assets/`.
