import customtkinter as ctk
from config import SURFACE, TEXT_PRIMARY, TEXT_SECONDARY, ACCENT, ACCENT_LIGHT, BORDER, DANGER, FONT_FAMILY


class Sidebar(ctk.CTkFrame):
    def __init__(self, master, on_navigate, **kwargs):
        super().__init__(master, width=200, fg_color=SURFACE, corner_radius=0, **kwargs)
        self.on_navigate = on_navigate
        self._active = "dashboard"
        self._alert_count = 0
        self._buttons = {}
        self.grid_propagate(False)
        self._build()

    def _build(self):
        # Logo / app title
        title = ctk.CTkLabel(
            self,
            text="FieldLog",
            font=ctk.CTkFont(family=FONT_FAMILY, size=18, weight="bold"),
            text_color=TEXT_PRIMARY,
        )
        title.pack(pady=(24, 4), padx=16, anchor="w")

        sub = ctk.CTkLabel(
            self,
            text="Maintenance Tracker",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=TEXT_SECONDARY,
        )
        sub.pack(padx=16, anchor="w")

        # Divider
        ctk.CTkFrame(self, height=1, fg_color=BORDER).pack(fill="x", pady=16, padx=0)

        nav_items = [
            ("dashboard", "Dashboard"),
            ("equipment", "Equipment"),
            ("maintenance", "Maintenance"),
            ("alerts", "Alerts"),
        ]
        for key, label in nav_items:
            self._make_nav_button(key, label)

        # Right-edge border
        ctk.CTkFrame(self, width=1, fg_color=BORDER).place(relx=1.0, rely=0, relheight=1.0, anchor="ne")

    def _make_nav_button(self, key: str, label: str):
        frame = ctk.CTkFrame(self, fg_color="transparent", cursor="hand2")
        frame.pack(fill="x", padx=8, pady=2)

        btn = ctk.CTkButton(
            frame,
            text=label,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            fg_color="transparent",
            text_color=TEXT_SECONDARY,
            hover_color=ACCENT_LIGHT,
            anchor="w",
            command=lambda k=key: self._navigate(k),
            corner_radius=6,
            height=36,
        )
        btn.pack(fill="x")
        self._buttons[key] = btn

    def _navigate(self, key: str):
        self._active = key
        self._refresh_styles()
        self.on_navigate(key)

    def _refresh_styles(self):
        for key, btn in self._buttons.items():
            if key == self._active:
                btn.configure(fg_color=ACCENT_LIGHT, text_color=ACCENT)
            else:
                btn.configure(fg_color="transparent", text_color=TEXT_SECONDARY)

    def set_alert_count(self, count: int):
        self._alert_count = count
        label = f"Alerts  ({count})" if count > 0 else "Alerts"
        btn = self._buttons.get("alerts")
        if btn:
            btn.configure(text=label, text_color=DANGER if count > 0 else TEXT_SECONDARY)

    def set_active(self, key: str):
        self._active = key
        self._refresh_styles()
