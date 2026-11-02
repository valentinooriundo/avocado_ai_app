from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


# Debe ejecutarse antes de importar los servicios.
load_dotenv()


import flet as ft

from services.auth_session_service import (
    is_authenticated,
    restore_auth_data,
)
from services.settings_service import (
    load_language,
    load_theme,
)
from storage.db import Database
from ui.routes import configure_routes
from ui.state import AppState, set_state


BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

DB_PATH = PROJECT_ROOT / "avocado_app.db"
ASSETS_DIR = BASE_DIR / "assets"
UPLOADS_DIR = BASE_DIR / "uploads"


def main(page: ft.Page) -> None:
    app_name = "Avoruna"

    UPLOADS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    page.title = app_name
    page.padding = 0
    page.spacing = 0
    page.scroll = ft.ScrollMode.HIDDEN
    page.adaptive = False

    page.theme = ft.Theme(
        color_scheme_seed="#2F5D46",
    )

    page.dark_theme = ft.Theme(
        color_scheme_seed="#2F5D46",
    )

    page.data = {}

    db = Database(
        str(DB_PATH)
    )

    db.init_schema()
    page.data["db"] = db

    language = load_language(db)

    set_state(
        page,
        AppState(
            app_name=app_name,
            lang=language,
        ),
    )

    saved_theme = load_theme(db)

    page.theme_mode = (
        ft.ThemeMode.DARK
        if saved_theme == "dark"
        else ft.ThemeMode.LIGHT
    )

    restore_auth_data(page)
    configure_routes(page)

    initial_route = (
        "/dashboard"
        if is_authenticated(page)
        else "/welcome"
    )

    page.run_task(
        page.push_route,
        initial_route,
    )


if __name__ == "__main__":
    ft.run(
        main,
        assets_dir=str(ASSETS_DIR),
        upload_dir=str(UPLOADS_DIR),
        port=8550,
    )
