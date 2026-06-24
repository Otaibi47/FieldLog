import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import customtkinter as ctk
from api_client import APIClient
from components.sidebar import Sidebar
from screens.dashboard import DashboardScreen
from screens.equipment import EquipmentScreen
from screens.maintenance import MaintenanceScreen
from screens.alerts import AlertsScreen
from config import BG, FONT_FAMILY, TEXT_PRIMARY

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


class FieldLogApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("FieldLog")
        self.geometry("1100x700")
        self.minsize(900, 600)
        self.configure(fg_color=BG)

        self.api = APIClient()
        try:
            self.api.init_token()
        except Exception:
            pass  # Backend may not be running — UI still loads

        self._screens: dict = {}
        self._current: str = ""
        self._build()
        self._navigate("dashboard")
        self._check_alerts()

    def _build(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = Sidebar(self, on_navigate=self._navigate)
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        self.content_frame = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        self.content_frame.grid(row=0, column=1, sticky="nsew")
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)

    def _navigate(self, key: str):
        if key == self._current:
            return
        if self._current and self._current in self._screens:
            self._screens[self._current].grid_remove()

        if key not in self._screens:
            self._screens[key] = self._build_screen(key)

        self._screens[key].grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        self.sidebar.set_active(key)
        self._current = key

        # Refresh data when switching screens
        screen = self._screens[key]
        if hasattr(screen, "refresh"):
            try:
                screen.refresh()
            except Exception:
                pass

    def _build_screen(self, key: str):
        kwargs = {"master": self.content_frame, "api_client": self.api}
        screens = {
            "dashboard": DashboardScreen,
            "equipment": EquipmentScreen,
            "maintenance": MaintenanceScreen,
            "alerts": AlertsScreen,
        }
        cls = screens.get(key)
        return cls(**kwargs) if cls else ctk.CTkFrame(self.content_frame)

    def _check_alerts(self):
        try:
            overdue = self.api.get_overdue()
            self.sidebar.set_alert_count(len(overdue))
        except Exception:
            pass
        # Recheck every 5 minutes
        self.after(300_000, self._check_alerts)


def main():
    app = FieldLogApp()
    app.mainloop()


if __name__ == "__main__":
    main()
