import customtkinter as ctk
from config import SUCCESS, WARNING, DANGER, TEXT_SECONDARY, FONT_FAMILY

STATUS_COLORS = {
    "operational": SUCCESS,   # #16A34A
    "degraded":    WARNING,   # #D97706
    "offline":     DANGER,    # #DC2626
}

STATUS_LABELS = {
    "operational": "Operational",
    "degraded":    "Degraded",
    "offline":     "Offline",
}


class StatusBadge(ctk.CTkFrame):
    """
    Signature element: 3px solid colored left-rule + status text.
    Not a pill. Not a dot. A precise vertical rule.
    """

    def __init__(self, master, status: str, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        color = STATUS_COLORS.get(status, TEXT_SECONDARY)
        text  = STATUS_LABELS.get(status, status.title())

        # 3px left rule — must use pack_propagate(False) to hold width
        rule = ctk.CTkFrame(self, width=3, fg_color=color, corner_radius=0)
        rule.pack(side="left", fill="y", padx=(0, 8))
        rule.pack_propagate(False)

        ctk.CTkLabel(
            self,
            text=text,
            font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"),
            text_color=color,
            fg_color="transparent",
        ).pack(side="left", pady=4)
