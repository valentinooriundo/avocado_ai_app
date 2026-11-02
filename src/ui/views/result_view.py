from __future__ import annotations

from pathlib import Path

import flet as ft

from services.scan_flow_service import get_latest_scan
from services.settings_service import load_theme
from ui.components.app_shell import build_app_shell
from ui.theme_tokens import BRAND_PRIMARY, BRAND_SOFT, text_color, muted_color, border_color, surface_color


BRAND_GREEN = BRAND_PRIMARY

LABEL_NAMES = {
    "aun_no_lista": "Aún no lista",
    "en_proceso": "En proceso",
    "lista_para_cosecha": "Lista para cosecha",
}


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


def _nav(
    page: ft.Page,
    route: str,
) -> None:
    page.run_task(
        page.push_route,
        route,
    )


def _result_color(
    result: dict,
):
    if not result.get(
        "is_reliable",
        False,
    ):
        return ft.Colors.AMBER_700

    color_name = str(
        result.get(
            "result_color",
            "",
        )
    ).lower()

    if color_name == "green":
        return ft.Colors.GREEN_600

    if color_name == "red":
        return ft.Colors.RED_600

    if color_name == "amber":
        return ft.Colors.AMBER_700

    return BRAND_GREEN


def _read_result_image(
    page: ft.Page,
    result: dict,
) -> bytes | None:
    if isinstance(page.data, dict):
        current_bytes = page.data.get(
            "scan_image_bytes"
        )

        if isinstance(
            current_bytes,
            bytes,
        ):
            return current_bytes

    saved_path = result.get(
        "saved_image_path"
    )

    if not saved_path:
        return None

    image_path = Path(
        saved_path
    )

    if not image_path.exists():
        return None

    try:
        return image_path.read_bytes()
    except OSError:
        return None


def create_result_view(
    page: ft.Page,
) -> ft.View:
    db = page.data.get("db") if isinstance(page.data, dict) else None

    if db is not None:
        saved = load_theme(db)
        page.theme_mode = (
            ft.ThemeMode.DARK
            if saved == "dark"
            else ft.ThemeMode.LIGHT
        )

    result = {}

    if isinstance(page.data, dict):
        result = page.data.get(
            "scan_result",
            {},
        ) or {}

    if not result:
        result = get_latest_scan() or {}

    if isinstance(page.data, dict) and result:
        page.data["scan_result"] = result

    has_result = bool(result)

    label_text = result.get(
        "label_text",
        "Resultado no disponible",
    )

    confidence = float(
        result.get(
            "confidence",
            0.0,
        )
    )

    margin = float(
        result.get(
            "margin",
            0.0,
        )
    )

    is_reliable = bool(
        result.get(
            "is_reliable",
            False,
        )
    )

    scores = result.get(
        "scores",
        {},
    ) or {}

    recommendation = result.get(
        "recommended_action",
        (
            "Realiza un nuevo análisis para "
            "obtener una recomendación."
        ),
    )

    result_color = _result_color(
        result
    )

    image_bytes = _read_result_image(
        page,
        result,
    )

    if image_bytes:
        image_control = ft.Image(
            src=image_bytes,
            fit=ft.BoxFit.COVER,
            expand=True,
            gapless_playback=True,
            semantics_label=(
                "Fotografía de la palta analizada"
            ),
        )
    else:
        image_control = ft.Container(
            expand=True,
            alignment=ft.Alignment(0, 0),
            bgcolor=ft.Colors.with_opacity(
                0.08,
                BRAND_GREEN,
            ),
            content=ft.Icon(
                ft.Icons.IMAGE_NOT_SUPPORTED_OUTLINED,
                size=54,
                color=BRAND_GREEN,
            ),
        )

    result_title = (
        label_text
        if is_reliable
        else "Resultado no concluyente"
    )

    result_subtitle = (
        "El modelo identificó el nivel de madurez "
        "con suficiente confianza."
        if is_reliable
        else (
            "La fotografía debe repetirse para evitar "
            "una decisión poco confiable."
        )
    )

    status_text = (
        "ANÁLISIS CONFIABLE"
        if is_reliable
        else "REQUIERE OTRA FOTO"
    )

    def probability_card(
        label_key: str,
    ) -> ft.Control:
        probability = float(
            scores.get(
                label_key,
                0.0,
            )
        )

        visible_name = LABEL_NAMES.get(
            label_key,
            label_key,
        )

        return ft.Container(
            padding=ft.Padding(
                14,
                12,
                14,
                12,
            ),
            border_radius=16,
            bgcolor=_c_surface(page),
            border=ft.Border.all(
                1,
                _c_border(page),
            ),
            content=ft.Column(
                spacing=8,
                controls=[
                    ft.Row(
                        alignment=(
                            ft.MainAxisAlignment
                            .SPACE_BETWEEN
                        ),
                        controls=[
                            ft.Text(
                                visible_name,
                                size=11,
                                color=_c_text(page),
                                weight=ft.FontWeight.W_800,
                            ),
                            ft.Text(
                                f"{probability * 100:.2f}%",
                                size=11,
                                color=BRAND_GREEN,
                                weight=ft.FontWeight.W_900,
                            ),
                        ],
                    ),
                    ft.ProgressBar(
                        value=max(
                            0.0,
                            min(
                                1.0,
                                probability,
                            ),
                        ),
                        height=8,
                        border_radius=99,
                        color=BRAND_GREEN,
                        bgcolor=ft.Colors.with_opacity(
                            0.12,
                            ft.Colors.GREEN_400,
                        ),
                    ),
                ],
            ),
        )

    header = ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        controls=[
            ft.IconButton(
                icon=ft.Icons.ARROW_BACK,
                tooltip="Volver",
                on_click=lambda _: _nav(
                    page,
                    "/scan",
                ),
            ),
            ft.Text(
                "Resultado del análisis",
                size=13,
                color=_c_muted(page),
                weight=ft.FontWeight.W_800,
            ),
            ft.IconButton(
                icon=ft.Icons.HISTORY,
                tooltip="Ver historial",
                on_click=lambda _: _nav(
                    page,
                    "/history",
                ),
            ),
        ],
    )

    image_panel = ft.Container(
        height=280,
        border_radius=24,
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        border=ft.Border.all(
            1,
            _c_border(page),
        ),
        content=ft.Stack(
            expand=True,
            controls=[
                image_control,
                ft.Container(
                    alignment=ft.Alignment(
                        0,
                        0.80,
                    ),
                    content=ft.Container(
                        padding=ft.Padding(
                            14,
                            8,
                            14,
                            8,
                        ),
                        border_radius=999,
                        bgcolor=ft.Colors.with_opacity(
                            0.90,
                            result_color,
                        ),
                        content=ft.Text(
                            status_text,
                            size=10,
                            color=ft.Colors.WHITE,
                            weight=ft.FontWeight.W_900,
                        ),
                    ),
                ),
            ],
        ),
    )

    summary_card = ft.Container(
        padding=ft.Padding(
            18,
            18,
            18,
            18,
        ),
        border_radius=22,
        bgcolor=_c_surface(page),
        border=ft.Border.all(
            1,
            _c_border(page),
        ),
        content=ft.Column(
            horizontal_alignment=(
                ft.CrossAxisAlignment.CENTER
            ),
            spacing=8,
            controls=[
                ft.Text(
                    result_title,
                    size=25,
                    color=result_color,
                    weight=ft.FontWeight.W_900,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text(
                    result_subtitle,
                    size=11,
                    color=_c_muted(page),
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Container(
                    height=8,
                ),
                ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=22,
                    controls=[
                        ft.Column(
                            horizontal_alignment=(
                                ft.CrossAxisAlignment.CENTER
                            ),
                            spacing=2,
                            controls=[
                                ft.Text(
                                    f"{confidence * 100:.2f}%",
                                    size=22,
                                    color=_c_text(page),
                                    weight=ft.FontWeight.W_900,
                                ),
                                ft.Text(
                                    "Confianza",
                                    size=10,
                                    color=_c_muted(page),
                                ),
                            ],
                        ),
                        ft.Container(
                            width=1,
                            height=42,
                            bgcolor=_c_border(page),
                        ),
                        ft.Column(
                            horizontal_alignment=(
                                ft.CrossAxisAlignment.CENTER
                            ),
                            spacing=2,
                            controls=[
                                ft.Text(
                                    f"{margin * 100:.2f}%",
                                    size=22,
                                    color=_c_text(page),
                                    weight=ft.FontWeight.W_900,
                                ),
                                ft.Text(
                                    "Margen",
                                    size=10,
                                    color=_c_muted(page),
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        ),
    )

    recommendation_card = ft.Container(
        padding=ft.Padding(
            16,
            14,
            16,
            14,
        ),
        border_radius=18,
        bgcolor=ft.Colors.with_opacity(
            0.10,
            result_color,
        ),
        border=ft.Border.all(
            1,
            ft.Colors.with_opacity(
                0.28,
                result_color,
            ),
        ),
        content=ft.Row(
            spacing=12,
            vertical_alignment=(
                ft.CrossAxisAlignment.START
            ),
            controls=[
                ft.Icon(
                    (
                        ft.Icons.LIGHTBULB_OUTLINE
                        if is_reliable
                        else ft.Icons.CAMERA_ALT_OUTLINED
                    ),
                    color=result_color,
                    size=23,
                ),
                ft.Column(
                    expand=True,
                    spacing=4,
                    controls=[
                        ft.Text(
                            (
                                "RECOMENDACIÓN"
                                if is_reliable
                                else "REPETIR CAPTURA"
                            ),
                            size=10,
                            color=result_color,
                            weight=ft.FontWeight.W_900,
                        ),
                        ft.Text(
                            recommendation,
                            size=12,
                            color=_c_text(page),
                        ),
                    ],
                ),
            ],
        ),
    )

    saved_notice = ft.Container(
        padding=ft.Padding(
            12,
            10,
            12,
            10,
        ),
        border_radius=14,
        bgcolor=ft.Colors.with_opacity(
            0.08,
            ft.Colors.BLUE_400,
        ),
        content=ft.Row(
            spacing=9,
            controls=[
                ft.Icon(
                    ft.Icons.CLOUD_DONE_OUTLINED,
                    size=18,
                    color=ft.Colors.BLUE_500,
                ),
                ft.Text(
                    (
                        "El resultado ya fue guardado "
                        "automáticamente en el historial."
                        if has_result
                        else "No hay un análisis disponible."
                    ),
                    size=10,
                    color=_c_muted(page),
                    expand=True,
                ),
            ],
        ),
    )

    content = ft.Container(
        expand=True,
        padding=ft.Padding(
            14,
            10,
            14,
            24,
        ),
        content=ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            horizontal_alignment=(
                ft.CrossAxisAlignment.CENTER
            ),
            controls=[
                ft.Container(
                    width=620,
                    content=ft.Column(
                        spacing=14,
                        controls=[
                            header,
                            image_panel,
                            summary_card,
                            ft.Text(
                                "PROBABILIDAD POR NIVEL",
                                size=10,
                                color=_c_muted(page),
                                weight=ft.FontWeight.W_900,
                            ),
                            probability_card(
                                "aun_no_lista"
                            ),
                            probability_card(
                                "en_proceso"
                            ),
                            probability_card(
                                "lista_para_cosecha"
                            ),
                            recommendation_card,
                            saved_notice,
                            ft.FilledButton(
                                content=ft.Text(
                                    (
                                        "TOMAR OTRA FOTOGRAFÍA"
                                        if not is_reliable
                                        else "NUEVO ANÁLISIS"
                                    ),
                                    weight=ft.FontWeight.W_900,
                                ),
                                icon=ft.Icons.PHOTO_CAMERA,
                                height=52,
                                on_click=lambda _: _nav(
                                    page,
                                    "/scan/camera",
                                ),
                                style=ft.ButtonStyle(
                                    bgcolor=BRAND_GREEN,
                                    color=ft.Colors.WHITE,
                                    shape=ft.RoundedRectangleBorder(
                                        radius=16
                                    ),
                                ),
                            ),
                            ft.OutlinedButton(
                                content=ft.Text(
                                    "VER HISTORIAL",
                                    weight=ft.FontWeight.W_900,
                                ),
                                icon=ft.Icons.HISTORY,
                                height=52,
                                on_click=lambda _: _nav(
                                    page,
                                    "/history",
                                ),
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(
                                        radius=16
                                    ),
                                ),
                            ),
                        ],
                    ),
                ),
            ],
        ),
    )

    root = build_app_shell(
        page,
        content,
    )

    return ft.View(
        route="/result",
        controls=[
            ft.SafeArea(
                expand=True,
                content=root,
            ),
        ],
    )
