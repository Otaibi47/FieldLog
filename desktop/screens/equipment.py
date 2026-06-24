import customtkinter as ctk
from datetime import date
from components.data_table import DataTable
from components.status_badge import StatusBadge
from config import (
    BG, SURFACE, BORDER, TEXT_PRIMARY, TEXT_SECONDARY,
    ACCENT, DANGER, FONT_FAMILY,
)


class EquipmentScreen(ctk.CTkFrame):
    def __init__(self, master, api_client, **kwargs):
        super().__init__(master, fg_color=BG, **kwargs)
        self.api = api_client
        self._build()
        self.refresh()

    def _build(self):
        # Header row
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(24, 8))

        ctk.CTkLabel(
            header,
            text="Equipment",
            font=ctk.CTkFont(family=FONT_FAMILY, size=20, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).pack(side="left")

        ctk.CTkButton(
            header,
            text="+ Add Equipment",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            fg_color=ACCENT,
            hover_color="#1E40AF",
            corner_radius=6,
            command=self._open_add_form,
        ).pack(side="right")

        # Table
        self._table = DataTable(
            self,
            columns=[
                ("Name", 3),
                ("Type", 2),
                ("Location", 3),
                ("Status", 2),
                ("Next Due", 2),
                ("Actions", 2),
            ],
            height=500,
        )
        self._table.pack(fill="both", expand=True, padx=24, pady=(0, 24))

    def refresh(self):
        try:
            items = self.api.get_equipment()
        except Exception:
            items = []

        self._table.clear_rows()
        for i, item in enumerate(items):
            badge = StatusBadge(self._table, status=item.get("status", "operational"))

            actions = ctk.CTkFrame(self._table, fg_color="transparent")
            edit_btn = ctk.CTkButton(
                actions,
                text="Edit",
                width=48,
                height=24,
                font=ctk.CTkFont(family=FONT_FAMILY, size=12),
                fg_color="transparent",
                text_color=ACCENT,
                hover_color="#EFF6FF",
                corner_radius=4,
                command=lambda it=item: self._open_edit_form(it),
            )
            edit_btn.pack(side="left", padx=(0, 4))

            del_btn = ctk.CTkButton(
                actions,
                text="Delete",
                width=54,
                height=24,
                font=ctk.CTkFont(family=FONT_FAMILY, size=12),
                fg_color="transparent",
                text_color=DANGER,
                hover_color="#FEF2F2",
                corner_radius=4,
                command=lambda it=item: self._confirm_delete(it),
            )
            del_btn.pack(side="left")

            self._table.add_row(
                [
                    item.get("name", "—"),
                    item.get("type", "—").title(),
                    item.get("location", "—"),
                    badge,
                    item.get("next_maintenance_due", "—"),
                    actions,
                ],
                even=(i % 2 == 1),
            )

    def _open_add_form(self):
        EquipmentFormModal(self, self.api, on_save=self.refresh)

    def _open_edit_form(self, item: dict):
        EquipmentFormModal(self, self.api, on_save=self.refresh, item=item)

    def _confirm_delete(self, item: dict):
        dlg = ctk.CTkToplevel(self)
        dlg.title("Confirm Delete")
        dlg.geometry("360x140")
        dlg.resizable(False, False)
        dlg.grab_set()
        ctk.CTkLabel(
            dlg,
            text=f"Delete \"{item['name']}\"?\nThis will also remove all maintenance logs.",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            text_color=TEXT_PRIMARY,
        ).pack(pady=(24, 16))
        btn_row = ctk.CTkFrame(dlg, fg_color="transparent")
        btn_row.pack()
        ctk.CTkButton(
            btn_row, text="Cancel", fg_color="#F3F4F6", text_color=TEXT_PRIMARY,
            hover_color=BORDER, corner_radius=6, command=dlg.destroy,
        ).pack(side="left", padx=8)
        ctk.CTkButton(
            btn_row, text="Delete", fg_color=DANGER, hover_color="#B91C1C",
            corner_radius=6, command=lambda: self._do_delete(item["id"], dlg),
        ).pack(side="left")

    def _do_delete(self, item_id: str, dlg):
        try:
            self.api.delete_equipment(item_id)
        except Exception:
            pass
        dlg.destroy()
        self.refresh()


class EquipmentFormModal(ctk.CTkToplevel):
    def __init__(self, master, api_client, on_save, item: dict = None):
        super().__init__(master)
        self.api = api_client
        self.on_save = on_save
        self.item = item
        self.title("Edit Equipment" if item else "Add Equipment")
        self.geometry("480x540")
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

        v = self.item or {}
        self._name = field("Equipment Name", "e.g. Compressor Unit C-04", v.get("name", ""))
        self._type_var = ctk.StringVar(value=v.get("type", "compressor"))
        ctk.CTkLabel(form, text="Type", font=ctk.CTkFont(family=FONT_FAMILY, size=12),
                     text_color=TEXT_SECONDARY, anchor="w").pack(fill="x", pady=(8, 2))
        ctk.CTkOptionMenu(form, values=["compressor", "pipeline", "rig", "pump", "valve", "other"],
                          variable=self._type_var, font=ctk.CTkFont(family=FONT_FAMILY, size=13),
                          corner_radius=6, fg_color=SURFACE, button_color=ACCENT,
                          ).pack(fill="x")
        self._location = field("Location", "e.g. Block 7 - North Field", v.get("location", ""))
        self._status_var = ctk.StringVar(value=v.get("status", "operational"))
        ctk.CTkLabel(form, text="Status", font=ctk.CTkFont(family=FONT_FAMILY, size=12),
                     text_color=TEXT_SECONDARY, anchor="w").pack(fill="x", pady=(8, 2))
        ctk.CTkOptionMenu(form, values=["operational", "degraded", "offline"],
                          variable=self._status_var, font=ctk.CTkFont(family=FONT_FAMILY, size=13),
                          corner_radius=6, fg_color=SURFACE, button_color=ACCENT,
                          ).pack(fill="x")
        self._last_maint = field("Last Maintenance Date (YYYY-MM-DD)", "2024-01-15",
                                 v.get("last_maintenance_date", "") or "")
        self._next_due = field("Next Maintenance Due (YYYY-MM-DD)", "2024-07-15",
                               v.get("next_maintenance_due", "") or "")
        self._notes = field("Notes (optional)", "", v.get("notes", "") or "")

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(pady=16)
        ctk.CTkButton(btn_row, text="Cancel", fg_color="#F3F4F6", text_color=TEXT_PRIMARY,
                      hover_color=BORDER, corner_radius=6, command=self.destroy).pack(side="left", padx=8)
        ctk.CTkButton(btn_row, text="Save", fg_color=ACCENT, hover_color="#1E40AF",
                      corner_radius=6, command=self._save).pack(side="left")

    def _save(self):
        data = {
            "name": self._name.get().strip(),
            "type": self._type_var.get(),
            "location": self._location.get().strip(),
            "status": self._status_var.get(),
            "next_maintenance_due": self._next_due.get().strip(),
            "notes": self._notes.get().strip() or None,
        }
        last = self._last_maint.get().strip()
        if last:
            data["last_maintenance_date"] = last
        try:
            if self.item:
                self.api.update_equipment(self.item["id"], data)
            else:
                self.api.create_equipment(data)
            self.on_save()
            self.destroy()
        except Exception as e:
            ctk.CTkLabel(self, text=f"Error: {e}", text_color=DANGER,
                         font=ctk.CTkFont(family=FONT_FAMILY, size=12)).pack()
