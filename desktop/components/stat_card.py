import customtkinter as ctk
from config import SURFACE, BORDER, TEXT_PRIMARY, TEXT_SECONDARY, ACCENT, FONT_FAMILY


class StatCard(ctk.CTkFrame):
    """
    White card — icon · large number · label · colored accent underline at bottom.
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

        # Content (padded inset)
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=16, pady=(14, 12))

        # Icon
        ctk.CTkLabel(
            content,
            text=icon,
            font=ctk.CTkFont(family=FONT_FAMILY, size=20),
            text_color=accent_color,
            fg_color="transparent",
        ).pack(anchor="w")

        # Value
        self._value_label = ctk.CTkLabel(
            content,
            text=value,
            font=ctk.CTkFont(family=FONT_FAMILY, size=28, weight="bold"),
            text_color=value_color,
            fg_color="transparent",
        )
        self._value_label.pack(anchor="w", pady=(8, 0))

        # Label
        ctk.CTkLabel(
            content,
            text=label,
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=TEXT_SECONDARY,
            fg_color="transparent",
        ).pack(anchor="w", pady=(3, 0))

        # Accent underline at bottom of card
        underline = ctk.CTkFrame(self, height=3, fg_color=accent_color, corner_radius=0)
        underline.pack(fill="x", side="bottom")
        underline.pack_propagate(False)

    def update_value(self, value: str, color: str = None):
        self._value_label.configure(text=value)
        if color:
            self._value_label.configure(text_color=color)
