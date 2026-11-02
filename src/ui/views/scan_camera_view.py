from __future__ import annotations

import asyncio
from datetime import datetime
from pathlib import Path

import flet as ft
import flet_camera as fc
import flet_permission_handler as fph

from services.scan_flow_service import process_scan_input
from services.settings_service import load_theme
from ui.components.app_shell import build_app_shell
from ui.theme_tokens import BRAND_PRIMARY, BRAND_SOFT, text_color, muted_color, border_color, surface_color


BRAND_GREEN = BRAND_PRIMARY
PROJECT_DIR = Path(__file__).resolve().parents[3]
MOBILE_CAPTURE_DIR = PROJECT_DIR / "captures" / "mobile"


def _is_dark(page: ft.Page) -> bool:
    return page.theme_mode == ft.ThemeMode.DARK


def _c_surface(page: ft.Page) -> str:
    return "#11161C" if _is_dark(page) else "#FFFFFF"


def _c_text(page: ft.Page) -> str:
    return "#F5F7FA" if _is_dark(page) else "#172018"


def _c_muted(page: ft.Page) -> str:
    return "#97A3B6" if _is_dark(page) else "#667085"


def _c_border(page: ft.Page) -> str:
    return "#253041" if _is_dark(page) else "#DCE5D6"


def _nav(page: ft.Page, route: str) -> None:
    page.run_task(page.push_route, route)


def create_scan_camera_view(page: ft.Page) -> ft.View:
    db = page.data.get("db") if isinstance(page.data, dict) else None

    if db is not None:
        saved = load_theme(db)
        page.theme_mode = (
            ft.ThemeMode.DARK
            if saved == "dark"
            else ft.ThemeMode.LIGHT
        )

    if page.data is None:
        page.data = {}

    MOBILE_CAPTURE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    state = {
        "initialized": False,
        "busy": False,
        "cameras": [],
        "selected_index": 0,
    }

    permission_handler = fph.PermissionHandler()

    status_icon = ft.Icon(
        ft.Icons.CAMERA_ALT_OUTLINED,
        size=18,
        color=BRAND_GREEN,
    )

    status_text = ft.Text(
        "Activa la cámara para comenzar.",
        size=12,
        color=_c_muted(page),
        weight=ft.FontWeight.W_700,
    )

    progress_ring = ft.ProgressRing(
        width=20,
        height=20,
        stroke_width=2,
        color=ft.Colors.WHITE,
        visible=False,
    )

    camera_overlay = ft.Stack(
        expand=True,
        controls=[
            ft.Container(
                expand=True,
                alignment=ft.Alignment(0, 0),
                content=ft.Container(
                    width=230,
                    height=320,
                    border_radius=28,
                    border=ft.Border.all(
                        3,
                        BRAND_GREEN,
                    ),
                ),
            ),
            ft.Container(
                left=18,
                right=18,
                top=18,
                padding=ft.Padding(12, 9, 12, 9),
                border_radius=14,
                bgcolor=ft.Colors.with_opacity(
                    0.66,
                    ft.Colors.BLACK,
                ),
                content=ft.Row(
                    spacing=9,
                    controls=[
                        ft.Icon(
                            ft.Icons.CENTER_FOCUS_STRONG,
                            color=ft.Colors.WHITE,
                            size=18,
                        ),
                        ft.Text(
                            "Coloca una sola palta Hass dentro del recuadro",
                            size=11,
                            color=ft.Colors.WHITE,
                            weight=ft.FontWeight.W_800,
                            expand=True,
                        ),
                    ],
                ),
            ),
            ft.Container(
                left=18,
                right=18,
                bottom=18,
                padding=ft.Padding(12, 9, 12, 9),
                border_radius=14,
                bgcolor=ft.Colors.with_opacity(
                    0.66,
                    ft.Colors.BLACK,
                ),
                content=ft.Text(
                    "Evita sombras fuertes, movimiento y fondos muy claros.",
                    size=10,
                    color=ft.Colors.WHITE,
                    text_align=ft.TextAlign.CENTER,
                ),
            ),
        ],
    )

    camera = fc.Camera(
        expand=True,
        preview_enabled=True,
        content=camera_overlay,
    )

    activate_button_text = ft.Text(
        "Activar cámara",
        weight=ft.FontWeight.W_900,
    )

    capture_button_text = ft.Text(
        "Capturar y analizar",
        weight=ft.FontWeight.W_900,
        color=ft.Colors.WHITE,
    )

    activate_button = ft.OutlinedButton(
        content=ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=8,
            controls=[
                ft.Icon(
                    ft.Icons.POWER_SETTINGS_NEW,
                    size=18,
                ),
                activate_button_text,
            ],
        ),
        height=50,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(
                radius=15
            ),
        ),
    )

    switch_button = ft.IconButton(
        icon=ft.Icons.CAMERASWITCH_OUTLINED,
        tooltip="Cambiar cámara",
        disabled=True,
    )

    capture_button = ft.FilledButton(
        content=ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10,
            controls=[
                progress_ring,
                ft.Icon(
                    ft.Icons.PHOTO_CAMERA,
                    size=20,
                    color=ft.Colors.WHITE,
                ),
                capture_button_text,
            ],
        ),
        height=54,
        disabled=True,
        style=ft.ButtonStyle(
            bgcolor=BRAND_GREEN,
            color=ft.Colors.WHITE,
            shape=ft.RoundedRectangleBorder(
                radius=16
            ),
        ),
    )

    def show_message(message: str) -> None:
        page.show_dialog(
            ft.SnackBar(
                content=ft.Text(message),
            )
        )

    def sync_controls() -> None:
        busy = bool(state["busy"])
        initialized = bool(
            state["initialized"]
        )

        activate_button.disabled = busy
        capture_button.disabled = (
            busy or not initialized
        )
        switch_button.disabled = (
            busy
            or not initialized
            or len(state["cameras"]) < 2
        )
        progress_ring.visible = busy

    async def request_camera_permission() -> bool:
        try:
            permission_status = await permission_handler.request(
                fph.Permission.CAMERA
            )

            status_name = getattr(
                permission_status,
                "name",
                "",
            ).upper()

            if status_name in {
                "GRANTED",
                "LIMITED",
            }:
                return True

            if status_name == "PERMANENTLY_DENIED":
                status_icon.name = (
                    ft.Icons.NO_PHOTOGRAPHY_OUTLINED
                )
                status_icon.color = ft.Colors.RED_400
                status_text.value = (
                    "El permiso de cámara está bloqueado. "
                    "Habilítalo desde los ajustes del dispositivo."
                )
                page.update()
                return False

            if status_name:
                status_icon.name = (
                    ft.Icons.NO_PHOTOGRAPHY_OUTLINED
                )
                status_icon.color = ft.Colors.RED_400
                status_text.value = (
                    "No se concedió permiso para utilizar la cámara."
                )
                page.update()
                return False

            # Algunos clientes de prueba pueden devolver None y
            # solicitar el permiso al inicializar la cámara.
            return True

        except Exception:
            # Se intenta inicializar igualmente; la cámara devolverá
            # un error claro si el permiso no está disponible.
            return True

    async def initialize_camera(_=None) -> None:
        if state["busy"]:
            return

        state["busy"] = True
        activate_button_text.value = (
            "Preparando cámara..."
        )
        status_icon.name = (
            ft.Icons.HOURGLASS_TOP
        )
        status_icon.color = BRAND_GREEN
        status_text.value = (
            "Solicitando acceso y buscando cámaras disponibles..."
        )
        sync_controls()
        page.update()

        try:
            has_permission = (
                await request_camera_permission()
            )

            if not has_permission:
                return

            cameras = await camera.get_available_cameras()

            if not cameras:
                raise RuntimeError(
                    "No se encontró una cámara disponible."
                )

            state["cameras"] = cameras

            back_index = next(
                (
                    index
                    for index, description
                    in enumerate(cameras)
                    if description.lens_direction
                    == fc.CameraLensDirection.BACK
                ),
                0,
            )

            state["selected_index"] = (
                back_index
            )

            selected_camera = cameras[
                back_index
            ]

            await camera.initialize(
                description=selected_camera,
                resolution_preset=(
                    fc.ResolutionPreset.HIGH
                ),
                enable_audio=False,
                image_format_group=(
                    fc.ImageFormatGroup.JPEG
                ),
            )

            try:
                await camera.lock_capture_orientation()
            except Exception:
                pass

            state["initialized"] = True
            status_icon.name = (
                ft.Icons.CHECK_CIRCLE_OUTLINE
            )
            status_icon.color = BRAND_GREEN
            status_text.value = (
                "Cámara lista. Centra el fruto y captura la imagen."
            )
            activate_button_text.value = (
                "Cámara activada"
            )

        except Exception as exception:
            state["initialized"] = False
            status_icon.name = (
                ft.Icons.ERROR_OUTLINE
            )
            status_icon.color = ft.Colors.RED_400
            status_text.value = (
                f"No se pudo iniciar la cámara: {exception}"
            )
            activate_button_text.value = (
                "Reintentar"
            )

        finally:
            state["busy"] = False
            sync_controls()
            page.update()

    async def switch_camera(_=None) -> None:
        cameras = state["cameras"]

        if (
            not state["initialized"]
            or len(cameras) < 2
            or state["busy"]
        ):
            return

        state["busy"] = True
        status_text.value = (
            "Cambiando cámara..."
        )
        sync_controls()
        page.update()

        try:
            next_index = (
                state["selected_index"] + 1
            ) % len(cameras)

            await camera.set_description(
                cameras[next_index]
            )

            state["selected_index"] = (
                next_index
            )
            status_text.value = (
                "Cámara cambiada correctamente."
            )

        except Exception as exception:
            status_text.value = (
                f"No se pudo cambiar la cámara: {exception}"
            )

        finally:
            state["busy"] = False
            sync_controls()
            page.update()

    async def capture_and_analyze(_=None) -> None:
        if not state["initialized"]:
            show_message(
                "Activa la cámara antes de capturar."
            )
            return

        if state["busy"]:
            return

        state["busy"] = True
        capture_button_text.value = (
            "Analizando fotografía..."
        )
        status_icon.name = (
            ft.Icons.AUTO_AWESOME
        )
        status_icon.color = BRAND_GREEN
        status_text.value = (
            "Capturando y ejecutando el modelo de madurez..."
        )
        sync_controls()
        page.update()

        capture_path: Path | None = None

        try:
            photo_bytes = await camera.take_picture()

            if not photo_bytes:
                raise RuntimeError(
                    "La cámara no devolvió una fotografía."
                )

            capture_path = MOBILE_CAPTURE_DIR / (
                "mobile_"
                f"{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
                ".jpg"
            )

            capture_path.write_bytes(
                photo_bytes
            )

            result = await asyncio.to_thread(
                process_scan_input,
                local_path=str(capture_path),
            )

            page.data["scan_result"] = result
            page.data["scan_image_bytes"] = photo_bytes
            page.data["scan_image_path"] = result.get(
                "saved_image_path"
            )
            page.data["last_scan_id"] = result.get(
                "scan_id"
            )

            await page.push_route(
                "/result"
            )

        except Exception as exception:
            status_icon.name = (
                ft.Icons.ERROR_OUTLINE
            )
            status_icon.color = ft.Colors.RED_400
            status_text.value = (
                f"No se pudo completar el análisis: {exception}"
            )
            show_message(
                "No se pudo analizar la fotografía."
            )

        finally:
            state["busy"] = False
            capture_button_text.value = (
                "Capturar y analizar"
            )
            sync_controls()

            try:
                page.update()
            except Exception:
                pass

    async def on_camera_state_change(
        event: fc.CameraStateEvent,
    ) -> None:
        if event.has_error:
            state["initialized"] = False
            status_icon.name = (
                ft.Icons.ERROR_OUTLINE
            )
            status_icon.color = ft.Colors.RED_400
            status_text.value = (
                "Error de cámara: "
                f"{event.error_description}"
            )
            sync_controls()
            page.update()

    activate_button.on_click = initialize_camera
    switch_button.on_click = switch_camera
    capture_button.on_click = (
        capture_and_analyze
    )
    camera.on_state_change = (
        on_camera_state_change
    )

    camera_frame = ft.Container(
        height=530,
        border_radius=26,
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        bgcolor=ft.Colors.BLACK,
        border=ft.Border.all(
            1,
            _c_border(page),
        ),
        content=camera,
    )

    status_card = ft.Container(
        padding=ft.Padding(14, 12, 14, 12),
        border_radius=16,
        bgcolor=_c_surface(page),
        border=ft.Border.all(
            1,
            _c_border(page),
        ),
        content=ft.Row(
            spacing=10,
            controls=[
                status_icon,
                ft.Container(
                    expand=True,
                    content=status_text,
                ),
            ],
        ),
    )

    controls_panel = ft.Column(
        spacing=10,
        controls=[
            ft.Row(
                spacing=10,
                controls=[
                    ft.Container(
                        expand=True,
                        content=activate_button,
                    ),
                    switch_button,
                ],
            ),
            ft.Container(
                width=float("inf"),
                content=capture_button,
            ),
            ft.TextButton(
                content=ft.Text(
                    "Volver al escaneo",
                    weight=ft.FontWeight.W_800,
                ),
                icon=ft.Icons.ARROW_BACK,
                on_click=lambda _: _nav(
                    page,
                    "/scan",
                ),
            ),
        ],
    )

    content = ft.Container(
        expand=True,
        padding=ft.Padding(12, 10, 12, 20),
        content=ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=14,
            controls=[
                ft.Column(
                    spacing=4,
                    controls=[
                        ft.Text(
                            "Captura de palta Hass",
                            size=22,
                            color=_c_text(page),
                            weight=ft.FontWeight.W_900,
                        ),
                        ft.Text(
                            "Toma una fotografía clara para analizar "
                            "el nivel de madurez con MobileNetV2.",
                            size=12,
                            color=_c_muted(page),
                        ),
                    ],
                ),
                camera_frame,
                status_card,
                controls_panel,
            ],
        ),
    )

    root = build_app_shell(
        page,
        content,
    )

    return ft.View(
        route="/scan/camera",
        controls=[
            ft.SafeArea(
                expand=True,
                content=root,
            ),
        ],
    )
