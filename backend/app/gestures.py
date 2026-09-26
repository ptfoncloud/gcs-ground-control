import time
from app.schemas import HandFrame
from app.config import settings


class GestureClassifier:
    """
    Frame-count dwell (dwell_threshold=10) + global cooldown gate
    (settings.GESTURE_COOLDOWN_SEC), unchanged from the original stub.

    Vocabulary is built only from what vehicle_manager.send_command()
    actually supports: ARM, DISARM, SET_MODE (with a mode from
    FALLBACK_MODE_IDS). No hand pose maps to DISARM, on purpose. an
    accidental fist mid-flight should never cut the motors, id prefer to not damage them. FIST and
    swipe both route to RTL instead, which is reversible and safe if
    it misfires.

    Returns (command, kwargs) instead of a bare string, since SET_MODE
    needs a `mode` kwarg the router has to pass through.
    """

    FIST_THRESHOLD = 0.85
    FIST_MAX_FINGERS = 1

    PINCH_THRESHOLD = 0.80

    PALM_MAX_GRAB = 0.15
    PALM_MAX_PINCH = 0.15
    PALM_MIN_FINGERS = 4

    SWIPE_MIN_VELOCITY_MM_S = 400.0
    SWIPE_CONFIRM_FRAMES = 4

    def __init__(self):
        self.last_command_time = 0.0
        self.active_gesture = None
        self.dwell_frames = 0
        self.dwell_threshold = 10  # frames to confirm gesture

        self._swipe_dir = None
        self._swipe_frames = 0

    def _classify_pose(self, frame: HandFrame) -> str | None:
        if frame.grab_strength >= self.FIST_THRESHOLD and frame.extended_fingers <= self.FIST_MAX_FINGERS:
            return "FIST"
        if frame.pinch_strength >= self.PINCH_THRESHOLD:
            return "PINCH"
        if (frame.grab_strength <= self.PALM_MAX_GRAB
                and frame.pinch_strength <= self.PALM_MAX_PINCH
                and frame.extended_fingers >= self.PALM_MIN_FINGERS):
            return "PALM"
        return None

    def _check_swipe(self, frame: HandFrame) -> str | None:
        vx = frame.palm_velocity[0]

        if abs(vx) < self.SWIPE_MIN_VELOCITY_MM_S:
            self._swipe_dir = None
            self._swipe_frames = 0
            return None

        direction = "RIGHT" if vx > 0 else "LEFT"
        if direction != self._swipe_dir:
            self._swipe_dir = direction
            self._swipe_frames = 1
            return None

        self._swipe_frames += 1
        if self._swipe_frames < self.SWIPE_CONFIRM_FRAMES:
            return None

        self._swipe_dir = None
        self._swipe_frames = 0
        return direction

    def process_frame(self, frame: HandFrame) -> tuple[str, dict] | None:
        now = time.time()

        if now - self.last_command_time < settings.GESTURE_COOLDOWN_SEC:
            return None

        swipe = self._check_swipe(frame)
        if swipe is not None:
            self.last_command_time = now
            self.active_gesture = None
            self.dwell_frames = 0
            return ("SET_MODE", {"mode": "RTL"})

        pose = self._classify_pose(frame)

        if pose != self.active_gesture:
            self.active_gesture = pose
            self.dwell_frames = 1
            return None

        if pose is None:
            self.dwell_frames = 0
            return None

        self.dwell_frames += 1
        if self.dwell_frames < self.dwell_threshold:
            return None

        self.last_command_time = now
        self.dwell_frames = 0

        if pose == "PINCH":
            return ("ARM", {})
        elif pose == "PALM":
            return ("SET_MODE", {"mode": "LOITER"})
        elif pose == "FIST":
            return ("SET_MODE", {"mode": "RTL"})

        return None


classifier = GestureClassifier()