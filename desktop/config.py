import os

API_BASE_URL = os.getenv("API_BASE_URL", "https://fieldlog-production-8300.up.railway.app")

# Colors
BG = "#F8F9FA"
SURFACE = "#FFFFFF"
BORDER = "#E5E7EB"
TEXT_PRIMARY = "#111827"
TEXT_SECONDARY = "#6B7280"
ACCENT = "#1D4ED8"
ACCENT_LIGHT = "#EFF6FF"
SUCCESS = "#16A34A"
WARNING = "#D97706"
DANGER = "#DC2626"
DANGER_LIGHT = "#FEF2F2"

# Font families
FONT_FAMILY = "Segoe UI"
FONT_MONO = "Cascadia Code"

# Sidebar — dark theme (contrast against white content area)
SIDEBAR_BG           = "#1E293B"   # dark slate
SIDEBAR_HOVER        = "#273549"   # slightly lighter on hover
SIDEBAR_ACTIVE_BG    = "#334155"   # active item background
SIDEBAR_TEXT         = "#94A3B8"   # inactive nav text
SIDEBAR_TEXT_ACTIVE  = "#F1F5F9"   # active nav text (near-white)
SIDEBAR_RULE         = "#3B82F6"   # active left-rule (lighter blue on dark bg)
SIDEBAR_LABEL        = "#64748B"   # section label ("NAVIGATION")
