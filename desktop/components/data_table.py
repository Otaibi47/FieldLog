import customtkinter as ctk
from config import SURFACE, BORDER, TEXT_PRIMARY, TEXT_SECONDARY, FONT_FAMILY, BG


class DataTable(ctk.CTkScrollableFrame):
    """Generic scrollable table with column headers and row rendering callback."""

    def __init__(self, master, columns: list[tuple[str, int]], **kwargs):
        super().__init__(master, fg_color=SURFACE, corner_radius=8, **kwargs)
        self.columns = columns  # list of (header, weight)
        self._build_header()

    def _build_header(self):
        header_frame = ctk.CTkFrame(self, fg_color="#F3F4F6", corner_radius=0)
        header_frame.pack(fill="x")
        for i, (col, weight) in enumerate(self.columns):
            header_frame.columnconfigure(i, weight=weight)

        for i, (col, _) in enumerate(self.columns):
            ctk.CTkLabel(
                header_frame,
                text=col.upper(),
                font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
                text_color=TEXT_SECONDARY,
                anchor="w",
            ).grid(row=0, column=i, padx=(12 if i == 0 else 8), pady=8, sticky="ew")

    def clear_rows(self):
        for widget in self.winfo_children():
            if isinstance(widget, ctk.CTkFrame) and widget.cget("fg_color") not in ("#F3F4F6",):
                widget.destroy()

    def add_row(self, cells: list, even: bool = False):
        """Add a row. cells is a list of str | CTkWidget."""
        row_frame = ctk.CTkFrame(
            self,
            fg_color="#F9FAFB" if even else SURFACE,
            corner_radius=0,
        )
        row_frame.pack(fill="x")

        for i, (cell, (_, weight)) in enumerate(zip(cells, self.columns)):
            row_frame.columnconfigure(i, weight=weight)
            if isinstance(cell, str):
                ctk.CTkLabel(
                    row_frame,
                    text=cell,
                    font=ctk.CTkFont(family=FONT_FAMILY, size=13),
                    text_color=TEXT_PRIMARY,
                    anchor="w",
                ).grid(row=0, column=i, padx=(12 if i == 0 else 8), pady=6, sticky="ew")
            else:
                cell.grid(row=0, column=i, padx=(12 if i == 0 else 8), pady=4, sticky="ew")

        # Divider
        ctk.CTkFrame(self, height=1, fg_color=BORDER).pack(fill="x")
        return row_frame
