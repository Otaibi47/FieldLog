import customtkinter as ctk
from config import (
    FONT_FAMILY,
    SIDEBAR_BG, SIDEBAR_HOVER, SIDEBAR_ACTIVE_BG,
    SIDEBAR_TEXT, SIDEBAR_TEXT_ACTIVE, SIDEBAR_RULE, SIDEBAR_LABEL,
)

_NAV = [
    ("dashboard",   "Dashboard"),
    ("equipment",   "Equipment"),
    ("maintenance", "Maintenance"),
    ("alerts",      "Alerts"),
]


class Sidebar(ctk.CTkFrame):
    def __init__(self, master, on_navigate, **kwargs):
        super().__init__(master, width=210, fg_color=SIDEBAR_BG, corner_radius=0, **kwargs)
        self.on_navigate = on_navigate
        self._active = "dashboard"
        self._items: dict[str, dict] = {}
        # grid_propagate(False) keeps the sidebar's own size set by the
        # parent grid (sticky="nsew") rather than by its children
        self.grid_propagate(False)
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)

        # ── brand ──────────────────────────────────────────────────────────
        self.grid_rowconfigure(0, minsize=52)
        ctk.CTkLabel(
            self,
            text="FieldLog",
            font=ctk.CTkFont(family=FONT_FAMILY, size=15, weight="bold"),
            text_color=SIDEBAR_TEXT_ACTIVE,
            fg_color="transparent",
        ).grid(row=0, column=0, sticky="w", padx=16)

        # ── divider ────────────────────────────────────────────────────────
        self.grid_rowconfigure(1, minsize=1)
        ctk.CTkFrame(self, height=1, fg_color="#334155", corner_radius=0).grid(
            row=1, column=0, sticky="ew",
        )

        # ── nav label ──────────────────────────────────────────────────────
        self.grid_rowconfigure(2, minsize=32)
        ctk.CTkLabel(
            self,
            text="NAVIGATION",
            font=ctk.CTkFont(family=FONT_FAMILY, size=10, weight="bold"),
            text_color=SIDEBAR_LABEL,
            fg_color="transparent",
        ).grid(row=2, column=0, sticky="sw", padx=16, pady=(0, 4))

        # ── nav items (rows 3-6) ────────────────────────────────────────────
        for i, (key, label) in enumerate(_NAV):
            self.grid_rowconfigure(i + 3, minsize=40)
            self._make_item(key, label, row=i + 3)

        # ── spacer swallows all remaining height ───────────────────────────
        self.grid_rowconfigure(7, weight=1)
        ctk.CTkFrame(self, fg_color="transparent", corner_radius=0).grid(
            row=7, column=0, sticky="nsew",
        )

    def _make_item(self, key: str, label: str, row: int):
        # height=40 + pack_propagate(False) overrides CTkFrame's default height=200
        # which would otherwise make each row request 200px from the grid
        outer = ctk.CTkFrame(self, fg_color=SIDEBAR_BG, corner_radius=0, height=40)
        outer.grid(row=row, column=0, sticky="ew", padx=8, pady=1)
        outer.pack_propagate(False)

        rule = ctk.CTkFrame(outer, width=3, fg_color=SIDEBAR_BG, corner_radius=0)
        rule.pack(side="left", fill="y")
        rule.pack_propagate(False)

        lbl = ctk.CTkLabel(
            outer,
            text=label,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            text_color=SIDEBAR_TEXT,
            fg_color="transparent",
            anchor="w",
            cursor="hand2",
        )
        lbl.pack(side="left", fill="x", expand=True, padx=(8, 8))

        for widget in (outer, rule, lbl):
            widget.bind("<Button-1>", lambda e, k=key: self._navigate(k))
        for widget in (outer, lbl):
            widget.bind("<Enter>", lambda e, o=outer, k=key: self._on_hover(o, k, True))
            widget.bind("<Leave>", lambda e, o=outer, k=key: self._on_hover(o, k, False))

        self._items[key] = {"outer": outer, "rule": rule, "lbl": lbl}

    # ── interaction ────────────────────────────────────────────────────────

    def _on_hover(self, outer, key: str, entering: bool):
        if key == self._active:
            return
        outer.configure(fg_color=SIDEBAR_HOVER if entering else SIDEBAR_BG)

    def _navigate(self, key: str):
        self._active = key
        self._refresh_styles()
        self.on_navigate(key)

    def _refresh_styles(self):
        for key, item in self._items.items():
            if key == self._active:
                item["outer"].configure(fg_color=SIDEBAR_ACTIVE_BG)
                item["rule"].configure(fg_color=SIDEBAR_RULE)
                item["lbl"].configure(text_color=SIDEBAR_TEXT_ACTIVE)
            else:
                item["outer"].configure(fg_color=SIDEBAR_BG)
                item["rule"].configure(fg_color=SIDEBAR_BG)
                item["lbl"].configure(text_color=SIDEBAR_TEXT)

    def set_alert_count(self, count: int):
        item = self._items.get("alerts")
        if not item:
            return
        item["lbl"].configure(text=f"Alerts  ({count})" if count > 0 else "Alerts")
        if self._active != "alerts":
            item["lbl"].configure(
                text_color="#F87171" if count > 0 else SIDEBAR_TEXT
            )

    def set_active(self, key: str):
        self._active = key
        self._refresh_styles()
