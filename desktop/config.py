import os

API_BASE_URL = os.getenv("API_BASE_URL", "https://fieldlog-production-8300.up.railway.app")

# ── Core palette — dark mode (slate/blue, WCAG AA) ────────────────────────────
# Depth hierarchy:  SIDEBAR_BG < BG < SURFACE  (darker → lighter)
BG             = "#0F172A"   # slate-950  — page / window background
SURFACE        = "#1E293B"   # slate-800  — cards, panels, table rows
BORDER         = "#334155"   # slate-700  — dividers, input borders

TEXT_PRIMARY   = "#F1F5F9"   # slate-100  — headings, values       (16:1 on BG ✓)
TEXT_SECONDARY = "#94A3B8"   # slate-400  — subtitles, labels       ( 7:1 on BG ✓)

ACCENT         = "#3B82F6"   # blue-500   — CTAs, active accent
ACCENT_LIGHT   = "#172554"   # blue-950   — active / hover bg tint

SUCCESS        = "#4ADE80"   # green-400  — operational
WARNING        = "#FBBF24"   # amber-400  — degraded
DANGER         = "#F87171"   # red-400    — offline / overdue
DANGER_LIGHT   = "#1C0B0B"   # custom     — danger bg tint

# ── Typography ────────────────────────────────────────────────────────────────
FONT_FAMILY = "Segoe UI"
FONT_MONO   = "Cascadia Code"

# ── Sidebar — dark theme ──────────────────────────────────────────────────────
SIDEBAR_BG          = "#0B1120"   # deeper than BG — creates visual separation
SIDEBAR_HOVER       = "#1A2540"
SIDEBAR_ACTIVE_BG   = "#172554"   # blue-950 tint
SIDEBAR_TEXT        = "#CBD5E1"   # slate-300
SIDEBAR_TEXT_ACTIVE = "#60A5FA"   # blue-400
SIDEBAR_RULE        = "#3B82F6"   # blue-500
SIDEBAR_LABEL       = "#475569"   # slate-600
