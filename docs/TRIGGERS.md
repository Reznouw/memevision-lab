# Trigger Reference

MemeVision Lab maps camera events to string triggers. Meme configs live in `configs/memes/by_trigger/`, one JSON file per trigger.

## Hand Triggers

| Trigger | Meaning | Source |
| --- | --- | --- |
| `thumbs_up` | Thumb extended, long fingers folded | `GestureEngine` |
| `peace` | Index and middle extended | `GestureEngine` |
| `pointing` | Index extended | `GestureEngine` |
| `open_palm` | Four long fingers extended; fingers may be spread or together | `GestureEngine` |
| `fist` | Long fingers folded toward wrist | `GestureEngine` |

## Face Triggers

| Trigger | Meaning | Source |
| --- | --- | --- |
| `open_mouth` | Mouth visibly open | `FaceTracker` |
| `neutral_face` | Face detected without a stronger expression | `FaceTracker` |
| `look_side` | Nose/face orientation suggests side look | `FaceTracker` |
| `closed_eyes` | Eye landmarks indicate closed eyes | `FaceTracker` |
| `serious_face` | Reserved/curated face trigger for serious reactions | Config alias |
| `sad_face` | Reserved/curated face trigger for sad reactions | Config alias |
| `head_tilt` | Reserved/curated face trigger for tilt reactions | Config alias |

## Motion Triggers

| Trigger | Meaning | Source |
| --- | --- | --- |
| `head_shake` | Face/nose moves left-right-left over a short window | `MotionGestureEngine` |
| `scuba_wave_side` | One anchored hand near face plus a lateral hand movement | `MotionGestureEngine` |
| `two_hand_palm_bounce` | Two hands move vertically together or alternating | `MotionGestureEngine` |

## Adding A Trigger

1. Prefer reusing an existing trigger.
2. If the trigger exists, add a meme to `configs/memes/by_trigger/<trigger>.json`.
3. If the trigger does not exist, start with `docs/CONTRIBUTING_CODE.md`.
4. Future no-code trigger creation will be handled by Gesture Recorder and `configs/gestures/`.

## Naming Rules

- Use lowercase snake_case.
- Name the action, not the meme: `open_palm`, not `rock_stop`.
- Keep hand, face, and motion meanings separate.
- Avoid generic names like `movement` or `reaction`.
