import flet as ft
from ui.i18n import I18N

class AppState:
    def __init__(self, app_name: str, lang: str = "es"):
        self.app_name = app_name
        self.lang = lang

    def t(self, key: str) -> str:
        return I18N.get(self.lang, I18N["es"]).get(key, I18N["es"].get(key, key))

def get_state(page: ft.Page) -> AppState:
    return page.data.get("state")

def set_state(page: ft.Page, state: AppState) -> None:
    page.data["state"] = state
