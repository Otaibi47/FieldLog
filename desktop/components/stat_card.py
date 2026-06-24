import customtkinter as ctk
from config import SURFACE, BORDER, TEXT_PRIMARY, TEXT_SECONDARY, ACCENT, FONT_FAMILY


class StatCard(ctk.CTkFrame):
    """
    Metric card: icon → colored accent line → large number → small label.
    accent_color drives both the icon tint and the horizontal rule.
    value_color drives the number (defaults to accent_color).
    """

    def __init__(
        self,
        master,
        icon: str,
        value: str,
        label: str,
        accent_color: str = ACCENT,
        value_color: str = None,
        **kwargs,
    ):
        super().__init__(
            master,
            fg_color=SURFACE,
            corner_radius=8,
            border_width=1,
            border_color=BORDER,
            **kwargs,
        )
        value_color = value_color or accent_color

        # Icon
        ctk.CTkLabel(
            self,
            text=icon,
            font=ctk.CTkFont(family=FONT_FAMILY, size=20),
            text_color=accent_color,
            fg_color="transparent",
        ).pack(anchor="w", padx=16, pady=(16, 8))

        # Colored accent line
        ctk.CTkFrame(self, height=2, fg_color=accent_color, corner_radius=0).pack(
            fill="x", padx=16, pady=(0, 12)
        )

        # Value (large number)
        self._value_label = ctk.CTkLabel(
            self,
            text=value,
            font=ctk.CTkFont(family=FONT_FAMILY, size=24, weight="bold"),
            text_color=value_color,
            fg_color="transparent",
        )
        self._value_label.pack(anchor="w", padx=16)

        # Label
        ctk.CTkLabel(
            self,
            text=label,
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=TEXT_SECONDARY,
            fg_color="transparent",
        ).pack(anchor="w", padx=16, pady=(4, 16))

    def update_value(self, value: str, color: str = None):
        self._value_label.configure(text=value)
        if color:
            self._value_label.configure(text_color=color)
