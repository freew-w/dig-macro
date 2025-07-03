import os
import threading
import time
import ast
from pathlib import Path
import cv2
import numpy as np
import mss
import pynput
import region_selector

# configuration
BAR_WIDTH_THRESHOLD = 40
DIG_COOLDOWN = 0.3  # seconds


class Macro:
    def __init__(self):
        self.keyboard_controller = pynput.keyboard.Controller()
        self.scan_region = None
        self.is_running = False

    def select_scan_region(self):
        if self.load_scan_region():
            return

        self.scan_region = region_selector.RegionSelector().region
        if self.scan_region == None:
            return
        with open(f"scan_region_{self.scan_region}", "w") as f:
            f.write("")

    def load_scan_region(self):
        try:
            self.scan_region = ast.literal_eval(
                [
                    str(f)
                    for f in Path(".").iterdir()
                    if f.name.startswith("scan_region_")
                ][0].strip("scan_region_")
            )

            return True
        except:
            return False

    def start(self):
        if not self.load_scan_region():
            print("set scan region first")
            return

        self.is_running = True
        last_dig_time = 0

        with mss.mss() as sct:
            while self.is_running:
                screenshot = np.array(sct.grab(self.scan_region))
                screenshot = cv2.cvtColor(screenshot, cv2.COLOR_BGRA2GRAY)
                _, screenshot = cv2.threshold(
                    screenshot, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
                )
                contours, _ = cv2.findContours(
                    screenshot, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
                )
                rectangles = sum(
                    1
                    for contour in contours
                    if cv2.boundingRect(contour)[2] > BAR_WIDTH_THRESHOLD
                )

                current_time = time.time()
                if current_time - last_dig_time > DIG_COOLDOWN and rectangles == 2:
                    self.keyboard_controller.press(pynput.keyboard.Key.space)
                    self.keyboard_controller.release(pynput.keyboard.Key.space)
                    last_dig_time = current_time

    def stop(self):
        self.is_running = False


def main():
    digger = Macro()
    digger.load_scan_region()

    with pynput.keyboard.GlobalHotKeys(
        {
            "<ctrl>+p": lambda: threading.Thread(
                target=digger.start, daemon=True
            ).start(),
            "<ctrl>+e": digger.stop,
            "<ctrl>+s": digger.select_scan_region,
            "<ctrl>+q": lambda: os._exit(0),
        }
    ) as h:
        h.join()


if __name__ == "__main__":
    main()
