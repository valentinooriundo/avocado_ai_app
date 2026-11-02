from __future__ import annotations

import flet as ft

# Paleta principal Avoruna - versión profesional y suave
BRAND_PRIMARY = "#2F5D46"
BRAND_PRIMARY_DARK = "#244636"
BRAND_SOFT = "#EAF3EE"
BRAND_BG = "#F6F8F4"
BRAND_CARD = "#FFFFFF"
BRAND_TEXT = "#172018"
BRAND_MUTED = "#667085"
BRAND_BORDER = "#D8E2D8"

SUCCESS = "#2F7D57"
WARNING = "#B7791F"
DANGER = "#C05621"


def is_dark(page: ft.Page) -> bool:
    return page.theme_mode == ft.ThemeMode.DARK


def bg_color(page: ft.Page) -> str:
    return "#0F1412" if is_dark(page) else BRAND_BG


def surface_color(page: ft.Page) -> str:
    return "#161D19" if is_dark(page) else BRAND_CARD


def text_color(page: ft.Page) -> str:
    return "#F5F7F6" if is_dark(page) else BRAND_TEXT


def muted_color(page: ft.Page) -> str:
    return "#98A2B3" if is_dark(page) else BRAND_MUTED


def border_color(page: ft.Page) -> str:
    return "#29342D" if is_dark(page) else BRAND_BORDER
