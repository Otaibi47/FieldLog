import threading
import customtkinter as ctk
from screens.maintenance import MaintenanceFormModal
from components.loading import LoadingFrame, ErrorFrame
from config import (
    BG, SURFACE, BORDER, TEXT_PRIMARY, TEXT_SECONDARY,
    ACCENT, ACCENT_LIGHT, SUCCESS, DANGER, DANGER_LIGHT, FONT_FAMILY,
)

# Severity tiers in display order: (label, border_color, badge_bg, predicate)
_TIERS = [
    ("Critical", "#DC2626", "#2D1515", lambda d: d >= 61),
    ("High",     "#EA580C", "#2D1A08", lambda d: 31 <= d <= 60),
    ("Moderate", "#D97706", "#2D2008", lambda d: 1  <= d <= 30),
]


class AlertsScreen(ctk.CTkFrame):
    def __init__(self, master, api_client, **kwargs):
        super().__init__(master, fg_color=BG, **kwargs)
        self.api = api_client
        self._equipment_list: list[dict] = []
        self._card_widgets:   list       = []   # top-level widgets in _cards_scroll
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)   # cards / empty row expands

        # ── Row 0: page header ─────────────────────────────────────────────
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=24, pady=(28, 0))
        ctk.CTkLabel(
            hdr, text="Overdue Equipment",
            font=ctk.CTkFont(family=FONT_FAMILY, size=20, weight="bold"),
            text_color=TEXT_PRIMARY, fg_color="transparent",
        ).pack(anchor="w")
        ctk.CTkLabel(
            hdr, text="Equipment past their next scheduled maintenance date",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            text_color=TEXT_SECONDARY, fg_color="transparent",
        ).pack(anchor="w", pady=(2, 0))

        # ── Row 1: divider ─────────────────────────────────────────────────
        ctk.CTkFrame(self, height=1, fg_color=BORDER, corner_radius=0).grid(
            row=1, column=0, sticky="ew", pady=(16, 0)
        )

        # ── Row 2: red alert banner (hidden until items exist) ─────────────
        self._banner = ctk.CTkFrame(self, fg_color=DANGER_LIGHT, corner_radius=0)
        self._banner.grid(row=2, column=0, sticky="ew", padx=24, pady=(12, 0))
        self._banner.grid_remove()

        rule = ctk.CTkFrame(self._banner, width=4, fg_color=DANGER, corner_radius=0)
        rule.pack(side="left", fill="y")
        rule.pack_propagate(False)

        banner_body = ctk.CTkFrame(self._banner, fg_color="transparent")
        banner_body.pack(side="left", fill="both", expand=True, padx=14, pady=10)
        self._banner_title = ctk.CTkLabel(
            banner_body, text="",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
            text_color=DANGER, fg_color="transparent", anchor="w",
        )
        self._banner_title.pack(fill="x")
        ctk.CTkLabel(
            banner_body,
            text="Address these items immediately to avoid equipment failure.",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color=DANGER, fg_color="transparent", anchor="w",
        ).pack(fill="x", pady=(1, 0))

        # ── Row 3: loading (shown first on every navigation) ──────────────
        self._loading = LoadingFrame(self, "Loading alerts")
        self._loading.grid(row=3, column=0, sticky="nsew")

        # ── Row 3: scrollable cards (hidden until data arrives) ────────────
        self._cards_scroll = ctk.CTkScrollableFrame(
            self, fg_color=BG, corner_radius=0
        )
        self._cards_scroll.grid(
            row=3, column=0, sticky="nsew", padx=24, pady=(16, 24)
        )
        self._cards_scroll.grid_remove()

        # ── Row 3: empty state (same slot, toggled vs cards) ───────────────
        self._empty = ctk.CTkFrame(self, fg_color="transparent")
        self._empty.grid(row=3, column=0, sticky="nsew")
        self._empty.grid_remove()

        # ── Row 3: error state (same slot) ────────────────────────────────
        self._error_frame = ErrorFrame(self, on_retry=self.refresh)
        self._error_frame.grid(row=3, column=0, sticky="nsew")
        self._error_frame.grid_remove()

        ctk.CTkLabel(
            self._empty, text="✓",
            font=ctk.CTkFont(family=FONT_FAMILY, size=48),
            text_color=SUCCESS, fg_color="transparent",
        ).pack()
        ctk.CTkLabel(
            self._empty, text="All equipment is on schedule",
            font=ctk.CTkFont(family=FONT_FAMILY, size=16, weight="bold"),
            text_color=TEXT_PRIMARY, fg_color="transparent",
        ).pack(pady=(8, 2))
        ctk.CTkLabel(
            self._empty, text="No overdue maintenance items found",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            text_color=TEXT_SECONDARY, fg_color="transparent",
        ).pack()

    # ── loading / error helpers ───────────────────────────────────────────────

    def _show_loading(self):
        self._error_frame.grid_remove()
        self._banner.grid_remove()
        self._cards_scroll.grid_remove()
        self._empty.grid_remove()
        self._loading.grid()
        self._loading.start()

    def _show_error(self):
        self._loading.stop()
        self._loading.grid_remove()
        self._banner.grid_remove()
        self._cards_scroll.grid_remove()
        self._empty.grid_remove()
        self._error_frame.grid()

    # ── data ──────────────────────────────────────────────────────────────────

    def refresh(self):
        self._show_loading()
        threading.Thread(target=self._load, daemon=True).start()

    def _load(self):
        try:
            items = self.api.get_overdue()
        except Exception:
            self.after(0, self._show_error)
            return
        try:
            eq = self.api.get_equipment()
        except Exception:
            eq = []
        self.after(0, lambda i=items, e=eq: self._render(i, e))

    # ── render ────────────────────────────────────────────────────────────────

    def _clear_cards(self):
        for w in self._card_widgets:
            try:
                w.destroy()
            except Exception:
                pass
        self._card_widgets.clear()

    def _render(self, items: list[dict], eq: list[dict]):
        self._loading.stop()
        self._loading.grid_remove()
        self._error_frame.grid_remove()
        self._equipment_list = eq
        self._clear_cards()

        if not items:
            self._banner.grid_remove()
            self._cards_scroll.grid_remove()
            self._empty.grid()
            return

        count = len(items)
        self._banner_title.configure(
            text=f"{count} {'item' if count == 1 else 'items'} "
                 f"require immediate maintenance attention"
        )
        self._banner.grid()
        self._empty.grid_remove()
        self._cards_scroll.grid()

        first_tier = True
        for tier_name, tier_color, badge_bg, pred in _TIERS:
            tier_items = [i for i in items if pred(i.get("days_overdue", 0))]
            if not tier_items:
                continue

            # Section header — 24px gap between tiers achieved by
            # 12px card bottom-padding + 12px header top-padding
            top_pad = 0 if first_tier else 12
            first_tier = False

            lbl = ctk.CTkLabel(
                self._cards_scroll,
                text=f"{tier_name}  ({len(tier_items)})",
                font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
                text_color=tier_color, fg_color="transparent",
                anchor="w",
            )
            lbl.pack(fill="x", pady=(top_pad, 8))
            self._card_widgets.append(lbl)

            for item in tier_items:
                self._make_card(item, tier_name, tier_color, badge_bg)

    def _make_card(self, item: dict, tier: str, tier_color: str, badge_bg: str):
        days      = item.get("days_overdue", 0)
        name      = item.get("name", "—")
        location  = item.get("location", "—")
        last_maint = item.get("last_maintenance_date") or "Never"

        # ── Outer card ────────────────────────────────────────────────────
        card = ctk.CTkFrame(
            self._cards_scroll,
            fg_color=SURFACE,
            corner_radius=8,
            border_width=1,
            border_color=tier_color,
        )
        card.pack(fill="x", pady=(0, 12))
        self._card_widgets.append(card)

        # ── Left accent strip (4px) ───────────────────────────────────────
        strip = ctk.CTkFrame(card, width=4, fg_color=tier_color, corner_radius=0)
        strip.pack(side="left", fill="y")
        strip.pack_propagate(False)

        # ── Right: day count (packed before content → takes side="right") ─
        right = ctk.CTkFrame(card, fg_color="transparent")
        right.pack(side="right", padx=(0, 24), pady=16)

        ctk.CTkLabel(
            right,
            text=str(days),
            font=ctk.CTkFont(family=FONT_FAMILY, size=36, weight="bold"),
            text_color=tier_color, fg_color="transparent",
        ).pack(anchor="center")
        ctk.CTkLabel(
            right,
            text="days overdue",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=TEXT_SECONDARY, fg_color="transparent",
        ).pack(anchor="center", pady=(2, 0))

        # ── Content area (fills remaining width) ─────────────────────────
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(side="left", fill="both", expand=True, padx=(14, 0), pady=16)

        # Top row: equipment name + severity badge
        top_row = ctk.CTkFrame(content, fg_color="transparent")
        top_row.pack(fill="x")

        # Badge packed first so it holds its right position even with long names
        badge_frame = ctk.CTkFrame(top_row, fg_color=badge_bg, corner_radius=4)
        badge_frame.pack(side="right")
        ctk.CTkLabel(
            badge_frame,
            text=tier.upper(),
            font=ctk.CTkFont(family=FONT_FAMILY, size=10, weight="bold"),
            text_color=tier_color, fg_color="transparent",
        ).pack(padx=8, pady=3)

        ctk.CTkLabel(
            top_row,
            text=name,
            font=ctk.CTkFont(family=FONT_FAMILY, size=16, weight="bold"),
            text_color=TEXT_PRIMARY, fg_color="transparent",
        ).pack(side="left", fill="x", expand=True)

        # Meta row: location · last maintained
        ctk.CTkLabel(
            content,
            text=f"{location}  ·  Last maintained: {last_maint}",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color=TEXT_SECONDARY, fg_color="transparent",
            anchor="w",
        ).pack(fill="x", pady=(6, 0))

        # Log Maintenance button
        ctk.CTkButton(
            content,
            text="Log Maintenance",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            fg_color=ACCENT_LIGHT,
            hover_color="#1D3A8A",
            border_width=1,
            border_color=ACCENT,
            text_color=ACCENT,
            corner_radius=6,
            height=28, width=130,
            command=lambda n=name: self._open_log_modal(n),
        ).pack(anchor="w", pady=(10, 0))

    def _open_log_modal(self, equipment_name: str):
        if not self._equipment_list:
            return
        # Place the target equipment first so the modal pre-selects it
        eq = sorted(
            self._equipment_list,
            key=lambda e: 0 if e.get("name") == equipment_name else 1,
        )
        MaintenanceFormModal(self, self.api, eq, on_save=self.refresh)
