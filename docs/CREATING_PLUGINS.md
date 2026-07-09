# Creating Plugins

Plugins are mini-projects loaded by the MemeVision Lab catalog.

## Folder Structure

```text
plugins/my_plugin/
  manifest.json
  plugin.py
  preview.png
  README.md
```

Copy the starter template from:

```text
templates/plugin/
```

Then rename the folder and update `manifest.json`.

## Manifest

```json
{
  "id": "my_plugin",
  "name": "My Plugin",
  "description": "Short description shown in the catalog.",
  "category": "effects",
  "author": "Your Name",
  "version": "0.1.0",
  "entrypoint": "plugin.py",
  "preview": "preview.png",
  "required_trackers": ["hands"],
  "tags": ["fun", "camera"]
}
```

## Python Contract

```python
class Plugin:
    def setup(self, context):
        pass

    def start(self):
        pass

    def update(self, frame, tracking_data):
        return frame

    def stop(self):
        pass
```

`frame` will be the current OpenCV frame. `tracking_data` will contain active
hands, face, pose, and gesture results once the vision core is implemented.

## Rules

- Do not block the frame loop.
- Do not open your own camera if the shared camera service is available.
- Do not commit copyrighted assets unless redistribution is allowed.
- Keep plugin configuration in JSON where possible.
- Use lowercase snake_case for plugin folder names and `id` values.
- Keep plugins self-contained under `plugins/<plugin_id>/`.

## Related Guides

- Add meme assets and trigger JSON: `docs/ADDING_MEMES.md`.
- Meme contribution checklist: `docs/CONTRIBUTING_MEMES.md`.
- Change gesture detection or core behavior: `docs/CONTRIBUTING_CODE.md`.
