import sys
import os
import threading
sys.path.insert(0, os.path.dirname(__file__))

import customtkinter as ctk
from api_client import APIClient
from components.sidebar import Sidebar
from screens.dashboard import DashboardScreen
from screens.equipment import EquipmentScreen
from screens.maintenance import MaintenanceScreen
from screens.alerts import AlertsScreen
from config import BG, BORDER

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class FieldLogApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("FieldLog")
        self.geometry("1160x720")
        self.minsize(960, 620)
        self.configure(fg_color=BG)

        self.api = APIClient()
        self._screens: dict = {}
        self._current: str = ""

        self._build()
        self._navigate("dashboard")
        threading.Thread(target=self._init_backend, daemon=True).start()

    def _build(self):
        self.grid_columnconfigure(0, weight=0)   # sidebar — 220px fixed
        self.grid_columnconfigure(1, weight=0)   # 1px border separator
        self.grid_columnconfigure(2, weight=1)   # content — fills remaining
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = Sidebar(self, on_navigate=self._navigate)
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        # 1px right-edge border on the sidebar
        ctk.CTkFrame(self, width=1, fg_color=BORDER, corner_radius=0).grid(
            row=0, column=1, sticky="nsew"
        )

        self.content_frame = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        self.content_frame.grid(row=0, column=2, sticky="nsew")
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)

    def _init_backend(self):
        self.api.init_token()
        self.after(0, self._refresh_current)
        self.after(0, self._check_alerts)

    def _refresh_current(self):
        screen = self._screens.get(self._current)
        if screen and hasattr(screen, "refresh"):
            screen.refresh()

    def _navigate(self, key: str):
        if key == self._current:
            return
        if self._current and self._current in self._screens:
            self._screens[self._current].grid_remove()

        if key not in self._screens:
            self._screens[key] = self._build_screen(key)

        self._screens[key].grid(row=0, column=0, sticky="nsew")
        self.sidebar.set_active(key)
        self._current = key

        screen = self._screens[key]
        if hasattr(screen, "refresh"):
            screen.refresh()

    def _build_screen(self, key: str):
        cls_map = {
            "dashboard":   DashboardScreen,
            "equipment":   EquipmentScreen,
            "maintenance": MaintenanceScreen,
            "alerts":      AlertsScreen,
        }
        cls = cls_map.get(key)
        return cls(master=self.content_frame, api_client=self.api) if cls else ctk.CTkFrame(self.content_frame)

    def _check_alerts(self):
        def _load():
            try:
                overdue = self.api.get_overdue()
                self.after(0, lambda c=len(overdue): self.sidebar.set_alert_count(c))
            except Exception:
                pass
        threading.Thread(target=_load, daemon=True).start()
        self.after(300_000, self._check_alerts)


def main():
    app = FieldLogApp()
    app.mainloop()


if __name__ == "__main__":
    main()
