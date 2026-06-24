import customtkinter as ctk
from datetime import datetime, date, timedelta
from components.data_table import DataTable
from config import (
    BG, SURFACE, BORDER, TEXT_PRIMARY, TEXT_SECONDARY,
    ACCENT, DANGER, FONT_FAMILY,
)


class MaintenanceScreen(ctk.CTkFrame):
    def __init__(self, master, api_client, **kwargs):
        super().__init__(master, fg_color=BG, **kwargs)
        self.api = api_client
        self._equipment_list = []
        self._build()
        self.refresh()

    def _build(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(24, 8))

        ctk.CTkLabel(
            header,
            text="Maintenance Log",
            font=ctk.CTkFont(family=FONT_FAMILY, size=20, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).pack(side="left")

        self._filter_var = ctk.StringVar(value="All Equipment")
        self._filter_menu = ctk.CTkOptionMenu(
            header,
            values=["All Equipment"],
            variable=self._filter_var,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            corner_radius=6,
            fg_color=SURFACE,
            button_color=ACCENT,
            command=lambda _: self.refresh(),
        )
        self._filter_menu.pack(side="right", padx=(8, 0))

        ctk.CTkButton(
            header,
            text="+ Log Maintenance",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            fg_color=ACCENT,
            hover_color="#1E40AF",
            corner_radius=6,
            command=self._open_log_form,
        ).pack(side="right")

        self._table = DataTable(
            self,
            columns=[
                ("Equipment", 3),
                ("Type", 2),
                ("Performed By", 2),
                ("Date", 2),
                ("Next Due", 2),
            ],
            height=500,
        )
        self._table.pack(fill="both", expand=True, padx=24, pady=(0, 24))

    def refresh(self):
        try:
            self._equipment_list = self.api.get_equipment()
            names = ["All Equipment"] + [e["name"] for e in self._equipment_list]
            self._filter_menu.configure(values=names)
        except Exception:
            self._equipment_list = []

        selected_name = self._filter_var.get()
        eq_id = None
        if selected_name != "All Equipment":
            for e in self._equipment_list:
                if e["name"] == selected_name:
                    eq_id = e["id"]
                    break

        try:
            logs = self.api.get_maintenance_logs(equipment_id=eq_id)
        except Exception:
            logs = []

        self._table.clear_rows()
        for i, log in enumerate(logs):
            date_str = log.get("performed_at", "")[:10] if log.get("performed_at") else "—"
            self._table.add_row(
                [
                    log.get("equipment_name") or "—",
                    log.get("maintenance_type", "—").title(),
                    log.get("performed_by", "—"),
                    date_str,
                    log.get("next_due_date", "—"),
                ],
                even=(i % 2 == 1),
            )

    def _open_log_form(self):
        MaintenanceFormModal(self, self.api, self._equipment_list, on_save=self.refresh)


class MaintenanceFormModal(ctk.CTkToplevel):
    def __init__(self, master, api_client, equipment_list: list, on_save):
        super().__init__(master)
        self.api = api_client
        self.equipment_list = equipment_list
        self.on_save = on_save
        self.title("Log Maintenance")
        self.geometry("480x560")
        self.resizable(False, False)
        self.grab_set()
        self._build()

    def _build(self):
        form = ctk.CTkScrollableFrame(self, fg_color="white")
        form.pack(fill="both", expand=True, padx=24, pady=24)

        def field(label, placeholder="", default=""):
            ctk.CTkLabel(form, text=label, font=ctk.CTkFont(family=FONT_FAMILY, size=12),
                         text_color=TEXT_SECONDARY, anchor="w").pack(fill="x", pady=(8, 2))
            entry = ctk.CTkEntry(form, placeholder_text=placeholder,
                                 font=ctk.CTkFont(family=FONT_FAMILY, size=13),
                                 corner_radius=6, border_color=BORDER, height=36)
            if default:
                entry.insert(0, default)
            entry.pack(fill="x")
            return entry

        # Equipment picker
        eq_names = [e["name"] for e in self.equipment_list]
        self._eq_var = ctk.StringVar(value=eq_names[0] if eq_names else "")
        ctk.CTkLabel(form, text="Equipment", font=ctk.CTkFont(family=FONT_FAMILY, size=12),
                     text_color=TEXT_SECONDARY, anchor="w").pack(fill="x", pady=(8, 2))
        ctk.CTkOptionMenu(form, values=eq_names or ["—"], variable=self._eq_var,
                          font=ctk.CTkFont(family=FONT_FAMILY, size=13),
                          corner_radius=6, fg_color=SURFACE, button_color=ACCENT).pack(fill="x")

        self._type_var = ctk.StringVar(value="routine")
        ctk.CTkLabel(form, text="Maintenance Type", font=ctk.CTkFont(family=FONT_FAMILY, size=12),
                     text_color=TEXT_SECONDARY, anchor="w").pack(fill="x", pady=(8, 2))
        ctk.CTkOptionMenu(form, values=["routine", "corrective", "emergency"],
                          variable=self._type_var, font=ctk.CTkFont(family=FONT_FAMILY, size=13),
                          corner_radius=6, fg_color=SURFACE, button_color=ACCENT).pack(fill="x")

        self._performed_by = field("Performed By", "Technician name")
        self._description = field("Description", "What was done?")
        self._parts = field("Parts Replaced (optional)", "")
        default_date = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        self._performed_at = field("Performed At (ISO datetime)", "2024-06-15T09:00:00", default_date)
        default_next = str(date.today() + timedelta(days=90))
        self._next_due = field("Next Due Date (YYYY-MM-DD)", "2024-09-15", default_next)

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(pady=16)
        ctk.CTkButton(btn_row, text="Cancel", fg_color="#F3F4F6", text_color=TEXT_PRIMARY,
                      hover_color=BORDER, corner_radius=6, command=self.destroy).pack(side="left", padx=8)
        ctk.CTkButton(btn_row, text="Save Log", fg_color=ACCENT, hover_color="#1E40AF",
                      corner_radius=6, command=self._save).pack(side="left")

        self._error_label = ctk.CTkLabel(self, text="", text_color=DANGER,
                                          font=ctk.CTkFont(family=FONT_FAMILY, size=12))
        self._error_label.pack()

    def _save(self):
        eq_name = self._eq_var.get()
        eq_id = next((e["id"] for e in self.equipment_list if e["name"] == eq_name), None)
        if not eq_id:
            self._error_label.configure(text="Please select valid equipment")
            return
        data = {
            "equipment_id": eq_id,
            "performed_by": self._performed_by.get().strip(),
            "maintenance_type": self._type_var.get(),
            "description": self._description.get().strip(),
            "parts_replaced": self._parts.get().strip() or None,
            "performed_at": self._performed_at.get().strip(),
            "next_due_date": self._next_due.get().strip(),
        }
        try:
            self.api.create_maintenance_log(data)
            self.on_save()
            self.destroy()
        except Exception as e:
            self._error_label.configure(text=f"Error: {e}")
