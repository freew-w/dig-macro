import tkinter
import mss
from PIL import Image, ImageTk


def select_region():
    # Create root
    root = tkinter.Tk()
    root.attributes("-fullscreen", True)
    root.attributes("-topmost", True)

    # Create canvas
    canvas = tkinter.Canvas(root, cursor="cross")
    canvas.pack(expand=True, fill=tkinter.BOTH)

    # Capture screenshot
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        screenshot = sct.grab(monitor)
        pillow_image = Image.frombytes(
            "RGB", screenshot.size, screenshot.bgra, "raw", "BGRX"
        )

    # Display screenshot
    tk_image = ImageTk.PhotoImage(pillow_image)
    canvas.create_image(0, 0, image=tk_image, anchor=tkinter.NW)

    # Selection state
    region = None
    start_x, start_y = 0, 0
    rect_id = None

    def on_press(event):
        nonlocal start_x, start_y, rect_id
        start_x = event.x
        start_y = event.y
        rect_id = canvas.create_rectangle(
            event.x,
            event.y,
            event.x,
            event.y,
            outline="red",
            width=2,
            fill="",
            dash=(4, 4),
        )

    def on_move(event):
        nonlocal rect_id
        if rect_id:
            canvas.coords(rect_id, start_x, start_y, event.x, event.y)

    def on_release(event):
        nonlocal region
        x1, y1, x2, y2 = start_x, start_y, event.x, event.y
        region = {
            "top": min(y1, y2),
            "left": min(x1, x2),
            "width": abs(x2 - x1),
            "height": abs(y2 - y1),
        }
        root.destroy()

    def cancel(event=None):
        nonlocal region
        region = None
        root.destroy()

    # Bind events
    canvas.bind("<ButtonPress-1>", on_press)
    canvas.bind("<B1-Motion>", on_move)
    canvas.bind("<ButtonRelease-1>", on_release)
    root.bind("<Escape>", cancel)

    root.mainloop()
    return region
