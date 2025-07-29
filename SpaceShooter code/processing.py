import cv2
import imutils
import numpy as np
from sklearn.metrics import pairwise
import time


class FrameProcessor:
    def __init__(self, top, right, bottom, left):
        self.top = top
        self.right = right
        self.bottom = bottom
        self.left = left

    def process_frame(self, frame):
        """Process the frame to extract the region of interest and apply transformations."""
        frame = imutils.resize(frame, width=700)
        frame = cv2.flip(frame, 1)
        roi = frame[self.top : self.bottom, self.left : self.right]
        cv2.rectangle(
            frame, (self.left, self.top), (self.right, self.bottom), (0, 255, 0), 2
        )
        blurred = cv2.GaussianBlur(roi, (11, 11), 0)
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        return frame, roi, hsv


class ContourProcessor:
    def __init__(self, control):
        self.control = control

    def process_contours(self, contours, roi, start):
        cnt = max(contours, key=cv2.contourArea)
        epsilon = 0.0005 * cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, epsilon, True)
        hull = cv2.convexHull(approx)
        cv2.drawContours(roi, [hull], -1, (0, 255, 0), 2)

        extreme_top = tuple(hull[hull[:, :, 1].argmin()][0])
        extreme_bottom = tuple(hull[hull[:, :, 1].argmax()][0])
        extreme_left = tuple(hull[hull[:, :, 0].argmin()][0])
        extreme_right = tuple(hull[hull[:, :, 0].argmax()][0])

        cX = int((extreme_left[0] + extreme_right[0]) / 2)
        cY = int((extreme_top[1] + extreme_bottom[1]) / 2)

        cv2.circle(roi, (cX, cY), 5, (255, 0, 0), 3)
        cv2.circle(roi, extreme_left, 3, (0, 0, 255), 2)
        cv2.circle(roi, extreme_right, 3, (0, 0, 255), 2)

        distances = pairwise.euclidean_distances(
            [(cX, cY)], [extreme_left, extreme_right]
        )[0]
        max_distance = distances[distances.argmax()]

        x1, y1 = extreme_left
        x2, y2 = extreme_right
        slope = float((y2 - y1) / (x2 - x1))

        millis = int(round(time.time() * 1000))
        seconds = millis / 5
        if seconds % 8 == 0:
            print(f"DISTANCE: {round(max_distance, 2)}")
            print(f"SLOPE: {slope}")

        if start > 0:
            annotate = self.control.startControlling(max_distance, slope)
            cv2.putText(
                roi,
                f"Pressed Key: {annotate}",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 0, 255),
                2,
                cv2.LINE_4,
            )

        cv2.imshow("Extreme Points in Convex Hull", roi)
