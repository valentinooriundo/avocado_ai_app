import flet as ft

from services.auth_session_service import is_authenticated

from ui.views.welcome_view import create_welcome_view
from ui.views.login_view import create_login_view
from ui.views.register_view import (
    create_register_view,
    create_register_success_view,
)
from ui.views.camera_stub_view import create_camera_stub_view

from ui.views.forgot_password_view import create_forgot_password_view
from ui.views.verify_otp_view import create_verify_otp_view
from ui.views.new_password_view import create_new_password_view

from ui.views.home_view import create_home_view
from ui.views.scan_view import create_scan_view
from ui.views.scan_camera_view import create_scan_camera_view
from ui.views.result_view import create_result_view
from ui.views.history_view import create_history_view
from ui.views.settings_view import create_settings_view
from ui.views.alerts_view import create_alerts_view
from ui.views.profile_view import create_profile_view
from ui.views.team_view import create_team_view
from ui.views.learning_view import create_learning_view
from ui.views.support_view import create_support_view
from ui.views.dashboard_view import create_dashboard_view
from ui.views.reports_view import create_reports_view
from ui.views.fincas_view import create_fincas_view
from ui.views.parcelas_view import create_parcelas_view
from ui.views.sync_view import create_sync_view


def _route_path(route: str) -> str:
    return (route or "").split("?", 1)[0].rstrip("/")


def configure_routes(page: ft.Page):
    # Rutas disponibles sin iniciar sesión
    public_routes = {
        "/welcome",
        "/login",
        "/oauth_callback",
        "/register",
        "/register/success",
        "/help",
        "/help/verify",
        "/help/new-password",

        # Flujo público de escaneo
        "/scan",
        "/scan/camera",
        "/result",
    }

    def route_change(e: ft.RouteChangeEvent):
        route = _route_path(page.route)
        show_register_success_toast = False

        if route == "":
            route = "/welcome"

        logged_in = is_authenticated(page)

        # Un usuario autenticado ya no necesita volver al login
        # ni a la pantalla inicial.
        if logged_in and route in {
            "/login",
            "/welcome",
            "/oauth_callback",
        }:
            page.run_task(
                page.push_route,
                "/dashboard",
            )
            return

        # Un usuario no autenticado solamente puede acceder
        # a las rutas declaradas como públicas.
        if not logged_in and route not in public_routes:
            page.run_task(
                page.push_route,
                "/login",
            )
            return

        page.views.clear()

        if route == "/welcome":
            page.views.append(
                create_welcome_view(page)
            )

        elif route == "/home":
            page.views.append(
                create_home_view(page)
            )

        elif route == "/scan":
            page.views.append(
                create_scan_view(page)
            )

        elif route == "/scan/camera":
            page.views.append(
                create_scan_camera_view(page)
            )

        elif route == "/result":
            page.views.append(
                create_result_view(page)
            )

        elif route == "/history":
            page.views.append(
                create_history_view(page)
            )

        elif route == "/settings":
            page.views.append(
                create_settings_view(page)
            )

        elif route == "/alerts":
            page.views.append(
                create_alerts_view(page)
            )

        elif route == "/profile":
            page.views.append(
                create_profile_view(page)
            )

        elif route == "/team":
            page.views.append(
                create_team_view(page)
            )

        elif route == "/learn":
            page.views.append(
                create_learning_view(page)
            )

        elif route == "/support":
            page.views.append(
                create_support_view(page)
            )

        elif route == "/login":
            page.views.append(
                create_login_view(page)
            )

        elif route == "/oauth_callback":
            page.views.append(
                create_login_view(page)
            )

        elif route == "/register":
            page.views.append(
                create_register_view(page)
            )

        elif route == "/register/success":
            page.views.append(
                create_register_success_view(page)
            )

            show_register_success_toast = page.data.pop(
                "register_success_pending",
                False,
            )

        elif route == "/help":
            page.views.append(
                create_forgot_password_view(page)
            )

        elif route == "/help/verify":
            page.views.append(
                create_verify_otp_view(page)
            )

        elif route == "/help/new-password":
            page.views.append(
                create_new_password_view(page)
            )

        elif route == "/camera":
            page.views.append(
                create_camera_stub_view(page)
            )

        elif route == "/dashboard":
            page.views.append(
                create_dashboard_view(page)
            )

        elif route == "/reports":
            page.views.append(
                create_reports_view(page)
            )

        elif route == "/fincas":
            page.views.append(
                create_fincas_view(page)
            )

        elif route == "/parcelas":
            page.views.append(
                create_parcelas_view(page)
            )

        elif route == "/sync":
            page.views.append(
                create_sync_view(page)
            )

        else:
            if logged_in:
                page.views.append(
                    create_dashboard_view(page)
                )
            else:
                page.views.append(
                    create_welcome_view(page)
                )

        page.update()

        if show_register_success_toast:
            page.show_dialog(
                ft.SnackBar(
                    content=ft.Row(
                        spacing=10,
                        controls=[
                            ft.Icon(
                                ft.Icons.CHECK_CIRCLE_OUTLINE,
                                color=ft.Colors.WHITE,
                            ),
                            ft.Text(
                                (
                                    "Cuenta creada correctamente. "
                                    "Ya puedes iniciar sesión."
                                ),
                                color=ft.Colors.WHITE,
                                weight=ft.FontWeight.W_700,
                            ),
                        ],
                    ),
                    bgcolor="#2F5D46",
                    show_close_icon=True,
                    duration=ft.Duration(seconds=4),
                )
            )

    def view_pop(e: ft.ViewPopEvent):
        if len(page.views) > 1:
            page.views.pop()
            top = page.views[-1]

            page.run_task(
                page.push_route,
                top.route,
            )
        else:
            if is_authenticated(page):
                page.run_task(
                    page.push_route,
                    "/dashboard",
                )
            else:
                page.run_task(
                    page.push_route,
                    "/welcome",
                )

    page.on_route_change = route_change
    page.on_view_pop = view_pop
