import customtkinter as ctk
from config import TEXT_SECONDARY, ACCENT, FONT_FAMILY


class LoadingFrame(ctk.CTkFrame):
    """Centered pulsing text loading indicator."""

    def __init__(self, master, message: str = "Loading", **kwargs):
        super().__init__(master, fg_color="transparent", corner_radius=0, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._base = message.rstrip(".")
        self._dots = 1
        self._job  = None

        self._lbl = ctk.CTkLabel(
            self,
            text=f"{self._base}.",
            font=ctk.CTkFont(family=FONT_FAMILY, size=14),
            text_color=TEXT_SECONDARY,
            fg_color="transparent",
        )
        self._lbl.grid(row=0, column=0)

    def start(self):
        self.stop()
        self._tick()

    def stop(self):
        if self._job:
            try:
                self.after_cancel(self._job)
            except Exception:
                pass
            self._job = None

    def _tick(self):
        self._dots = self._dots % 3 + 1
        try:
            self._lbl.configure(text=f"{self._base}{'.' * self._dots}")
            self._job = self.after(450, self._tick)
        except Exception:
            pass


class ErrorFrame(ctk.CTkFrame):
    """Centered error state with Retry button."""

    def __init__(self, master, on_retry=None, **kwargs):
        super().__init__(master, fg_color="transparent", corner_radius=0, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.grid(row=0, column=0)

        ctk.CTkLabel(
            inner,
            text="Couldn't load data. Check your connection.",
            font=ctk.CTkFont(family=FONT_FAMILY, size=14),
            text_color=TEXT_SECONDARY,
            fg_color="transparent",
        ).pack(pady=(0, 14))

        if on_retry:
            ctk.CTkButton(
                inner,
                text="Retry",
                font=ctk.CTkFont(family=FONT_FAMILY, size=13),
                fg_color=ACCENT,
                hover_color="#1E40AF",
                text_color="#FFFFFF",
                corner_radius=6,
                height=34,
                width=90,
                command=on_retry,
            ).pack()
