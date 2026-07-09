class Plugin:
    """Starter plugin contract for a MemeVision Lab mini-project."""

    def setup(self, context):
        self.context = context

    def start(self):
        pass

    def update(self, frame, tracking_data):
        return frame

    def stop(self):
        pass
