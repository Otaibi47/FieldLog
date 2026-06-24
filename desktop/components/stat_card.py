import customtkinter as ctk
from config import SURFACE, BORDER, TEXT_PRIMARY, TEXT_SECONDARY, FONT_FAMILY


class StatCard(ctk.CTkFrame):
    def __init__(self, master, icon: str, value: str, label: str, value_color=TEXT_PRIMARY, **kwargs):
        super().__init__(
            master,
            fg_color=SURFACE,
            corner_radius=8,
            border_width=1,
            border_color=BORDER,
            **kwargs,
        )
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self,
            text=icon,
            font=ctk.CTkFont(family=FONT_FAMILY, size=22),
            text_color=TEXT_SECONDARY,
        ).pack(anchor="w", padx=16, pady=(16, 4))

        self._value_label = ctk.CTkLabel(
            self,
            text=value,
            font=ctk.CTkFont(family=FONT_FAMILY, size=28, weight="bold"),
            text_color=value_color,
        )
        self._value_label.pack(anchor="w", padx=16)

        ctk.CTkLabel(
            self,
            text=label,
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=TEXT_SECONDARY,
        ).pack(anchor="w", padx=16, pady=(2, 16))

    def update_value(self, value: str, color=None):
        self._value_label.configure(text=value)
        if color:
            self._value_label.configure(text_color=color)
