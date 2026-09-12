import time
import math
import pyautogui
from typing import Tuple

# Configure PyAutoGUI safety
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.05

class OSActuator:
    def __init__(self):
        self.screen_width, self.screen_height = pyautogui.size()

    def smooth_move_to(self, x: int, y: int, duration: float = 0.35):
        '''
        Moves the cursor smoothly so judges can see actuation in action.
        '''
        # Clamp to screen bounds
        target_x = max(0, min(x, self.screen_width - 1))
        target_y = max(0, min(y, self.screen_height - 1))
        
        pyautogui.moveTo(target_x, target_y, duration=duration, tween=pyautogui.easeInOutQuad)

    def click_at(self, x: int, y: int, button: str = "left"):
        self.smooth_move_to(x, y)
        pyautogui.click(x, y, button=button)
        time.sleep(0.1)

    def type_into_field(self, x: int, y: int, text: str, clear_first: bool = True):
        self.click_at(x, y)
        if clear_first:
            pyautogui.hotkey("ctrl", "a")
            pyautogui.press("backspace")
        
        # Type with small human cadence
        for char in str(text):
            pyautogui.write(char)
            time.sleep(0.015)
        time.sleep(0.1)
