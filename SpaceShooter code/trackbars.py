import cv2


class Trackbars:
    def __init__(self):
        self.window_name = "Result"
        # self.create_trackbars()

    def create_trackbars(self):
        """Create trackbars for HSV values and start control."""
        cv2.namedWindow(self.window_name)
        cv2.createTrackbar("h", self.window_name, 0, 255, lambda x: None)
        cv2.createTrackbar("s", self.window_name, 0, 255, lambda x: None)
        cv2.createTrackbar("v", self.window_name, 0, 255, lambda x: None)
        cv2.createTrackbar("Start", self.window_name, 0, 1, lambda x: None)

    def get_trackbar_values(self):
        """Get the current values of the trackbars."""
        h = cv2.getTrackbarPos("h", self.window_name)
        s = cv2.getTrackbarPos("s", self.window_name)
        v = cv2.getTrackbarPos("v", self.window_name)
        start = cv2.getTrackbarPos("Start", self.window_name)
        return h, s, v, start
