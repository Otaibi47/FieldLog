import threading
import customtkinter as ctk
from datetime import datetime, date, timedelta
from components.data_table import DataTable
from config import (
    BG, SURFACE, BORDER, TEXT_PRIMARY, TEXT_SECONDARY,
    ACCENT, DANGER, FONT_FAMILY,
)
from screens.equipment import _field, _dropdown


# ─────────────────────────── screen ──────────────────────────────────────────

class MaintenanceScreen(ctk.CTkFrame):
    def __init__(self, master, api_client, **kwargs):
        super().__init__(master, fg_color=BG, **kwargs)
        self.api = api_client
        self._equipment_list: list[dict] = []
        self._build()

    def _build(self):
        # Page header
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=24, pady=(28, 0))

        left = ctk.CTkFrame(hdr, fg_color="transparent")
        left.pack(side="left", fill="y")
        ctk.CTkLabel(
            left, text="Maintenance Log",
            font=ctk.CTkFont(family=FONT_FAMILY, size=20, weight="bold"),
            text_color=TEXT_PRIMARY, fg_color="transparent",
        ).pack(anchor="w")
        ctk.CTkLabel(
            left, text="Track all maintenance activity across your equipment",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            text_color=TEXT_SECONDARY, fg_color="transparent",
        ).pack(anchor="w", pady=(2, 0))

        right = ctk.CTkFrame(hdr, fg_color="transparent")
        right.pack(side="right", fill="y", anchor="center")

        self._filter_var = ctk.StringVar(value="All Equipment")
        self._filter_menu = ctk.CTkOptionMenu(
            right, values=["All Equipment"], variable=self._filter_var,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            fg_color=SURFACE,
            button_color="#E5E7EB", button_hover_color="#D1D5DB",
            text_color=TEXT_PRIMARY,
            corner_radius=6, height=36, width=160,
            command=lambda _: self._load_logs(),
        )
        self._filter_menu.pack(side="right", padx=(8, 0))

        ctk.CTkButton(
            right, text="+ Log Maintenance",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            fg_color=ACCENT, hover_color="#1E40AF",
            corner_radius=6, height=36,
            command=self._open_log_form,
        ).pack(side="right")

        ctk.CTkFrame(self, height=1, fg_color=BORDER, corner_radius=0).pack(
            fill="x", pady=(16, 0)
        )

        # Table
        self._table = DataTable(
            self,
            columns=[
                ("Equipment",    190),
                ("Type",         100),
                ("Performed By", 150),
                ("Date",         110),
                ("Next Due",     110),
            ],
            height=520,
        )
        self._table.pack(fill="both", expand=True, padx=24, pady=(16, 24))

    # ------------------------------------------------------------------ data

    def refresh(self):
        threading.Thread(target=self._load_all, daemon=True).start()

    def _load_all(self):
        try:
            eq = self.api.get_equipment()
        except Exception:
            eq = []
        self.after(0, lambda d=eq: self._update_filter(d))
        self._load_logs_data(None)

    def _update_filter(self, equipment_list):
        self._equipment_list = equipment_list
        names = ["All Equipment"] + [e["name"] for e in equipment_list]
        self._filter_menu.configure(values=names)

    def _load_logs(self):
        threading.Thread(target=self._load_logs_data, args=(None,), daemon=True).start()

    def _load_logs_data(self, _):
        selected = self._filter_var.get()
        eq_id = next(
            (e["id"] for e in self._equipment_list if e["name"] == selected), None
        )
        try:
            logs = self.api.get_maintenance_logs(equipment_id=eq_id)
        except Exception:
            logs = []
        self.after(0, lambda d=logs: self._render(d))

    def _render(self, logs):
        self._table.clear_rows()
        for i, log in enumerate(logs):
            date_str = (log.get("performed_at") or "")[:10] or "—"
            self._table.add_row([
                log.get("equipment_name") or "—",
                log.get("maintenance_type", "—").title(),
                log.get("performed_by", "—"),
                date_str,
                log.get("next_due_date", "—"),
            ], even=(i % 2 == 1))

    def _open_log_form(self):
        MaintenanceFormModal(self, self.api, self._equipment_list, on_save=self.refresh)


# ─────────────────────────── modal ───────────────────────────────────────────

class MaintenanceFormModal(ctk.CTkToplevel):
    def __init__(self, master, api_client, equipment_list, on_save):
        super().__init__(master)
        self.api            = api_client
        self.equipment_list = equipment_list
        self.on_save        = on_save
        self.configure(fg_color=SURFACE)
        self.title("Log Maintenance")
        self.geometry("500x640")
        self.resizable(False, False)
        self.grab_set()
        self._build()

    def _build(self):
        # Accent top bar
        ctk.CTkFrame(self, height=4, fg_color=ACCENT, corner_radius=0).pack(fill="x")

        title_bar = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=0)
        title_bar.pack(fill="x", padx=24, pady=(16, 0))
        ctk.CTkLabel(
            title_bar, text="Log Maintenance",
            font=ctk.CTkFont(family=FONT_FAMILY, size=16, weight="bold"),
            text_color=TEXT_PRIMARY, fg_color="transparent",
        ).pack(anchor="w")
        ctk.CTkLabel(
            title_bar, text="Record a completed maintenance event",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color=TEXT_SECONDARY, fg_color="transparent",
        ).pack(anchor="w", pady=(2, 0))

        ctk.CTkFrame(self, height=1, fg_color=BORDER, corner_radius=0).pack(
            fill="x", pady=(14, 0)
        )

        body = ctk.CTkScrollableFrame(self, fg_color=SURFACE, corner_radius=0)
        body.pack(fill="both", expand=True)

        eq_names = [e["name"] for e in self.equipment_list]
        self._eq_var   = _dropdown(body, "Equipment",        eq_names or ["No equipment yet"], eq_names[0] if eq_names else "")
        self._type_var = _dropdown(body, "Maintenance Type", ["routine","corrective","emergency"], "routine")
        self._performed_by = _field(body, "Performed By",    "Technician name")
        self._description  = _field(body, "Description",     "What was done?")
        self._parts        = _field(body, "Parts Replaced (optional)", "")
        self._performed_at = _field(
            body, "Performed At (ISO datetime)", "2024-06-15T09:00:00",
            datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        )
        self._next_due = _field(
            body, "Next Due Date (YYYY-MM-DD)", "2024-09-15",
            str(date.today() + timedelta(days=90)),
        )

        self._error = ctk.CTkLabel(
            body, text="",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color=DANGER, fg_color="transparent",
        )
        self._error.pack(anchor="w", padx=24, pady=(4, 0))

        ctk.CTkFrame(self, height=1, fg_color=BORDER, corner_radius=0).pack(fill="x")
        foot = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=0)
        foot.pack(fill="x", padx=24, pady=16)

        ctk.CTkButton(
            foot, text="Cancel", width=88,
            fg_color=SURFACE, text_color=TEXT_PRIMARY,
            border_width=1, border_color=BORDER,
            hover_color=BG, corner_radius=6,
            command=self.destroy,
        ).pack(side="right", padx=(8, 0))
        ctk.CTkButton(
            foot, text="Save Log", width=110,
            fg_color=ACCENT, hover_color="#1E40AF",
            corner_radius=6, command=self._save,
        ).pack(side="right")

    def _save(self):
        eq_name = self._eq_var.get()
        eq_id   = next((e["id"] for e in self.equipment_list if e["name"] == eq_name), None)
        if not eq_id:
            self._error.configure(text="Please select a valid equipment item.")
            return

        data = {
            "equipment_id":    eq_id,
            "performed_by":    self._performed_by.get().strip(),
            "maintenance_type": self._type_var.get(),
            "description":     self._description.get().strip(),
            "parts_replaced":  self._parts.get().strip() or None,
            "performed_at":    self._performed_at.get().strip(),
            "next_due_date":   self._next_due.get().strip(),
        }

        def _run():
            try:
                self.api.create_maintenance_log(data)
                self.after(0, lambda: (self.on_save(), self.destroy()))
            except Exception as e:
                self.after(0, lambda err=str(e): self._error.configure(text=f"Error: {err}"))

        threading.Thread(target=_run, daemon=True).start()
