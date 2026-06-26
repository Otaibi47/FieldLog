import threading
import customtkinter as ctk
from components.data_table import DataTable
from config import (
    BG, SURFACE, BORDER, TEXT_PRIMARY, TEXT_SECONDARY,
    SUCCESS, DANGER, DANGER_LIGHT, FONT_FAMILY, FONT_MONO,
)


class AlertsScreen(ctk.CTkFrame):
    def __init__(self, master, api_client, **kwargs):
        super().__init__(master, fg_color=BG, **kwargs)
        self.api = api_client
        self._build()

    def _build(self):
        # Use grid internally so grid_remove()/grid() preserve row positions
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)   # table / empty row expands

        # ── Row 0: page header ─────────────────────────────────────────────
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=24, pady=(28, 0))

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

        # ── Row 1: divider ─────────────────────────────────────────────────
        ctk.CTkFrame(self, height=1, fg_color=BORDER, corner_radius=0).grid(
            row=1, column=0, sticky="ew", pady=(16, 0)
        )

        # ── Row 2: red banner (hidden until items exist) ───────────────────
        self._banner = ctk.CTkFrame(self, fg_color=DANGER_LIGHT, corner_radius=0)
        self._banner.grid(row=2, column=0, sticky="ew", padx=24, pady=(12, 0))
        self._banner.grid_remove()   # hidden; grid_remove preserves row slot

        rule = ctk.CTkFrame(self._banner, width=4, fg_color=DANGER, corner_radius=0)
        rule.pack(side="left", fill="y")
        rule.pack_propagate(False)

        banner_body = ctk.CTkFrame(self._banner, fg_color="transparent")
        banner_body.pack(side="left", fill="both", expand=True, padx=14, pady=10)

        self._banner_title = ctk.CTkLabel(
            banner_body, text="",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
            text_color=DANGER, fg_color="transparent", anchor="w",
        )
        self._banner_title.pack(fill="x")
        ctk.CTkLabel(
            banner_body,
            text="Address these items immediately to avoid equipment failure.",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color=DANGER, fg_color="transparent", anchor="w",
        ).pack(fill="x", pady=(1, 0))

        # ── Row 3: data table ──────────────────────────────────────────────
        self._table = DataTable(
            self,
            columns=[
                ("Equipment Name", 210),
                ("Location",       155),
                ("Due Date",       105),
                ("Days Overdue",   120),
                ("Last Maintained",135),
            ],
            height=460,
        )
        self._table.grid(row=3, column=0, sticky="nsew", padx=24, pady=(16, 24))

        # ── Row 3: empty state (same slot, hidden until no items) ──────────
        self._empty = ctk.CTkFrame(self, fg_color="transparent")
        self._empty.grid(row=3, column=0, sticky="nsew")
        self._empty.grid_remove()

        ctk.CTkLabel(
            self._empty, text="✓",
            font=ctk.CTkFont(family=FONT_FAMILY, size=48),
            text_color=SUCCESS, fg_color="transparent",
        ).pack()
        ctk.CTkLabel(
            self._empty, text="All equipment is on schedule",
            font=ctk.CTkFont(family=FONT_FAMILY, size=16, weight="bold"),
            text_color=TEXT_PRIMARY, fg_color="transparent",
        ).pack(pady=(8, 2))
        ctk.CTkLabel(
            self._empty, text="No overdue maintenance items found",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            text_color=TEXT_SECONDARY, fg_color="transparent",
        ).pack()

    # ── data ──────────────────────────────────────────────────────────────────

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
            self._banner.grid()       # restore to row 2
            self._empty.grid_remove()
            self._table.grid()        # restore to row 3
        else:
            self._banner.grid_remove()
            self._table.grid_remove()
            self._empty.grid()        # restore to row 3
            return

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
