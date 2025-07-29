from typing import Set
import pygame
from directkeys import LeftArrow, RightArrow, Space, W, S
from directkeys import PressKey, ReleaseKey


class Control:
    # current_key_pressed = set()
    # ckp_string: Set[str] = set()

    # def startControlling(self, distance, slope):
    #     keyPressed = False
    #     keyPressed_lr = False
    #     recentKey = None
    #     self.space_pressed = False 
        
    #     # if 120 <= distance <= 220:
    #     #     PressKey(W)
    #     #     recentKey = W
    #     #     print('Press W')
    #     #     keyPressed = True
    #     #     self.current_key_pressed.add(W)
    #     #     self.ckp_string.add("W")
    #     # elif 20 <= distance <= 115:
    #     #     PressKey(S)
    #     #     recentKey = S
    #     #     print('Press S')
    #     #     keyPressed = True
    #     #     self.current_key_pressed.add(S)
    #     #     self.ckp_string.add("S")

    #     if -0.41 < slope < -0.25:
    #         PressKey(LeftArrow)
            
    #         self.current_key_pressed.add(LeftArrow)
    #         self.ckp_string.add("LeftArrow")
    #         keyPressed = True
    #         keyPressed_lr = True
    #         print('Press <--')
    #     elif 0.15 < slope < 0.40:
    #         PressKey(RightArrow)
            
    #         self.current_key_pressed.add(RightArrow)
    #         self.ckp_string.add("RightArrow")
    #         keyPressed = True
    #         keyPressed_lr = True
    #         print('Press -->')

    #     if distance < 1000:  # Example condition to hold space
    #         if not self.space_pressed:
    #             PressKey(Space)
    #             self.space_pressed = True
    #             print('Press Space')
                
    #     else:
    #         if self.space_pressed:
    #             ReleaseKey(Space)
    #             self.space_pressed = False
                
                
    #     # if keyPressed:
    #     #     if recentKey == W and S in self.current_key_pressed:
    #     #         self.current_key_pressed.remove(S)
    #     #         self.ckp_string.remove("S")
    #     #         ReleaseKey(S)

    #     #     elif recentKey == S and W in self.current_key_pressed:
    #     #         self.current_key_pressed.remove(W)
    #     #         self.ckp_string.remove("W")
    #     #         ReleaseKey(W)

    #     if not keyPressed and len(self.current_key_pressed) != 0:
    #         for key in self.current_key_pressed:
    #             ReleaseKey(key)
    #             # print('Release')
    #         self.current_key_pressed = set()
    #         self.ckp_string = set()

    #     if not keyPressed_lr and ((LeftArrow in self.current_key_pressed) or (RightArrow in self.current_key_pressed)):
    #         if LeftArrow in self.current_key_pressed:
    #             ReleaseKey(LeftArrow)
    #             self.current_key_pressed.remove(LeftArrow)
    #             self.ckp_string.remove("LeftArrow")
    #         elif RightArrow in self.current_key_pressed:
    #             ReleaseKey(RightArrow)
    #             self.current_key_pressed.remove(RightArrow)
    #             self.ckp_string.remove("RightArrow")

    #     return " ".join(self.ckp_string)
    def __init__(self):
        self.current_key_pressed = set()
        self.ckp_string = set()

    def startControlling(self, distance, slope):
        keyPressed = False
        keyPressed_lr = False
        
        # Manage arrow keys based on slope
        if -0.41 < slope < -0.25:
            if LeftArrow not in self.current_key_pressed:
                PressKey(LeftArrow)
                self.current_key_pressed.add(LeftArrow)
                self.ckp_string.add("LeftArrow")
                print('Press <--')
            keyPressed = True
            keyPressed_lr = True
        else:
            if LeftArrow in self.current_key_pressed:
                ReleaseKey(LeftArrow)
                self.current_key_pressed.remove(LeftArrow)
                self.ckp_string.remove("LeftArrow")

        if 0.15 < slope < 0.40:
            if RightArrow not in self.current_key_pressed:
                PressKey(RightArrow)
                self.current_key_pressed.add(RightArrow)
                self.ckp_string.add("RightArrow")
                print('Press -->')
            keyPressed = True
            keyPressed_lr = True
        else:
            if RightArrow in self.current_key_pressed:
                ReleaseKey(RightArrow)
                self.current_key_pressed.remove(RightArrow)
                self.ckp_string.remove("RightArrow")

        # Manage space key based on distance
        if distance < 1000:
            if Space not in self.current_key_pressed:
                PressKey(Space)
                self.current_key_pressed.add(Space)
                self.ckp_string.add("Space")
                print('Press Space')
        else:
            if Space in self.current_key_pressed:
                ReleaseKey(Space)
                self.current_key_pressed.remove(Space)
                self.ckp_string.remove("Space")

        # If no keys should be pressed, release all
        if not keyPressed and Space not in self.current_key_pressed and len(self.current_key_pressed) > 0:
            for key in list(self.current_key_pressed):
                ReleaseKey(key)
            self.current_key_pressed.clear()
            self.ckp_string.clear()

        return " ".join(self.ckp_string)

