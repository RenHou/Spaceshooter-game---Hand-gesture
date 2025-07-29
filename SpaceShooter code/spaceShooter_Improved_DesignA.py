from __future__ import division
import pygame
import random
from os import path
import pyodbc
import time
import sys
import os
import cv2
import threading
from main import MainApp

## assets folder
img_dir = path.join(path.dirname(os.path.abspath(__file__)), 'assets')
sound_folder = path.join(path.dirname(os.path.abspath(__file__)), 'sounds')

###############################
## to be placed in "constant.py" later
WIDTH = 400
HEIGHT = 600
FPS = 60
POWERUP_TIME = 5000
BAR_LENGTH = 100
BAR_HEIGHT = 10

# Define Colors 
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
LIGHTGREEN = (38,125,128)
LIGHTGRAY = (220, 220, 220)
BLUE = (0, 120, 215)
TEAL = (0, 128, 128)
#new added constant 
StartButton = pygame.Rect(146, 326,115,50)
LeaderboardButton = pygame.Rect(126, 412,158,50)
CloseButton = pygame.Rect(142, 550,115,28)
Top6AndNewScoreList = []
SaveButon = pygame.Rect(66,347,101,36)
NoButton = pygame.Rect(220,347,101,36)
# Hand detection dialog buttons
TryAgainButton = pygame.Rect(100, 400, 80, 35)
CancelButton = pygame.Rect(220, 400, 80, 35)
# global score
score=0
mobs = pygame.sprite.Group()
max_mobs=10
gesture_app = None
level_shown = 1
level_display_time = 0
current_level_image = None
###############################

###############################
## to placed in "__init__.py" later
## initialize pygame and creagamete window
pygame.init()
pygame.mixer.init()  ## For sound
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Shooter")
clock = pygame.time.Clock()     ## For syncing the FPS
###############################
# new added constant
gold_image = pygame.image.load(path.join(img_dir, 'gold.png')).convert()
silver_image = pygame.image.load(path.join(img_dir, 'silver.png')).convert()
bronze_image = pygame.image.load(path.join(img_dir, 'bronze.png')).convert()
gold_image = pygame.transform.scale(gold_image,(33,49))
gold_image.set_colorkey(BLACK)
silver_image = pygame.transform.scale(silver_image,(33,49))
silver_image.set_colorkey(BLACK)
bronze_image = pygame.transform.scale(bronze_image,(33,49))
bronze_image.set_colorkey(BLACK)

font_name = pygame.font.match_font('Arial')

class HandDetector:
    def __init__(self):
        self.cap = None
        self.detection_running = False
        self.object_detected = False
        self.detection_thread = None
    
    def start_detection(self):
        """Start camera and object detection"""
        if not self.detection_running:
            self.detection_running = True
            self.object_detected = False
            
            # Start camera immediately in main thread to ensure it opens
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                print("Error: Could not open camera")
                self.detection_running = False
                return False
            
            # Set camera properties for faster detection
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)  # Smaller resolution for speed
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
            self.cap.set(cv2.CAP_PROP_FPS, 15)  # Lower FPS for speed
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer lag
            
            # Start detection thread
            self.detection_thread = threading.Thread(target=self._detect_objects)
            self.detection_thread.daemon = True
            self.detection_thread.start()
            return True
        return False
    
    def stop_detection(self):
        """Stop camera detection"""
        self.detection_running = False
        if self.detection_thread:
            self.detection_thread.join(timeout=1.0)
        if self.cap:
            self.cap.release()
            self.cap = None
        print("Camera stopped")
    
    def _detect_objects(self):
        """Fast object detection using simplified motion detection"""
        try:
            if not self.cap or not self.cap.isOpened():
                return
            
            print("Camera detection started - camera light should be ON")
            
            # Quick warmup - just 3 frames
            for i in range(3):
                ret, frame = self.cap.read()
                if not ret:
                    print("Could not read frame during warmup")
                    return
                time.sleep(0.05)
            
            # Get baseline frame
            ret, prev_frame = self.cap.read()
            if not ret:
                print("Could not read baseline frame")
                return
            
            # Resize for faster processing
            prev_frame = cv2.resize(prev_frame, (160, 120))
            prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
            prev_gray = cv2.GaussianBlur(prev_gray, (5, 5), 0)  # Smaller kernel for speed
            
            detection_count = 0
            
            while self.detection_running and self.cap and self.cap.isOpened():
                ret, frame = self.cap.read()
                if not ret:
                    break
                
                # Resize for faster processing
                frame = cv2.resize(frame, (160, 120))
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                gray = cv2.GaussianBlur(gray, (5, 5), 0)
                
                # Simple frame difference
                frame_diff = cv2.absdiff(prev_gray, gray)
                thresh = cv2.threshold(frame_diff, 25, 255, cv2.THRESH_BINARY)[1]
                
                # Count motion pixels
                motion_pixels = cv2.countNonZero(thresh)
                
                # Lower threshold for faster detection
                if motion_pixels > 200:  # Much lower threshold
                    detection_count += 1
                    print(f"Motion detected! Pixels: {motion_pixels}, Count: {detection_count}")
                    
                    # Detect faster - only need 2 detections
                    if detection_count >= 2:
                        self.object_detected = True
                        print("Object confirmed - stopping detection")
                        break
                
                # Update baseline more frequently
                prev_gray = gray.copy()
                
                time.sleep(0.05)  # Faster polling
            
        except Exception as e:
            print(f"Camera detection error: {e}")
            self.detection_running = False
        finally:
            print("Detection thread finished")

def check_camera_permissions():
    """Check if camera is available and accessible"""
    try:
        # Try to open camera briefly to check if it's available
        test_cap = cv2.VideoCapture(0)
        if test_cap.isOpened():
            # Read one frame to verify camera works
            ret, frame = test_cap.read()
            test_cap.release()
            return ret  # Return True if we successfully read a frame
        else:
            test_cap.release()
            return False
    except Exception as e:
        print(f"Camera permission check failed: {e}")
        return False

def show_camera_error_dialog():
    """Show camera error dialog when camera is not available"""
    bg_image = pygame.image.load(path.join(img_dir, "MainPageBackground.png")).convert()
    bg_image = pygame.transform.scale(bg_image, (WIDTH, HEIGHT))
    
    # Button dimensions
    button_width = 100
    button_height = 40
    ok_btn = pygame.Rect(WIDTH/2 - button_width/2, 400, button_width, button_height)
    
    while True:
        # Draw space background
        screen.blit(bg_image, (0, 0))
        
        # Draw title at the top (moved down a bit for consistency)
        draw_text(screen, "SPACE SHOOTER", 35, WIDTH/2, 100, color=WHITE)
        
        # Draw dialog box
        dialog_rect = pygame.Rect(50, 180, WIDTH-100, 280)
        pygame.draw.rect(screen, WHITE, dialog_rect)
        pygame.draw.rect(screen, BLACK, dialog_rect, 3)
        
        # Error icon (X mark)
        error_center = (WIDTH/2, 240)
        error_size = 30
        pygame.draw.circle(screen, RED, error_center, error_size//2)
        pygame.draw.circle(screen, BLACK, error_center, error_size//2, 2)
        
        # Draw X
        offset = error_size//4
        pygame.draw.line(screen, WHITE, 
                        (error_center[0] - offset, error_center[1] - offset),
                        (error_center[0] + offset, error_center[1] + offset), 3)
        pygame.draw.line(screen, WHITE,
                        (error_center[0] + offset, error_center[1] - offset),
                        (error_center[0] - offset, error_center[1] + offset), 3)
        
        # Error message
        draw_text(screen, "CAMERA ERROR", 20, WIDTH/2, 290, color=RED)
        draw_text(screen, "Camera not available", 14, WIDTH/2, 320, color=BLACK)
        draw_text(screen, "Check camera permissions", 14, WIDTH/2, 340, color=BLACK)
        
        # OK Button
        pygame.draw.rect(screen, TEAL, ok_btn)
        pygame.draw.rect(screen, BLACK, ok_btn, 2)
        draw_text(screen, "OK", 14, ok_btn.centerx, ok_btn.centery, color=WHITE)
        
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                if ok_btn.collidepoint(mouse_pos):
                    return True  # Start game anyway without camera
        
        pygame.display.update()
        clock.tick(FPS)

def show_hand_detected_success():
    """Show success message when object is detected"""
    print("Showing hand detection success message")
    for i in range(60):  # Show for 1 second at 60 FPS
        screen.fill(BLACK)
        
        # Success message
        draw_text(screen, "OBJECT DETECTED!", 40, WIDTH/2, HEIGHT/2 - 50, color=GREEN)
        draw_text(screen, "Starting game...", 20, WIDTH/2, HEIGHT/2 + 20, color=WHITE)
        
        # Simple loading animation
        dots = "." * ((i // 10) % 4)
        draw_text(screen, f"Loading{dots}", 16, WIDTH/2, HEIGHT/2 + 60, color=LIGHTGRAY)
        
        pygame.display.update()
        clock.tick(60)
    
    print("Success message completed")

def show_hand_detection_dialog():
    """Show hand detection dialog with timeout and styled error message"""
    if not check_camera_permissions():
        return show_camera_error_dialog()
    
    # Initialize hand detector
    detector = HandDetector()
    if not detector.start_detection():
        return show_camera_error_dialog()
    
    bg_image = pygame.image.load(path.join(img_dir, "MainPageBackground.png")).convert()
    bg_image = pygame.transform.scale(bg_image, (WIDTH, HEIGHT))
    
    # Detection parameters - reduced timeout for faster experience
    detection_timeout = 8000  # 8 seconds timeout
    start_time = pygame.time.get_ticks()
    dots_animation = 0
    
    print("Hand detection dialog started - camera should be active now")
    
    while True:
        current_time = pygame.time.get_ticks()
        elapsed_time = current_time - start_time
        
        # Check if timeout reached
        if elapsed_time > detection_timeout:
            print("Detection timeout reached")
            detector.stop_detection()
            return show_styled_no_hand_detection_dialog()
        
        # Check if object detected
        if detector.object_detected:
            print("Object detected - showing success")
            detector.stop_detection()
            show_hand_detected_success()
            return True  # This will start the game
        
        # Draw background
        screen.blit(bg_image, (0, 0))
        
        # Draw semi-transparent overlay
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(150)
        overlay.fill(BLACK)
        screen.blit(overlay, (0, 0))
        
        # Draw title (moved down a bit for consistency)
        draw_text(screen, "SPACE SHOOTER", 35, WIDTH/2, 120, color=WHITE)
        
        # Draw detection dialog
        dialog_rect = pygame.Rect(50, 180, WIDTH-100, 280)
        pygame.draw.rect(screen, WHITE, dialog_rect)
        pygame.draw.rect(screen, BLACK, dialog_rect, 3)
        
        # Animate dots for "Detecting..."
        dots_animation += 1
        dots_count = (dots_animation // 20) % 4  # Faster animation
        dots_text = "." * dots_count
        
        # Messages
        draw_text(screen, "OBJECT DETECTION", 24, WIDTH/2, 220, color=BLACK)
        draw_text(screen, f"Detecting{dots_text}", 18, WIDTH/2, 260, color=BLUE)
        draw_text(screen, "Wave your hand in front of camera", 14, WIDTH/2, 290, color=BLACK)
        
        # Progress bar
        progress_width = 200
        progress_height = 8
        progress_x = WIDTH/2 - progress_width/2
        progress_y = 320
        
        # Background of progress bar
        pygame.draw.rect(screen, LIGHTGRAY, (progress_x, progress_y, progress_width, progress_height))
        
        # Progress fill
        progress_fill = (elapsed_time / detection_timeout) * progress_width
        pygame.draw.rect(screen, BLUE, (progress_x, progress_y, progress_fill, progress_height))
        
        # Time remaining
        remaining_time = max(0, (detection_timeout - elapsed_time) // 1000)
        draw_text(screen, f"Time: {remaining_time}s", 12, WIDTH/2, 345, color=BLACK)
        
        
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                detector.stop_detection()
                pygame.quit()
                quit()
        
        pygame.display.update()
        clock.tick(FPS)

def show_styled_no_hand_detection_dialog():
    """Show styled 'NO OBJECT DETECTION' dialog"""
    bg_image = pygame.image.load(path.join(img_dir, "MainPageBackground.png")).convert()
    bg_image = pygame.transform.scale(bg_image, (WIDTH, HEIGHT))
    warning_image = pygame.image.load(path.join(img_dir,"warningSign.png")).convert()
    warning_image= pygame.transform.scale(warning_image,(75,42))
    warning_image.set_colorkey('BLACK')
    # Button dimensions
    button_width = 100
    button_height = 40
    try_again_btn = pygame.Rect(WIDTH/2 - button_width - 10, 400, button_width, button_height)
    cancel_btn = pygame.Rect(WIDTH/2 + 10, 400, button_width, button_height)
    
    while True:
        # Draw space background
        screen.blit(bg_image, (0, 0))
        
        # Draw title lower to avoid overlap with spaceships - moved from y=100 to y=130
        draw_text(screen, "SPACE SHOOTER", 35, WIDTH/2, 130, color=WHITE)
        
        # Draw9 dialog box
        dialog_rect = pygame.Rect(50, 180, WIDTH-100, 280)
        pygame.draw.rect(screen, WHITE, dialog_rect)
        pygame.draw.rect(screen, BLACK, dialog_rect, 3)

        screen.blit(warning_image, (162, 215))

        
        # Error message
        draw_text(screen, "NO OBJECT DETECTION", 20, WIDTH/2, 280, color=RED)
        draw_text(screen, "No movement detected", 14, WIDTH/2, 320, color=BLACK)
        
        # Buttons
        pygame.draw.rect(screen, TEAL, try_again_btn)
        pygame.draw.rect(screen, RED, cancel_btn)  # Red for cancel
        pygame.draw.rect(screen, BLACK, try_again_btn, 2)
        pygame.draw.rect(screen, BLACK, cancel_btn, 2)
        
        # Button text
        draw_text(screen, "Try Again", 14, try_again_btn.centerx, 410, color=WHITE)
        draw_text(screen, "Cancel", 14, cancel_btn.centerx, 410, color=WHITE)
        
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                if try_again_btn.collidepoint(mouse_pos):
                    return show_hand_detection_dialog()  # Try again
                elif cancel_btn.collidepoint(mouse_pos):
                    return False  # Cancel - return to main menu or exit
        
        pygame.display.update()
        clock.tick(FPS)

def show_tutorial_mode():
    """Tutorial mode for hand gestures - uses specific background images for each step"""
    print("Starting tutorial mode...")
     # Draw the initial tutorial background before starting gesture detection
    initial_bg = pygame.image.load(path.join(img_dir, "tm_hold.png")).convert()
    initial_bg = pygame.transform.scale(initial_bg, (WIDTH, HEIGHT))
    screen.blit(initial_bg, (0, 0))
    pygame.display.update()
    pygame.time.wait(500)  # Optional: short pause to let the user see the background

    gesture_app= MainApp()
    gesture_app.run()
    
    # Tutorial steps with corresponding background files
    tutorial_steps = [
        {
            "title": "Hold to stay",
            "instruction": "Keep your hand steady in front of camera",
            "gesture_type": "hold",
            "background": "tm_hold.png"
        },
        {
            "title": "Try to move left", 
            "instruction": "Move your hand to the left",
            "gesture_type": "left",
            "background": "tm_left.png"
        },
        {
            "title": "Try to move right",
            "instruction": "Move your hand to the right", 
            "gesture_type": "right",
            "background": "tm_right.png"
        }
    ]
    
    current_step = 0    
    current_bg_image = None
    
    print(f"Tutorial started with {len(tutorial_steps)} steps")

    left_detected = False
    right_detected = False

    while current_step < len(tutorial_steps):
        step_completed = False        
        current_tutorial = tutorial_steps[current_step]
        
        # Load background image for current step if not already loaded
        if current_bg_image is None or current_step < len(tutorial_steps):
            try:
                current_bg_image = pygame.image.load(path.join(img_dir, current_tutorial["background"])).convert()
                current_bg_image = pygame.transform.scale(current_bg_image, (WIDTH, HEIGHT))
                print(f"Loaded background: {current_tutorial['background']}")
            except pygame.error as e:
                print(f"Could not load background {current_tutorial['background']}: {e}")
                # Fall back to black background if image not found
                current_bg_image = pygame.Surface((WIDTH, HEIGHT))
                current_bg_image.fill(BLACK)

        keystate = pygame.key.get_pressed()  

        # Draw tutorial interface
        screen.fill(BLACK)
        
        # Draw the specific background for current step
        screen.blit(current_bg_image, (0, 0))
        
        # Draw step indicator
        draw_text(screen, f"Step {current_step + 1} of {len(tutorial_steps)}", 14, WIDTH/2, HEIGHT - 50, color=WHITE)
        
        # For movement gestures, use direction detection
        if current_tutorial["gesture_type"] == "hold":
            pygame.time.wait(6000)
            step_completed = True
        elif current_tutorial["gesture_type"] == "left":
            # Try to get a frame from the camera
            if not left_detected and keystate[pygame.K_LEFT]:
                step_completed = True
        elif current_tutorial["gesture_type"] == "right": 
            # Try to get a frame from the camera
            if not right_detected and keystate[pygame.K_RIGHT]:
                step_completed = True
        
        # Move to next step if current one is completed
        if step_completed:
            print(f"Step {current_step + 1} completed: {current_tutorial['title']}")
            current_step += 1
            step_start_time = pygame.time.get_ticks()
            step_completed = False
            current_bg_image = None  # Force reload of next background
            
            # Add small delay between steps
            pygame.time.wait(1000)
            continue

        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                gesture_app.stop_detection()
                pygame.quit()
                quit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    gesture_app.stop_detection()
                    pygame.quit()
                    quit()
        
        pygame.display.update()
        clock.tick(FPS)
    
    # All steps completed - show completion screen
    show_tutorial_completion()
    return True

def show_tutorial_completion():
    """Show tutorial completion message using tm_done.png background"""
    try:
        bg_image = pygame.image.load(path.join(img_dir, "tm_done.png")).convert()
        bg_image = pygame.transform.scale(bg_image, (WIDTH, HEIGHT))
        print("Loaded completion background: tm_done.png")
    except pygame.error as e:
        print(f"Could not load tm_done.png: {e}")
        # Fall back to space background if tm_done.png not found
        bg_image = pygame.image.load(path.join(img_dir, "MainPageBackground.png")).convert()
        bg_image = pygame.transform.scale(bg_image, (WIDTH, HEIGHT))
    
    # Show completion message for 3 seconds
    start_time = pygame.time.get_ticks()
    
    while pygame.time.get_ticks() - start_time < 3000:  # 3 seconds
        screen.fill(BLACK)
        screen.blit(bg_image, (0, 0))
  
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
        
        pygame.display.update()
        clock.tick(FPS)
    
    print("Tutorial completed successfully!")

def draw_text(surf, text, size, x, y, color=WHITE, bold=False):
    """Helper function to draw text on screen with optional bold"""
    font = pygame.font.Font(font_name, size)
    if bold:
        font.set_bold(True)
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect()
    text_rect.center = (x, y)
    surf.blit(text_surface, text_rect)

def main_menu():
    global screen, gesture_app
    gesture_app = MainApp()  # Initialize the hand gesture app
    # Load and play menu music
    menu_song = pygame.mixer.music.load(path.join(sound_folder, "menu.ogg"))
    pygame.mixer.music.play(-1)  # Loop indefinitely

    # Load the title/background image
    title = pygame.image.load(path.join(img_dir, "MainPageBackground.png")).convert()
    title = pygame.transform.scale(title, (WIDTH, HEIGHT))
    
    # Create buttons with adjusted sizes and positions to match images
    start_button = pygame.Rect(WIDTH/2 - 80, HEIGHT/2.5+92, 158, 50)
    leaderboard_button = pygame.Rect(WIDTH/2 - 80, HEIGHT/2 + 115, 158, 50)
    
    # Define tutorial checkbox rect for both display and click detection
    tutorial_checkbox_rect = pygame.Rect(WIDTH/2 + 60, HEIGHT/3 + 60, 25, 25)
    
    # Hand gesture toggle options
    gesture_toggle = True
    tutorial_toggle = False
    
    while True:
        screen.blit(title, (0, 0))
        
        # Draw "SPACE SHOOTER" text at the top
        draw_text(screen, "SPACE SHOOTER", 35, WIDTH/2, HEIGHT/5.5)
        
        # Draw hand gesture options
        draw_text(screen, "Use Hand Gestures", 24, WIDTH/2 - 57, HEIGHT/3.3+5)
        
        # Draw ON/OFF toggle for gestures with colors matching the bright green in images
        if gesture_toggle:
            # Green toggle - ON
            pygame.draw.rect(screen, (0, 255, 0), (WIDTH/2 + 60, HEIGHT/3 - 10, 52, 25))
            pygame.draw.circle(screen, WHITE, (WIDTH/2 + 103, HEIGHT/3 + 2), 14)
            # Display "ON" text inside the toggle - using bold
            draw_text(screen, "ON", 15, WIDTH/2 + 74, HEIGHT/3 - 8, bold=True)
            # Display Hand Gesture mode text when toggle is ON
            draw_text(screen, "Mode: Hand Gesture mode", 24, WIDTH/2-25, HEIGHT/3.3+40)
            
            # Only show tutorial mode checkbox when in Hand Gesture mode
            draw_text(screen, "Tutorial Mode", 24, WIDTH/2 - 85, HEIGHT/3 + 60)
            
            # Draw the checkbox outline
            pygame.draw.rect(screen, WHITE, tutorial_checkbox_rect, 15)
            
            # Draw checkmark if tutorial mode is enabled
            if tutorial_toggle:
                # Draw a proper checkmark inside the checkbox
                start_pos = (tutorial_checkbox_rect.x + 5, tutorial_checkbox_rect.y + 12)
                mid_pos = (tutorial_checkbox_rect.x + 10, tutorial_checkbox_rect.y + 17)
                end_pos = (tutorial_checkbox_rect.x + 20, tutorial_checkbox_rect.y + 7)
                
                # Draw the checkmark as a polyline
                pygame.draw.lines(screen, BLACK, False, [start_pos, mid_pos, end_pos], 3)
        else:
            # Gray toggle - OFF
            pygame.draw.rect(screen, (100, 100, 100), (WIDTH/2 + 60, HEIGHT/3 - 10, 52, 25))
            pygame.draw.circle(screen, WHITE, (WIDTH/2 + 70, HEIGHT/3 + 2), 14)
            # Display "OFF" text inside the toggle - using bold
            draw_text(screen, "OFF", 14, WIDTH/2 + 98, HEIGHT/3 - 8, bold=True)
            # Display Keyboard Mode text when toggle is OFF
            draw_text(screen, "Mode: Keyboard mode", 24, WIDTH/2-43, HEIGHT/3.3+40)
            # Tutorial mode is hidden in Keyboard Mode
        
        # Draw buttons with teal color (0, 128, 128) as shown in images
        pygame.draw.rect(screen, TEAL, start_button)
        pygame.draw.rect(screen, TEAL, leaderboard_button)

        # Button text in white
        draw_text(screen, "Start", 30, WIDTH/2, HEIGHT/2 + 40)
        draw_text(screen, "Leaderboard", 30, WIDTH/2, HEIGHT/2 + 120)
        
        # Draw "Press Q to exit the game" at the bottom of the screen with brackets around Q
        draw_text(screen, "Press [Q] To Exit the game", 25, WIDTH/2, HEIGHT - 50)
            
        # Process events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if gesture_app:
                    gesture_app.stop()
                pygame.quit()
                quit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    if gesture_app:
                        gesture_app.stop()
                    pygame.quit()
                    quit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                    
                # Check if Start button clicked
                if start_button.collidepoint(mouse_pos):
                    if gesture_toggle:
                        # Check if tutorial mode is enabled
                        if tutorial_toggle:
                            # Start tutorial mode first
                            gesture_app.run()
                            tutorial_success = show_tutorial_mode()
                            if tutorial_success:
                                return gesture_toggle
                            else:
                                # Tutorial was cancelled, return to main menu
                                continue
                        else:
                            # Show hand detection dialog before starting gesture mode (no tutorial)
                            if show_hand_detection_dialog():
                                if gesture_app:
                                    gesture_app.run()
                                return gesture_toggle
                            else:
                                # User cancelled or hand detection failed
                                continue
                    else:
                        # Start keyboard mode directly
                        return gesture_toggle
                        
                # Check if Leaderboard button clicked
                if leaderboard_button.collidepoint(mouse_pos):
                    # Show leaderboard (functionality to be added)
                    displayLeaderboard()
                    screen.blit(title, (0, 0))
                    pygame.display.update()

                # Check if gesture toggle clicked
                if WIDTH/2 + 60 <= mouse_pos[0] <= WIDTH/2 + 100 and HEIGHT/3 - 10 <= mouse_pos[1] <= HEIGHT/3 + 15:
                    gesture_toggle = not gesture_toggle
                
                # Check if tutorial checkbox clicked (only when in Hand Gesture mode)
                if gesture_toggle and tutorial_checkbox_rect.collidepoint(mouse_pos):
                    tutorial_toggle = not tutorial_toggle
        pygame.display.update()
        clock.tick(FPS)
    
def getReady():
    # Play ready sound before starting the game
    ready = pygame.mixer.Sound(path.join(sound_folder, 'getready.ogg'))
    ready.play()
    screen.fill(BLACK)
    draw_text(screen, "GET READY!", 40, WIDTH/2, HEIGHT/2)
    pygame.display.update()

def draw_text(surf, text, size, x, y, bold=False,color=WHITE, align="midtop"):
    font = pygame.font.Font(font_name, size)
    font.set_bold(bold)

    lines = text.split('\n')
    y_offset = 0

    for line in lines:
        text_surface = font.render(line, True, color)
        text_rect = text_surface.get_rect()
        setattr(text_rect, align, (x, y + y_offset))
        surf.blit(text_surface, text_rect)
        y_offset += text_surface.get_height() + 5

def draw_shield_bar(surf, x, y, pct):
    pct = max(pct, 0) 
    fill = (pct / 100) * BAR_LENGTH
    outline_rect = pygame.Rect(x, y, BAR_LENGTH, BAR_HEIGHT)
    fill_rect = pygame.Rect(x, y, fill, BAR_HEIGHT)
    pygame.draw.rect(surf, GREEN, fill_rect)
    pygame.draw.rect(surf, WHITE, outline_rect, 2)


def draw_lives(surf, x, y, lives, img):
    for i in range(lives):
        img_rect= img.get_rect()
        img_rect.x = x + 30 * i
        img_rect.y = y
        surf.blit(img, img_rect)

def draw_button(surf,text,text_color,size,button_color,button_rect):
    pygame.draw.rect(surf, button_color, button_rect)
    font = pygame.font.Font(font_name,size)
    text = font.render(text, True, text_color)
    text_rect = text.get_rect(center=button_rect.center)
    surf.blit(text, text_rect)

def newmob(mobs):
    global score
    global max_mobs

    if len(mobs) >= max_mobs:  
        return
    
    if score >= 10000:
        kind_list = ['normal','blue','green','pink']
        max_mobs=25
    elif score >= 5000:
        kind_list = ['normal','blue','green']
        max_mobs=20
    elif score >= 2000:
        kind_list = ['normal','blue']
        max_mobs=15
    else:
        kind_list = ['normal']
        max_mobs=10

    chosen_kind = random.choice(kind_list)
    mob_element = Mob(chosen_kind)
    all_sprites.add(mob_element)
    mobs.add(mob_element)

def displayLeaderboard():

    menu_song = pygame.mixer.music.load(path.join(sound_folder, "menu.ogg"))
    pygame.mixer.music.play(-1)

    title = pygame.image.load(path.join(img_dir, "LeaderboardBackground2.png")).convert()
    title = pygame.transform.scale(title, (WIDTH, HEIGHT), screen)

    screen.blit(title, (0,0))
    pygame.display.update()

    while True:
        ev = pygame.event.poll()
        if ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_q:
                pygame.quit()
                quit()
        elif ev.type == pygame.QUIT:
                pygame.quit()
                quit() 
        elif ev.type == pygame.MOUSEBUTTONDOWN:
            if CloseButton.collidepoint(ev.pos):
                return
        else:
            draw_button(screen,"Close",BLACK,16, (217,217,217),CloseButton)
            displayRanking()
            pygame.display.update()

def displayRanking():
    latestPlayerRanking =updateTop6AndNew()
    start_y = 215
    spacing = 47
    if not Top6AndNewScoreList:
        draw_text(screen, "No records found", 24, WIDTH // 2, start_y, color=WHITE)
        pygame.display.update()
        return
    
    for i, row in enumerate(Top6AndNewScoreList):
        name = row.name
        point = row.score 
        point_str = str(point)
        y = start_y + i * spacing

        if i == 0:
            screen.blit(gold_image, (53, y - 14))  # adjust -14 for medal center align
        elif i == 1:
            screen.blit(silver_image, (53, y - 14))
        elif i == 2:
            screen.blit(bronze_image, (53, y - 14))
        elif i==6:
            draw_text(screen, f"{latestPlayerRanking}th", 18, 70, y)
            newBatch = pygame.image.load(path.join(img_dir, 'newbatch.png')).convert()
            newBatch = pygame.transform.scale(newBatch,(52,29))
            newBatch.set_colorkey(BLACK)
            screen.blit(newBatch,(18,y-14))
        else:
            draw_text(screen, f"{i+1}th", 18, 70, y)
        
        draw_text(screen, name, 18, 130, y,align='topleft')
        draw_text(screen, point_str, 18, 260, y,align='topleft')


def updateTop6AndNew():
    conn = pyodbc.connect(
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=localhost;'
    'DATABASE=LeaderboardSpaceShooter;'
    'Trusted_Connection=yes;'
    )
    cursor = conn.cursor()
    # Run a query
    cursor.execute("SELECT [username],[score] FROM Leaderboard ORDER BY [score] DESC")    
    data = cursor.fetchall()
    Top6AndNewScoreList.clear()
    size = min(len(data), 6)
    for i in range(size):
        row = data[i]
        username= row[0]
        score = row[1]
        playerRecord = PlayerRecord(username,score)
        playerRecord.notNew()
        Top6AndNewScoreList.append(playerRecord)

    cursor.execute('SELECT TOP (1) [username],[score] FROM Leaderboard ORDER BY [saveTime] DESC')   
    lastestUser= cursor.fetchone()

    if lastestUser is None:
        conn.close()
        return 0  # No records in the table
    
    username= lastestUser[0]
    score = lastestUser[1]
    playerRecord = PlayerRecord(username,score)
    
    conn.close
    # Add the latest player to the list if they're not already present
    if not any(record.name == playerRecord.name for record in Top6AndNewScoreList):
        Top6AndNewScoreList.append(playerRecord)
        
        for i,row in enumerate(data): 
            username= row[0]
            if username == playerRecord.name:
                return i+1
            i+=1
    return 0


def saveRecord(score):
    title = pygame.image.load(path.join(img_dir, "LeaderboardBackground1.png")).convert()
    title = pygame.transform.scale(title, (WIDTH, HEIGHT), screen)
    message_rect = pygame.Rect(0, HEIGHT - 90, WIDTH, 40)
    message_bg = title.subsurface(message_rect).copy()
    message = ''
    screen.blit(title, (0, 0))
    pygame.display.update()

    saveNameRect = pygame.Rect(66, 188, 254, 109)
    user_text = ''
    active = False

    while True:
        
        screen.blit(title, (0, 0))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if saveNameRect.collidepoint(event.pos):
                    active = True
                if SaveButon.collidepoint(event.pos):
                    if user_text != '':
                        if not checkDuplicateName(user_text):
                            AddRecordInDatabase(user_text, score)
                            displayLeaderboard()
                            return
                        else:
                            message = 'The name has been used'
                    else:
                        message = 'Please key in your name'
                if NoButton.collidepoint(event.pos):
                    displayLeaderboard()
                    return

            elif event.type == pygame.KEYDOWN:
                if active:
                    if event.key == pygame.K_BACKSPACE:
                        user_text = user_text[:-1]
                    else:
                        if len(user_text) < 10 and event.unicode:
                            user_text += event.unicode

        # Draw input background box
        pygame.draw.rect(screen, LIGHTGREEN, saveNameRect)
        draw_text(screen, 'Save Your Name', 20, saveNameRect.centerx, 209)

        # Draw input area (clear text zone)
        input_rect = pygame.Rect(saveNameRect.x + 10, saveNameRect.y + saveNameRect.height - 50,
                                 saveNameRect.width - 20, 30)
        pygame.draw.rect(screen, LIGHTGREEN, input_rect)

        # Draw input border
        pygame.draw.line(
            screen,
            BLUE if active else WHITE,
            (saveNameRect.x + 15, saveNameRect.y + saveNameRect.height - 22),
            (saveNameRect.x + saveNameRect.width - 15, saveNameRect.y + saveNameRect.height - 22),
            3
        )

        # Draw buttons
        draw_button(screen, 'Save', BLACK, 20, WHITE, SaveButon)
        draw_button(screen, 'No', BLACK, 20, WHITE, NoButton)

        # Draw user-typed name
        if user_text:
            font = pygame.font.Font(font_name, 16)
            text_surface = font.render(user_text, True, WHITE)
            text_rect = text_surface.get_rect()
            text_rect.left = saveNameRect.x + 20
            text_rect.centery = saveNameRect.y + saveNameRect.height - 35

            max_width = saveNameRect.width - 40
            if text_rect.width > max_width:
                clipped_surface = pygame.Surface((max_width, text_rect.height))
                clipped_surface.blit(text_surface, (0, 0))
                screen.blit(clipped_surface, text_rect)
            else:
                screen.blit(text_surface, text_rect)

        
        if message:
            screen.blit(message_bg, message_rect)  
            draw_text(screen, message, 20, WIDTH / 2, HEIGHT - 70, True)
                

        pygame.display.update()
        clock.tick(FPS)


def AddRecordInDatabase(name, score):
    saveTime = int(time.time())
    
    try:
        conn = pyodbc.connect(
            'DRIVER={ODBC Driver 17 for SQL Server};'
            'SERVER=localhost;'
            'DATABASE=LeaderboardSpaceShooter;'
            'Trusted_Connection=yes;'
        )
        cursor = conn.cursor()
        
        # Fixed: Parameters should be passed as a tuple
        cursor.execute('INSERT INTO Leaderboard VALUES(?,?,?)', (name, score, saveTime))
        
        # Important: Commit the transaction
        conn.commit()
        
        print(f"Record added successfully: {name}, {score}, {saveTime}")
        
    except pyodbc.Error as e:
        print(f"Database error: {e}")
        
    finally:
        cursor.close()
        conn.close()

def checkDuplicateName(name):
    conn = pyodbc.connect(
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=localhost;'
    'DATABASE=LeaderboardSpaceShooter;'
    'Trusted_Connection=yes;'
    )
    cursor = conn.cursor()

    # Run a query
    cursor.execute('SELECT username FROM Leaderboard WHERE username=?',name)
    result = cursor.fetchone()
    conn.close()  # close the connection
    
    # Return True if name exists (duplicate), False if no results (name is available)
    return result is not None

def show_game_over():
    game_over_text = pygame.font.Font(font_name, 50).render("GAME OVER", True, WHITE)
    text_rect = game_over_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))

    screen.blit(background, background_rect)  
    all_sprites.draw(screen)  
    screen.blit(game_over_text, text_rect)
    pygame.display.flip()

    pygame.time.wait(1500) 
    
class PlayerRecord():
    def __init__(self,username,score):
        self.name =username
        self.score =score
        self.new = True

    def notNew(self):
        self.new = False 

class Explosion(pygame.sprite.Sprite):
    def __init__(self, center, size):
        pygame.sprite.Sprite.__init__(self)
        self.size = size
        self.image = explosion_anim[self.size][0]
        self.rect = self.image.get_rect()
        self.rect.center = center
        self.frame = 0 
        self.last_update = pygame.time.get_ticks()
        self.frame_rate = 75

    def update(self):
        now = pygame.time.get_ticks()
        if now - self.last_update > self.frame_rate:
            self.last_update = now
            self.frame += 1
            if self.frame == len(explosion_anim[self.size]):
                self.kill()
            else:
                center = self.rect.center
                self.image = explosion_anim[self.size][self.frame]
                self.rect = self.image.get_rect()
                self.rect.center = center


class Player(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        ## scale the player img down
        self.image = pygame.transform.scale(player_img, (50, 38))
        self.image.set_colorkey(BLACK)
        self.rect = self.image.get_rect()
        self.radius = 20
        self.rect.centerx = WIDTH / 2
        self.rect.bottom = HEIGHT - 35
        self.speedx = 0 
        self.shield = 100
        self.shoot_delay = 400
        self.last_shot = pygame.time.get_ticks()
        self.lives = 1
        self.hidden = False
        self.hide_timer = pygame.time.get_ticks()
        self.power = 1
        self.power_timer = pygame.time.get_ticks()
        self.max_health = 100  
        self.health = self.max_health

    def adjust_health_cap(self, score):
        if score >= 10000:
            self.max_health = 200
        elif score >= 5000:
            self.max_health = 150
        elif score >= 2000:
            self.max_health = 125
        else:
            self.max_health = 100

        if self.health > self.max_health:
                self.health = self.max_health
        
    def adjust_size(self, score):
        if score >= 10000:
            scale = (150, 108)
            offset_y = 7
        elif score >= 5000:
            scale = (120, 87)
            offset_y = 5
        elif score >= 2000:
            scale = (90, 66)
            offset_y = 2
        else:
            scale = (50, 38)
            offset_y = 0

        if self.image.get_size() != scale:
            self.image = pygame.transform.scale(player_img, scale)
            self.image.set_colorkey(BLACK)
            old_centerx = self.rect.centerx
            self.rect = self.image.get_rect()
            self.rect.centerx = old_centerx
            self.rect.bottom = HEIGHT - 40 - offset_y  
            self.radius = int(self.rect.width * 0.45)

    def update(self):
        ## time out for powerups
        if self.power >=2 and pygame.time.get_ticks() - self.power_time > POWERUP_TIME:
            self.power -= 1
            self.power_time = pygame.time.get_ticks()

        ## unhide 
        if self.hidden and pygame.time.get_ticks() - self.hide_timer > 1000:
            self.hidden = False
            self.rect.centerx = WIDTH / 2
            self.rect.bottom = HEIGHT - 30

        self.speedx = 0     ## makes the player static in the screen by default. 
        # then we have to check whether there is an event hanlding being done for the arrow keys being 
        ## pressed 

        ## will give back a list of the keys which happen to be pressed down at that moment
        keystate = pygame.key.get_pressed()     
        if keystate[pygame.K_LEFT]:
            self.speedx = -5
        elif keystate[pygame.K_RIGHT]:
            self.speedx = 5

        #Fire weapons by holding spacebar
        if keystate[pygame.K_SPACE]:
            self.shoot()

        ## check for the borders at the left and right
        if self.rect.right > WIDTH:
            self.rect.right = WIDTH
        if self.rect.left < 0:
            self.rect.left = 0

        self.rect.x += self.speedx

    def shoot(self):
        ## to tell the bullet where to spawn
        now = pygame.time.get_ticks()
        if now - self.last_shot > self.shoot_delay:
            self.last_shot = now
            if self.power == 1:
                bullet = Bullet(self.rect.centerx, self.rect.top)
                all_sprites.add(bullet)
                bullets.add(bullet)
                shooting_sound.play()
            if self.power == 2:
                bullet1 = Bullet(self.rect.left, self.rect.centery)
                bullet2 = Bullet(self.rect.right, self.rect.centery)
                all_sprites.add(bullet1)
                all_sprites.add(bullet2)
                bullets.add(bullet1)
                bullets.add(bullet2)
                shooting_sound.play()

            """ MOAR POWAH """
            if self.power >= 3:
                bullet1 = Bullet(self.rect.left, self.rect.centery)
                bullet2 = Bullet(self.rect.right, self.rect.centery)
                missile1 = Missile(self.rect.centerx, self.rect.top) # Missile shoots from center of ship
                all_sprites.add(bullet1)
                all_sprites.add(bullet2)
                all_sprites.add(missile1)
                bullets.add(bullet1)
                bullets.add(bullet2)
                bullets.add(missile1)
                shooting_sound.play()
                missile_sound.play()

    def adjust_fire_rate(self, score):
        if score >= 10000:
            self.shoot_delay = 200
        elif score >= 5000:
            self.shoot_delay = 250
        elif score >= 2000:
            self.shoot_delay = 300
        else:
            self.shoot_delay = 400

    def powerup(self):
        self.power += 1
        self.power_time = pygame.time.get_ticks()

    def hide(self):
        self.hidden = True
        self.hide_timer = pygame.time.get_ticks()
        self.rect.center = (WIDTH / 2, HEIGHT + 200)


# defines the enemies
class Mob(pygame.sprite.Sprite):
    def __init__(self, kind='normal'):
        pygame.sprite.Sprite.__init__(self)

        self.speedy = random.randrange(1,4)
        self.kind = kind
        if kind == 'normal':
           self.image_orig = random.choice(meteor_images)
           self.hit_points = 1
        else:
           self.image_orig = random.choice(special_meteor_images[kind])
           if kind == 'blue':
              self.hit_points = 2
              self.speedy = random.randrange(2,6)
           elif kind == 'green':
              self.hit_points = 3
              self.speedy = random.randrange(4,7)
           elif kind == 'pink':
              self.hit_points = 4
              self.speedy = random.randrange(5,8)

        self.image_orig.set_colorkey(BLACK)
        self.image = self.image_orig.copy()
        self.rect = self.image.get_rect()
        self.radius = int(self.rect.width * 0.9 / 2)
        self.rect.x = random.randrange(0, WIDTH - self.rect.width)
        self.rect.y = random.randrange(-150, -100)
        self.speedx = random.randrange(-3, 3)
        self.rotation = 0
        self.rotation_speed = random.randrange(-8, 8)
        self.last_update = pygame.time.get_ticks()

    def rotate(self):
        time_now = pygame.time.get_ticks()
        if time_now - self.last_update > 50: # in milliseconds
            self.last_update = time_now
            self.rotation = (self.rotation + self.rotation_speed) % 360 
            new_image = pygame.transform.rotate(self.image_orig, self.rotation)
            old_center = self.rect.center
            self.image = new_image
            self.rect = self.image.get_rect()
            self.rect.center = old_center

    def update(self):
        self.rotate()
        self.rect.x += self.speedx
        self.rect.y += self.speedy
        ## now what if the mob element goes out of the screen

        if (self.rect.top > HEIGHT + 10) or (self.rect.left < -25) or (self.rect.right > WIDTH + 20):
            self.rect.x = random.randrange(0, WIDTH - self.rect.width)
            self.rect.y = random.randrange(-100, -40)
            self.speedy = random.randrange(1, 8)        ## for randomizing the speed of the Mob

## defines the sprite for Powerups
class Pow(pygame.sprite.Sprite):
    def __init__(self, center):
        pygame.sprite.Sprite.__init__(self)
        self.type = random.choice(['shield', 'gun'])
        self.image = powerup_images[self.type]
        self.image.set_colorkey(BLACK)
        self.rect = self.image.get_rect()
        ## place the bullet according to the current position of the player
        self.rect.center = center
        self.speedy = 2

    def update(self):
        """should spawn right in front of the player"""
        self.rect.y += self.speedy
        ## kill the sprite after it moves over the top border
        if self.rect.top > HEIGHT:
            self.kill()

            

## defines the sprite for bullets
class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = bullet_img
        self.image.set_colorkey(BLACK)
        self.rect = self.image.get_rect()
        ## place the bullet according to the current position of the player
        self.rect.bottom = y 
        self.rect.centerx = x
        self.speedy = -10

    def update(self):
        """should spawn right in front of the player"""
        self.rect.y += self.speedy
        ## kill the sprite after it moves over the top border
        if self.rect.bottom < 0:
            self.kill()


## FIRE ZE MISSILES
class Missile(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = missile_img
        self.image.set_colorkey(BLACK)
        self.rect = self.image.get_rect()
        self.rect.bottom = y
        self.rect.centerx = x
        self.speedy = -10

    def update(self):
        """should spawn right in front of the player"""
        self.rect.y += self.speedy
        if self.rect.bottom < 0:
            self.kill()


###################################################
## Load all game images

background = pygame.image.load(path.join(img_dir, 'gameBackground.png')).convert()
background_rect = background.get_rect()
## ^^ draw this rect first 
meteorIndicator = pygame.image.load(path.join(img_dir, 'meteorIndicator.png')).convert()
meteorIndicator_rect = meteorIndicator.get_rect()
meteorIndicator_rect.topright = (WIDTH - 1.5, 1)

player_img = pygame.image.load(path.join(img_dir, 'playerShip1_orange.png')).convert()
player_mini_img = pygame.transform.scale(player_img, (25, 19))
player_mini_img.set_colorkey(BLACK)
bullet_img = pygame.image.load(path.join(img_dir, 'laserRed16.png')).convert()
missile_img = pygame.image.load(path.join(img_dir, 'missile.png')).convert_alpha()
# meteor_img = pygame.image.load(path.join(img_dir, 'meteorBrown_med1.png')).convert()
meteor_images = []
meteor_list = [
    'meteorBrown_big1.png',
    'meteorBrown_big2.png', 
    'meteorBrown_med1.png', 
    'meteorBrown_med3.png',
    'meteorBrown_small1.png',
    'meteorBrown_small2.png',
    'meteorBrown_tiny1.png'
]

for image in meteor_list:
    meteor_images.append(pygame.image.load(path.join(img_dir, image)).convert())

special_meteor_images = {
    'blue': [],
    'green': [],
    'pink': []
}

blue_meteors = ['meteorBlue_big1.png', 'meteorBlue_big1.png', 'meteorBlue_med1.png', 'meteorBlue_med3.png','meteorBlue_small1.png','meteorBlue_small2.png','meteorBlue_tiny1.png']
green_meteors = ['meteorGreen_big1.png', 'meteorGreen_big1.png', 'meteorGreen_med1.png', 'meteorGreen_med3.png','meteorGreen_small1.png','meteorGreen_small2.png','meteorGreen_tiny1.png']
pink_meteors = ['meteorPink_big1.png', 'meteorPink_big1.png', 'meteorPink_med1.png', 'meteorPink_med3.png','meteorPink_small1.png','meteorPink_small2.png','meteorPink_tiny1.png']

for image in blue_meteors:
    img = pygame.image.load(path.join(img_dir, image)).convert()
    img.set_colorkey(BLACK)
    special_meteor_images['blue'].append(img)

for image in green_meteors:
    img = pygame.image.load(path.join(img_dir, image)).convert()
    img.set_colorkey(BLACK)
    special_meteor_images['green'].append(img)

for image in pink_meteors:
    img = pygame.image.load(path.join(img_dir, image)).convert()
    img.set_colorkey(BLACK)
    special_meteor_images['pink'].append(img)

levelup_images = {
    2: pygame.image.load(path.join(img_dir, 'level2.png')).convert_alpha(),
    3: pygame.image.load(path.join(img_dir, 'level3.png')).convert_alpha(),
    4: pygame.image.load(path.join(img_dir, 'level4.png')).convert_alpha()
}

## meteor explosion
explosion_anim = {}
explosion_anim['lg'] = []
explosion_anim['sm'] = []
explosion_anim['player'] = []
for i in range(9):
    filename = 'regularExplosion0{}.png'.format(i)
    img = pygame.image.load(path.join(img_dir, filename)).convert()
    img.set_colorkey(BLACK)
    ## resize the explosion
    img_lg = pygame.transform.scale(img, (75, 75))
    explosion_anim['lg'].append(img_lg)
    img_sm = pygame.transform.scale(img, (32, 32))
    explosion_anim['sm'].append(img_sm)

    ## player explosion
    filename = 'sonicExplosion0{}.png'.format(i)
    img = pygame.image.load(path.join(img_dir, filename)).convert()
    img.set_colorkey(BLACK)
    explosion_anim['player'].append(img)

## load power ups
powerup_images = {}
powerup_images['shield'] = pygame.image.load(path.join(img_dir, 'shield_gold.png')).convert()
powerup_images['gun'] = pygame.image.load(path.join(img_dir, 'bolt_gold.png')).convert()


###################################################


###################################################
### Load all game sounds
shooting_sound = pygame.mixer.Sound(path.join(sound_folder, 'pew.wav'))
missile_sound = pygame.mixer.Sound(path.join(sound_folder, 'rocket.ogg'))
expl_sounds = []
for sound in ['expl3.wav', 'expl6.wav']:
    expl_sounds.append(pygame.mixer.Sound(path.join(sound_folder, sound)))
## main background music
#pygame.mixer.music.load(path.join(sound_folder, 'tgfcoder-FrozenJam-SeamlessLoop.ogg'))
pygame.mixer.music.set_volume(0.2)      ## simmered the sound down a little

player_die_sound = pygame.mixer.Sound(path.join(sound_folder, 'rumble1.ogg'))
###################################################

#############################
## Game loop
def game_loop():
    global all_sprites, player, mobs, bullets, powerups, score, level_shown, current_level_image, level_display_time,gesture_app
    gesture_enabled = False
    running = True
    menu_display = True
    while running:
        if menu_display:
            gesture_enabled= main_menu()
            if not gesture_enabled:
                gesture_app.stop()
            getReady()
            pygame.time.wait(3000)

            #Stop menu music
            pygame.mixer.music.stop()
            #Play the gameplay music
            pygame.mixer.music.load(path.join(sound_folder, 'tgfcoder-FrozenJam-SeamlessLoop.ogg'))
            pygame.mixer.music.play(-1)     ## makes the gameplay sound in an endless loop
            
            menu_display = False
            
            ## group all the sprites together for ease of update
            all_sprites = pygame.sprite.Group()
            player = Player()
            all_sprites.add(player)

            ## spawn a group of mob
            mobs = pygame.sprite.Group()
            for i in range(10):      ## 10 mobs
                newmob(mobs)

            ## group for bullets
            bullets = pygame.sprite.Group()
            powerups = pygame.sprite.Group()
            #### Score board variable
            score = 0
        
    #1 Process input/events
        clock.tick(FPS)     ## will make the loop run at the same speed all the time
        for event in pygame.event.get():        # gets all the events which have occured till now and keeps tab of them.
            ## listening for the the X button at the top
            if event.type == pygame.QUIT:
                running = False

            ## Press ESC to exit game
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False            

        #2 Update
        all_sprites.update()
        player.adjust_fire_rate(score)
        player.adjust_health_cap(score)
        player.adjust_size(score)
        # New: Automatically shoot continuously if gestures enabled
        if gesture_enabled:
            player.shoot()

        if score >= 10000 and level_shown < 4:
            level_shown = 4
            level_display_time = pygame.time.get_ticks()
            current_level_image = levelup_images[4]
        elif score >= 5000 and level_shown < 3:
            level_shown = 3
            level_display_time = pygame.time.get_ticks()
            current_level_image = levelup_images[3]
        elif score >= 2000 and level_shown < 2:
            level_shown = 2
            level_display_time = pygame.time.get_ticks()
            current_level_image = levelup_images[2]

        ## check if a bullet hit a mob
        ## now we have a group of bullets and a group of mob
        hits = pygame.sprite.groupcollide(mobs, bullets, False, True)

        ## now as we delete the mob element when we hit one with a bullet, we need to respawn them again
        ## as there will be no mob_elements left out 
        for hit in hits:
            hit.hit_points-=1
            if hit.hit_points <= 0:
                score += hit.radius         ## give different scores for hitting big and small metoers
                random.choice(expl_sounds).play()

                expl = Explosion(hit.rect.center, 'lg')
                all_sprites.add(expl)
                if random.random() > 0.9:
                    pow = Pow(hit.rect.center)
                    all_sprites.add(pow)            
                    powerups.add(pow)
                newmob(mobs)        ## spawn a new mob
                hit.kill()
                newmob(mobs)

        ## ^^ the above loop will create the amount of mob objects which were killed spawn again
        #########################

        ## check if the player collides with the mob
        hits = pygame.sprite.spritecollide(player, mobs, True, pygame.sprite.collide_circle)        ## gives back a list, True makes the mob element disappear
        for hit in hits:
            player.health -= hit.radius * 2
            expl = Explosion(hit.rect.center, 'sm')
            all_sprites.add(expl)
            newmob(mobs)
            if player.health <= 0: 
                player_die_sound.play()
                death_explosion = Explosion(player.rect.center, 'player')
                all_sprites.add(death_explosion)
                # running = False     ## GAME OVER 3:D
                player.hide()
                player.lives -= 1
                player.health = 100

        ## if the player hit a power up
        hits = pygame.sprite.spritecollide(player, powerups, True)
        for hit in hits:
            if hit.type == 'shield':
                if player.health < player.max_health:  
                    player.health += random.randrange(10, 30)
                    if player.health > player.max_health:
                        player.health = player.max_health

            if hit.type == 'gun':
                player.powerup()

        ## if player died and the explosion has finished, end game
        if player.lives == 0 and not death_explosion.alive():
            show_game_over()  
            saveRecord(score)
            menu_display = True
            score=0

        #3 Draw/render
        screen.fill(BLACK)
        ## draw the stargaze.png image
        screen.blit(background, background_rect)

        all_sprites.draw(screen)

        draw_text(screen, str(score), 18, WIDTH / 2, 10)     ## 10px down from the screen
        
        screen.blit(meteorIndicator, meteorIndicator_rect)
        # Draw player health bar below ship
        total_width = int(WIDTH * (player.max_health / 200)) 
        bar_width = int((player.health / player.max_health) * total_width)
        bar_height = 12
        bar_x = 0
        bar_y = HEIGHT - 25  

        pygame.draw.rect(screen, GREEN, (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(screen, WHITE, (bar_x, bar_y, int(WIDTH * (player.max_health / 200)), bar_height), 2)
        if current_level_image:
            if pygame.time.get_ticks() - level_display_time < 2000: 
                img_rect = current_level_image.get_rect(center=(WIDTH // 2, HEIGHT // 2))
                screen.blit(current_level_image, img_rect)
            else:
                current_level_image = None 

        if gesture_enabled:
            draw_text(screen, "Gesture Control: ON", 12, WIDTH / 2, HEIGHT - 30)
            player.shoot()
        else:
            draw_text(screen, "Keyboard Control", 12, WIDTH / 2, HEIGHT - 30)

        ## Done after drawing everything to the screen
        pygame.display.flip()       
    
    return score

def main():
    game_loop()

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                waiting = False
            if event.type == pygame.KEYUP:
                waiting = False
    
    # Cleanup
    if gesture_app:
        gesture_app.disable_gestures()
    pygame.quit()

if __name__ == "__main__":
    main()