import customtkinter as ctk
from config import SURFACE, BORDER, TEXT_PRIMARY, TEXT_SECONDARY, FONT_FAMILY

_HEADER_BG  = "#F3F4F6"
_ROW_ALT_BG = "#F9FAFB"
_ROW_HOVER  = "#F0F4FF"


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
        hdr = ctk.CTkFrame(self, fg_color=_HEADER_BG, corner_radius=0)
        hdr.pack(fill="x")

        for i, (col, width) in enumerate(self.columns):
            ctk.CTkLabel(
                hdr,
                text=col.upper(),
                width=width,
                font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
                text_color=TEXT_SECONDARY,
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

        # Row hover — bind on the row itself
        row.bind("<Enter>", lambda e, r=row: r.configure(fg_color=_ROW_HOVER))
        row.bind("<Leave>", lambda e, r=row, b=bg: r.configure(fg_color=b))

        for i, (cell, (_, width)) in enumerate(zip(cells, self.columns)):
            padx = (12 if i == 0 else 8, 0)

            if isinstance(cell, str):
                ctk.CTkLabel(
                    row,
                    text=cell,
                    width=width,
                    font=ctk.CTkFont(family=FONT_FAMILY, size=13),
                    text_color=TEXT_PRIMARY,
                    fg_color=bg,
                    anchor="w",
                ).pack(side="left", padx=padx, pady=10)

            elif callable(cell):
                cell_frame = ctk.CTkFrame(row, fg_color=bg, corner_radius=0, width=width)
                cell_frame.pack(side="left", padx=padx, pady=6)
                cell_frame.pack_propagate(False)
                cell(cell_frame)

        div = ctk.CTkFrame(self, height=1, fg_color=BORDER, corner_radius=0)
        div.pack(fill="x")
        self._rows.append(div)

        return row
