import customtkinter as ctk
from config import SURFACE, BORDER, TEXT_PRIMARY, TEXT_SECONDARY, ACCENT, FONT_FAMILY


class StatCard(ctk.CTkFrame):
    """
    Shadow wrapper → white card → left colour strip → icon / number / label.
    The shadow is simulated by a 2px darker frame behind the card.
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
        # Shadow wrapper (slightly darker, 2px offset → bottom-right shadow illusion)
        super().__init__(master, fg_color="#D1D5DB", corner_radius=9, **kwargs)
        value_color = value_color or accent_color

        # Card surface — slightly inset from shadow
        card = ctk.CTkFrame(
            self,
            fg_color=SURFACE,
            corner_radius=8,
            border_width=1,
            border_color=BORDER,
        )
        card.pack(fill="both", expand=True, padx=(0, 2), pady=(0, 2))

        # 4px coloured left strip (the signature rule element on cards)
        strip = ctk.CTkFrame(card, width=4, fg_color=accent_color, corner_radius=0)
        strip.pack(side="left", fill="y")
        strip.pack_propagate(False)

        # Content column
        col = ctk.CTkFrame(card, fg_color="transparent")
        col.pack(side="left", fill="both", expand=True)

        # Icon
        ctk.CTkLabel(
            col,
            text=icon,
            font=ctk.CTkFont(family=FONT_FAMILY, size=18),
            text_color=accent_color,
            fg_color="transparent",
        ).pack(anchor="w", padx=14, pady=(14, 6))

        # Value
        self._value_label = ctk.CTkLabel(
            col,
            text=value,
            font=ctk.CTkFont(family=FONT_FAMILY, size=28, weight="bold"),
            text_color=value_color,
            fg_color="transparent",
        )
        self._value_label.pack(anchor="w", padx=14)

        # Label
        ctk.CTkLabel(
            col,
            text=label,
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=TEXT_SECONDARY,
            fg_color="transparent",
        ).pack(anchor="w", padx=14, pady=(4, 14))

    def update_value(self, value: str, color: str = None):
        self._value_label.configure(text=value)
        if color:
            self._value_label.configure(text_color=color)
