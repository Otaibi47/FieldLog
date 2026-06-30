import sys
import subprocess
import threading
import customtkinter as ctk
from components.data_table import DataTable
from components.status_badge import StatusBadge
from components.loading import LoadingFrame, ErrorFrame
from config import (
    BG, SURFACE, BORDER, TEXT_PRIMARY, TEXT_SECONDARY,
    ACCENT, ACCENT_LIGHT, DANGER, DANGER_LIGHT, FONT_FAMILY, API_BASE_URL,
)


# ─────────────────────────── screen ──────────────────────────────────────────

class EquipmentScreen(ctk.CTkFrame):
    def __init__(self, master, api_client, on_data_change=None, **kwargs):
        super().__init__(master, fg_color=BG, **kwargs)
        self.api = api_client
        self._on_data_change = on_data_change
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

        # Content area — table / loading / error share the same grid slot
        _ca = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        _ca.pack(fill="both", expand=True)
        _ca.grid_columnconfigure(0, weight=1)
        _ca.grid_rowconfigure(0, weight=1)

        self._table = DataTable(
            _ca,
            columns=[
                ("Name",     200),
                ("Type",      95),
                ("Location", 160),
                ("Status",   120),
                ("Next Due", 105),
                ("QR",        60),
                ("Actions",  140),
            ],
            height=520,
        )
        self._table.grid(row=0, column=0, sticky="nsew", padx=24, pady=(16, 24))
        self._table.grid_remove()

        self._loading = LoadingFrame(_ca, "Loading equipment")
        self._loading.grid(row=0, column=0, sticky="nsew")

        self._error_frame = ErrorFrame(_ca, on_retry=self.refresh)
        self._error_frame.grid(row=0, column=0, sticky="nsew")
        self._error_frame.grid_remove()

    # ── loading / error helpers ───────────────────────────────────────────────

    def _show_loading(self):
        self._error_frame.grid_remove()
        self._table.grid_remove()
        self._loading.grid()
        self._loading.start()

    def _show_error(self):
        self._loading.stop()
        self._loading.grid_remove()
        self._table.grid_remove()
        self._error_frame.grid()

    # ── data ──────────────────────────────────────────────────────────────────

    def refresh(self):
        self._show_loading()
        threading.Thread(target=self._load, daemon=True).start()

    def _load(self):
        try:
            items = self.api.get_equipment()
        except Exception:
            self.after(0, self._show_error)
            return
        self.after(0, lambda d=items: self._render(d))

    def _render(self, items):
        self._loading.stop()
        self._loading.grid_remove()
        self._error_frame.grid_remove()
        self._table.grid()
        self._table.clear_rows()
        if not items:
            return

        for i, item in enumerate(items):

            def make_badge(status):
                def _b(f):
                    StatusBadge(f, status=status).pack(anchor="w", pady=4)
                return _b

            def make_qr(it):
                def _b(f):
                    ctk.CTkButton(
                        f, text="QR",
                        font=ctk.CTkFont(family=FONT_FAMILY, size=12),
                        fg_color="#172554",
                        hover_color="#1D3A8A",
                        border_width=1,
                        border_color="#60A5FA",
                        text_color="#60A5FA",
                        corner_radius=6,
                        height=28, width=46,
                        cursor="hand2",
                        command=lambda x=it: _QRDialog(self, x),
                    ).pack(side="left", padx=(0, 6))
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
                make_qr(item),
                make_actions(item),
            ], even=(i % 2 == 1))

    # ── actions ───────────────────────────────────────────────────────────────

    def _open_add_form(self):
        EquipmentFormModal(self, self.api, on_save=self._after_mutation)

    def _open_edit_form(self, item):
        EquipmentFormModal(self, self.api, on_save=self._after_mutation, item=item)

    def _after_mutation(self):
        self.refresh()
        if self._on_data_change:
            self._on_data_change()

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
            if self._on_data_change:
                self.after(0, self._on_data_change)
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


# ─────────────────────────── QR code dialog ──────────────────────────────────

def _ensure_pkg(pkg: str):
    import importlib
    try:
        importlib.import_module(pkg.split("[")[0])
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])


class _QRDialog(ctk.CTkToplevel):
    def __init__(self, master, item: dict):
        super().__init__(master)
        self._item = item
        self.title(f"QR Code — {item.get('name', '')}")
        self.geometry("400x460")
        self.resizable(False, False)
        self.configure(fg_color=SURFACE)
        self.grab_set()
        self._build()
        threading.Thread(target=self._generate, daemon=True).start()

    def _build(self):
        ctk.CTkFrame(self, height=4, fg_color=ACCENT, corner_radius=0).pack(fill="x")

        ctk.CTkLabel(
            self,
            text=self._item.get("name", ""),
            font=ctk.CTkFont(family=FONT_FAMILY, size=15, weight="bold"),
            text_color=TEXT_PRIMARY, fg_color="transparent",
        ).pack(pady=(18, 2))
        ctk.CTkLabel(
            self,
            text="Scan to view full maintenance history",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color=TEXT_SECONDARY, fg_color="transparent",
        ).pack()

        ctk.CTkFrame(self, height=1, fg_color=BORDER, corner_radius=0).pack(
            fill="x", pady=(14, 0)
        )

        # Image area — swapped in after generation
        self._img_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._img_frame.pack(expand=True, fill="both")

        self._status_lbl = ctk.CTkLabel(
            self._img_frame,
            text="Generating QR code...",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            text_color=TEXT_SECONDARY, fg_color="transparent",
        )
        self._status_lbl.pack(expand=True)

        ctk.CTkFrame(self, height=1, fg_color=BORDER, corner_radius=0).pack(fill="x")

        foot = ctk.CTkFrame(self, fg_color="transparent")
        foot.pack(fill="x", padx=20, pady=12)

        self._url_lbl = ctk.CTkLabel(
            foot, text="",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=TEXT_SECONDARY, fg_color="transparent",
            wraplength=300,
        )
        self._url_lbl.pack(anchor="w")

        ctk.CTkButton(
            foot, text="Close",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            fg_color=SURFACE, text_color=TEXT_PRIMARY,
            border_width=1, border_color=BORDER,
            hover_color=BG, corner_radius=6,
            height=34, width=80,
            command=self.destroy,
        ).pack(side="right", pady=(8, 0))

        self._copy_btn = ctk.CTkButton(
            foot, text="Copy URL",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            fg_color=ACCENT_LIGHT, text_color=ACCENT,
            border_width=1, border_color=ACCENT,
            hover_color="#1D3A8A", corner_radius=6,
            height=34, width=90,
            command=self._copy_url,
            state="disabled",
        )
        self._copy_btn.pack(side="right", pady=(8, 0), padx=(0, 8))

    def _generate(self):
        try:
            _ensure_pkg("qrcode")
            import qrcode
            from PIL import Image

            item_id = self._item.get("id", "")
            url = f"{API_BASE_URL}/equipment/{item_id}/history"
            self._qr_url = url

            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=9,
                border=3,
            )
            qr.add_data(url)
            qr.make(fit=True)
            pil_img = qr.make_image(fill_color="#0F172A", back_color="#F1F5F9").convert("RGB")

            self.after(0, lambda img=pil_img: self._show_qr(img))
        except Exception as ex:
            self.after(0, lambda e=str(ex): self._status_lbl.configure(
                text=f"Error: {e}", text_color=DANGER
            ))

    def _show_qr(self, pil_img):
        import customtkinter as ctk
        self._status_lbl.destroy()

        self._qr_ctk = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(270, 270))
        ctk.CTkLabel(
            self._img_frame, image=self._qr_ctk, text="",
            fg_color="transparent",
        ).pack(expand=True, pady=10)

        short_url = self._qr_url
        if len(short_url) > 55:
            short_url = short_url[:52] + "..."
        self._url_lbl.configure(text=short_url)
        self._copy_btn.configure(state="normal")

    def _copy_url(self):
        url = getattr(self, "_qr_url", "")
        self.clipboard_clear()
        self.clipboard_append(url)
        self._copy_btn.configure(text="Copied!")
        self.after(2000, lambda: self._copy_btn.configure(text="Copy URL"))
