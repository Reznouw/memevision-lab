# Meme Library Strategy

MemeVision Lab should not try to recognize 20 memes at once. The stable pattern is:

- Choose a reaction mode.
- Keep 4-5 strong triggers active.
- Map each trigger to one clear meme.
- Let users swap the meme asset without changing the detector.

## Reaction Modes

### Hands Only

Use this when the meme is triggered by a hand pose.

Good examples:

- `thumbs_up` -> approval / thumbs-up cat / OK meme
- `peace` -> peace / victory / chill meme
- `pointing` -> pointing monkey / accusation meme
- `open_palm` -> magic / matrix / stop / power meme

Avoid mapping facial memes here. Example: `bruh.gif` should not trigger from `fist`.

### Face Only

Use this when the meme depends on expression.

Good examples:

- `blank_stare` -> Bruh Moment
- `open_mouth` -> Surprised Pikachu / screaming cat
- `smile` -> Doge / Pepe Happy
- `side_eye` -> Side Eye Dog
- `closed_eyes` -> Sad Hamster / sleepy meme

Face tracking is the next tracker to add. Assets can be prepared now.

### Mixed

Use this for party mode, demos, or when the user wants everything active. Mixed mode is fun but can be noisy, so it should not be the default.

## File Naming

Use these starter names:

### Hand Assets

- `local_assets/memes/thumbs_up_cat.gif`
- `local_assets/memes/peace.gif`
- `local_assets/memes/pointing.gif`
- `local_assets/memes/matrix_code.gif`

### Face Assets

- `local_assets/memes/bruh.gif`
- `local_assets/memes/surprised_pikachu.gif`
- `local_assets/memes/side_eye_dog.gif`
- `local_assets/memes/huh_cat.gif`
- `local_assets/memes/sad_hamster.gif`

### Sounds

- `local_assets/sounds/bruh.mp3`
- `local_assets/sounds/vine_boom.mp3`
- `local_assets/sounds/metal_pipe.mp3`
- `local_assets/sounds/bonk.mp3`

## Current Decision

- `bruh` is a face reaction, not a hand reaction.
- `fist` should remain unassigned until we have a meme that visually matches fist/power/punch.
- Default mode should be `Hands only` because hand tracking exists now.
- `Face only` is visible in the UI but will become useful after Face Mesh is implemented.
