import customtkinter as ctk
from config import SUCCESS, WARNING, DANGER, TEXT_PRIMARY, FONT_FAMILY

STATUS_COLORS = {
    "operational": SUCCESS,
    "degraded": WARNING,
    "offline": DANGER,
}

STATUS_LABELS = {
    "operational": "Operational",
    "degraded": "Degraded",
    "offline": "Offline",
}


class StatusBadge(ctk.CTkFrame):
    """Status badge with a 3px colored left-rule — the signature design element."""

    def __init__(self, master, status: str, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        color = STATUS_COLORS.get(status, "#9CA3AF")
        label_text = STATUS_LABELS.get(status, status.title())

        # 3px left rule
        rule = ctk.CTkFrame(self, width=3, fg_color=color, corner_radius=0)
        rule.pack(side="left", fill="y", padx=(0, 6))

        ctk.CTkLabel(
            self,
            text=label_text,
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color=color,
        ).pack(side="left", pady=2)
