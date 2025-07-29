"""
Motion detection using OpenCV for camera-based character control.
"""

import cv2
import numpy as np
import threading
import time

class MotionDetector:
    def __init__(self):
        """Initialize the motion detector."""
        self.camera = None
        self.camera_available = False
        self.background_subtractor = None
        self.frame = None
        self.processed_frame = None
        
        # Motion detection parameters
        self.motion_threshold = 500  # Minimum contour area to consider as motion
        self.learning_rate = 0.01  # Background learning rate
        self.blur_kernel_size = 5
        
        # Motion tracking
        self.last_left_motion = 0
        self.last_right_motion = 0
        self.frame_width = 640
        self.frame_height = 480
        
        # Threading for camera operations
        self.capture_thread = None
        self.stop_capture = False
        
        # Initialize camera
        self._initialize_camera()
    
    def _initialize_camera(self):
        """Initialize the camera and background subtractor."""
        try:
            # Try to initialize camera
            self.camera = cv2.VideoCapture(0)
            
            if not self.camera.isOpened():
                print("Warning: Could not open camera. Motion detection disabled.")
                return
            
            # Set camera properties
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)
            self.camera.set(cv2.CAP_PROP_FPS, 30)
            
            # Test camera by reading a frame
            ret, test_frame = self.camera.read()
            if not ret:
                print("Warning: Could not read from camera. Motion detection disabled.")
                self.camera.release()
                return
            
            # Initialize background subtractor
            self.background_subtractor = cv2.createBackgroundSubtractorMOG2(
                detectShadows=True,
                varThreshold=50,
                history=500
            )
            
            self.camera_available = True
            print("Camera initialized successfully")
            
            # Start capture thread
            self._start_capture_thread()
            
        except Exception as e:
            print(f"Error initializing camera: {e}")
            self.camera_available = False
    
    def _start_capture_thread(self):
        """Start the camera capture thread."""
        if self.camera_available:
            self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
            self.capture_thread.start()
    
    def _capture_loop(self):
        """Main camera capture loop running in separate thread."""
        while not self.stop_capture and self.camera_available:
            try:
                ret, frame = self.camera.read()
                if ret:
                    self.frame = frame
                    self._process_frame(frame)
                else:
                    print("Warning: Failed to read camera frame")
                    break
                    
                # Small delay to prevent excessive CPU usage
                time.sleep(0.01)
                
            except Exception as e:
                print(f"Error in capture loop: {e}")
                break
    
    def _process_frame(self, frame):
        """
        Process camera frame for motion detection.
        
        Args:
            frame: Raw camera frame from OpenCV
        """
        try:
            # Flip frame horizontally for mirror effect
            frame = cv2.flip(frame, 1)
            
            # Apply Gaussian blur to reduce noise
            blurred = cv2.GaussianBlur(frame, (self.blur_kernel_size, self.blur_kernel_size), 0)
            
            # Apply background subtraction
            fg_mask = self.background_subtractor.apply(blurred, learningRate=self.learning_rate)
            
            # Morphological operations to clean up the mask
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
            fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel)
            
            # Find contours
            contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Process motion in left and right halves
            self._analyze_motion(contours, frame.shape)
            
            # Store processed frame for debug visualization
            self.processed_frame = self._create_debug_frame(frame, fg_mask, contours)
            
        except Exception as e:
            print(f"Error processing frame: {e}")
    
    def _analyze_motion(self, contours, frame_shape):
        """
        Analyze motion contours to determine left/right movement.
        
        Args:
            contours: Detected motion contours
            frame_shape: Shape of the camera frame (height, width, channels)
        """
        height, width = frame_shape[:2]
        center_x = width // 2
        
        left_motion = 0
        right_motion = 0
        
        for contour in contours:
            # Filter small contours
            area = cv2.contourArea(contour)
            if area < self.motion_threshold:
                continue
            
            # Get centroid of motion
            moments = cv2.moments(contour)
            if moments["m00"] != 0:
                centroid_x = int(moments["m10"] / moments["m00"])
                
                # Determine which side the motion is on
                if centroid_x < center_x:
                    left_motion += area
                else:
                    right_motion += area
        
        # Update motion values
        self.last_left_motion = left_motion
        self.last_right_motion = right_motion
    
    def _create_debug_frame(self, original_frame, fg_mask, contours):
        """
        Create a debug frame showing motion detection visualization.
        
        Args:
            original_frame: Original camera frame
            fg_mask: Foreground mask from background subtraction
            contours: Detected motion contours
            
        Returns:
            numpy.ndarray: Debug frame for visualization
        """
        # Create a copy of the original frame
        debug_frame = original_frame.copy()
        
        # Draw center line
        height, width = debug_frame.shape[:2]
        center_x = width // 2
        cv2.line(debug_frame, (center_x, 0), (center_x, height), (0, 255, 0), 2)
        
        # Draw motion contours
        for contour in contours:
            area = cv2.contourArea(contour)
            if area >= self.motion_threshold:
                # Draw contour
                cv2.drawContours(debug_frame, [contour], -1, (0, 255, 255), 2)
                
                # Draw bounding rectangle
                x, y, w, h = cv2.boundingRect(contour)
                cv2.rectangle(debug_frame, (x, y), (x + w, y + h), (255, 0, 255), 2)
                
                # Label with area
                cv2.putText(debug_frame, f"A:{int(area)}", (x, y - 10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Add motion indicators
        cv2.putText(debug_frame, f"L: {self.last_left_motion}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        cv2.putText(debug_frame, f"R: {self.last_right_motion}", (width - 100, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        
        return debug_frame
    
    def get_motion_direction(self):
        """
        Get the current motion direction based on detected movement.
        
        Returns:
            tuple: (left_motion, right_motion) motion values, or None if camera unavailable
        """
        if not self.camera_available:
            return None
            
        return (self.last_left_motion, self.last_right_motion)
    
    def get_debug_frame(self):
        """
        Get the current debug frame for visualization.
        
        Returns:
            numpy.ndarray: Debug frame, or None if unavailable
        """
        return self.processed_frame
    
    def update(self):
        """Update method called from main game loop."""
        # This method can be used for any periodic updates if needed
        pass
    
    def cleanup(self):
        """Clean up camera resources."""
        print("Cleaning up camera resources...")
        
        # Stop capture thread
        self.stop_capture = True
        if self.capture_thread and self.capture_thread.is_alive():
            self.capture_thread.join(timeout=1.0)
        
        # Release camera
        if self.camera:
            self.camera.release()
            
        # Clean up OpenCV windows
        cv2.destroyAllWindows()
        
        print("Camera cleanup completed")
