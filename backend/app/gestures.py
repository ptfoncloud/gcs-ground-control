import time
from app.schemas import HandFrame
from app.config import settings

class GestureClassifier:
    def __init__(self):
        self.last_command_time = 0.0
        self.active_gesture = None
        self.dwell_frames = 0
        self.dwell_threshold = 10  # frames to confirm gesture

    def process_frame(self, frame: HandFrame) -> str | None:
        now = time.time()
        if now - self.last_command_time < settings.GESTURE_COOLDOWN_SEC:
            return None

        # Logic: Fist, Flat Palm, Pinch, Swipe
        # Return string command (e.g., 'RTL', 'TAKEOFF') or None
        return None

classifier = GestureClassifier()
