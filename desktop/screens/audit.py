import os
import threading
import customtkinter as ctk
from datetime import date, datetime, timedelta
from tkinter import filedialog, messagebox
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

# PDF label for each action type
_ACTION_LABEL = {
    "created":        "Created",
    "updated":        "Updated",
    "deleted":        "Deleted",
    "status_changed": "Status Chg",
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
        self._current_logs: list[dict] = []
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
        _wrap = ctk.CTkFrame(self, fg_color="transparent")
        _wrap.pack(fill="x", padx=24, pady=(14, 0))

        bar = ctk.CTkFrame(_wrap, fg_color="transparent")
        bar.pack(fill="x")

        # Right-side widgets packed first so they anchor to the right edge
        self._count_label = ctk.CTkLabel(
            bar, text="",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color=TEXT_SECONDARY, fg_color="transparent",
        )
        self._count_label.pack(side="right")

        ctk.CTkButton(
            bar, text="Export PDF",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            fg_color=SURFACE, text_color=DANGER,
            border_width=1, border_color=BORDER,
            hover_color="#2D1515", corner_radius=6, height=34, width=100,
            command=self._export_pdf,
        ).pack(side="right", padx=(0, 10))

        ctk.CTkFrame(bar, width=1, fg_color=BORDER, corner_radius=0).pack(
            side="right", fill="y", padx=(8, 8)
        )

        # Left-side: Action filter
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

        # ── Custom date row (hidden until "Custom Range" selected) ────────────
        self._custom_row = ctk.CTkFrame(_wrap, fg_color="transparent")

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

        self._current_logs = result
        self._render(result)

    # ── render ────────────────────────────────────────────────────────────────

    def _render(self, logs: list[dict]):
        self._table.clear_rows()
        self._count_label.configure(text=f"{len(logs)} record{'s' if len(logs) != 1 else ''}")

        for i, entry in enumerate(logs):
            ts = entry.get("timestamp", "")
            try:
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

    # ── PDF export ────────────────────────────────────────────────────────────

    def _ensure_pkg(self, pkg: str) -> bool:
        import importlib, subprocess, sys
        try:
            importlib.import_module(pkg)
            return True
        except ImportError:
            pass
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", pkg, "-q"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            importlib.import_module(pkg)
            return True
        except Exception as e:
            self.after(0, lambda err=str(e): messagebox.showerror(
                "Install failed",
                f"Could not install {pkg}.\n\nRun manually:\n  pip install {pkg}\n\n{err}",
            ))
            return False

    def _export_pdf(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            title="Export Audit Log as PDF",
            initialfile=f"FieldLog_AuditLog_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        )
        if not path:
            return
        logs           = self._current_logs[:]
        action_filter  = self._action_var.get()
        date_filter    = self._date_var.get()
        threading.Thread(
            target=self._do_pdf,
            args=(path, logs, action_filter, date_filter),
            daemon=True,
        ).start()

    def _do_pdf(self, path: str, logs: list, action_filter: str, date_filter: str):
        try:
            if not self._ensure_pkg("reportlab"):
                return

            from reportlab.lib.pagesizes import A4, landscape
            from reportlab.lib.units import mm
            from reportlab.lib import colors
            from reportlab.platypus import (
                SimpleDocTemplate, Table, TableStyle,
                Paragraph, Spacer,
            )
            from reportlab.lib.styles import ParagraphStyle

            PAGE = landscape(A4)
            PW, PH  = PAGE
            MARGIN  = 18 * mm
            HDR_H   = 16 * mm
            FOOT_H  = 12 * mm
            USABLE  = PW - 2 * MARGIN

            C_ACCENT      = colors.HexColor("#1D4ED8")
            C_ACCENT_MUTE = colors.HexColor("#BFDBFE")
            C_GRAY        = colors.HexColor("#6B7280")
            C_LIGHT_GRAY  = colors.HexColor("#F3F4F6")
            C_ALT_ROW     = colors.HexColor("#F9FAFB")
            C_BORDER      = colors.HexColor("#E5E7EB")
            C_TEXT        = colors.HexColor("#111827")

            def _draw_chrome(canvas, doc):
                canvas.saveState()

                canvas.setFillColor(C_ACCENT)
                canvas.rect(0, PH - HDR_H, PW, HDR_H, fill=1, stroke=0)

                canvas.setFillColor(colors.white)
                canvas.setFont("Helvetica-Bold", 13)
                canvas.drawString(MARGIN, PH - HDR_H + 5.5 * mm, "FieldLog")

                canvas.setFillColor(C_ACCENT_MUTE)
                canvas.rect(MARGIN + 32 * mm, PH - HDR_H + 4 * mm, 0.4 * mm, 8 * mm,
                            fill=1, stroke=0)

                canvas.setFillColor(colors.white)
                canvas.setFont("Helvetica", 10)
                canvas.drawString(MARGIN + 35 * mm, PH - HDR_H + 5.5 * mm, "Audit Log")

                canvas.setFont("Helvetica", 9)
                canvas.drawRightString(PW - MARGIN, PH - HDR_H + 5.5 * mm,
                                       date.today().strftime("%B %d, %Y"))

                canvas.setStrokeColor(C_BORDER)
                canvas.setLineWidth(0.5)
                canvas.line(MARGIN, FOOT_H - 2 * mm, PW - MARGIN, FOOT_H - 2 * mm)

                canvas.setFillColor(C_GRAY)
                canvas.setFont("Helvetica", 7.5)
                canvas.drawString(MARGIN, FOOT_H - 6 * mm, "FieldLog  -  Confidential")
                canvas.drawRightString(PW - MARGIN, FOOT_H - 6 * mm, f"Page {doc.page}")

                canvas.restoreState()

            doc = SimpleDocTemplate(
                path, pagesize=PAGE,
                leftMargin=MARGIN, rightMargin=MARGIN,
                topMargin=HDR_H + 10 * mm,
                bottomMargin=FOOT_H + 6 * mm,
            )

            normal = ParagraphStyle("fl_normal", fontName="Helvetica",
                                    fontSize=8, leading=11, textColor=C_TEXT)
            bold   = ParagraphStyle("fl_bold",   fontName="Helvetica-Bold",
                                    fontSize=8, leading=11, textColor=C_TEXT)
            muted  = ParagraphStyle("fl_muted",  fontName="Helvetica",
                                    fontSize=8, leading=11, textColor=C_GRAY)

            elements = []

            # ── Summary bar ────────────────────────────────────────────────────
            active_filters = []
            if action_filter != "All":
                active_filters.append(f"Action: {action_filter}")
            if date_filter != "All Time":
                active_filters.append(f"Period: {date_filter}")
            filter_str = "  |  ".join(active_filters) if active_filters else "All records"

            summary_data = [[
                Paragraph(f"<b>{len(logs)}</b>  records", bold),
                Paragraph(filter_str, muted),
                Paragraph(f"Generated {date.today().strftime('%d %b %Y')}", muted),
            ]]
            summary_tbl = Table(
                summary_data,
                colWidths=[USABLE * 0.15, USABLE * 0.60, USABLE * 0.25],
            )
            summary_tbl.setStyle(TableStyle([
                ("BACKGROUND",    (0, 0), (-1, -1), C_LIGHT_GRAY),
                ("TOPPADDING",    (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING",   (0, 0), (-1, -1), 8),
                ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
                ("LINEBELOW",     (0, 0), (-1, -1), 0.5, C_BORDER),
                ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ]))
            elements.append(summary_tbl)
            elements.append(Spacer(1, 5 * mm))

            # ── Data table ─────────────────────────────────────────────────────
            col_widths = [
                USABLE * 0.14,   # Timestamp
                USABLE * 0.10,   # Action
                USABLE * 0.10,   # Entity
                USABLE * 0.20,   # Name
                USABLE * 0.46,   # Description
            ]

            hdr_style = ParagraphStyle("fl_hdr", fontName="Helvetica-Bold",
                                       fontSize=8, leading=10, textColor=colors.white)
            col_labels = ["Timestamp", "Action", "Entity", "Name", "Description"]
            data = [[Paragraph(h, hdr_style) for h in col_labels]]

            for entry in logs:
                ts = entry.get("timestamp", "")
                try:
                    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    ts_str = dt.strftime("%b %d, %Y  %I:%M %p")
                except Exception:
                    ts_str = (ts or "")[:16]

                action_raw = entry.get("action_type", "")
                action_str = _ACTION_LABEL.get(action_raw, action_raw.title())

                entity_raw = entry.get("entity_type", "")
                entity_str = {
                    "equipment":       "Equipment",
                    "maintenance_log": "Maint. Log",
                }.get(entity_raw, entity_raw.title())

                desc = entry.get("description") or ""
                if len(desc) > 130:
                    desc = desc[:127] + "..."

                data.append([
                    Paragraph(ts_str, normal),
                    Paragraph(action_str, normal),
                    Paragraph(entity_str, normal),
                    Paragraph(entry.get("entity_name") or "—", normal),
                    Paragraph(desc, normal),
                ])

            tbl = Table(data, colWidths=col_widths, repeatRows=1, hAlign="LEFT")
            tbl.setStyle(TableStyle([
                ("BACKGROUND",    (0, 0), (-1, 0),  C_ACCENT),
                ("TOPPADDING",    (0, 0), (-1, 0),  7),
                ("BOTTOMPADDING", (0, 0), (-1, 0),  7),
                ("LEFTPADDING",   (0, 0), (-1, 0),  8),
                ("ROWBACKGROUNDS",(0, 1), (-1, -1),  [colors.white, C_ALT_ROW]),
                ("TOPPADDING",    (0, 1), (-1, -1),  5),
                ("BOTTOMPADDING", (0, 1), (-1, -1),  5),
                ("LEFTPADDING",   (0, 1), (-1, -1),  8),
                ("RIGHTPADDING",  (0, 0), (-1, -1),  6),
                ("LINEBELOW",     (0, 0), (-1, -1),  0.35, C_BORDER),
                ("VALIGN",        (0, 0), (-1, -1),  "TOP"),
                ("LINEAFTER",     (0, 0), (0, -1),   0.5,  C_BORDER),
            ]))
            elements.append(tbl)

            doc.build(elements, onFirstPage=_draw_chrome, onLaterPages=_draw_chrome)
            self.after(0, lambda: os.startfile(path))

        except Exception as e:
            self.after(0, lambda err=str(e): messagebox.showerror("Export failed", err))
