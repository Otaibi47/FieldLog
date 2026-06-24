import customtkinter as ctk
from config import (
    FONT_FAMILY, DANGER,
    SIDEBAR_BG, SIDEBAR_HOVER, SIDEBAR_ACTIVE_BG,
    SIDEBAR_TEXT, SIDEBAR_TEXT_ACTIVE, SIDEBAR_RULE, SIDEBAR_LABEL,
)


class Sidebar(ctk.CTkFrame):
    def __init__(self, master, on_navigate, **kwargs):
        super().__init__(master, width=210, fg_color=SIDEBAR_BG, corner_radius=0, **kwargs)
        self.on_navigate = on_navigate
        self._active = "dashboard"
        self._items: dict[str, dict] = {}
        self.pack_propagate(False)
        self._build()

    def _build(self):
        # App brand
        brand = ctk.CTkFrame(self, fg_color="transparent")
        brand.pack(fill="x", padx=20, pady=(28, 22))

        ctk.CTkLabel(
            brand,
            text="FieldLog",
            font=ctk.CTkFont(family=FONT_FAMILY, size=17, weight="bold"),
            text_color=SIDEBAR_TEXT_ACTIVE,
            fg_color="transparent",
        ).pack(anchor="w")
        ctk.CTkLabel(
            brand,
            text="Maintenance Tracker",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=SIDEBAR_TEXT,
            fg_color="transparent",
        ).pack(anchor="w", pady=(3, 0))

        ctk.CTkFrame(self, height=1, fg_color="#334155", corner_radius=0).pack(fill="x")

        ctk.CTkLabel(
            self,
            text="NAVIGATION",
            font=ctk.CTkFont(family=FONT_FAMILY, size=10, weight="bold"),
            text_color=SIDEBAR_LABEL,
            fg_color="transparent",
        ).pack(anchor="w", padx=20, pady=(18, 6))

        for key, label in [
            ("dashboard",   "Dashboard"),
            ("equipment",   "Equipment"),
            ("maintenance", "Maintenance"),
            ("alerts",      "Alerts"),
        ]:
            self._make_item(key, label)

    def _make_item(self, key: str, label: str):
        # Container row
        outer = ctk.CTkFrame(self, fg_color=SIDEBAR_BG, corner_radius=6)
        outer.pack(fill="x", padx=10, pady=2)

        # 3px left accent rule
        rule = ctk.CTkFrame(outer, width=3, fg_color=SIDEBAR_BG, corner_radius=0)
        rule.pack(side="left", fill="y")
        rule.pack_propagate(False)

        # CTkLabel — more reliable than CTkButton for nav items on Windows
        lbl = ctk.CTkLabel(
            outer,
            text=label,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            text_color=SIDEBAR_TEXT,
            fg_color="transparent",
            anchor="w",
            cursor="hand2",
        )
        lbl.pack(fill="x", padx=(8, 8), pady=9)

        # Click + hover bindings on all three widgets so the whole row is a target
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
                text_color="#F87171" if count > 0 else SIDEBAR_TEXT
            )

    def set_active(self, key: str):
        self._active = key
        self._refresh_styles()
