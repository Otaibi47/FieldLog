import customtkinter as ctk
from components.data_table import DataTable
from config import (
    BG, DANGER, DANGER_LIGHT, BORDER, TEXT_PRIMARY, TEXT_SECONDARY,
    FONT_FAMILY, FONT_MONO,
)


class AlertsScreen(ctk.CTkFrame):
    def __init__(self, master, api_client, **kwargs):
        super().__init__(master, fg_color=BG, **kwargs)
        self.api = api_client
        self._build()
        self.refresh()

    def _build(self):
        self._banner = ctk.CTkFrame(self, fg_color=DANGER_LIGHT, corner_radius=8,
                                     border_width=1, border_color=DANGER)
        self._banner_label = ctk.CTkLabel(
            self._banner,
            text="",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
            text_color=DANGER,
        )
        self._banner_label.pack(padx=16, pady=10)

        ctk.CTkLabel(
            self,
            text="Overdue Equipment",
            font=ctk.CTkFont(family=FONT_FAMILY, size=20, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).pack(anchor="w", padx=24, pady=(24, 8))

        self._table = DataTable(
            self,
            columns=[
                ("Equipment Name", 3),
                ("Location", 3),
                ("Due Date", 2),
                ("Days Overdue", 2),
                ("Last Maintained", 2),
            ],
            height=500,
        )
        self._table.pack(fill="both", expand=True, padx=24, pady=(0, 24))

    def refresh(self):
        try:
            items = self.api.get_overdue()
        except Exception:
            items = []

        if items:
            count = len(items)
            self._banner_label.configure(
                text=f"  ⚠  {count} item{'s' if count != 1 else ''} require immediate attention"
            )
            self._banner.pack(fill="x", padx=24, pady=(16, 8))
        else:
            self._banner.pack_forget()

        self._table.clear_rows()
        for i, item in enumerate(items):
            days_label = ctk.CTkLabel(
                self._table,
                text=str(item.get("days_overdue", "—")),
                font=ctk.CTkFont(family=FONT_MONO, size=13, weight="bold"),
                text_color=DANGER,
            )
            last = item.get("last_maintenance_date") or "Never"
            self._table.add_row(
                [
                    item.get("name", "—"),
                    item.get("location", "—"),
                    item.get("next_maintenance_due", "—"),
                    days_label,
                    last,
                ],
                even=(i % 2 == 1),
            )
