import threading
import customtkinter as ctk
from datetime import date, timedelta
from components.data_table import DataTable
from config import (
    BG, SURFACE, BORDER, TEXT_PRIMARY, TEXT_SECONDARY,
    ACCENT, SUCCESS, WARNING, DANGER, FONT_FAMILY,
)

# Action type → (text label, text color, bg color)
_ACTION_STYLE = {
    "created":        ("Created",  SUCCESS, "#0F2B1F"),
    "updated":        ("Updated",  ACCENT,  "#172554"),
    "deleted":        ("Deleted",  DANGER,  "#1C0B0B"),
    "status_changed": ("Status",   WARNING, "#1C1200"),
}


def _action_badge(action_type: str):
    def _build(frame):
        text, fg, bg = _ACTION_STYLE.get(
            action_type, (action_type.title(), TEXT_SECONDARY, SURFACE)
        )
        wrap = ctk.CTkFrame(frame, fg_color=bg, corner_radius=4)
        wrap.pack(anchor="w", pady=6)
        ctk.CTkLabel(
            wrap, text=text,
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            text_color=fg, fg_color="transparent",
        ).pack(padx=8, pady=3)
    return _build


class AuditLogScreen(ctk.CTkFrame):
    def __init__(self, master, api_client, **kwargs):
        super().__init__(master, fg_color=BG, **kwargs)
        self.api = api_client
        self._all_logs: list[dict] = []
        self._build()

    def _build(self):
        # ── Header ────────────────────────────────────────────────────────────
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=24, pady=(28, 0))
        ctk.CTkLabel(
            hdr, text="Audit Log",
            font=ctk.CTkFont(family=FONT_FAMILY, size=20, weight="bold"),
            text_color=TEXT_PRIMARY, fg_color="transparent",
        ).pack(anchor="w")
        ctk.CTkLabel(
            hdr, text="Every action in the system, automatically recorded",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            text_color=TEXT_SECONDARY, fg_color="transparent",
        ).pack(anchor="w", pady=(2, 0))
        ctk.CTkFrame(self, height=1, fg_color=BORDER, corner_radius=0).pack(
            fill="x", pady=(16, 0)
        )

        # ── Filter bar wrapper ─────────────────────────────────────────────────
        # _wrap holds the main bar row + the optional custom date row so that
        # pack_forget/pack on the custom row stays inside _wrap and never
        # jumps below the table.
        _wrap = ctk.CTkFrame(self, fg_color="transparent")
        _wrap.pack(fill="x", padx=24, pady=(14, 0))

        bar = ctk.CTkFrame(_wrap, fg_color="transparent")
        bar.pack(fill="x")

        # Action filter
        ctk.CTkLabel(
            bar, text="Action:",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            text_color=TEXT_SECONDARY, fg_color="transparent",
        ).pack(side="left", padx=(0, 8))

        self._action_var = ctk.StringVar(value="All")
        ctk.CTkOptionMenu(
            bar,
            values=["All", "Created", "Updated", "Deleted", "Status Changed"],
            variable=self._action_var,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            fg_color=SURFACE, button_color=BORDER,
            button_hover_color="#3D4F6B",
            text_color=TEXT_PRIMARY,
            dropdown_fg_color=SURFACE,
            dropdown_text_color=TEXT_PRIMARY,
            corner_radius=6,
            width=170, height=34,
            command=lambda _: self._apply_filter(),
        ).pack(side="left")

        # Separator pip
        ctk.CTkFrame(bar, width=1, fg_color=BORDER, corner_radius=0).pack(
            side="left", fill="y", padx=(12, 12)
        )

        # Date range filter
        ctk.CTkLabel(
            bar, text="Period:",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            text_color=TEXT_SECONDARY, fg_color="transparent",
        ).pack(side="left", padx=(0, 8))

        self._date_var = ctk.StringVar(value="All Time")
        ctk.CTkOptionMenu(
            bar,
            values=["All Time", "Last 7 Days", "Last 30 Days", "Last 90 Days", "Custom Range"],
            variable=self._date_var,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            fg_color=SURFACE, button_color=BORDER,
            button_hover_color="#3D4F6B",
            text_color=TEXT_PRIMARY,
            dropdown_fg_color=SURFACE,
            dropdown_text_color=TEXT_PRIMARY,
            corner_radius=6,
            width=148, height=34,
            command=self._on_date_change,
        ).pack(side="left")

        # Refresh button
        ctk.CTkButton(
            bar, text="Refresh",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            fg_color=SURFACE, hover_color=BORDER,
            border_width=1, border_color=BORDER,
            text_color=TEXT_PRIMARY,
            corner_radius=6, height=34, width=90,
            command=self.refresh,
        ).pack(side="left", padx=(12, 0))

        self._count_label = ctk.CTkLabel(
            bar, text="",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color=TEXT_SECONDARY, fg_color="transparent",
        )
        self._count_label.pack(side="right")

        # ── Custom date row (hidden until "Custom Range" selected) ────────────
        self._custom_row = ctk.CTkFrame(_wrap, fg_color="transparent")
        # Not packed initially; shown in _on_date_change

        ctk.CTkLabel(
            self._custom_row, text="From:",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color=TEXT_SECONDARY, fg_color="transparent",
        ).pack(side="left", padx=(0, 4))
        self._from_entry = ctk.CTkEntry(
            self._custom_row, placeholder_text="YYYY-MM-DD",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            fg_color=SURFACE, border_color=BORDER, border_width=1,
            corner_radius=6, height=32, width=130,
        )
        self._from_entry.pack(side="left", padx=(0, 12))

        ctk.CTkLabel(
            self._custom_row, text="To:",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color=TEXT_SECONDARY, fg_color="transparent",
        ).pack(side="left", padx=(0, 4))
        self._to_entry = ctk.CTkEntry(
            self._custom_row, placeholder_text="YYYY-MM-DD",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            fg_color=SURFACE, border_color=BORDER, border_width=1,
            corner_radius=6, height=32, width=130,
        )
        self._to_entry.pack(side="left", padx=(0, 12))

        ctk.CTkButton(
            self._custom_row, text="Apply",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            fg_color=ACCENT, hover_color="#1E40AF", text_color="#FFFFFF",
            corner_radius=6, height=32, width=70,
            command=self._apply_filter,
        ).pack(side="left")

        ctk.CTkFrame(self, height=1, fg_color=BORDER, corner_radius=0).pack(
            fill="x", pady=(12, 0)
        )

        # ── Table ─────────────────────────────────────────────────────────────
        self._table = DataTable(
            self,
            columns=[
                ("Timestamp",   140),
                ("Action",       95),
                ("Entity",       90),
                ("Name",        175),
                ("Description", 280),
            ],
        )
        self._table.pack(fill="both", expand=True, padx=24, pady=(0, 24))

    # ── date range toggle ─────────────────────────────────────────────────────

    def _on_date_change(self, value: str):
        if value == "Custom Range":
            self._custom_row.pack(fill="x", pady=(8, 0))
        else:
            self._custom_row.pack_forget()
            self._apply_filter()

    # ── data ──────────────────────────────────────────────────────────────────

    def refresh(self):
        threading.Thread(target=self._load, daemon=True).start()

    def _load(self):
        try:
            logs = self.api.get_audit_logs()
        except Exception:
            logs = []
        self.after(0, lambda d=logs: self._store_and_render(d))

    def _store_and_render(self, logs: list[dict]):
        self._all_logs = logs
        self._apply_filter()

    # ── filtering ─────────────────────────────────────────────────────────────

    def _apply_filter(self):
        result = self._all_logs[:]

        # Action filter
        action = self._action_var.get()
        action_map = {
            "Created":        "created",
            "Updated":        "updated",
            "Deleted":        "deleted",
            "Status Changed": "status_changed",
        }
        if action != "All":
            result = [l for l in result if l.get("action_type") == action_map.get(action)]

        # Date range filter
        dr = self._date_var.get()
        today = date.today()
        cutoff_from = cutoff_to = None

        if dr == "Last 7 Days":
            cutoff_from, cutoff_to = today - timedelta(days=7), today
        elif dr == "Last 30 Days":
            cutoff_from, cutoff_to = today - timedelta(days=30), today
        elif dr == "Last 90 Days":
            cutoff_from, cutoff_to = today - timedelta(days=90), today
        elif dr == "Custom Range":
            try:
                cutoff_from = date.fromisoformat(self._from_entry.get().strip())
                cutoff_to   = date.fromisoformat(self._to_entry.get().strip())
            except ValueError:
                cutoff_from = cutoff_to = None

        if cutoff_from and cutoff_to:
            filtered = []
            for log in result:
                raw = (log.get("timestamp") or "")[:10]
                try:
                    if cutoff_from <= date.fromisoformat(raw) <= cutoff_to:
                        filtered.append(log)
                except ValueError:
                    pass
            result = filtered

        self._render(result)

    # ── render ────────────────────────────────────────────────────────────────

    def _render(self, logs: list[dict]):
        self._table.clear_rows()
        self._count_label.configure(text=f"{len(logs)} record{'s' if len(logs) != 1 else ''}")

        for i, entry in enumerate(logs):
            ts = entry.get("timestamp", "")
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                ts_str = dt.strftime("%b %d  %I:%M %p")
            except Exception:
                ts_str = (ts or "")[:16]

            entity_raw = entry.get("entity_type", "")
            entity_label = {
                "equipment":       "Equipment",
                "maintenance_log": "Maint. Log",
            }.get(entity_raw, entity_raw.title())

            self._table.add_row([
                ts_str,
                _action_badge(entry.get("action_type", "")),
                entity_label,
                entry.get("entity_name") or "—",
                entry.get("description") or "—",
            ], even=(i % 2 == 1))
