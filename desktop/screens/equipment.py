import threading
import customtkinter as ctk
from components.data_table import DataTable
from components.status_badge import StatusBadge
from config import (
    BG, SURFACE, BORDER, TEXT_PRIMARY, TEXT_SECONDARY,
    ACCENT, ACCENT_LIGHT, DANGER, DANGER_LIGHT, FONT_FAMILY,
)


# ─────────────────────────── screen ──────────────────────────────────────────

class EquipmentScreen(ctk.CTkFrame):
    def __init__(self, master, api_client, **kwargs):
        super().__init__(master, fg_color=BG, **kwargs)
        self.api = api_client
        self._build()

    def _build(self):
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=24, pady=(28, 0))

        left = ctk.CTkFrame(hdr, fg_color="transparent")
        left.pack(side="left", fill="y")
        ctk.CTkLabel(
            left, text="Equipment",
            font=ctk.CTkFont(family=FONT_FAMILY, size=20, weight="bold"),
            text_color=TEXT_PRIMARY, fg_color="transparent",
        ).pack(anchor="w")
        ctk.CTkLabel(
            left, text="Register and manage your field equipment",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            text_color=TEXT_SECONDARY, fg_color="transparent",
        ).pack(anchor="w", pady=(2, 0))

        ctk.CTkButton(
            hdr, text="+ Add Equipment",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            fg_color=ACCENT, hover_color="#1E40AF",
            text_color="#FFFFFF",
            corner_radius=8, height=36,
            width=140,
            command=self._open_add_form,
        ).pack(side="right", anchor="center")

        ctk.CTkFrame(self, height=1, fg_color=BORDER, corner_radius=0).pack(
            fill="x", pady=(16, 0)
        )

        self._table = DataTable(
            self,
            columns=[
                ("Name",     210),
                ("Type",     100),
                ("Location", 170),
                ("Status",   130),
                ("Next Due", 110),
                ("Actions",  130),
            ],
            height=520,
        )
        self._table.pack(fill="both", expand=True, padx=24, pady=(16, 24))

    # ── data ──────────────────────────────────────────────────────────────────

    def refresh(self):
        threading.Thread(target=self._load, daemon=True).start()

    def _load(self):
        try:
            items = self.api.get_equipment()
        except Exception:
            items = []
        self.after(0, lambda d=items: self._render(d))

    def _render(self, items):
        self._table.clear_rows()
        if not items:
            return

        for i, item in enumerate(items):

            def make_badge(status):
                def _b(f):
                    StatusBadge(f, status=status).pack(anchor="w", pady=4)
                return _b

            def make_actions(it):
                def _b(f):
                    ctk.CTkButton(
                        f, text="Edit",
                        font=ctk.CTkFont(family=FONT_FAMILY, size=12),
                        fg_color=ACCENT_LIGHT,
                        hover_color="#1D3A8A",
                        border_width=1,
                        border_color=ACCENT,
                        text_color=ACCENT,
                        corner_radius=6,
                        height=28, width=58,
                        cursor="hand2",
                        command=lambda x=it: self._open_edit_form(x),
                    ).pack(side="left", padx=(0, 6))

                    ctk.CTkButton(
                        f, text="Delete",
                        font=ctk.CTkFont(family=FONT_FAMILY, size=12),
                        fg_color=DANGER_LIGHT,
                        hover_color="#7F1D1D",
                        border_width=1,
                        border_color=DANGER,
                        text_color=DANGER,
                        corner_radius=6,
                        height=28, width=62,
                        cursor="hand2",
                        command=lambda x=it: self._confirm_delete(x),
                    ).pack(side="left")
                return _b

            self._table.add_row([
                item.get("name", "—"),
                item.get("type", "—").title(),
                item.get("location", "—"),
                make_badge(item.get("status", "operational")),
                item.get("next_maintenance_due", "—"),
                make_actions(item),
            ], even=(i % 2 == 1))

    # ── actions ───────────────────────────────────────────────────────────────

    def _open_add_form(self):
        EquipmentFormModal(self, self.api, on_save=self.refresh)

    def _open_edit_form(self, item):
        EquipmentFormModal(self, self.api, on_save=self.refresh, item=item)

    def _confirm_delete(self, item):
        dlg = ctk.CTkToplevel(self)
        dlg.title("Confirm Delete")
        dlg.geometry("420x170")
        dlg.resizable(False, False)
        dlg.configure(fg_color=SURFACE)
        dlg.grab_set()

        ctk.CTkFrame(dlg, height=4, fg_color=DANGER, corner_radius=0).pack(fill="x")

        ctk.CTkLabel(
            dlg,
            text=f"Delete \"{item['name']}\"?",
            font=ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold"),
            text_color=TEXT_PRIMARY, fg_color="transparent",
        ).pack(anchor="w", padx=24, pady=(18, 2))
        ctk.CTkLabel(
            dlg,
            text="This will also remove all maintenance logs for this equipment.",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color=TEXT_SECONDARY, fg_color="transparent",
        ).pack(anchor="w", padx=24)

        foot = ctk.CTkFrame(dlg, fg_color="transparent")
        foot.pack(anchor="e", padx=24, pady=18)
        ctk.CTkButton(
            foot, text="Cancel", width=88,
            fg_color=SURFACE, text_color=TEXT_PRIMARY,
            border_width=1, border_color=BORDER,
            hover_color=BG, corner_radius=6,
            command=dlg.destroy,
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            foot, text="Delete", width=88,
            fg_color=DANGER, hover_color="#B91C1C",
            text_color="#FFFFFF",
            corner_radius=6,
            command=lambda: self._do_delete(item["id"], dlg),
        ).pack(side="left")

    def _do_delete(self, item_id, dlg):
        dlg.destroy()
        def _run():
            try:
                self.api.delete_equipment(item_id)
            except Exception:
                pass
            self.after(0, self.refresh)
        threading.Thread(target=_run, daemon=True).start()


# ─────────────────────────── modal ───────────────────────────────────────────

class EquipmentFormModal(ctk.CTkToplevel):
    def __init__(self, master, api_client, on_save, item: dict = None):
        super().__init__(master)
        self.api     = api_client
        self.on_save = on_save
        self.item    = item
        self.configure(fg_color=SURFACE)
        self.title("Edit Equipment" if item else "Add Equipment")
        self.geometry("500x620")
        self.resizable(False, False)
        self.grab_set()
        self._build()

    def _build(self):
        ctk.CTkFrame(self, height=4, fg_color=ACCENT, corner_radius=0).pack(fill="x")

        title_bar = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=0)
        title_bar.pack(fill="x", padx=24, pady=(16, 0))
        ctk.CTkLabel(
            title_bar,
            text="Edit Equipment" if self.item else "Add Equipment",
            font=ctk.CTkFont(family=FONT_FAMILY, size=16, weight="bold"),
            text_color=TEXT_PRIMARY, fg_color="transparent",
        ).pack(anchor="w")
        ctk.CTkLabel(
            title_bar,
            text="Update details for this field unit" if self.item else "Register a new field unit",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color=TEXT_SECONDARY, fg_color="transparent",
        ).pack(anchor="w", pady=(2, 0))

        ctk.CTkFrame(self, height=1, fg_color=BORDER, corner_radius=0).pack(
            fill="x", pady=(14, 0)
        )

        body = ctk.CTkScrollableFrame(self, fg_color=SURFACE, corner_radius=0)
        body.pack(fill="both", expand=True)

        v = self.item or {}
        self._name       = _field(body, "Equipment Name",              "e.g. Compressor Unit C-04",  v.get("name", ""))
        self._type_var   = _dropdown(body, "Type",                     ["compressor","pipeline","rig","pump","valve","other"], v.get("type","compressor"))
        self._location   = _field(body, "Location",                    "e.g. Block 7 - North Field",  v.get("location",""))
        self._status_var = _dropdown(body, "Status",                   ["operational","degraded","offline"], v.get("status","operational"))
        self._last_maint = _field(body, "Last Maintenance (YYYY-MM-DD)", "2024-01-15",                v.get("last_maintenance_date","") or "")
        self._next_due   = _field(body, "Next Due Date (YYYY-MM-DD)",  "2024-07-15",                  v.get("next_maintenance_due","") or "")
        self._notes      = _field(body, "Notes (optional)",            "",                            v.get("notes","") or "")

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
            foot, text="Save Equipment", width=130,
            fg_color=ACCENT, hover_color="#1E40AF",
            text_color="#FFFFFF",
            corner_radius=6,
            command=self._save,
        ).pack(side="right")

    def _save(self):
        data = {
            "name":                 self._name.get().strip(),
            "type":                 self._type_var.get(),
            "location":             self._location.get().strip(),
            "status":               self._status_var.get(),
            "next_maintenance_due": self._next_due.get().strip(),
            "notes":                self._notes.get().strip() or None,
        }
        last = self._last_maint.get().strip()
        if last:
            data["last_maintenance_date"] = last

        def _run():
            try:
                if self.item:
                    self.api.update_equipment(self.item["id"], data)
                else:
                    self.api.create_equipment(data)
                self.after(0, lambda: (self.on_save(), self.destroy()))
            except Exception as e:
                self.after(0, lambda err=str(e): self._error.configure(text=f"Error: {err}"))

        threading.Thread(target=_run, daemon=True).start()


# ─────────────────────────── shared form helpers ─────────────────────────────

def _field(parent, label: str, placeholder: str = "", default: str = "") -> ctk.CTkEntry:
    ctk.CTkLabel(
        parent, text=label,
        font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"),
        text_color=TEXT_PRIMARY, fg_color="transparent", anchor="w",
    ).pack(fill="x", padx=24, pady=(12, 2))
    e = ctk.CTkEntry(
        parent,
        placeholder_text=placeholder,
        font=ctk.CTkFont(family=FONT_FAMILY, size=13),
        fg_color=SURFACE,
        border_color=BORDER,
        border_width=1,
        corner_radius=6,
        height=38,
    )
    if default:
        e.insert(0, default)
    e.pack(fill="x", padx=24)
    return e


def _dropdown(parent, label: str, values: list, current: str) -> ctk.StringVar:
    ctk.CTkLabel(
        parent, text=label,
        font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"),
        text_color=TEXT_PRIMARY, fg_color="transparent", anchor="w",
    ).pack(fill="x", padx=24, pady=(12, 2))
    var = ctk.StringVar(value=current)
    ctk.CTkOptionMenu(
        parent,
        values=values,
        variable=var,
        font=ctk.CTkFont(family=FONT_FAMILY, size=13),
        fg_color=SURFACE,
        button_color=BORDER,
        button_hover_color="#3D4F6B",
        text_color=TEXT_PRIMARY,
        dropdown_fg_color=SURFACE,
        dropdown_text_color=TEXT_PRIMARY,
        dropdown_hover_color=ACCENT_LIGHT,
        corner_radius=6,
        height=38,
    ).pack(fill="x", padx=24)
    return var
