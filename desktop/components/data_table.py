import customtkinter as ctk
from config import SURFACE, BORDER, ACCENT, TEXT_PRIMARY, FONT_FAMILY

_HEADER_BG   = "#1E3A5F"
_HEADER_TEXT = "#93C5FD"
_ROW_ALT_BG  = "#243347"
_ROW_DIVIDER = "#2D3F5A"
_ROW_HOVER   = "#2A4A70"


class DataTable(ctk.CTkScrollableFrame):
    """
    Scrollable table.
    columns: list of (header_str, pixel_width)
    add_row cells: str → label  |  callable(parent_frame) → widget builder
    """

    def __init__(self, master, columns: list[tuple[str, int]], **kwargs):
        super().__init__(master, fg_color=SURFACE, corner_radius=0, **kwargs)
        self.columns = columns
        self._rows: list = []
        self._build_header()

    def _build_header(self):
        ctk.CTkFrame(self, height=3, fg_color=ACCENT, corner_radius=0).pack(fill="x")

        hdr = ctk.CTkFrame(self, fg_color=_HEADER_BG, corner_radius=0)
        hdr.pack(fill="x")

        for i, (col, width) in enumerate(self.columns):
            ctk.CTkLabel(
                hdr,
                text=col.upper(),
                width=width,
                font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"),
                text_color=_HEADER_TEXT,
                fg_color="transparent",
                anchor="w",
            ).pack(side="left", padx=(12 if i == 0 else 8, 0), pady=10)

        ctk.CTkFrame(self, height=1, fg_color=BORDER, corner_radius=0).pack(fill="x")

    def clear_rows(self):
        for w in self._rows:
            try:
                w.destroy()
            except Exception:
                pass
        self._rows.clear()

    def add_row(self, cells: list, even: bool = False) -> ctk.CTkFrame:
        bg = _ROW_ALT_BG if even else SURFACE

        row = ctk.CTkFrame(self, fg_color=bg, corner_radius=0)
        row.pack(fill="x")
        self._rows.append(row)

        # Enter: immediately paint hover.
        # Leave: wait 10 ms then check if cursor is still anywhere inside the
        # row widget tree — if yes, ignore (cursor moved onto a child widget).
        def _enter(_e):
            row.configure(fg_color=_ROW_HOVER)

        def _leave(_e):
            def _check():
                try:
                    w = row.winfo_containing(
                        row.winfo_pointerx(), row.winfo_pointery()
                    )
                    if w is not None and str(w).startswith(str(row)):
                        return          # cursor is still inside the row tree
                    row.configure(fg_color=bg)
                except Exception:
                    row.configure(fg_color=bg)
            row.after(10, _check)

        def _bind(widget):
            widget.bind("<Enter>", _enter)
            widget.bind("<Leave>", _leave)

        _bind(row)

        for i, (cell, (_, width)) in enumerate(zip(cells, self.columns)):
            padx = (12 if i == 0 else 8, 0)

            if isinstance(cell, str):
                lbl = ctk.CTkLabel(
                    row,
                    text=cell,
                    width=width,
                    font=ctk.CTkFont(family=FONT_FAMILY, size=13),
                    text_color=TEXT_PRIMARY,
                    fg_color="transparent",   # inherits row background on hover
                    anchor="w",
                )
                lbl.pack(side="left", padx=padx, pady=10)
                _bind(lbl)

            elif callable(cell):
                cell_frame = ctk.CTkFrame(
                    row, fg_color="transparent", corner_radius=0, width=width
                )
                cell_frame.pack(side="left", padx=padx, pady=6)
                cell_frame.pack_propagate(False)
                _bind(cell_frame)
                cell(cell_frame)
                # Bind grandchildren created by the cell builder
                for child in cell_frame.winfo_children():
                    _bind(child)
                    for grandchild in child.winfo_children():
                        _bind(grandchild)

        div = ctk.CTkFrame(self, height=1, fg_color=_ROW_DIVIDER, corner_radius=0)
        div.pack(fill="x")
        self._rows.append(div)

        return row
