import os
import threading
import time
import json
import cv2
import numpy as np
import mss
import pynput
import region_selector
import point_selector

# Configuration
BAR_WIDTH_THRESHOLD = 65
DIG_COOLDOWN_SECONDS = 0.22
CHECK_IS_DIGGING_BLACK_COLOR_THRESHOLD = 25
START_DIGGING_COOLDOWN_SECONDS = 12
CONFIG_FILE = "macro_config.json"

# Global variables
mouse_controller = pynput.mouse.Controller()
keyboard_controller = pynput.keyboard.Controller()
is_running = False
scan_region = None
digging_check_point = None


def save_config():
    config = {"scan_region": scan_region, "digging_check_point": digging_check_point}
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)


def load_config():
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        pass
    return {"scan_region": None, "digging_check_point": None}


def set_scan_region():
    global scan_region
    region = region_selector.select_region()
    if region:
        scan_region = region
        save_config()
        print("Scan region set successfully")
        return True
    print("Region selection cancelled")
    return False


def set_digging_check_point():
    global digging_check_point
    point = point_selector.select_point()
    if point:
        digging_check_point = point
        save_config()
        print("Digging check point set successfully")
        return True
    print("Point selection cancelled")
    return False


def check_is_digging(sct):
    """Returns False if not digging"""
    if not digging_check_point:
        return False

    pixel = np.array(sct.grab(digging_check_point))
    return not all(
        channel <= CHECK_IS_DIGGING_BLACK_COLOR_THRESHOLD for channel in pixel[0, 0, :3]
    )


def move():
    keyboard_controller.press("w")
    keyboard_controller.press("d")
    time.sleep(0.3)
    keyboard_controller.release("w")
    keyboard_controller.release("d")


def start_macro():
    # Load config at start
    config = load_config()
    global scan_region, digging_check_point
    scan_region = config["scan_region"]
    digging_check_point = config["digging_check_point"]

    # Validate configuration
    if not scan_region:
        print("Set scan region first (Ctrl+R)")
        return
    if not digging_check_point:
        print("Set digging check point first (Ctrl+P)")
        return

    global is_running
    is_running = True
    print("Macro started (Ctrl+E to stop)")

    # Variables
    last_start_digging_time = time.time()
    last_dig_time = 0

    with mss.mss() as sct:
        while is_running:
            current_time = time.time()

            # Move and start digging if not digging
            if (
                current_time - last_start_digging_time > START_DIGGING_COOLDOWN_SECONDS
                and not check_is_digging(sct)
            ):
                move()
                time.sleep(1)
                mouse_controller.click(pynput.mouse.Button.left)
                last_start_digging_time = current_time

            # Capture and process screenshot
            screenshot = np.array(sct.grab(scan_region))
            gray = cv2.cvtColor(screenshot, cv2.COLOR_BGRA2GRAY)
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            contours, _ = cv2.findContours(
                thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )

            bar_count = sum(
                1 for c in contours if cv2.boundingRect(c)[2] > BAR_WIDTH_THRESHOLD
            )

            # Dig if bar count is 2
            if current_time - last_dig_time > DIG_COOLDOWN_SECONDS and bar_count == 2:
                mouse_controller.click(pynput.mouse.Button.left)
                last_dig_time = current_time


def stop_macro():
    global is_running
    is_running = False
    print("Macro stopped")


def quit_program():
    stop_macro()
    os._exit(0)


def main():
    # Hotkey setup
    with pynput.keyboard.GlobalHotKeys(
        {
            "<ctrl>+r": set_scan_region,
            "<ctrl>+p": set_digging_check_point,
            "<ctrl>+s": lambda: threading.Thread(
                target=start_macro, daemon=True
            ).start(),
            "<ctrl>+e": stop_macro,
            "<ctrl>+q": quit_program,
        }
    ) as hotkeys:

        print("Hotkeys activated:")
        print("Ctrl+R: Set scan region")
        print("Ctrl+P: Set digging check point")
        print("Ctrl+S: Start macro")
        print("Ctrl+E: Stop macro")
        print("Ctrl+Q: Quit program")
        print("\nWaiting for commands...")
        hotkeys.join()


if __name__ == "__main__":
    main()
