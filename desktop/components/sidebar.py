import pathlib
import customtkinter as ctk
from PIL import Image
from config import (
    FONT_FAMILY, TEXT_PRIMARY, TEXT_SECONDARY,
    SIDEBAR_BG, SIDEBAR_HOVER, SIDEBAR_ACTIVE_BG,
    SIDEBAR_TEXT, SIDEBAR_TEXT_ACTIVE, SIDEBAR_RULE, SIDEBAR_LABEL,
    DANGER,
)

_NAV = [
    ("dashboard",   "Dashboard"),
    ("equipment",   "Equipment"),
    ("maintenance", "Maintenance"),
    ("alerts",      "Alerts"),
]


class Sidebar(ctk.CTkFrame):
    def __init__(self, master, on_navigate, **kwargs):
        super().__init__(master, width=220, fg_color=SIDEBAR_BG, corner_radius=0, **kwargs)
        self.on_navigate = on_navigate
        self._active = "dashboard"
        self._items: dict[str, dict] = {}
        self.grid_propagate(False)
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)

        # ── Logo / Brand ──────────────────────────────────────────────────────
        self.grid_rowconfigure(0, minsize=130)
        brand = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0, height=130)
        brand.grid(row=0, column=0, sticky="ew")
        brand.pack_propagate(False)

        _logo_path = pathlib.Path(__file__).parent / "assets" / "logo.png"
        if _logo_path.exists():
            self._logo_img = ctk.CTkImage(
                light_image=Image.open(_logo_path), size=(64, 64)
            )
            ctk.CTkLabel(
                brand, image=self._logo_img, text="", fg_color="transparent",
            ).pack(anchor="center", pady=(14, 6))
        else:
            ctk.CTkFrame(brand, height=14, fg_color="transparent").pack()

        ctk.CTkLabel(
            brand,
            text="FieldLog",
            font=ctk.CTkFont(family=FONT_FAMILY, size=16, weight="bold"),
            text_color=TEXT_PRIMARY,
            fg_color="transparent",
        ).pack(anchor="center")
        ctk.CTkLabel(
            brand,
            text="Maintenance Tracker",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=TEXT_SECONDARY,
            fg_color="transparent",
        ).pack(anchor="center", pady=(2, 0))

        # ── Divider ───────────────────────────────────────────────────────────
        self.grid_rowconfigure(1, minsize=25)
        ctk.CTkFrame(self, height=1, fg_color="#E5E7EB", corner_radius=0).grid(
            row=1, column=0, sticky="ew", padx=12, pady=(12, 12),
        )

        # ── Section label ─────────────────────────────────────────────────────
        self.grid_rowconfigure(2, minsize=36)
        ctk.CTkLabel(
            self,
            text="NAVIGATION",
            font=ctk.CTkFont(family=FONT_FAMILY, size=10, weight="bold"),
            text_color=SIDEBAR_LABEL,
            fg_color="transparent",
        ).grid(row=2, column=0, sticky="sw", padx=20, pady=(0, 4))

        # ── Nav items ─────────────────────────────────────────────────────────
        for i, (key, label) in enumerate(_NAV):
            self.grid_rowconfigure(i + 3, minsize=40)
            self._make_item(key, label, row=i + 3)

        # ── Spacer ────────────────────────────────────────────────────────────
        self.grid_rowconfigure(7, weight=1)
        ctk.CTkFrame(self, fg_color="transparent", corner_radius=0).grid(
            row=7, column=0, sticky="nsew",
        )

    def _make_item(self, key: str, label: str, row: int):
        # height=40 + pack_propagate(False) prevents CTkFrame's default height=200
        outer = ctk.CTkFrame(self, fg_color=SIDEBAR_BG, corner_radius=6, height=40)
        outer.grid(row=row, column=0, sticky="ew", padx=12, pady=2)
        outer.pack_propagate(False)

        # 3px left accent rule — invisible when inactive, blue when active
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
                text_color=DANGER if count > 0 else SIDEBAR_TEXT
            )

    def set_active(self, key: str):
        self._active = key
        self._refresh_styles()
