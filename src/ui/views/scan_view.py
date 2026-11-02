from __future__ import annotations

import asyncio
import base64
import os
from datetime import datetime
from pathlib import Path

import flet as ft

from services.camera_capture_service import (
    capture_image_with_assistance,
)
from services.scan_flow_service import (
    get_latest_scan,
    process_scan_input,
)
from services.settings_service import load_theme
from ui.components.app_shell import build_app_shell


# =========================================================
# PALETA AVORUNA
# =========================================================

BRAND_PRIMARY = "#2F5D46"
BRAND_PRIMARY_DARK = "#244A38"
BRAND_SOFT = "#EAF3EE"
PAGE_BG = "#F6F8F4"

SUCCESS = "#2F7D57"
WARNING = "#B7791F"
DANGER = "#B54747"


# =========================================================
# UTILIDADES VISUALES
# =========================================================

def _is_dark(page: ft.Page) -> bool:
    return page.theme_mode == ft.ThemeMode.DARK


def _screen_mode(page: ft.Page) -> str:
    width = page.width or 390

    if width < 760:
        return "mobile"

    if width < 1100:
        return "tablet"

    return "desktop"


def _is_web(page: ft.Page) -> bool:
    try:
        web_value = getattr(page, "web", None)

        if isinstance(web_value, bool):
            return web_value

    except Exception:
        pass

    try:
        platform = getattr(page, "platform", None)

        if isinstance(platform, str):
            return platform.lower() == "web"

        platform_name = getattr(
            platform,
            "name",
            "",
        )

        return str(platform_name).lower() == "web"

    except Exception:
        return False


def _c_bg(page: ft.Page) -> str:
    return "#0F1412" if _is_dark(page) else PAGE_BG


def _c_surface(page: ft.Page) -> str:
    return "#161D19" if _is_dark(page) else "#FFFFFF"


def _c_soft(page: ft.Page) -> str:
    return "#1D2721" if _is_dark(page) else BRAND_SOFT


def _c_text(page: ft.Page) -> str:
    return "#F5F7F6" if _is_dark(page) else "#172018"


def _c_muted(page: ft.Page) -> str:
    return "#98A2B3" if _is_dark(page) else "#667085"


def _c_border(page: ft.Page) -> str:
    return "#2B382F" if _is_dark(page) else "#D8E2D8"


def _shadow(page: ft.Page) -> ft.BoxShadow:
    return ft.BoxShadow(
        blur_radius=22,
        spread_radius=0,
        color=ft.Colors.with_opacity(
            0.18 if _is_dark(page) else 0.06,
            ft.Colors.BLACK,
        ),
        offset=ft.Offset(0, 8),
    )


def _nav(
    page: ft.Page,
    route: str,
) -> None:
    page.run_task(
        page.push_route,
        route,
    )


def _card(
    page: ft.Page,
    content: ft.Control,
    *,
    padding: int = 16,
    radius: int = 20,
    shadow: bool = False,
) -> ft.Container:
    return ft.Container(
        padding=ft.Padding(
            padding,
            padding,
            padding,
            padding,
        ),
        border_radius=radius,
        bgcolor=_c_surface(page),
        border=ft.Border.all(
            1,
            _c_border(page),
        ),
        shadow=_shadow(page) if shadow else None,
        content=content,
    )


def _soft_card(
    page: ft.Page,
    content: ft.Control,
    *,
    padding: int = 14,
    radius: int = 16,
) -> ft.Container:
    return ft.Container(
        padding=ft.Padding(
            padding,
            padding,
            padding,
            padding,
        ),
        border_radius=radius,
        bgcolor=_c_soft(page),
        border=ft.Border.all(
            1,
            _c_border(page),
        ),
        content=content,
    )


def _image_to_data_uri(
    image_path: str,
) -> str | None:
    try:
        path = Path(image_path)

        if not path.exists():
            return None

        mime_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".webp": "image/webp",
        }

        mime_type = mime_types.get(
            path.suffix.lower(),
            "image/jpeg",
        )

        encoded = base64.b64encode(
            path.read_bytes()
        ).decode("utf-8")

        return (
            f"data:{mime_type};base64,"
            f"{encoded}"
        )

    except Exception:
        return None


def _pick_image_with_tkinter() -> str | None:
    try:
        import tkinter as tk
        from tkinter import filedialog

    except Exception:
        return None

    root = tk.Tk()
    root.withdraw()
    root.attributes(
        "-topmost",
        True,
    )

    try:
        selected_path = filedialog.askopenfilename(
            title="Seleccionar imagen",
            filetypes=[
                (
                    "Imágenes",
                    "*.png;*.jpg;*.jpeg;*.webp",
                ),
                (
                    "PNG",
                    "*.png",
                ),
                (
                    "JPG",
                    "*.jpg;*.jpeg",
                ),
                (
                    "WEBP",
                    "*.webp",
                ),
            ],
        )

    finally:
        try:
            root.destroy()
        except Exception:
            pass

    return selected_path or None


def _result_color(
    result: dict,
):
    if not result.get(
        "is_reliable",
        False,
    ):
        return WARNING

    color_name = str(
        result.get(
            "result_color",
            "",
        )
    ).lower()

    if color_name == "green":
        return SUCCESS

    if color_name == "red":
        return DANGER

    if color_name == "amber":
        return WARNING

    return BRAND_PRIMARY


# =========================================================
# VISTA
# =========================================================

def create_scan_view(
    page: ft.Page,
) -> ft.View:
    if page.data is None:
        page.data = {}

    db = page.data.get("db")

    if db is not None:
        saved_theme = load_theme(db)

        page.theme_mode = (
            ft.ThemeMode.DARK
            if saved_theme == "dark"
            else ft.ThemeMode.LIGHT
        )

    mode = _screen_mode(page)
    is_mobile = mode == "mobile"
    is_web = _is_web(page)

    state = {
        "local_path": "",
        "image_url": "",
        "busy": False,
    }

    # -----------------------------------------------------
    # CONTROLES DE ESTADO
    # -----------------------------------------------------

    progress_ring = ft.ProgressRing(
        width=18,
        height=18,
        stroke_width=2,
        color=ft.Colors.WHITE,
        visible=False,
    )

    analyze_button_text = ft.Text(
        "Analizar imagen",
        color=ft.Colors.WHITE,
        weight=ft.FontWeight.W_900,
    )

    selected_source_title = ft.Text(
        "Sin imagen seleccionada",
        size=12,
        color=_c_text(page),
        weight=ft.FontWeight.W_800,
    )

    selected_source_detail = ft.Text(
        (
            "Usa la cámara del celular o selecciona "
            "otra fuente disponible."
        ),
        size=10,
        color=_c_muted(page),
    )

    preview_image = ft.Image(
        src="",
        fit=ft.BoxFit.COVER,
        expand=True,
        visible=False,
        gapless_playback=True,
    )

    preview_placeholder = ft.Container(
        expand=True,
        alignment=ft.Alignment(0, 0),
        bgcolor=_c_soft(page),
        content=ft.Column(
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=(
                ft.CrossAxisAlignment.CENTER
            ),
            spacing=10,
            controls=[
                ft.Container(
                    width=76,
                    height=76,
                    border_radius=38,
                    bgcolor=ft.Colors.with_opacity(
                        0.10,
                        BRAND_PRIMARY,
                    ),
                    alignment=ft.Alignment(0, 0),
                    content=ft.Icon(
                        ft.Icons.IMAGE_SEARCH_OUTLINED,
                        size=34,
                        color=BRAND_PRIMARY,
                    ),
                ),
                ft.Text(
                    "Vista previa",
                    size=12,
                    color=_c_text(page),
                    weight=ft.FontWeight.W_800,
                ),
                ft.Text(
                    (
                        "La fotografía seleccionada "
                        "aparecerá aquí."
                    ),
                    size=10,
                    color=_c_muted(page),
                    text_align=ft.TextAlign.CENTER,
                ),
            ],
        ),
    )

    preview_stack = ft.Stack(
        expand=True,
        controls=[
            preview_placeholder,
            preview_image,
        ],
    )

    preview_card = _card(
        page,
        ft.Container(
            height=280 if is_mobile else 390,
            border_radius=18,
            clip_behavior=(
                ft.ClipBehavior.ANTI_ALIAS
            ),
            content=preview_stack,
        ),
        padding=10,
        radius=22,
        shadow=True,
    )

    # -----------------------------------------------------
    # MENSAJES
    # -----------------------------------------------------

    def show_message(
        message: str,
        *,
        error: bool = False,
    ) -> None:
        page.show_dialog(
            ft.SnackBar(
                content=ft.Text(
                    message,
                    color=ft.Colors.WHITE,
                ),
                bgcolor=(
                    DANGER
                    if error
                    else BRAND_PRIMARY_DARK
                ),
                show_close_icon=True,
                duration=ft.Duration(
                    seconds=4
                ),
            )
        )

    def set_busy(
        value: bool,
    ) -> None:
        state["busy"] = value
        progress_ring.visible = value

        analyze_button_text.value = (
            "Analizando..."
            if value
            else "Analizar imagen"
        )

        analyze_button.disabled = value
        clear_button.disabled = value

        page.update()

    # -----------------------------------------------------
    # PREVISUALIZACIÓN
    # -----------------------------------------------------

    def set_preview_from_local(
        image_path: str,
    ) -> None:
        data_uri = _image_to_data_uri(
            image_path
        )

        if not data_uri:
            preview_image.src = ""
            preview_image.visible = False
            preview_placeholder.visible = True
            return

        preview_image.src = data_uri
        preview_image.visible = True
        preview_placeholder.visible = False

    def set_preview_from_url(
        image_url: str,
    ) -> None:
        preview_image.src = image_url
        preview_image.visible = True
        preview_placeholder.visible = False

    def clear_selection(
        _=None,
    ) -> None:
        state["local_path"] = ""
        state["image_url"] = ""

        url_field.value = ""

        selected_source_title.value = (
            "Sin imagen seleccionada"
        )
        selected_source_detail.value = (
            "Usa la cámara del celular o selecciona "
            "otra fuente disponible."
        )

        preview_image.src = ""
        preview_image.visible = False
        preview_placeholder.visible = True

        page.update()

    # -----------------------------------------------------
    # FUENTES
    # -----------------------------------------------------

    def on_url_change(
        event,
    ) -> None:
        value = (
            event.control.value or ""
        ).strip()

        state["image_url"] = value

        if value:
            state["local_path"] = ""

            selected_source_title.value = (
                "Imagen desde URL"
            )
            selected_source_detail.value = (
                value
                if len(value) <= 76
                else value[:73] + "..."
            )

            set_preview_from_url(
                value
            )

        else:
            selected_source_title.value = (
                "Sin imagen seleccionada"
            )
            selected_source_detail.value = (
                "Ingresa una URL válida o utiliza "
                "otra fuente."
            )

            preview_image.src = ""
            preview_image.visible = False
            preview_placeholder.visible = True

        page.update()

    async def select_desktop_image() -> None:
        if is_web:
            show_message(
                (
                    "La selección local mediante escritorio "
                    "no está disponible en esta ejecución web."
                ),
                error=True,
            )
            return

        selected_path = await asyncio.to_thread(
            _pick_image_with_tkinter
        )

        if not selected_path:
            show_message(
                "No se seleccionó ninguna imagen."
            )
            return

        state["local_path"] = selected_path
        state["image_url"] = ""

        url_field.value = ""

        selected_source_title.value = (
            "Archivo local seleccionado"
        )
        selected_source_detail.value = (
            os.path.basename(
                selected_path
            )
        )

        set_preview_from_local(
            selected_path
        )

        page.update()

    def on_select_desktop_image(
        _=None,
    ) -> None:
        page.run_task(
            select_desktop_image
        )

    async def open_desktop_camera() -> None:
        if is_web:
            show_message(
                (
                    "La cámara asistida con OpenCV "
                    "solo está disponible en escritorio."
                ),
                error=True,
            )
            return

        show_message(
            "Abriendo cámara asistida..."
        )

        captured_path = await asyncio.to_thread(
            capture_image_with_assistance
        )

        if not captured_path:
            show_message(
                (
                    "La captura fue cancelada o no se "
                    "pudo abrir la cámara."
                ),
                error=True,
            )
            return

        state["local_path"] = captured_path
        state["image_url"] = ""

        url_field.value = ""

        selected_source_title.value = (
            "Fotografía capturada"
        )
        selected_source_detail.value = (
            os.path.basename(
                captured_path
            )
        )

        set_preview_from_local(
            captured_path
        )

        page.update()

    def on_open_desktop_camera(
        _=None,
    ) -> None:
        page.run_task(
            open_desktop_camera
        )

    def open_mobile_camera(
        _=None,
    ) -> None:
        _nav(
            page,
            "/scan/camera",
        )

    # -----------------------------------------------------
    # ANÁLISIS
    # -----------------------------------------------------

    async def analyze_selected_image() -> None:
        local_path = (
            state["local_path"] or None
        )

        image_url = (
            state["image_url"]
            or (
                url_field.value or ""
            ).strip()
            or None
        )

        if not local_path and not image_url:
            show_message(
                (
                    "Selecciona una imagen o ingresa "
                    "una URL antes de analizar."
                ),
                error=True,
            )
            return

        set_busy(
            True
        )

        try:
            result = await asyncio.to_thread(
                process_scan_input,
                local_path=local_path,
                image_url=image_url,
            )

            page.data["scan_result"] = result
            page.data["scan_image_path"] = (
                result.get(
                    "saved_image_path"
                )
            )
            page.data["last_scan_id"] = (
                result.get(
                    "scan_id"
                )
            )

            await page.push_route(
                "/result"
            )

        except Exception as exception:
            error_text = str(
                exception
            ).lower()

            if (
                "403" in error_text
                or "bloqueó la descarga" in error_text
            ):
                message = (
                    "El sitio web no permite descargar esa imagen. "
                    "Usa otra URL directa, guarda la imagen en tu "
                    "dispositivo o tómala con la cámara."
                )

            elif (
                "404" in error_text
                or "no fue encontrada" in error_text
            ):
                message = (
                    "La imagen no fue encontrada en la URL ingresada."
                )

            elif (
                "no devuelve directamente" in error_text
                or "no es una imagen válida" in error_text
            ):
                message = (
                    "La dirección ingresada no apunta directamente "
                    "a una imagen válida."
                )

            elif (
                "tardó demasiado" in error_text
                or "no se pudo conectar" in error_text
            ):
                message = (
                    "No se pudo descargar la imagen. Verifica tu "
                    "conexión o utiliza otra URL."
                )

            else:
                message = (
                    "No se pudo analizar la imagen. Verifica la "
                    "dirección e inténtalo nuevamente."
                )

            show_message(
                message,
                error=True,
            )

        finally:
            state["busy"] = False

            try:
                set_busy(
                    False
                )
            except Exception:
                pass

    def on_analyze_click(
        _=None,
    ) -> None:
        page.run_task(
            analyze_selected_image
        )

    # -----------------------------------------------------
    # CAMPOS Y BOTONES
    # -----------------------------------------------------

    url_field = ft.TextField(
        label="URL pública de imagen",
        hint_text=(
            "https://ejemplo.com/palta.jpg"
        ),
        prefix_icon=ft.Icons.LINK,
        keyboard_type=ft.KeyboardType.URL,
        autocorrect=False,
        height=54,
        text_size=12,
        border_radius=15,
        border_color=_c_border(page),
        focused_border_color=BRAND_PRIMARY,
        bgcolor=_c_surface(page),
        on_change=on_url_change,
    )

    mobile_camera_button = ft.FilledButton(
        content=ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10,
            controls=[
                ft.Icon(
                    ft.Icons.PHOTO_CAMERA_OUTLINED,
                    size=21,
                    color=ft.Colors.WHITE,
                ),
                ft.Text(
                    "Abrir cámara",
                    color=ft.Colors.WHITE,
                    weight=ft.FontWeight.W_900,
                ),
            ],
        ),
        height=56,
        on_click=open_mobile_camera,
        style=ft.ButtonStyle(
            bgcolor=BRAND_PRIMARY,
            color=ft.Colors.WHITE,
            shape=ft.RoundedRectangleBorder(
                radius=17
            ),
        ),
    )

    upload_button = ft.OutlinedButton(
        content=ft.Text(
            "Seleccionar archivo",
            weight=ft.FontWeight.W_800,
        ),
        icon=ft.Icons.FOLDER_OUTLINED,
        height=50,
        on_click=on_select_desktop_image,
        style=ft.ButtonStyle(
            color=BRAND_PRIMARY,
            side=ft.BorderSide(
                1,
                BRAND_PRIMARY,
            ),
            shape=ft.RoundedRectangleBorder(
                radius=15
            ),
        ),
    )

    desktop_camera_button = ft.OutlinedButton(
        content=ft.Text(
            "Cámara asistida",
            weight=ft.FontWeight.W_800,
        ),
        icon=ft.Icons.PHOTO_CAMERA_OUTLINED,
        height=50,
        on_click=on_open_desktop_camera,
        style=ft.ButtonStyle(
            color=BRAND_PRIMARY,
            side=ft.BorderSide(
                1,
                _c_border(page),
            ),
            shape=ft.RoundedRectangleBorder(
                radius=15
            ),
        ),
    )

    analyze_button = ft.FilledButton(
        content=ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=9,
            controls=[
                progress_ring,
                analyze_button_text,
            ],
        ),
        height=54,
        on_click=on_analyze_click,
        style=ft.ButtonStyle(
            bgcolor=BRAND_PRIMARY_DARK,
            color=ft.Colors.WHITE,
            shape=ft.RoundedRectangleBorder(
                radius=16,
            ),
        ),
    )

    clear_button = ft.OutlinedButton(
        content=ft.Text(
            "Limpiar",
            weight=ft.FontWeight.W_800,
        ),
        icon=ft.Icons.REFRESH,
        height=50,
        on_click=clear_selection,
        style=ft.ButtonStyle(
            color=_c_text(page),
            side=ft.BorderSide(
                1,
                _c_border(page),
            ),
            shape=ft.RoundedRectangleBorder(
                radius=15
            ),
        ),
    )

    # -----------------------------------------------------
    # ÚLTIMO RESULTADO
    # -----------------------------------------------------

    latest_scan = get_latest_scan()

    def open_latest_result(
        _=None,
    ) -> None:
        if not latest_scan:
            return

        page.data["scan_result"] = latest_scan
        page.data["scan_image_path"] = (
            latest_scan.get(
                "saved_image_path"
            )
        )
        page.data["last_scan_id"] = (
            latest_scan.get(
                "scan_id"
            )
        )

        _nav(
            page,
            "/result",
        )

    if latest_scan:
        latest_color = _result_color(
            latest_scan
        )

        latest_card = _soft_card(
            page,
            ft.Row(
                spacing=12,
                controls=[
                    ft.Container(
                        width=44,
                        height=44,
                        border_radius=14,
                        bgcolor=ft.Colors.with_opacity(
                            0.12,
                            latest_color,
                        ),
                        alignment=ft.Alignment(0, 0),
                        content=ft.Icon(
                            ft.Icons.CHECK_CIRCLE_OUTLINE,
                            color=latest_color,
                            size=22,
                        ),
                    ),
                    ft.Column(
                        expand=True,
                        spacing=3,
                        controls=[
                            ft.Text(
                                "Último análisis",
                                size=10,
                                color=_c_muted(page),
                                weight=ft.FontWeight.W_700,
                            ),
                            ft.Text(
                                latest_scan.get(
                                    "label_text",
                                    "Resultado",
                                ),
                                size=14,
                                color=latest_color,
                                weight=ft.FontWeight.W_900,
                            ),
                            ft.Text(
                                (
                                    "Confianza: "
                                    f"{float(latest_scan.get('confidence', 0.0)) * 100:.2f}%"
                                ),
                                size=10,
                                color=_c_muted(page),
                            ),
                        ],
                    ),
                    ft.IconButton(
                        icon=ft.Icons.CHEVRON_RIGHT,
                        tooltip="Ver resultado",
                        on_click=open_latest_result,
                    ),
                ],
            ),
            padding=13,
            radius=17,
        )

    else:
        latest_card = _soft_card(
            page,
            ft.Row(
                spacing=12,
                controls=[
                    ft.Icon(
                        ft.Icons.HISTORY_TOGGLE_OFF,
                        color=_c_muted(page),
                    ),
                    ft.Text(
                        (
                            "Aún no hay análisis "
                            "registrados."
                        ),
                        size=11,
                        color=_c_muted(page),
                    ),
                ],
            ),
            padding=13,
            radius=17,
        )

    # -----------------------------------------------------
    # DISEÑO RESPONSIVO
    # -----------------------------------------------------

    # Encabezado principal. Se utiliza un verde sólido y una
    # composición limpia para mantener una apariencia profesional.
    hero_text = ft.Column(
        expand=True,
        spacing=8,
        controls=[
            ft.Container(
                padding=ft.Padding(10, 5, 10, 5),
                border_radius=999,
                bgcolor=ft.Colors.with_opacity(
                    0.14,
                    ft.Colors.WHITE,
                ),
                content=ft.Row(
                    tight=True,
                    spacing=6,
                    controls=[
                        ft.Icon(
                            ft.Icons.CENTER_FOCUS_STRONG,
                            size=14,
                            color=ft.Colors.WHITE,
                        ),
                        ft.Text(
                            "ANÁLISIS DE MADUREZ",
                            size=9,
                            color=ft.Colors.WHITE,
                            weight=ft.FontWeight.W_800,
                        ),
                    ],
                ),
            ),
            ft.Text(
                "Evalúa una palta Hass",
                size=24 if is_mobile else 30,
                color=ft.Colors.WHITE,
                weight=ft.FontWeight.W_900,
            ),
            ft.Text(
                (
                    "Captura o selecciona una fotografía clara del fruto "
                    "para estimar su nivel de madurez antes de la cosecha."
                ),
                size=11 if is_mobile else 12,
                color=ft.Colors.with_opacity(
                    0.82,
                    ft.Colors.WHITE,
                ),
            ),
        ],
    )

    hero_icon = ft.Container(
        width=68 if is_mobile else 82,
        height=68 if is_mobile else 82,
        border_radius=22,
        bgcolor=ft.Colors.with_opacity(
            0.12,
            ft.Colors.WHITE,
        ),
        alignment=ft.Alignment(0, 0),
        content=ft.Icon(
            ft.Icons.PHOTO_CAMERA_OUTLINED,
            size=30 if is_mobile else 36,
            color=ft.Colors.WHITE,
        ),
    )

    hero = ft.Container(
        padding=ft.Padding(
            18 if is_mobile else 24,
            18 if is_mobile else 22,
            18 if is_mobile else 24,
            18 if is_mobile else 22,
        ),
        border_radius=22,
        bgcolor=BRAND_PRIMARY_DARK,
        content=(
            ft.Column(
                spacing=16,
                controls=[
                    hero_text,
                    hero_icon,
                ],
            )
            if is_mobile
            else ft.Row(
                spacing=22,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    hero_text,
                    hero_icon,
                ],
            )
        ),
    )

    # Tarjeta de acceso principal a la cámara.
    camera_access_card = _card(
        page,
        ft.Column(
            spacing=14,
            controls=[
                ft.Row(
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Container(
                            width=46,
                            height=46,
                            border_radius=14,
                            bgcolor=BRAND_SOFT,
                            alignment=ft.Alignment(0, 0),
                            content=ft.Icon(
                                ft.Icons.SMARTPHONE_OUTLINED,
                                size=23,
                                color=BRAND_PRIMARY,
                            ),
                        ),
                        ft.Column(
                            expand=True,
                            spacing=3,
                            controls=[
                                ft.Text(
                                    "Cámara del dispositivo",
                                    size=14,
                                    color=_c_text(page),
                                    weight=ft.FontWeight.W_900,
                                ),
                                ft.Text(
                                    "Opción recomendada para realizar el análisis directamente en campo.",
                                    size=10,
                                    color=_c_muted(page),
                                ),
                            ],
                        ),
                    ],
                ),
                mobile_camera_button,
                ft.Row(
                    spacing=7,
                    controls=[
                        ft.Icon(
                            ft.Icons.INFO_OUTLINE,
                            size=15,
                            color=_c_muted(page),
                        ),
                        ft.Text(
                            "Usa buena iluminación y enfoca una sola palta.",
                            size=9,
                            color=_c_muted(page),
                        ),
                    ],
                ),
            ],
        ),
        padding=16,
        radius=20,
        shadow=True,
    )

    # Resumen de la fuente elegida.
    source_summary = ft.Container(
        padding=ft.Padding(13, 12, 13, 12),
        border_radius=16,
        bgcolor=_c_soft(page),
        border=ft.Border.all(
            1,
            _c_border(page),
        ),
        content=ft.Row(
            spacing=11,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Container(
                    width=38,
                    height=38,
                    border_radius=12,
                    bgcolor=ft.Colors.with_opacity(
                        0.10,
                        BRAND_PRIMARY,
                    ),
                    alignment=ft.Alignment(0, 0),
                    content=ft.Icon(
                        ft.Icons.IMAGE_OUTLINED,
                        color=BRAND_PRIMARY,
                        size=19,
                    ),
                ),
                ft.Column(
                    expand=True,
                    spacing=2,
                    controls=[
                        selected_source_title,
                        selected_source_detail,
                    ],
                ),
            ],
        ),
    )

    # Métodos alternativos. Los mismos controles y eventos del archivo
    # original se conservan; únicamente cambia su distribución visual.
    if is_mobile:
        alternative_controls = [
            url_field,
        ]
    else:
        alternative_controls = [
            url_field,
            ft.Row(
                spacing=10,
                controls=[
                    ft.Container(
                        expand=True,
                        content=upload_button,
                    ),
                    ft.Container(
                        expand=True,
                        content=desktop_camera_button,
                    ),
                ],
            ),
        ]

    other_sources = _card(
        page,
        ft.Column(
            spacing=13,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Column(
                            spacing=2,
                            controls=[
                                ft.Text(
                                    "Otras fuentes",
                                    size=13,
                                    color=_c_text(page),
                                    weight=ft.FontWeight.W_900,
                                ),
                                ft.Text(
                                    "Selecciona una alternativa disponible.",
                                    size=9,
                                    color=_c_muted(page),
                                ),
                            ],
                        ),
                        ft.Container(
                            width=34,
                            height=34,
                            border_radius=11,
                            bgcolor=BRAND_SOFT,
                            alignment=ft.Alignment(0, 0),
                            content=ft.Icon(
                                ft.Icons.IMAGE_SEARCH_OUTLINED,
                                size=18,
                                color=BRAND_PRIMARY,
                            ),
                        ),
                    ],
                ),
                *alternative_controls,
            ],
        ),
        padding=16,
        radius=20,
    )

    actions = (
        ft.Column(
            spacing=10,
            controls=[
                analyze_button,
                clear_button,
            ],
        )
        if is_mobile
        else ft.Row(
            spacing=10,
            controls=[
                ft.Container(
                    expand=True,
                    content=analyze_button,
                ),
                ft.Container(
                    width=142,
                    content=clear_button,
                ),
            ],
        )
    )

    history_button = ft.TextButton(
        content=ft.Text(
            "Ver historial completo",
            color=BRAND_PRIMARY,
            weight=ft.FontWeight.W_800,
        ),
        icon=ft.Icons.HISTORY,
        on_click=lambda _: _nav(
            page,
            "/history",
        ),
    )

    latest_section = ft.Column(
        spacing=8,
        controls=[
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Text(
                        "Actividad reciente",
                        size=12,
                        color=_c_text(page),
                        weight=ft.FontWeight.W_900,
                    ),
                    history_button,
                ],
            ),
            latest_card,
        ],
    )

    preview_section = ft.Column(
        spacing=10,
        controls=[
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Column(
                        spacing=2,
                        controls=[
                            ft.Text(
                                "Fotografía para analizar",
                                size=14,
                                color=_c_text(page),
                                weight=ft.FontWeight.W_900,
                            ),
                            ft.Text(
                                "Revisa la imagen antes de iniciar el procesamiento.",
                                size=9,
                                color=_c_muted(page),
                            ),
                        ],
                    ),
                    ft.Container(
                        padding=ft.Padding(9, 5, 9, 5),
                        border_radius=999,
                        bgcolor=BRAND_SOFT,
                        content=ft.Text(
                            "PALTA HASS",
                            size=8,
                            color=BRAND_PRIMARY,
                            weight=ft.FontWeight.W_900,
                        ),
                    ),
                ],
            ),
            preview_card,
            source_summary,
        ],
    )

    if is_mobile:
        body = ft.Column(
            spacing=14,
            controls=[
                hero,
                camera_access_card,
                preview_section,
                other_sources,
                actions,
                latest_section,
                ft.Container(height=8),
            ],
        )

    else:
        left_width = 340 if mode == "tablet" else 370

        left_column = ft.Column(
            spacing=14,
            controls=[
                hero,
                camera_access_card,
                latest_section,
            ],
        )

        right_column = ft.Column(
            spacing=14,
            controls=[
                _card(
                    page,
                    preview_section,
                    padding=16,
                    radius=22,
                    shadow=True,
                ),
                other_sources,
                actions,
            ],
        )

        body = ft.Row(
            spacing=18,
            vertical_alignment=ft.CrossAxisAlignment.START,
            controls=[
                ft.Container(
                    width=left_width,
                    content=left_column,
                ),
                ft.Container(
                    expand=True,
                    content=right_column,
                ),
            ],
        )

    content_max_width = 1040 if mode == "tablet" else 1160

    scan_content = ft.Container(
        expand=True,
        bgcolor=_c_bg(page),
        padding=ft.Padding(
            14 if is_mobile else 22,
            14 if is_mobile else 20,
            14 if is_mobile else 22,
            24,
        ),
        content=ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=0,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Container(
                    width=None if is_mobile else content_max_width,
                    content=body,
                ),
            ],
        ),
    )

    try:
        root = build_app_shell(
            page,
            scan_content,
            title="Escaneo",
            subtitle="Análisis de palta Hass",
        )

    except TypeError:
        # Compatibilidad temporal con una versión anterior
        # de app_shell.py.
        root = build_app_shell(
            page,
            scan_content,
        )

    return ft.View(
        route="/scan",
        controls=[
            ft.SafeArea(
                expand=True,
                content=root,
            ),
        ],
    )
