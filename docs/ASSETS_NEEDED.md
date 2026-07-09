# Assets Needed

MemeVision Lab already supports local image/GIF overlays and optional sounds.
Put files under these folders:

- `local_assets/memes/`
- `local_assets/sounds/`

Supported meme formats:

- `.png`
- `.jpg`
- `.jpeg`
- `.webp`
- `.gif`

Supported audio formats depend on `pygame`, but these are safest:

- `.wav`
- `.ogg`
- `.mp3`

## Priority Assets

These are the first files worth adding because current hand gestures can trigger them now:

| Trigger | Meme | Expected File | Optional Sound |
| --- | --- | --- | --- |
| `thumbs_up` | Thumbs Up Cat | `local_assets/memes/thumbs_up_cat.gif` | none |
| `peace` | Macaco Pointing fallback | `local_assets/memes/macaco_pointing.gif` | none |
| `pointing` | Macaco Pointing | `local_assets/memes/macaco_pointing.gif` | none |
| `open_palm` | Matrix Code | `local_assets/memes/matrix_code.gif` | none |

`bruh.gif` is now reserved for face tracking, because it is a facial reaction rather than a hand/fist reaction.

## Full Starter Config

The current config also references these files for future gestures and face tracking:

- `local_assets/memes/absolute_cinema.gif`
- `local_assets/sounds/cinema.mp3`
- `local_assets/memes/scuba_cat.gif`
- `local_assets/memes/surprised_pikachu.gif`
- `local_assets/sounds/vine_boom.mp3`
- `local_assets/memes/doge.gif`
- `local_assets/memes/not_stonks.gif`
- `local_assets/memes/elmo_fire.gif`
- `local_assets/memes/let_him_cook.gif`
- `local_assets/memes/huh_cat.gif`
- `local_assets/memes/sad_hamster.gif`
- `local_assets/memes/kermit_tea.gif`
- `local_assets/memes/side_eye_dog.gif`
- `local_assets/memes/gojo_honored_one.gif`
- `local_assets/memes/hollow_purple.gif`
- `local_assets/memes/itachi_genjutsu.gif`
- `local_assets/memes/galaxy_brain.gif`
- `local_assets/memes/bonk_doge.gif`
- `local_assets/memes/among_us_sus.gif`
- `local_assets/memes/screaming_cat.gif`
- `local_assets/memes/this_is_fine.gif`
- `local_assets/memes/gigachad.gif`
- `local_assets/memes/sigma_face.gif`
- `local_assets/memes/npc_wojak.gif`
- `local_assets/memes/pepe_crying.gif`
- `local_assets/memes/pepe_happy.gif`
- `local_assets/memes/stonks.gif`
- `local_assets/memes/keyboard_cat.gif`

## Copyright Note

Keep redistributed/public repo assets licensed or original. For personal local use,
you can place your own files in `local_assets/`; those files should stay untracked.
