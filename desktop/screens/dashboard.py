import customtkinter as ctk
from datetime import datetime
from components.stat_card import StatCard
from components.data_table import DataTable
from config import (
    BG, TEXT_PRIMARY, TEXT_SECONDARY, FONT_FAMILY,
    DANGER, DANGER_LIGHT, BORDER, SURFACE, WARNING, SUCCESS,
)


class DashboardScreen(ctk.CTkScrollableFrame):
    def __init__(self, master, api_client, **kwargs):
        super().__init__(master, fg_color=BG, **kwargs)
        self.api = api_client
        self._build()
        self.refresh()

    def _build(self):
        # Page title
        ctk.CTkLabel(
            self,
            text="Dashboard",
            font=ctk.CTkFont(family=FONT_FAMILY, size=20, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).pack(anchor="w", pady=(24, 2))
        ctk.CTkLabel(
            self,
            text="Overview of equipment health and recent activity",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            text_color=TEXT_SECONDARY,
        ).pack(anchor="w", pady=(0, 20))

        # Stat cards row
        cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        cards_frame.pack(fill="x", pady=(0, 24))
        for i in range(4):
            cards_frame.columnconfigure(i, weight=1)

        self._card_total = StatCard(cards_frame, "🔧", "—", "Total Equipment")
        self._card_total.grid(row=0, column=0, padx=(0, 8), sticky="ew")

        self._card_operational = StatCard(cards_frame, "✅", "—", "Operational", value_color=SUCCESS)
        self._card_operational.grid(row=0, column=1, padx=4, sticky="ew")

        self._card_overdue = StatCard(cards_frame, "⚠️", "—", "Overdue", value_color=DANGER)
        self._card_overdue.grid(row=0, column=2, padx=4, sticky="ew")

        self._card_logs = StatCard(cards_frame, "📋", "—", "Logs This Month")
        self._card_logs.grid(row=0, column=3, padx=(8, 0), sticky="ew")

        # Recent Maintenance section
        ctk.CTkLabel(
            self,
            text="Recent Maintenance",
            font=ctk.CTkFont(family=FONT_FAMILY, size=15, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).pack(anchor="w", pady=(0, 8))

        self._recent_table = DataTable(
            self,
            columns=[("Equipment", 3), ("Type", 2), ("Performed By", 2), ("Date", 2), ("Next Due", 2)],
            height=180,
        )
        self._recent_table.pack(fill="x", pady=(0, 24))

        # Overdue Alerts section
        ctk.CTkLabel(
            self,
            text="Overdue Alerts",
            font=ctk.CTkFont(family=FONT_FAMILY, size=15, weight="bold"),
            text_color=DANGER,
        ).pack(anchor="w", pady=(0, 8))

        self._alerts_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._alerts_frame.pack(fill="x", pady=(0, 24))

    def refresh(self):
        try:
            summary = self.api.get_dashboard_summary()
            self._card_total.update_value(str(summary["total_equipment"]))
            self._card_operational.update_value(str(summary["operational_count"]))
            self._card_overdue.update_value(str(summary["overdue_count"]))
            self._card_logs.update_value(str(summary["logs_this_month"]))
        except Exception:
            pass

        try:
            logs = self.api.get_maintenance_logs()[:5]
            self._recent_table.clear_rows()
            for i, log in enumerate(logs):
                date_str = log["performed_at"][:10] if log.get("performed_at") else "—"
                self._recent_table.add_row(
                    [
                        log.get("equipment_name") or "—",
                        log.get("maintenance_type", "—").title(),
                        log.get("performed_by", "—"),
                        date_str,
                        log.get("next_due_date", "—"),
                    ],
                    even=(i % 2 == 1),
                )
        except Exception:
            pass

        try:
            overdue = self.api.get_overdue()[:3]
            for w in self._alerts_frame.winfo_children():
                w.destroy()
            for item in overdue:
                self._add_alert_card(item)
            if not overdue:
                ctk.CTkLabel(
                    self._alerts_frame,
                    text="No overdue items",
                    text_color=TEXT_SECONDARY,
                    font=ctk.CTkFont(family=FONT_FAMILY, size=13),
                ).pack(anchor="w")
        except Exception:
            pass

    def _add_alert_card(self, item: dict):
        card = ctk.CTkFrame(
            self._alerts_frame,
            fg_color=DANGER_LIGHT,
            corner_radius=8,
            border_width=1,
            border_color=DANGER,
        )
        card.pack(fill="x", pady=4)

        # Left rule
        rule = ctk.CTkFrame(card, width=3, fg_color=DANGER, corner_radius=0)
        rule.pack(side="left", fill="y")

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(side="left", fill="both", expand=True, padx=12, pady=10)

        ctk.CTkLabel(
            inner,
            text=item.get("name", "—"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).pack(anchor="w")
        ctk.CTkLabel(
            inner,
            text=f"{item.get('location', '—')}  ·  {item.get('days_overdue', 0)} days overdue",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=DANGER,
        ).pack(anchor="w")
