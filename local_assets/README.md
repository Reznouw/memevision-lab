# Local Assets

Use these folders for personal meme files. Do not commit copyrighted assets unless you have redistribution rights.

## Folders

- `memes/hands/`: GIF/PNG/JPG/WEBP files triggered by hand gestures.
- `memes/face/`: GIF/PNG/JPG/WEBP files triggered by face expressions.
- `memes/motion/`: GIF/PNG/JPG/WEBP files triggered by movement gestures.
- `sounds/hands/`: MP3/WAV/OGG sounds for hand-triggered memes.
- `sounds/face/`: MP3/WAV/OGG sounds for face-triggered memes.
- `sounds/motion/`: MP3/WAV/OGG sounds for movement-triggered memes.

## Config Examples

Hand meme with audio:

```json
{
  "id": "thumbs_up_cat",
  "name": "Thumbs Up Cat",
  "triggers": ["thumbs_up"],
  "asset": "local_assets/memes/hands/thumbs_up_cat.gif",
  "sound": "local_assets/sounds/hands/thumbs_up_cat.mp3",
  "input_type": "hand",
  "cooldown_seconds": 2,
  "category": "reaction"
}
```

Face meme with audio:

```json
{
  "id": "bruh",
  "name": "Bruh Moment",
  "triggers": ["blank_stare", "neutral_face"],
  "asset": "local_assets/memes/face/bruh.gif",
  "sound": "local_assets/sounds/face/bruh.mp3",
  "input_type": "face",
  "cooldown_seconds": 3,
  "category": "sound"
}
```

Keep the `asset` and `sound` paths relative to the project root.
