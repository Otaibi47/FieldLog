import customtkinter as ctk
from config import (
    SURFACE, BORDER, TEXT_PRIMARY, TEXT_SECONDARY,
    ACCENT, ACCENT_LIGHT, DANGER, FONT_FAMILY,
)


class Sidebar(ctk.CTkFrame):
    def __init__(self, master, on_navigate, **kwargs):
        super().__init__(master, width=200, fg_color=SURFACE, corner_radius=0, **kwargs)
        self.on_navigate = on_navigate
        self._active = "dashboard"
        self._items: dict[str, dict] = {}   # key → {outer, rule, btn}
        self.pack_propagate(False)
        self._build()

    def _build(self):
        # App identity
        brand = ctk.CTkFrame(self, fg_color="transparent")
        brand.pack(fill="x", padx=16, pady=(28, 20))

        ctk.CTkLabel(
            brand,
            text="FieldLog",
            font=ctk.CTkFont(family=FONT_FAMILY, size=17, weight="bold"),
            text_color=TEXT_PRIMARY,
            fg_color="transparent",
        ).pack(anchor="w")
        ctk.CTkLabel(
            brand,
            text="Maintenance Tracker",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=TEXT_SECONDARY,
            fg_color="transparent",
        ).pack(anchor="w", pady=(2, 0))

        # Divider
        ctk.CTkFrame(self, height=1, fg_color=BORDER, corner_radius=0).pack(fill="x")

        ctk.CTkLabel(
            self,
            text="NAVIGATION",
            font=ctk.CTkFont(family=FONT_FAMILY, size=10, weight="bold"),
            text_color=TEXT_SECONDARY,
            fg_color="transparent",
        ).pack(anchor="w", padx=16, pady=(16, 6))

        for key, label in [
            ("dashboard",   "Dashboard"),
            ("equipment",   "Equipment"),
            ("maintenance", "Maintenance"),
            ("alerts",      "Alerts"),
        ]:
            self._make_item(key, label)

    def _make_item(self, key: str, label: str):
        # Container — drives the background highlight
        outer = ctk.CTkFrame(self, fg_color="transparent", corner_radius=6)
        outer.pack(fill="x", padx=8, pady=2)

        # 3px left rule (invisible when inactive, ACCENT when active)
        rule = ctk.CTkFrame(outer, width=3, fg_color="transparent", corner_radius=0)
        rule.pack(side="left", fill="y")
        rule.pack_propagate(False)

        btn = ctk.CTkButton(
            outer,
            text=label,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            fg_color="transparent",
            text_color=TEXT_SECONDARY,
            hover_color=ACCENT_LIGHT,
            anchor="w",
            corner_radius=4,
            height=38,
            command=lambda k=key: self._navigate(k),
        )
        btn.pack(fill="both", expand=True, padx=(4, 0))

        self._items[key] = {"outer": outer, "rule": rule, "btn": btn}

    def _navigate(self, key: str):
        self._active = key
        self._refresh_styles()
        self.on_navigate(key)

    def _refresh_styles(self):
        for key, item in self._items.items():
            if key == self._active:
                item["outer"].configure(fg_color=ACCENT_LIGHT)
                item["rule"].configure(fg_color=ACCENT)
                item["btn"].configure(
                    fg_color=ACCENT_LIGHT,
                    hover_color=ACCENT_LIGHT,
                    text_color=ACCENT,
                )
            else:
                item["outer"].configure(fg_color="transparent")
                item["rule"].configure(fg_color="transparent")
                item["btn"].configure(
                    fg_color="transparent",
                    hover_color=ACCENT_LIGHT,
                    text_color=TEXT_SECONDARY,
                )

    def set_alert_count(self, count: int):
        item = self._items.get("alerts")
        if not item:
            return
        label = f"Alerts  •  {count}" if count > 0 else "Alerts"
        item["btn"].configure(text=label)
        if count > 0 and self._active != "alerts":
            item["btn"].configure(text_color=DANGER)
        elif self._active != "alerts":
            item["btn"].configure(text_color=TEXT_SECONDARY)

    def set_active(self, key: str):
        self._active = key
        self._refresh_styles()
