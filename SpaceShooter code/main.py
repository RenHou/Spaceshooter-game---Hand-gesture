import cv2
import numpy as np
from camera import Camera
from trackbars import Trackbars
from processing import FrameProcessor, ContourProcessor
from control import Control
import threading
import time


class MainApp:
    def __init__(self):
        self.camera = Camera()
        self.control = Control()
        self.contour_processor = ContourProcessor(self.control)
        self.top, self.right, self.bottom, self.left = 0, 700, 525, 240
        self.frame_processor = FrameProcessor(
            self.top, self.right, self.bottom, self.left
        )
        self.trackbars = Trackbars()# this also can change to comment to have one
        self.running = False
        self.gesture_enabled = True
    
    def run(self):
        """Run the gesture control system in a separate thread"""
        if not self.running:
            self.running = True
            self.gesture_thread = threading.Thread(target=self._gesture_loop, daemon=True)
            self.gesture_thread.start()
            print("Hand gesture control started!")

    def _gesture_loop(self):
        """Main gesture control loop"""
        try:
            cap = self.camera.initialize_camera()
            # self.trackbars.create_trackbars()
        
            while self.running:  # <-- use self.running here!
                try:
                    ret, frame = cap.read()
                    if not ret:
                        break

                    frame, roi, hsv = self.frame_processor.process_frame(frame)
                    lower_skin = np.array([0, 41, 141])# follow user camera
                    #azri high lighting (0,41,141)
                    upper_skin = np.array([255, 255, 255])
                    mask = cv2.inRange(hsv, lower_skin, upper_skin)
                    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
                    contours, _ = cv2.findContours(
                        mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
                    )
                    if contours:
                        self.contour_processor.process_contours(contours, roi, 1)

                except Exception as e:
                    print(f"An error occurred: {e}")
                    time.sleep(0.1)

                if cv2.waitKey(5) & 0xFF == 27:
                    break

            self.camera.release_camera()
            cv2.destroyAllWindows()

        except Exception as e:
            print(f"Camera initialization failed: {e}")
            print("Hand gesture control disabled - using keyboard only")

    def stop(self):
        """Stop the gesture control system"""
        self.running = False
        self.gesture_enabled = False
        if hasattr(self, 'gesture_thread'):
            self.gesture_thread.join(timeout=1.0)
        print("Hand gesture control stopped")

    def enable_gestures(self):
        """Enable gesture control"""
        self.gesture_enabled = True
        if not self.running:
            self.run()

    def disable_gestures(self):
        """Disable gesture control"""
        self.gesture_enabled = False
    
    


