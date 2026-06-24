import threading
import customtkinter as ctk
from components.data_table import DataTable
from config import (
    BG, SURFACE, BORDER, TEXT_PRIMARY, TEXT_SECONDARY,
    DANGER, DANGER_LIGHT, FONT_FAMILY, FONT_MONO,
)


class AlertsScreen(ctk.CTkFrame):
    def __init__(self, master, api_client, **kwargs):
        super().__init__(master, fg_color=BG, **kwargs)
        self.api = api_client
        self._build()

    def _build(self):
        # Page header
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=24, pady=(28, 0))

        ctk.CTkLabel(
            hdr, text="Overdue Equipment",
            font=ctk.CTkFont(family=FONT_FAMILY, size=20, weight="bold"),
            text_color=TEXT_PRIMARY, fg_color="transparent",
        ).pack(anchor="w")
        ctk.CTkLabel(
            hdr, text="Equipment past their next scheduled maintenance date",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            text_color=TEXT_SECONDARY, fg_color="transparent",
        ).pack(anchor="w", pady=(2, 0))

        ctk.CTkFrame(self, height=1, fg_color=BORDER, corner_radius=0).pack(
            fill="x", pady=(16, 0)
        )

        # Alert banner (shown only when there are overdue items)
        self._banner = ctk.CTkFrame(
            self,
            fg_color=DANGER_LIGHT,
            corner_radius=0,
            border_width=0,
        )
        # 3px left rule on the banner itself
        self._banner_rule = ctk.CTkFrame(
            self._banner, width=4, fg_color=DANGER, corner_radius=0
        )
        self._banner_rule.pack(side="left", fill="y")
        self._banner_rule.pack_propagate(False)

        banner_text_frame = ctk.CTkFrame(self._banner, fg_color="transparent")
        banner_text_frame.pack(side="left", fill="both", expand=True, padx=14, pady=12)

        self._banner_title = ctk.CTkLabel(
            banner_text_frame, text="",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
            text_color=DANGER, fg_color="transparent",
            anchor="center",
        )
        self._banner_title.pack(fill="x")
        self._banner_sub = ctk.CTkLabel(
            banner_text_frame,
            text="Address these items immediately to avoid equipment failure.",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color=DANGER, fg_color="transparent",
            anchor="center",
        )
        self._banner_sub.pack(fill="x", pady=(1, 0))

        # Table
        self._table = DataTable(
            self,
            columns=[
                ("Equipment Name", 210),
                ("Location",       155),
                ("Due Date",       105),
                ("Days Overdue",   120),
                ("Last Maintained",135),
            ],
            height=480,
        )
        self._table.pack(fill="both", expand=True, padx=24, pady=(16, 24))

    # ------------------------------------------------------------------ data

    def refresh(self):
        threading.Thread(target=self._load, daemon=True).start()

    def _load(self):
        try:
            items = self.api.get_overdue()
        except Exception:
            items = []
        self.after(0, lambda d=items: self._render(d))

    def _render(self, items):
        if items:
            count = len(items)
            noun = "item" if count == 1 else "items"
            self._banner_title.configure(
                text=f"{count} {noun} require immediate maintenance attention"
            )
            self._banner.pack(fill="x", padx=24, pady=(16, 0), before=self._table)
        else:
            self._banner.pack_forget()

        self._table.clear_rows()
        for i, item in enumerate(items):
            days = str(item.get("days_overdue", "—"))

            def make_days(d):
                def _b(f):
                    ctk.CTkLabel(
                        f, text=d,
                        font=ctk.CTkFont(family=FONT_MONO, size=14, weight="bold"),
                        text_color=DANGER, fg_color="transparent",
                        anchor="center",
                    ).pack(fill="both", expand=True, pady=6)
                return _b

            self._table.add_row([
                item.get("name", "—"),
                item.get("location", "—"),
                item.get("next_maintenance_due", "—"),
                make_days(days),
                item.get("last_maintenance_date") or "Never",
            ], even=(i % 2 == 1))
