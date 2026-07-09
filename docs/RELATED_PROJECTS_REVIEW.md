# Related Projects Review

This document captures reference points from related open-source meme/camera/vision
projects. It is intentionally design-focused: we use ideas and patterns, not copied
code or copyrighted assets.

## Reviewed Repositories

| Project | Main Idea | Useful Lessons | Avoid / Watch |
| --- | --- | --- | --- |
| `jerry-git/thug-memes` | CLI meme generator using face detection and configurable overlays. | Strong configurable pipeline: detector choice, debug mode, config overrides, testable image transforms. | Mostly static image CLI; not a live camera UX reference. Dlib optionality can complicate install. |
| `aryaminus/memento` | OCR-based meme organizer/editor using OpenCV/Tesseract. | Meme library management matters: OCR/search/renaming can become a future asset organizer. | Tesseract/Wand add heavy system dependencies; not needed for live MVP. |
| `321david123/gesture-meme-tracker` | MediaPipe hand/face gestures mapped to meme display, with web and desktop versions. | Clear gesture guide, required asset table, deployment checklist, troubleshooting. Side-by-side webcam + meme panel is a strong UX pattern. | Web deployment is out of scope for our desktop-first app. Avoid hardcoded single-script architecture. |
| `pechenka232/Tung-Tung-Sahur-cyber-sahur-china-ai-` | Cursed OpenCV face filter with GIF/image assets. | Lean viral filter idea: a focused meme mode can be fun even if simple. | Repo style is intentionally chaotic; not a maintainability model. Be careful with meme licensing. |
| `kelfinofarelino/monkey-meme-gesture-cam` | Hand/facial gestures mapped to cute monkey reactions. | Small, understandable gesture set with explicit required assets. Good reminder to keep first reactions simple. | Limited gesture variety and likely script-style structure. |
| `dinhanhx/deep_fried_meme` | Image processing package for deep-fried meme effects. | We should add filter effects as reusable post-processors: saturation, contrast, noise, sharpening. | Static image processing only; do not block live pipeline with expensive effects. |
| `razancodes/emote-meme` | MediaPipe gesture/emotion detector with parallel meme display and GIF support. | Best reference for our next UX direction: webcam left, meme/GIF output right, debug landmarks optional, gesture contribution guide, exact asset filename table. | Uses model/task downloads and likely large single-file gesture logic; abstract ours into engines/plugins. |
| `rustielin/MemeVision` | Android OpenCV face detection, face swap, drawing, camera support. | Face swap/drawing are good future plugin categories. Multiple camera support is worth adding. | Android/Java stack is not directly reusable for current desktop Python app. |
| `christianroman/FaceMemesCV` | Live face detection and meme overlay with OpenCV. | Classic face overlay idea validates face-positioned stickers as a feature. | Old C++/iOS/OpenCV surface; not a direct architecture reference. |
| `dxxen/Meme-interactive-cam` | MediaPipe/OpenCV hand and facial expression meme triggers. | Very relevant gesture set: open mouth, finger at mouth, index up, thumb-out fist. Also documents Python version sensitivity. | Claims Python 3.11 stability; reinforces our need to pin MediaPipe versions. |
| `PandaWhoCodes/youtube_meme_base_generator` | Finds meme-worthy frames from YouTube videos using face/emotion detection. | Future offline mode: extract frames/clips from video and make meme bases. Emotion-tagged capture could extend our screenshot/recording features. | External APIs and YouTube download flows add legal/API complexity; not for MVP. |

## What We Should Adopt

- Keep the app desktop-first, but use a clearer live layout: camera feed plus a dedicated meme output panel instead of only overlaying everything inside the camera frame.
- Add an in-app gesture guide showing each gesture, expected asset, current detection status, and troubleshooting tips.
- Keep required assets explicit and filename-based, but allow the UI to detect missing files and show an actionable warning.
- Add optional debug landmarks/skeleton toggle. Users need this to understand why a gesture is not firing.
- Add a configurable detection priority order so similar gestures do not fight each other.
- Build meme effects as reusable modules: asset overlay, side-panel GIF, audio cue, deep-fried filter, face sticker, screenshot/clip capture.
- Maintain pinned dependency ranges for MediaPipe/OpenCV/Numpy because related projects repeatedly hit Python/version instability.

## What We Should Not Copy

- Do not collapse into one large script. Most reference projects are simple scripts; MemeVision Lab should keep `core/`, UI, plugins, assets, and config separated.
- Do not ship copyrighted memes/audio in the public project unless licensed. Keep `local_assets/` untracked.
- Do not introduce external cloud APIs for emotion detection in the near term.
- Do not make MediaPipe startup block camera preview.
- Do not require system OCR/Tesseract until asset-library organization becomes a real feature.

## Immediate Product Direction

The next phase should make MemeVision Lab feel less like a debug overlay and more like a real meme reactor:

1. Add a split Live Studio layout inside the existing desktop UI: camera preview on the left, current meme/GIF output on the right.
2. Add a `Debug Landmarks` toggle to show/hide MediaPipe hand skeletons.
3. Add a `Gesture Guide` panel with the current supported gestures and missing/loaded asset status.
4. Improve gesture detection priority and names based on the reference set:
   - `pointing`
   - `finger_to_mouth`
   - `open_mouth`
   - `fist`
   - `thumbs_up`
   - `open_palm`
5. Add simple deep-fried visual filter as a meme effect plugin, not as always-on processing.
6. Add camera index selection after the current single-camera path is stable.

## Reference-Informed Architecture Target

Keep this architecture boundary:

- `CameraWorker`: frame capture and orchestration only.
- `HandTracker` / future `FaceTracker`: raw landmark extraction.
- `GestureEngine`: maps landmarks to canonical gesture labels.
- `MemeReactionEngine`: maps canonical gestures to reaction objects with cooldown.
- `MemeAssetCache`: loads still/GIF frames and audio paths.
- UI: chooses presentation mode: overlay, split panel, debug view.
- Plugins: define new reaction/effect types without changing the camera loop.
