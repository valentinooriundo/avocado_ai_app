import asyncio
import flet as ft
from ui.state import get_state
from services.auth_service import load_session, clear_session

def create_dashboard_stub_view(page: ft.Page) -> ft.View:
    db = page.data["db"]
    state = get_state(page)
    user = load_session(db)

    def nav(route: str):
        asyncio.create_task(page.push_route(route))

    if not user:
        return ft.View(
            route="/dashboard",
            padding=20,
            controls=[
                ft.Text(state.t("dashboard_title") + " (stub)", size=20, weight=ft.FontWeight.W_600),
                ft.Container(height=8),
                ft.Text(state.t("dashboard_denied"), size=14),
                ft.Container(height=10),
                ft.FilledButton(content=state.t("login"), on_click=lambda _: nav("/login")),
                ft.TextButton(content=state.t("go_camera"), on_click=lambda _: nav("/camera")),
            ],
        )

    def logout(_):
        clear_session(db)
        nav("/welcome")

    return ft.View(
        route="/dashboard",
        padding=20,
        controls=[
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Text(f"{state.t('dashboard_title')} (stub) — {user}", size=20, weight=ft.FontWeight.W_600),
                    ft.TextButton(content=state.t("logout"), on_click=logout),
                ],
            ),
            ft.Container(height=10),
            ft.Text("Aquí irán métricas, historial avanzado y exportaciones.", size=14),
            ft.Container(height=10),
            ft.TextButton(content=state.t("go_camera"), on_click=lambda _: nav("/camera")),
        ],
    )
