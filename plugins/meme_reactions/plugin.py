class Plugin:
    """Starter plugin contract for the Meme Reactions mini-project."""

    def __init__(self) -> None:
        self.context = None
        self.active = False

    def setup(self, context):
        self.context = context

    def start(self):
        self.active = True

    def update(self, frame, tracking_data):
        return frame

    def stop(self):
        self.active = False
