import threading
import customtkinter as ctk
from components.stat_card import StatCard
from components.data_table import DataTable
from components.loading import LoadingFrame, ErrorFrame
from config import (
    BG, BORDER, TEXT_PRIMARY, TEXT_SECONDARY,
    ACCENT, SUCCESS, WARNING, DANGER, DANGER_LIGHT, FONT_FAMILY,
)


class DashboardScreen(ctk.CTkFrame):
    def __init__(self, master, api_client, **kwargs):
        super().__init__(master, fg_color=BG, **kwargs)
        self.api = api_client
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # ── Row 0: page header ─────────────────────────────────────────────
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=24, pady=(28, 0))
        ctk.CTkLabel(
            hdr, text="Dashboard",
            font=ctk.CTkFont(family=FONT_FAMILY, size=20, weight="bold"),
            text_color=TEXT_PRIMARY, fg_color="transparent",
        ).pack(anchor="w")
        ctk.CTkLabel(
            hdr, text="Overview of equipment health and recent activity",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            text_color=TEXT_SECONDARY, fg_color="transparent",
        ).pack(anchor="w", pady=(2, 0))

        # ── Row 1: divider ─────────────────────────────────────────────────
        ctk.CTkFrame(self, height=1, fg_color=BORDER, corner_radius=0).grid(
            row=1, column=0, sticky="ew", pady=(16, 0)
        )

        # ── Row 2: scrollable content (hidden until data arrives) ──────────
        self._content = ctk.CTkScrollableFrame(self, fg_color=BG, corner_radius=0)
        self._content.grid(row=2, column=0, sticky="nsew")
        self._content.grid_remove()

        # ── Row 2: loading (shown on first navigation) ─────────────────────
        self._loading = LoadingFrame(self, "Loading dashboard")
        self._loading.grid(row=2, column=0, sticky="nsew")

        # ── Row 2: error (shown on API failure) ────────────────────────────
        self._error_frame = ErrorFrame(self, on_retry=self.refresh)
        self._error_frame.grid(row=2, column=0, sticky="nsew")
        self._error_frame.grid_remove()

        # Build content structure inside _content (not yet visible)
        self._build_stat_cards()
        self._build_recent_section()
        self._build_alerts_section()

    # ── stat cards ────────────────────────────────────────────────────────────

    def _build_stat_cards(self):
        grid = ctk.CTkFrame(self._content, fg_color="transparent")
        grid.pack(fill="x", padx=24, pady=(20, 0))
        for i in range(4):
            grid.columnconfigure(i, weight=1)

        self._card_total = StatCard(
            grid, icon="⚙", value="—", label="Total Equipment", accent_color=ACCENT,
        )
        self._card_total.grid(row=0, column=0, padx=(0, 6), sticky="ew")

        self._card_op = StatCard(
            grid, icon="✓", value="—", label="Operational", accent_color=SUCCESS,
        )
        self._card_op.grid(row=0, column=1, padx=3, sticky="ew")

        self._card_overdue = StatCard(
            grid, icon="!", value="—", label="Overdue", accent_color=DANGER,
        )
        self._card_overdue.grid(row=0, column=2, padx=3, sticky="ew")

        self._card_logs = StatCard(
            grid, icon="#", value="—", label="Logs This Month", accent_color=WARNING,
        )
        self._card_logs.grid(row=0, column=3, padx=(6, 0), sticky="ew")

    # ── recent maintenance ────────────────────────────────────────────────────

    def _build_recent_section(self):
        self._section_label("Recent Maintenance", pady=(28, 10))

        self._recent_table = DataTable(
            self._content,
            columns=[
                ("Equipment",    180),
                ("Type",         100),
                ("Performed By", 150),
                ("Date",         110),
                ("Next Due",     110),
            ],
            height=220,
        )
        self._recent_table.pack(fill="x", padx=24)

    # ── overdue alerts ────────────────────────────────────────────────────────

    def _build_alerts_section(self):
        self._section_label("Overdue Alerts", pady=(28, 10), color=DANGER)
        self._alerts_frame = ctk.CTkFrame(self._content, fg_color="transparent")
        self._alerts_frame.pack(fill="x", padx=24, pady=(0, 28))

    def _section_label(self, text: str, pady=(24, 8), color=TEXT_PRIMARY):
        ctk.CTkLabel(
            self._content, text=text,
            font=ctk.CTkFont(family=FONT_FAMILY, size=15, weight="bold"),
            text_color=color, fg_color="transparent",
        ).pack(anchor="w", padx=24, pady=pady)

    # ── loading / error helpers ───────────────────────────────────────────────

    def _show_loading(self):
        self._error_frame.grid_remove()
        self._content.grid_remove()
        self._loading.grid()
        self._loading.start()

    def _show_error(self):
        self._loading.stop()
        self._loading.grid_remove()
        self._content.grid_remove()
        self._error_frame.grid()

    def _show_content(self):
        self._loading.stop()
        self._loading.grid_remove()
        self._error_frame.grid_remove()
        self._content.grid()

    # ── data ──────────────────────────────────────────────────────────────────

    def refresh(self):
        self._show_loading()
        threading.Thread(target=self._load, daemon=True).start()

    def _load(self):
        try:
            summary = self.api.get_dashboard_summary()
        except Exception:
            self.after(0, self._show_error)
            return
        try:
            logs = self.api.get_maintenance_logs()[:5]
        except Exception:
            logs = []
        try:
            overdue = self.api.get_overdue()[:3]
        except Exception:
            overdue = []
        self.after(0, lambda: self._render(summary, logs, overdue))

    def _render(self, summary, logs, overdue):
        self._show_content()

        if summary:
            self._card_total.update_value(str(summary["total_equipment"]))
            self._card_op.update_value(str(summary["operational_count"]))
            self._card_overdue.update_value(
                str(summary["overdue_count"]),
                color=DANGER if summary["overdue_count"] > 0 else TEXT_PRIMARY,
            )
            self._card_logs.update_value(str(summary["logs_this_month"]))

        self._recent_table.clear_rows()
        for i, log in enumerate(logs or []):
            date_str = (log.get("performed_at") or "")[:10] or "—"
            self._recent_table.add_row([
                log.get("equipment_name") or "—",
                log.get("maintenance_type", "—").title(),
                log.get("performed_by", "—"),
                date_str,
                log.get("next_due_date", "—"),
            ], even=(i % 2 == 1))

        for w in self._alerts_frame.winfo_children():
            w.destroy()

        if overdue:
            for item in overdue:
                self._add_alert_card(item)
        else:
            ctk.CTkLabel(
                self._alerts_frame,
                text="No overdue items — everything is on schedule.",
                font=ctk.CTkFont(family=FONT_FAMILY, size=13),
                text_color=TEXT_SECONDARY, fg_color="transparent",
            ).pack(anchor="w", pady=4)

    def _add_alert_card(self, item: dict):
        card = ctk.CTkFrame(
            self._alerts_frame,
            fg_color=DANGER_LIGHT,
            corner_radius=8,
            border_width=1,
            border_color="#7F1D1D",
        )
        card.pack(fill="x", pady=(0, 8))

        rule = ctk.CTkFrame(card, width=3, fg_color=DANGER, corner_radius=0)
        rule.pack(side="left", fill="y")
        rule.pack_propagate(False)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(side="left", fill="both", expand=True, padx=14, pady=12)

        ctk.CTkLabel(
            inner, text=item.get("name", "—"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
            text_color=TEXT_PRIMARY, fg_color="transparent",
        ).pack(anchor="w")
        ctk.CTkLabel(
            inner,
            text=f"{item.get('location', '—')}  ·  {item.get('days_overdue', 0)} days overdue",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color=DANGER, fg_color="transparent",
        ).pack(anchor="w", pady=(2, 0))

        badge = ctk.CTkFrame(card, fg_color="transparent")
        badge.pack(side="right", padx=16)
        ctk.CTkLabel(
            badge, text=str(item.get("days_overdue", 0)),
            font=ctk.CTkFont(family=FONT_FAMILY, size=22, weight="bold"),
            text_color=DANGER, fg_color="transparent",
        ).pack()
        ctk.CTkLabel(
            badge, text="days",
            font=ctk.CTkFont(family=FONT_FAMILY, size=10),
            text_color=DANGER, fg_color="transparent",
        ).pack()
