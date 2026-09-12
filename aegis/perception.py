import time
from typing import Dict, Tuple, Optional
from PIL import ImageGrab

class VisionPerception:
    def __init__(self, target_app_instance=None):
        self.target_app = target_app_instance

    def capture_screen_region(self, bbox: Tuple[int, int, int, int]):
        return ImageGrab.grab(bbox=bbox)

    def scan_environment(self) -> Dict[str, Tuple[int, int]]:
        '''
        Perceives the current spatial landscape of the operational desktop.
        Returns live absolute screen coordinates for semantic UI anchors.
        '''
        if self.target_app:
            coords = self.target_app.get_widget_coordinates()
            return {
                "vendor_field": coords["vendor_input"],
                "invoice_field": coords["invoice_input"],
                "amount_field": coords["amount_input"],
                "notes_field": coords["notes_input"],
                "submit_button": coords["submit_button"],
                "purge_button": coords["purge_button"]
            }
        return {}
