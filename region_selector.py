import mss
import tkinter
from PIL import ImageTk, Image


class RegionSelector:
    def __init__(self):
        self.region = None

        with mss.mss() as sct:
            self.screenshot = sct.grab(sct.monitors[1])
            self.screenshot = Image.frombytes(
                "RGB", self.screenshot.size, self.screenshot.bgra, "raw", "BGRX"
            )

        self.root = tkinter.Tk()
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-topmost", True)

        self.canvas = tkinter.Canvas(self.root, cursor="cross")
        self.canvas.pack(expand=True, fill=tkinter.BOTH)

        self.screenshot = ImageTk.PhotoImage(self.screenshot)
        self.canvas.create_image(0, 0, image=self.screenshot, anchor=tkinter.NW)

        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_move)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.root.bind("<Escape>", self.cancel)

        self.root.mainloop()

    def on_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        self.rect_id = self.canvas.create_rectangle(
            event.x, event.y, event.x, event.y, outline="red", width=2
        )

    def on_move(self, event):
        self.canvas.coords(self.rect_id, self.start_x, self.start_y, event.x, event.y)

    def on_release(self, event):
        self.region = {
            "top": min(self.start_y, event.y),
            "left": min(self.start_x, event.x),
            "width": abs(event.x - self.start_x),
            "height": abs(event.y - self.start_y),
        }
        self.root.destroy()

    def cancel(self, event):
        self.root.destroy()
