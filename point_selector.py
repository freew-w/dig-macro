import tkinter
import mss
from PIL import Image, ImageTk


def select_point():
    # Create root
    root = tkinter.Tk()
    root.attributes("-fullscreen", True)
    root.attributes("-topmost", True)

    # Create canvas
    canvas = tkinter.Canvas(root)
    canvas.pack(expand=True, fill=tkinter.BOTH)

    # Capture screenshot
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        screenshot = sct.grab(monitor)
        pil_image = Image.frombytes(
            "RGB", screenshot.size, screenshot.bgra, "raw", "BGRX"
        )

    # Display screenshot
    tk_image = ImageTk.PhotoImage(pil_image)
    canvas.create_image(0, 0, image=tk_image, anchor=tkinter.NW)

    # Point state
    point = None

    def on_press(event):
        nonlocal point
        point = {
            "top": event.y,
            "left": event.x,
            "width": 1,
            "height": 1,
        }
        root.destroy()

    def cancel(event=None):
        nonlocal point
        point = None
        root.destroy()

    # Bind events
    canvas.bind("<ButtonPress-1>", on_press)
    root.bind("<Escape>", cancel)

    root.mainloop()
    return point
