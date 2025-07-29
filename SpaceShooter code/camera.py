import cv2


class Camera:
    def __init__(self):
        self.cap = None

    def initialize_camera(self):
        """Initialize the webcam."""
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            raise Exception("Error: Could not open camera.")
        print("Camera initialized successfully.")
        return self.cap

    def release_camera(self):
        """Release the webcam."""
        if self.cap:
            self.cap.release()
            print("Camera released successfully.")
