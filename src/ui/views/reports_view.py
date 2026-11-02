from __future__ import annotations

import asyncio
from collections import Counter
from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path

import flet as ft

from services.scan_flow_service import get_scan_history
from services.settings_service import load_theme
from ui.components.app_shell import build_app_shell
from ui.theme_tokens import BRAND_PRIMARY


BRAND_GREEN = BRAND_PRIMARY
BRAND_DARK = "#2F5D46"
ACCENT_AMBER = "#F59E0B"
ACCENT_RED = "#DC2626"
ACCENT_BLUE = "#2563EB"

CATEGORY_META = {
    "lista_para_cosecha": {
        "label": "Lista para cosecha",
        "color": "#2F9E44",
    },
    "en_proceso": {
        "label": "En proceso",
        "color": ACCENT_AMBER,
    },
    "aun_no_lista": {
        "label": "Aún no lista",
        "color": ACCENT_RED,
    },
    "inconclusive": {
        "label": "No concluyente",
        "color": "#7C3AED",
    },
}


def _is_dark(page: ft.Page) -> bool:
    return page.theme_mode == ft.ThemeMode.DARK


def _screen_mode(page: ft.Page) -> str:
    width = page.width or 1200

    if width < 760:
        return "mobile"
    if width < 1080:
        return "tablet"
    return "desktop"


def _c_surface(page: ft.Page) -> str:
    return "#11161C" if _is_dark(page) else "#FFFFFF"


def _c_soft(page: ft.Page) -> str:
    return "#171E27" if _is_dark(page) else "#F4F8EF"


def _c_text(page: ft.Page) -> str:
    return "#F5F7FA" if _is_dark(page) else "#172018"


def _c_muted(page: ft.Page) -> str:
    return "#97A3B6" if _is_dark(page) else "#667085"


def _c_border(page: ft.Page) -> str:
    return "#253041" if _is_dark(page) else "#DCE5D6"


def _c_positive_bg(page: ft.Page) -> str:
    return "#17361C" if _is_dark(page) else "#EAF8E5"


def _shadow(page: ft.Page) -> ft.BoxShadow:
    return ft.BoxShadow(
        blur_radius=22,
        spread_radius=1,
        color=ft.Colors.with_opacity(
            0.20 if _is_dark(page) else 0.07,
            ft.Colors.BLACK,
        ),
        offset=ft.Offset(0, 8),
    )


def _card(
    page: ft.Page,
    content: ft.Control,
    *,
    padding: int = 18,
    radius: int = 20,
    border_color: str | None = None,
    height: int | None = None,
) -> ft.Container:
    return ft.Container(
        height=height,
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
            border_color or _c_border(page),
        ),
        shadow=_shadow(page),
        content=content,
    )


def _nav(page: ft.Page, route: str) -> None:
    page.run_task(
        page.push_route,
        route,
    )


def _show_message(
    page: ft.Page,
    message: str,
    *,
    error: bool = False,
) -> None:
    page.show_dialog(
        ft.SnackBar(
            content=ft.Row(
                spacing=9,
                controls=[
                    ft.Icon(
                        (
                            ft.Icons.ERROR_OUTLINE
                            if error
                            else ft.Icons.CHECK_CIRCLE_OUTLINE
                        ),
                        color=ft.Colors.WHITE,
                    ),
                    ft.Text(
                        message,
                        color=ft.Colors.WHITE,
                        weight=ft.FontWeight.W_700,
                    ),
                ],
            ),
            bgcolor=(
                "#B42318"
                if error
                else BRAND_DARK
            ),
            show_close_icon=True,
            duration=ft.Duration(seconds=4),
        )
    )


def _parse_datetime(value: object) -> datetime | None:
    if isinstance(value, datetime):
        return value

    clean_value = str(value or "").strip()

    if not clean_value:
        return None

    try:
        return datetime.fromisoformat(
            clean_value.replace("Z", "+00:00")
        ).replace(tzinfo=None)
    except (TypeError, ValueError):
        return None


def _category_key(item: dict) -> str:
    if not bool(item.get("is_reliable", False)):
        return "inconclusive"

    key = str(
        item.get("label_key", "")
    ).strip()

    if key in CATEGORY_META:
        return key

    label = str(
        item.get("label_text", "")
    ).lower()

    if "lista para cosecha" in label:
        return "lista_para_cosecha"
    if "proceso" in label:
        return "en_proceso"
    if "no lista" in label:
        return "aun_no_lista"

    return "inconclusive"


def _category_label(item: dict) -> str:
    return CATEGORY_META[
        _category_key(item)
    ]["label"]


def _confidence(item: dict) -> float:
    try:
        value = float(
            item.get("confidence", 0.0)
        )
    except (TypeError, ValueError):
        value = 0.0

    return max(
        0.0,
        min(1.0, value),
    )


def _period_start(
    period: str,
    now: datetime,
) -> datetime | None:
    if period == "Diario":
        return now.replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

    if period == "Semanal":
        return (
            now - timedelta(days=6)
        ).replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

    if period == "Mensual":
        return (
            now - timedelta(days=29)
        ).replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

    return None


def _filter_period(
    history: list[dict],
    period: str,
    now: datetime,
) -> list[dict]:
    start = _period_start(
        period,
        now,
    )

    if start is None:
        return list(history)

    filtered: list[dict] = []

    for item in history:
        created_at = _parse_datetime(
            item.get("created_at")
        )

        if created_at and created_at >= start:
            filtered.append(item)

    return filtered


def _previous_period_items(
    history: list[dict],
    period: str,
    now: datetime,
) -> list[dict]:
    if period == "Todo":
        return []

    days = {
        "Diario": 1,
        "Semanal": 7,
        "Mensual": 30,
    }.get(period, 0)

    if days <= 0:
        return []

    current_start = _period_start(
        period,
        now,
    )

    if current_start is None:
        return []

    previous_start = current_start - timedelta(
        days=days
    )

    previous_items: list[dict] = []

    for item in history:
        created_at = _parse_datetime(
            item.get("created_at")
        )

        if (
            created_at
            and previous_start <= created_at < current_start
        ):
            previous_items.append(item)

    return previous_items


def _average_confidence(
    items: list[dict],
) -> float:
    if not items:
        return 0.0

    return sum(
        _confidence(item)
        for item in items
    ) / len(items)


def _counts(items: list[dict]) -> Counter:
    return Counter(
        _category_key(item)
        for item in items
    )


def _percentage(
    value: int | float,
    total: int | float,
) -> float:
    if not total:
        return 0.0

    return float(value) / float(total)


def _delta_text(
    current: float,
    previous: float,
    *,
    percentage_points: bool = False,
) -> tuple[str, str]:
    delta = current - previous

    if percentage_points:
        text = f"{delta * 100:+.1f} pp vs. periodo anterior"
    else:
        text = f"{int(delta):+d} vs. periodo anterior"

    color = (
        "#2F9E44"
        if delta >= 0
        else ACCENT_RED
    )

    return text, color


def _period_caption(period: str) -> str:
    return {
        "Diario": "Hoy",
        "Semanal": "Últimos 7 días",
        "Mensual": "Últimos 30 días",
        "Todo": "Todo el historial",
    }.get(period, period)


def _pill_button(
    page: ft.Page,
    label: str,
    active: bool,
    on_click=None,
) -> ft.Container:
    return ft.Container(
        height=36,
        padding=ft.Padding(
            14,
            0,
            14,
            0,
        ),
        border_radius=11,
        bgcolor=(
            _c_positive_bg(page)
            if active
            else _c_soft(page)
        ),
        border=ft.Border.all(
            1,
            (
                BRAND_GREEN
                if active
                else _c_border(page)
            ),
        ),
        ink=True,
        on_click=on_click,
        alignment=ft.Alignment(0, 0),
        content=ft.Text(
            label,
            size=10,
            color=(
                BRAND_DARK
                if active and not _is_dark(page)
                else (
                    BRAND_GREEN
                    if active
                    else _c_muted(page)
                )
            ),
            weight=ft.FontWeight.W_900,
        ),
    )


def _icon_action(
    page: ft.Page,
    icon,
    label: str,
    on_click=None,
    *,
    primary: bool = False,
) -> ft.Container:
    return ft.Container(
        height=36,
        padding=ft.Padding(
            13,
            0,
            13,
            0,
        ),
        border_radius=11,
        bgcolor=(
            BRAND_DARK
            if primary
            else _c_soft(page)
        ),
        border=ft.Border.all(
            1,
            (
                BRAND_DARK
                if primary
                else _c_border(page)
            ),
        ),
        ink=True,
        on_click=on_click,
        alignment=ft.Alignment(0, 0),
        content=ft.Row(
            tight=True,
            spacing=7,
            controls=[
                ft.Icon(
                    icon,
                    size=15,
                    color=(
                        ft.Colors.WHITE
                        if primary
                        else _c_muted(page)
                    ),
                ),
                ft.Text(
                    label,
                    size=10,
                    color=(
                        ft.Colors.WHITE
                        if primary
                        else _c_text(page)
                    ),
                    weight=ft.FontWeight.W_800,
                ),
            ],
        ),
    )


def _metric_card(
    page: ft.Page,
    *,
    icon,
    title: str,
    value: str,
    suffix: str,
    subtitle: str,
    subtitle_color: str,
    accent_color: str,
) -> ft.Container:
    return _card(
        page,
        ft.Column(
            spacing=10,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text(
                            title,
                            size=11,
                            color=_c_muted(page),
                            weight=ft.FontWeight.W_900,
                        ),
                        ft.Container(
                            width=34,
                            height=34,
                            border_radius=11,
                            bgcolor=ft.Colors.with_opacity(
                                0.12,
                                accent_color,
                            ),
                            alignment=ft.Alignment(0, 0),
                            content=ft.Icon(
                                icon,
                                size=18,
                                color=accent_color,
                            ),
                        ),
                    ],
                ),
                ft.Row(
                    spacing=6,
                    vertical_alignment=ft.CrossAxisAlignment.END,
                    controls=[
                        ft.Text(
                            value,
                            size=29,
                            color=accent_color,
                            weight=ft.FontWeight.W_900,
                        ),
                        ft.Text(
                            suffix,
                            size=13,
                            color=_c_text(page),
                            weight=ft.FontWeight.W_800,
                        ),
                    ],
                ),
                ft.Text(
                    subtitle,
                    size=10,
                    color=subtitle_color,
                    weight=ft.FontWeight.W_700,
                ),
            ],
        ),
        height=150,
    )


def _progress_line(
    page: ft.Page,
    value: float,
    *,
    color: str,
    width: int,
) -> ft.Stack:
    safe_value = max(
        0.0,
        min(1.0, value),
    )

    fill_width = int(
        width * safe_value
    )

    return ft.Stack(
        width=width,
        height=10,
        controls=[
            ft.Container(
                width=width,
                height=6,
                top=2,
                border_radius=999,
                bgcolor=ft.Colors.with_opacity(
                    0.10,
                    (
                        ft.Colors.WHITE
                        if _is_dark(page)
                        else ft.Colors.BLACK
                    ),
                ),
            ),
            ft.Container(
                width=max(
                    0,
                    fill_width,
                ),
                height=6,
                top=2,
                border_radius=999,
                bgcolor=color,
            ),
        ],
    )


def _distribution_row(
    page: ft.Page,
    *,
    label: str,
    count: int,
    total: int,
    color: str,
    width: int,
) -> ft.Column:
    ratio = _percentage(
        count,
        total,
    )

    return ft.Column(
        spacing=6,
        controls=[
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Row(
                        spacing=7,
                        controls=[
                            ft.Container(
                                width=9,
                                height=9,
                                border_radius=999,
                                bgcolor=color,
                            ),
                            ft.Text(
                                label,
                                size=10,
                                color=_c_text(page),
                                weight=ft.FontWeight.W_700,
                            ),
                        ],
                    ),
                    ft.Text(
                        f"{count} · {ratio * 100:.1f}%",
                        size=10,
                        color=color,
                        weight=ft.FontWeight.W_900,
                    ),
                ],
            ),
            _progress_line(
                page,
                ratio,
                color=color,
                width=width,
            ),
        ],
    )


def _quality_row(
    page: ft.Page,
    *,
    label: str,
    value: float,
    detail: str,
    color: str,
    width: int,
) -> ft.Column:
    return ft.Column(
        spacing=6,
        controls=[
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Column(
                        spacing=1,
                        controls=[
                            ft.Text(
                                label,
                                size=10,
                                color=_c_text(page),
                                weight=ft.FontWeight.W_800,
                            ),
                            ft.Text(
                                detail,
                                size=8,
                                color=_c_muted(page),
                            ),
                        ],
                    ),
                    ft.Text(
                        f"{value * 100:.1f}%",
                        size=10,
                        color=color,
                        weight=ft.FontWeight.W_900,
                    ),
                ],
            ),
            _progress_line(
                page,
                value,
                color=color,
                width=width,
            ),
        ],
    )


def _build_activity_buckets(
    items: list[dict],
    period: str,
    now: datetime,
) -> list[tuple[str, Counter]]:
    buckets: list[tuple[str, datetime, datetime]] = []

    if period == "Diario":
        start_day = now.replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

        for hour in range(0, 24, 4):
            start = start_day + timedelta(
                hours=hour
            )
            end = start + timedelta(
                hours=4
            )
            buckets.append(
                (
                    f"{hour:02d}:00–{hour + 3:02d}:59",
                    start,
                    end,
                )
            )

    elif period == "Semanal":
        start_day = (
            now - timedelta(days=6)
        ).replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

        day_names = [
            "Lun",
            "Mar",
            "Mié",
            "Jue",
            "Vie",
            "Sáb",
            "Dom",
        ]

        for offset in range(7):
            start = start_day + timedelta(
                days=offset
            )
            end = start + timedelta(days=1)
            buckets.append(
                (
                    f"{day_names[start.weekday()]} {start.day:02d}",
                    start,
                    end,
                )
            )

    elif period == "Mensual":
        start_day = (
            now - timedelta(days=29)
        ).replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

        for block in range(5):
            start = start_day + timedelta(
                days=block * 6
            )
            end = min(
                start + timedelta(days=6),
                now + timedelta(seconds=1),
            )
            buckets.append(
                (
                    f"{start.day:02d}/{start.month:02d}–"
                    f"{(end - timedelta(seconds=1)).day:02d}/"
                    f"{(end - timedelta(seconds=1)).month:02d}",
                    start,
                    end,
                )
            )

    else:
        dated_items = [
            (
                _parse_datetime(
                    item.get("created_at")
                ),
                item,
            )
            for item in items
        ]
        dated_items = [
            pair
            for pair in dated_items
            if pair[0] is not None
        ]

        if not dated_items:
            return []

        earliest = min(
            pair[0]
            for pair in dated_items
        ).replace(
            day=1,
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )
        latest = max(
            pair[0]
            for pair in dated_items
        )

        cursor = earliest
        all_months: list[tuple[str, datetime, datetime]] = []

        while cursor <= latest:
            if cursor.month == 12:
                next_month = cursor.replace(
                    year=cursor.year + 1,
                    month=1,
                )
            else:
                next_month = cursor.replace(
                    month=cursor.month + 1,
                )

            all_months.append(
                (
                    cursor.strftime("%m/%Y"),
                    cursor,
                    next_month,
                )
            )
            cursor = next_month

        buckets = all_months[-6:]

    result: list[tuple[str, Counter]] = []

    for label, start, end in buckets:
        counter: Counter = Counter()

        for item in items:
            created_at = _parse_datetime(
                item.get("created_at")
            )

            if (
                created_at
                and start <= created_at < end
            ):
                counter[
                    _category_key(item)
                ] += 1

        result.append(
            (label, counter)
        )

    return result


def _activity_row(
    page: ft.Page,
    *,
    label: str,
    counter: Counter,
    width: int,
) -> ft.Column:
    total = sum(
        counter.values()
    )

    segment_controls: list[ft.Control] = []

    if total > 0:
        for key in (
            "lista_para_cosecha",
            "en_proceso",
            "aun_no_lista",
            "inconclusive",
        ):
            count = int(
                counter.get(key, 0)
            )

            if count <= 0:
                continue

            segment_width = max(
                4,
                int(
                    width * count / total
                ),
            )

            segment_controls.append(
                ft.Container(
                    width=segment_width,
                    height=10,
                    border_radius=999,
                    bgcolor=CATEGORY_META[key]["color"],
                )
            )

    track = ft.Container(
        width=width,
        height=10,
        border_radius=999,
        bgcolor=ft.Colors.with_opacity(
            0.08,
            (
                ft.Colors.WHITE
                if _is_dark(page)
                else ft.Colors.BLACK
            ),
        ),
        content=ft.Row(
            spacing=2,
            controls=segment_controls,
        ),
    )

    return ft.Column(
        spacing=5,
        controls=[
            ft.Text(
                label,
                size=9,
                color=_c_muted(page),
                weight=ft.FontWeight.W_800,
            ),
            ft.Row(
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    track,
                    ft.Text(
                        str(total),
                        size=10,
                        color=_c_text(page),
                        weight=ft.FontWeight.W_900,
                    ),
                ],
            ),
        ],
    )


def _format_datetime(value: object) -> str:
    parsed = _parse_datetime(value)

    if not parsed:
        return "Fecha no disponible"

    return parsed.strftime(
        "%d/%m/%Y · %H:%M"
    )


def _short_text(
    value: object,
    limit: int = 75,
) -> str:
    text = " ".join(
        str(value or "").split()
    )

    if len(text) <= limit:
        return text

    return text[: limit - 1].rstrip() + "…"


def _find_logo_path() -> Path | None:
    base_dir = Path(__file__).resolve().parents[3]

    candidates = [
        base_dir / "src" / "assets" / "icon.png",
        base_dir / "assets" / "icon.png",
        base_dir / "src" / "assets" / "logo.png",
        base_dir / "assets" / "logo.png",
    ]

    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return candidate

    return None


def _build_excel_bytes(
    items: list[dict],
    period: str,
) -> bytes:
    try:
        from openpyxl import Workbook
        from openpyxl.drawing.image import Image as XLImage
        from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
        from openpyxl.utils import get_column_letter
    except ImportError as exception:
        raise RuntimeError(
            "Falta instalar openpyxl. Ejecuta: uv add openpyxl"
        ) from exception

    workbook = Workbook()
    summary_sheet = workbook.active
    summary_sheet.title = "Resumen"
    detail_sheet = workbook.create_sheet(
        "Detalle"
    )

    green = BRAND_DARK.replace("#", "")
    soft_green = "EAF8E5"
    white = "FFFFFF"
    dark = "172018"
    gray = "667085"
    border_color = "DCE5D6"

    thin_side = Side(
        style="thin",
        color=border_color,
    )

    summary_sheet.sheet_view.showGridLines = False
    detail_sheet.sheet_view.showGridLines = False

    summary_sheet.merge_cells(
        "A1:H1"
    )
    summary_sheet["A1"] = "AVORUNA"
    summary_sheet["A1"].font = Font(
        size=20,
        bold=True,
        color=green,
    )
    summary_sheet["A1"].alignment = Alignment(
        horizontal="center"
    )

    summary_sheet.merge_cells(
        "A2:H2"
    )
    summary_sheet["A2"] = (
        "Sistema móvil inteligente para la detección "
        "del nivel de madurez de la palta Hass"
    )
    summary_sheet["A2"].font = Font(
        size=11,
        color=gray,
    )
    summary_sheet["A2"].alignment = Alignment(
        horizontal="center"
    )

    summary_sheet.merge_cells(
        "A3:H3"
    )
    summary_sheet["A3"] = (
        f"Reporte: {_period_caption(period)} · "
        f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    )
    summary_sheet["A3"].font = Font(
        size=10,
        color=gray,
    )
    summary_sheet["A3"].alignment = Alignment(
        horizontal="center"
    )

    logo_path = _find_logo_path()

    if logo_path:
        try:
            logo = XLImage(
                str(logo_path)
            )
            logo.width = 52
            logo.height = 52
            summary_sheet.add_image(
                logo,
                "A1",
            )
        except Exception:
            pass

    total = len(items)
    counts = _counts(items)
    avg_confidence = _average_confidence(
        items
    )
    reliable_count = sum(
        1
        for item in items
        if bool(item.get("is_reliable", False))
    )

    metric_headers = [
        "Indicador",
        "Valor",
        "Descripción",
    ]

    metric_rows = [
        (
            "Total de análisis",
            total,
            "Registros incluidos en el periodo seleccionado",
        ),
        (
            "Confianza promedio",
            avg_confidence,
            "Promedio de confianza del modelo",
        ),
        (
            "Lista para cosecha",
            int(counts.get("lista_para_cosecha", 0)),
            "Resultados confiables clasificados como listos",
        ),
        (
            "Resultados confiables",
            reliable_count,
            "Análisis con salida considerada confiable",
        ),
    ]

    for column, header in enumerate(
        metric_headers,
        start=1,
    ):
        cell = summary_sheet.cell(
            row=6,
            column=column,
            value=header,
        )
        cell.fill = PatternFill(
            "solid",
            fgColor=green,
        )
        cell.font = Font(
            bold=True,
            color=white,
        )
        cell.alignment = Alignment(
            horizontal="center"
        )
        cell.border = Border(
            left=thin_side,
            right=thin_side,
            top=thin_side,
            bottom=thin_side,
        )

    for row_index, row_data in enumerate(
        metric_rows,
        start=7,
    ):
        for column_index, value in enumerate(
            row_data,
            start=1,
        ):
            cell = summary_sheet.cell(
                row=row_index,
                column=column_index,
                value=value,
            )
            cell.border = Border(
                left=thin_side,
                right=thin_side,
                top=thin_side,
                bottom=thin_side,
            )
            cell.alignment = Alignment(
                vertical="center",
                wrap_text=True,
            )

            if row_index % 2 == 1:
                cell.fill = PatternFill(
                    "solid",
                    fgColor=soft_green,
                )

    summary_sheet["B8"].number_format = "0.00%"

    category_start = 13
    summary_sheet.cell(
        row=category_start,
        column=1,
        value="Distribución de resultados",
    ).font = Font(
        size=13,
        bold=True,
        color=green,
    )

    category_headers = [
        "Resultado",
        "Cantidad",
        "Porcentaje",
    ]

    for column, header in enumerate(
        category_headers,
        start=1,
    ):
        cell = summary_sheet.cell(
            row=category_start + 1,
            column=column,
            value=header,
        )
        cell.fill = PatternFill(
            "solid",
            fgColor=green,
        )
        cell.font = Font(
            bold=True,
            color=white,
        )
        cell.alignment = Alignment(
            horizontal="center"
        )

    for offset, key in enumerate(
        (
            "lista_para_cosecha",
            "en_proceso",
            "aun_no_lista",
            "inconclusive",
        ),
        start=2,
    ):
        count = int(
            counts.get(key, 0)
        )
        row = category_start + offset
        summary_sheet.cell(
            row=row,
            column=1,
            value=CATEGORY_META[key]["label"],
        )
        summary_sheet.cell(
            row=row,
            column=2,
            value=count,
        )
        percentage_cell = summary_sheet.cell(
            row=row,
            column=3,
            value=_percentage(
                count,
                total,
            ),
        )
        percentage_cell.number_format = "0.00%"

        for column in range(1, 4):
            cell = summary_sheet.cell(
                row=row,
                column=column,
            )
            cell.border = Border(
                left=thin_side,
                right=thin_side,
                top=thin_side,
                bottom=thin_side,
            )

    for column, width in {
        "A": 28,
        "B": 18,
        "C": 54,
        "D": 14,
        "E": 14,
        "F": 14,
        "G": 14,
        "H": 14,
    }.items():
        summary_sheet.column_dimensions[
            column
        ].width = width

    detail_headers = [
        "N.°",
        "Fecha y hora",
        "Resultado",
        "Confianza",
        "Confiable",
        "Estado",
        "Recomendación",
        "Modo de inferencia",
        "ID de análisis",
    ]

    for column, header in enumerate(
        detail_headers,
        start=1,
    ):
        cell = detail_sheet.cell(
            row=1,
            column=column,
            value=header,
        )
        cell.fill = PatternFill(
            "solid",
            fgColor=green,
        )
        cell.font = Font(
            bold=True,
            color=white,
        )
        cell.alignment = Alignment(
            horizontal="center",
            vertical="center",
            wrap_text=True,
        )
        cell.border = Border(
            left=thin_side,
            right=thin_side,
            top=thin_side,
            bottom=thin_side,
        )

    sorted_items = sorted(
        items,
        key=lambda item: (
            _parse_datetime(
                item.get("created_at")
            )
            or datetime.min
        ),
        reverse=True,
    )

    for row_index, item in enumerate(
        sorted_items,
        start=2,
    ):
        created_at = _parse_datetime(
            item.get("created_at")
        )

        row_values = [
            row_index - 1,
            created_at,
            _category_label(item),
            _confidence(item),
            "Sí" if item.get("is_reliable") else "No",
            str(item.get("status", "")),
            str(item.get("recommended_action", "")),
            (
                "Modelo real"
                if item.get("inference_mode") == "model"
                else "Desarrollo"
            ),
            str(item.get("scan_id", "")),
        ]

        for column_index, value in enumerate(
            row_values,
            start=1,
        ):
            cell = detail_sheet.cell(
                row=row_index,
                column=column_index,
                value=value,
            )
            cell.border = Border(
                left=thin_side,
                right=thin_side,
                top=thin_side,
                bottom=thin_side,
            )
            cell.alignment = Alignment(
                vertical="top",
                wrap_text=True,
            )

            if row_index % 2 == 0:
                cell.fill = PatternFill(
                    "solid",
                    fgColor="F7FAF5",
                )

        detail_sheet.cell(
            row=row_index,
            column=2,
        ).number_format = "dd/mm/yyyy hh:mm"
        detail_sheet.cell(
            row=row_index,
            column=4,
        ).number_format = "0.00%"

    detail_sheet.freeze_panes = "A2"
    detail_sheet.auto_filter.ref = (
        f"A1:I{max(2, len(sorted_items) + 1)}"
    )

    detail_widths = [
        7,
        20,
        24,
        13,
        12,
        15,
        55,
        18,
        36,
    ]

    for column_index, width in enumerate(
        detail_widths,
        start=1,
    ):
        detail_sheet.column_dimensions[
            get_column_letter(column_index)
        ].width = width

    detail_sheet.row_dimensions[1].height = 34

    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def _build_pdf_bytes(
    items: list[dict],
    period: str,
) -> bytes:
    try:
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import mm
        from reportlab.platypus import (
            Image as RLImage,
            Paragraph,
            SimpleDocTemplate,
            Spacer,
            Table,
            TableStyle,
        )
    except ImportError as exception:
        raise RuntimeError(
            "Falta instalar reportlab. Ejecuta: uv add reportlab"
        ) from exception

    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=13 * mm,
        rightMargin=13 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
        title="Reporte Avoruna",
        author="Avoruna",
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "AvorunaTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=19,
        leading=22,
        textColor=colors.HexColor(BRAND_DARK),
        alignment=TA_CENTER,
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        "AvorunaSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#667085"),
        alignment=TA_CENTER,
    )
    section_style = ParagraphStyle(
        "AvorunaSection",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=14,
        textColor=colors.HexColor(BRAND_DARK),
        spaceBefore=8,
        spaceAfter=6,
    )
    cell_style = ParagraphStyle(
        "AvorunaCell",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=7.2,
        leading=9,
        textColor=colors.HexColor("#172018"),
    )
    cell_bold_style = ParagraphStyle(
        "AvorunaCellBold",
        parent=cell_style,
        fontName="Helvetica-Bold",
    )

    story: list = []
    logo_path = _find_logo_path()

    title_content: list = []

    if logo_path:
        try:
            title_content.append(
                RLImage(
                    str(logo_path),
                    width=15 * mm,
                    height=15 * mm,
                )
            )
        except Exception:
            pass

    title_content.append(
        Paragraph(
            "AVORUNA",
            title_style,
        )
    )

    title_table = Table(
        [title_content],
        colWidths=(
            [18 * mm, 220 * mm]
            if len(title_content) == 2
            else [238 * mm]
        ),
    )
    title_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ]
        )
    )
    story.append(title_table)
    story.append(
        Paragraph(
            "Sistema móvil inteligente para la detección del nivel de madurez de la palta Hass",
            subtitle_style,
        )
    )
    story.append(
        Paragraph(
            f"{_period_caption(period)} · "
            f"Generado el {datetime.now().strftime('%d/%m/%Y a las %H:%M')}",
            subtitle_style,
        )
    )
    story.append(
        Spacer(1, 7 * mm)
    )

    total = len(items)
    counts = _counts(items)
    avg_confidence = _average_confidence(
        items
    )
    reliable_count = sum(
        1
        for item in items
        if bool(item.get("is_reliable", False))
    )

    summary_data = [
        [
            "Total de análisis",
            "Confianza promedio",
            "Lista para cosecha",
            "Resultados confiables",
        ],
        [
            str(total),
            f"{avg_confidence * 100:.2f}%",
            str(
                counts.get(
                    "lista_para_cosecha",
                    0,
                )
            ),
            f"{reliable_count} ({_percentage(reliable_count, total) * 100:.1f}%)",
        ],
    ]

    summary_table = Table(
        summary_data,
        colWidths=[58 * mm] * 4,
        rowHeights=[9 * mm, 11 * mm],
    )
    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(BRAND_DARK)),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 8),
                ("FONTSIZE", (0, 1), (-1, 1), 12),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#EAF8E5")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DCE5D6")),
            ]
        )
    )
    story.append(summary_table)
    story.append(
        Paragraph(
            "Distribución de resultados",
            section_style,
        )
    )

    distribution_data = [
        ["Resultado", "Cantidad", "Porcentaje"]
    ]

    for key in (
        "lista_para_cosecha",
        "en_proceso",
        "aun_no_lista",
        "inconclusive",
    ):
        count = int(
            counts.get(key, 0)
        )
        distribution_data.append(
            [
                CATEGORY_META[key]["label"],
                str(count),
                f"{_percentage(count, total) * 100:.2f}%",
            ]
        )

    distribution_table = Table(
        distribution_data,
        colWidths=[92 * mm, 45 * mm, 45 * mm],
        repeatRows=1,
    )
    distribution_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(BRAND_DARK)),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("ALIGN", (1, 1), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7FAF5")]),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DCE5D6")),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(distribution_table)
    story.append(
        Paragraph(
            "Detalle de análisis",
            section_style,
        )
    )

    detail_data = [
        [
            Paragraph("N.°", cell_bold_style),
            Paragraph("Fecha", cell_bold_style),
            Paragraph("Resultado", cell_bold_style),
            Paragraph("Confianza", cell_bold_style),
            Paragraph("Confiable", cell_bold_style),
            Paragraph("Recomendación", cell_bold_style),
            Paragraph("ID", cell_bold_style),
        ]
    ]

    sorted_items = sorted(
        items,
        key=lambda item: (
            _parse_datetime(
                item.get("created_at")
            )
            or datetime.min
        ),
        reverse=True,
    )

    for index, item in enumerate(
        sorted_items,
        start=1,
    ):
        detail_data.append(
            [
                Paragraph(str(index), cell_style),
                Paragraph(_format_datetime(item.get("created_at")), cell_style),
                Paragraph(_category_label(item), cell_style),
                Paragraph(f"{_confidence(item) * 100:.2f}%", cell_style),
                Paragraph("Sí" if item.get("is_reliable") else "No", cell_style),
                Paragraph(_short_text(item.get("recommended_action"), 115), cell_style),
                Paragraph(_short_text(item.get("scan_id"), 22), cell_style),
            ]
        )

    detail_table = Table(
        detail_data,
        colWidths=[10 * mm, 33 * mm, 38 * mm, 23 * mm, 21 * mm, 88 * mm, 30 * mm],
        repeatRows=1,
    )
    detail_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(BRAND_DARK)),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ALIGN", (0, 0), (0, -1), "CENTER"),
                ("ALIGN", (3, 1), (4, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7FAF5")]),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#DCE5D6")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(detail_table)

    document.build(story)
    return buffer.getvalue()


async def _download_bytes(
    page: ft.Page,
    *,
    file_name: str,
    content: bytes,
    extension: str,
) -> None:
    try:
        result_path = await ft.FilePicker().save_file(
            file_name=file_name,
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=[extension],
            src_bytes=content,
        )

        if page.web:
            _show_message(
                page,
                f"Descarga iniciada: {file_name}. Revisa la carpeta Descargas.",
            )
        elif result_path:
            _show_message(
                page,
                f"Archivo guardado en: {result_path}",
            )
        else:
            _show_message(
                page,
                "La descarga fue cancelada.",
                error=True,
            )

    except Exception as exception:
        _show_message(
            page,
            f"No se pudo descargar el archivo: {exception}",
            error=True,
        )


def create_reports_view(
    page: ft.Page,
) -> ft.View:
    db = (
        page.data.get("db")
        if isinstance(page.data, dict)
        else None
    )

    if db is not None:
        saved = load_theme(db)
        page.theme_mode = (
            ft.ThemeMode.DARK
            if saved == "dark"
            else ft.ThemeMode.LIGHT
        )

    if page.data is None:
        page.data = {}

    mode = _screen_mode(page)
    active_period = {
        "value": "Diario"
    }
    history_state = {
        "items": get_scan_history(
            limit=500
        )
    }

    dashboard = ft.Column(
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        spacing=14,
    )

    def open_result(item: dict):
        def handler(_=None):
            page.data["scan_result"] = item
            page.data["last_scan_id"] = item.get(
                "scan_id"
            )

            image_path = Path(
                str(
                    item.get(
                        "saved_image_path",
                        "",
                    )
                )
            )

            if image_path.exists():
                try:
                    page.data[
                        "scan_image_bytes"
                    ] = image_path.read_bytes()
                except OSError:
                    page.data.pop(
                        "scan_image_bytes",
                        None,
                    )

            _nav(
                page,
                "/result",
            )

        return handler

    def current_items() -> list[dict]:
        return _filter_period(
            history_state["items"],
            active_period["value"],
            datetime.now(),
        )

    async def export_excel(_):
        items = current_items()

        if not items:
            _show_message(
                page,
                "No hay análisis en el periodo seleccionado para exportar.",
                error=True,
            )
            return

        try:
            content = await asyncio.to_thread(
                _build_excel_bytes,
                items,
                active_period["value"],
            )
        except Exception as exception:
            _show_message(
                page,
                str(exception),
                error=True,
            )
            return

        file_name = (
            "Avoruna_Reporte_"
            f"{active_period['value']}_"
            f"{datetime.now().strftime('%Y-%m-%d_%H-%M')}.xlsx"
        )

        await _download_bytes(
            page,
            file_name=file_name,
            content=content,
            extension="xlsx",
        )

    async def export_pdf(_):
        items = current_items()

        if not items:
            _show_message(
                page,
                "No hay análisis en el periodo seleccionado para exportar.",
                error=True,
            )
            return

        try:
            content = await asyncio.to_thread(
                _build_pdf_bytes,
                items,
                active_period["value"],
            )
        except Exception as exception:
            _show_message(
                page,
                str(exception),
                error=True,
            )
            return

        file_name = (
            "Avoruna_Reporte_"
            f"{active_period['value']}_"
            f"{datetime.now().strftime('%Y-%m-%d_%H-%M')}.pdf"
        )

        await _download_bytes(
            page,
            file_name=file_name,
            content=content,
            extension="pdf",
        )

    def set_period(value: str) -> None:
        active_period["value"] = value
        render_dashboard()

    def refresh_data(_=None) -> None:
        history_state["items"] = get_scan_history(
            limit=500
        )
        render_dashboard()
        _show_message(
            page,
            "Reporte actualizado con los últimos análisis.",
        )

    def build_period_row() -> ft.Row:
        return ft.Row(
            spacing=8,
            wrap=True,
            controls=[
                _pill_button(
                    page,
                    "Diario",
                    active_period["value"] == "Diario",
                    on_click=lambda _: set_period("Diario"),
                ),
                _pill_button(
                    page,
                    "Semanal",
                    active_period["value"] == "Semanal",
                    on_click=lambda _: set_period("Semanal"),
                ),
                _pill_button(
                    page,
                    "Mensual",
                    active_period["value"] == "Mensual",
                    on_click=lambda _: set_period("Mensual"),
                ),
                _pill_button(
                    page,
                    "Todo",
                    active_period["value"] == "Todo",
                    on_click=lambda _: set_period("Todo"),
                ),
            ],
        )

    def build_header(
        filtered_items: list[dict],
    ) -> ft.Control:
        title_block = ft.Column(
            spacing=3,
            controls=[
                ft.Text(
                    "Reportes de madurez — Palta Hass",
                    size=(
                        20
                        if mode == "desktop"
                        else 17
                    ),
                    color=_c_text(page),
                    weight=ft.FontWeight.W_900,
                ),
                ft.Text(
                    (
                        f"{len(filtered_items)} análisis reales · "
                        f"{_period_caption(active_period['value'])}"
                    ),
                    size=11,
                    color=_c_muted(page),
                ),
            ],
        )

        actions = ft.Row(
            spacing=8,
            wrap=True,
            controls=[
                _icon_action(
                    page,
                    ft.Icons.REFRESH,
                    "Actualizar",
                    on_click=refresh_data,
                ),
                _icon_action(
                    page,
                    ft.Icons.PICTURE_AS_PDF_OUTLINED,
                    "PDF",
                    on_click=export_pdf,
                ),
                _icon_action(
                    page,
                    ft.Icons.TABLE_VIEW_OUTLINED,
                    "Excel",
                    on_click=export_excel,
                    primary=True,
                ),
            ],
        )

        if mode == "desktop":
            return ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    title_block,
                    ft.Row(
                        spacing=10,
                        controls=[
                            build_period_row(),
                            actions,
                        ],
                    ),
                ],
            )

        return ft.Column(
            spacing=11,
            controls=[
                title_block,
                build_period_row(),
                actions,
            ],
        )

    def build_metrics(
        items: list[dict],
        previous_items: list[dict],
    ) -> ft.Control:
        total = len(items)
        previous_total = len(
            previous_items
        )
        counts = _counts(items)
        average = _average_confidence(
            items
        )
        previous_average = _average_confidence(
            previous_items
        )

        total_subtitle, total_color = _delta_text(
            total,
            previous_total,
        )
        confidence_subtitle, confidence_color = _delta_text(
            average,
            previous_average,
            percentage_points=True,
        )

        if active_period["value"] == "Todo":
            total_subtitle = "Registros acumulados en SQLite"
            total_color = _c_muted(page)
            confidence_subtitle = "Promedio general del historial"
            confidence_color = _c_muted(page)

        ready_count = int(
            counts.get(
                "lista_para_cosecha",
                0,
            )
        )
        inconclusive_count = int(
            counts.get(
                "inconclusive",
                0,
            )
        )

        cards = [
            _metric_card(
                page,
                icon=ft.Icons.ASSESSMENT_OUTLINED,
                title="TOTAL DE ANÁLISIS",
                value=str(total),
                suffix="registros",
                subtitle=total_subtitle,
                subtitle_color=total_color,
                accent_color=BRAND_DARK,
            ),
            _metric_card(
                page,
                icon=ft.Icons.QUERY_STATS,
                title="CONFIANZA PROMEDIO",
                value=f"{average * 100:.1f}",
                suffix="%",
                subtitle=confidence_subtitle,
                subtitle_color=confidence_color,
                accent_color=ACCENT_BLUE,
            ),
            _metric_card(
                page,
                icon=ft.Icons.CHECK_CIRCLE_OUTLINE,
                title="LISTAS PARA COSECHA",
                value=str(ready_count),
                suffix="paltas",
                subtitle=(
                    f"{_percentage(ready_count, total) * 100:.1f}% del periodo"
                ),
                subtitle_color="#2F9E44",
                accent_color="#2F9E44",
            ),
            _metric_card(
                page,
                icon=ft.Icons.WARNING_AMBER_ROUNDED,
                title="NO CONCLUYENTES",
                value=str(inconclusive_count),
                suffix="análisis",
                subtitle=(
                    f"{_percentage(inconclusive_count, total) * 100:.1f}% requiere revisión"
                ),
                subtitle_color=(
                    ACCENT_RED
                    if inconclusive_count > 0
                    else _c_muted(page)
                ),
                accent_color="#7C3AED",
            ),
        ]

        if mode == "desktop":
            return ft.Row(
                spacing=12,
                controls=[
                    ft.Container(
                        expand=True,
                        content=card,
                    )
                    for card in cards
                ],
            )

        if mode == "tablet":
            return ft.Column(
                spacing=12,
                controls=[
                    ft.Row(
                        spacing=12,
                        controls=[
                            ft.Container(
                                expand=True,
                                content=cards[0],
                            ),
                            ft.Container(
                                expand=True,
                                content=cards[1],
                            ),
                        ],
                    ),
                    ft.Row(
                        spacing=12,
                        controls=[
                            ft.Container(
                                expand=True,
                                content=cards[2],
                            ),
                            ft.Container(
                                expand=True,
                                content=cards[3],
                            ),
                        ],
                    ),
                ],
            )

        return ft.Column(
            spacing=12,
            controls=cards,
        )

    def build_activity_card(
        items: list[dict],
    ) -> ft.Container:
        buckets = _build_activity_buckets(
            items,
            active_period["value"],
            datetime.now(),
        )

        chart_width = {
            "desktop": 360,
            "tablet": 300,
            "mobile": 205,
        }[mode]

        activity_controls: list[ft.Control] = []

        if buckets:
            activity_controls = [
                _activity_row(
                    page,
                    label=label,
                    counter=counter,
                    width=chart_width,
                )
                for label, counter in buckets
            ]
        else:
            activity_controls = [
                ft.Container(
                    padding=22,
                    alignment=ft.Alignment(0, 0),
                    content=ft.Text(
                        "No existen datos con fecha válida para mostrar la tendencia.",
                        size=10,
                        color=_c_muted(page),
                        text_align=ft.TextAlign.CENTER,
                    ),
                )
            ]

        legend = ft.Row(
            spacing=12,
            wrap=True,
            controls=[
                ft.Row(
                    spacing=5,
                    controls=[
                        ft.Container(
                            width=8,
                            height=8,
                            border_radius=999,
                            bgcolor=meta["color"],
                        ),
                        ft.Text(
                            meta["label"],
                            size=8,
                            color=_c_muted(page),
                        ),
                    ],
                )
                for meta in CATEGORY_META.values()
            ],
        )

        return _card(
            page,
            ft.Column(
                spacing=14,
                controls=[
                    ft.Text(
                        "Actividad de análisis",
                        size=14,
                        color=_c_text(page),
                        weight=ft.FontWeight.W_900,
                    ),
                    ft.Text(
                        "Cantidad de evaluaciones realizadas y distribución por resultado.",
                        size=9,
                        color=_c_muted(page),
                    ),
                    legend,
                    ft.Divider(
                        height=1,
                        color=_c_border(page),
                    ),
                    *activity_controls,
                ],
            ),
        )

    def build_distribution_card(
        items: list[dict],
    ) -> ft.Container:
        total = len(items)
        counts = _counts(items)
        progress_width = {
            "desktop": 340,
            "tablet": 290,
            "mobile": 205,
        }[mode]

        rows = [
            _distribution_row(
                page,
                label=CATEGORY_META[key]["label"],
                count=int(
                    counts.get(key, 0)
                ),
                total=total,
                color=CATEGORY_META[key]["color"],
                width=progress_width,
            )
            for key in (
                "lista_para_cosecha",
                "en_proceso",
                "aun_no_lista",
                "inconclusive",
            )
        ]

        return _card(
            page,
            ft.Column(
                spacing=15,
                controls=[
                    ft.Text(
                        "Distribución de madurez",
                        size=14,
                        color=_c_text(page),
                        weight=ft.FontWeight.W_900,
                    ),
                    ft.Text(
                        "Clasificación de los análisis de palta Hass del periodo.",
                        size=9,
                        color=_c_muted(page),
                    ),
                    ft.Divider(
                        height=1,
                        color=_c_border(page),
                    ),
                    *rows,
                ],
            ),
        )

    def build_quality_card(
        items: list[dict],
    ) -> ft.Container:
        total = len(items)
        reliable_count = sum(
            1
            for item in items
            if bool(item.get("is_reliable", False))
        )
        real_model_count = sum(
            1
            for item in items
            if item.get("inference_mode") == "model"
        )
        high_confidence_count = sum(
            1
            for item in items
            if _confidence(item) >= 0.70
        )

        progress_width = {
            "desktop": 340,
            "tablet": 290,
            "mobile": 205,
        }[mode]

        return _card(
            page,
            ft.Column(
                spacing=15,
                controls=[
                    ft.Text(
                        "Calidad del análisis",
                        size=14,
                        color=_c_text(page),
                        weight=ft.FontWeight.W_900,
                    ),
                    ft.Text(
                        "Indicadores técnicos obtenidos de los resultados almacenados.",
                        size=9,
                        color=_c_muted(page),
                    ),
                    ft.Divider(
                        height=1,
                        color=_c_border(page),
                    ),
                    _quality_row(
                        page,
                        label="Resultados confiables",
                        value=_percentage(
                            reliable_count,
                            total,
                        ),
                        detail=f"{reliable_count} de {total} análisis",
                        color="#2F9E44",
                        width=progress_width,
                    ),
                    _quality_row(
                        page,
                        label="Inferencia con modelo real",
                        value=_percentage(
                            real_model_count,
                            total,
                        ),
                        detail=f"{real_model_count} procesados por IA",
                        color=ACCENT_BLUE,
                        width=progress_width,
                    ),
                    _quality_row(
                        page,
                        label="Confianza igual o mayor a 70%",
                        value=_percentage(
                            high_confidence_count,
                            total,
                        ),
                        detail=f"{high_confidence_count} resultados con confianza alta",
                        color="#7C3AED",
                        width=progress_width,
                    ),
                ],
            ),
        )

    def build_priority_card(
        items: list[dict],
    ) -> ft.Container:
        sorted_items = sorted(
            items,
            key=lambda item: (
                _parse_datetime(
                    item.get("created_at")
                )
                or datetime.min
            ),
            reverse=True,
        )

        priority_items = [
            item
            for item in sorted_items
            if _category_key(item)
            in {
                "lista_para_cosecha",
                "inconclusive",
            }
        ][:4]

        rows: list[ft.Control] = []

        for item in priority_items:
            key = _category_key(item)
            meta = CATEGORY_META[key]
            default_action = (
                "Evaluar la programación de cosecha."
                if key == "lista_para_cosecha"
                else "Repetir la fotografía con mejor iluminación."
            )

            rows.append(
                ft.Container(
                    padding=ft.Padding(
                        10,
                        9,
                        10,
                        9,
                    ),
                    border_radius=13,
                    bgcolor=_c_soft(page),
                    ink=True,
                    on_click=open_result(item),
                    content=ft.Row(
                        spacing=10,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Container(
                                width=10,
                                height=10,
                                border_radius=999,
                                bgcolor=meta["color"],
                            ),
                            ft.Column(
                                expand=True,
                                spacing=2,
                                controls=[
                                    ft.Text(
                                        meta["label"],
                                        size=10,
                                        color=_c_text(page),
                                        weight=ft.FontWeight.W_900,
                                    ),
                                    ft.Text(
                                        _short_text(
                                            item.get("recommended_action")
                                            or default_action,
                                            72,
                                        ),
                                        size=8,
                                        color=_c_muted(page),
                                    ),
                                ],
                            ),
                            ft.Column(
                                horizontal_alignment=ft.CrossAxisAlignment.END,
                                spacing=1,
                                controls=[
                                    ft.Text(
                                        f"{_confidence(item) * 100:.1f}%",
                                        size=10,
                                        color=meta["color"],
                                        weight=ft.FontWeight.W_900,
                                    ),
                                    ft.Text(
                                        _format_datetime(
                                            item.get("created_at")
                                        ),
                                        size=7,
                                        color=_c_muted(page),
                                    ),
                                ],
                            ),
                        ],
                    ),
                )
            )

        if not rows:
            rows.append(
                ft.Container(
                    padding=24,
                    alignment=ft.Alignment(0, 0),
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=8,
                        controls=[
                            ft.Icon(
                                ft.Icons.VERIFIED_OUTLINED,
                                size=36,
                                color="#2F9E44",
                            ),
                            ft.Text(
                                "Sin acciones prioritarias",
                                size=11,
                                color=_c_text(page),
                                weight=ft.FontWeight.W_900,
                            ),
                            ft.Text(
                                "No se encontraron resultados listos para cosecha ni análisis no concluyentes.",
                                size=8,
                                color=_c_muted(page),
                                text_align=ft.TextAlign.CENTER,
                            ),
                        ],
                    ),
                )
            )

        return _card(
            page,
            ft.Column(
                spacing=11,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Column(
                                spacing=2,
                                controls=[
                                    ft.Text(
                                        "Acciones prioritarias",
                                        size=14,
                                        color=_c_text(page),
                                        weight=ft.FontWeight.W_900,
                                    ),
                                    ft.Text(
                                        "Resultados recientes que requieren atención.",
                                        size=9,
                                        color=_c_muted(page),
                                    ),
                                ],
                            ),
                            ft.Container(
                                padding=ft.Padding(
                                    10,
                                    4,
                                    10,
                                    4,
                                ),
                                border_radius=999,
                                bgcolor=ft.Colors.with_opacity(
                                    0.10,
                                    ACCENT_AMBER,
                                ),
                                content=ft.Text(
                                    str(len(priority_items)),
                                    size=10,
                                    color=ACCENT_AMBER,
                                    weight=ft.FontWeight.W_900,
                                ),
                            ),
                        ],
                    ),
                    ft.Divider(
                        height=1,
                        color=_c_border(page),
                    ),
                    *rows,
                    ft.Container(
                        height=36,
                        border_radius=11,
                        bgcolor=_c_positive_bg(page),
                        ink=True,
                        on_click=lambda _: _nav(
                            page,
                            "/history",
                        ),
                        alignment=ft.Alignment(0, 0),
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=7,
                            controls=[
                                ft.Text(
                                    "VER HISTORIAL COMPLETO",
                                    size=9,
                                    color=BRAND_DARK,
                                    weight=ft.FontWeight.W_900,
                                ),
                                ft.Icon(
                                    ft.Icons.ARROW_FORWARD,
                                    size=14,
                                    color=BRAND_DARK,
                                ),
                            ],
                        ),
                    ),
                ],
            ),
        )

    def build_empty_state() -> ft.Container:
        return _card(
            page,
            ft.Container(
                padding=ft.Padding(
                    24,
                    36,
                    24,
                    36,
                ),
                alignment=ft.Alignment(0, 0),
                content=ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10,
                    controls=[
                        ft.Icon(
                            ft.Icons.INSERT_CHART_OUTLINED,
                            size=52,
                            color=BRAND_GREEN,
                        ),
                        ft.Text(
                            "No hay análisis en este periodo",
                            size=16,
                            color=_c_text(page),
                            weight=ft.FontWeight.W_900,
                        ),
                        ft.Text(
                            "Selecciona otro periodo o realiza un nuevo análisis de palta Hass.",
                            size=10,
                            color=_c_muted(page),
                            text_align=ft.TextAlign.CENTER,
                        ),
                        _icon_action(
                            page,
                            ft.Icons.PHOTO_CAMERA_OUTLINED,
                            "Realizar análisis",
                            on_click=lambda _: _nav(
                                page,
                                "/scan",
                            ),
                            primary=True,
                        ),
                    ],
                ),
            ),
        )

    def render_dashboard(
        update: bool = True,
    ) -> None:
        now = datetime.now()
        items = _filter_period(
            history_state["items"],
            active_period["value"],
            now,
        )
        previous_items = _previous_period_items(
            history_state["items"],
            active_period["value"],
            now,
        )

        controls: list[ft.Control] = [
            build_header(items),
        ]

        if not items:
            controls.extend(
                [
                    build_metrics(
                        items,
                        previous_items,
                    ),
                    build_empty_state(),
                    ft.Container(height=16),
                ]
            )
        else:
            controls.append(
                build_metrics(
                    items,
                    previous_items,
                )
            )

            activity_card = build_activity_card(
                items
            )
            distribution_card = build_distribution_card(
                items
            )
            quality_card = build_quality_card(
                items
            )
            priority_card = build_priority_card(
                items
            )

            if mode == "desktop":
                controls.extend(
                    [
                        ft.Row(
                            spacing=12,
                            vertical_alignment=ft.CrossAxisAlignment.START,
                            controls=[
                                ft.Container(
                                    expand=3,
                                    content=activity_card,
                                ),
                                ft.Container(
                                    expand=2,
                                    content=distribution_card,
                                ),
                            ],
                        ),
                        ft.Row(
                            spacing=12,
                            vertical_alignment=ft.CrossAxisAlignment.START,
                            controls=[
                                ft.Container(
                                    expand=True,
                                    content=quality_card,
                                ),
                                ft.Container(
                                    expand=True,
                                    content=priority_card,
                                ),
                            ],
                        ),
                    ]
                )
            else:
                controls.extend(
                    [
                        activity_card,
                        distribution_card,
                        quality_card,
                        priority_card,
                    ]
                )

            controls.append(
                ft.Container(height=16)
            )

        dashboard.controls = controls

        if update:
            page.update()

    render_dashboard(
        update=False
    )

    reports_content = ft.Container(
        expand=True,
        padding=ft.Padding(
            18 if mode != "mobile" else 12,
            12,
            18 if mode != "mobile" else 12,
            24,
        ),
        content=dashboard,
    )

    root = build_app_shell(
        page,
        reports_content,
    )

    return ft.View(
        route="/reports",
        controls=[
            ft.SafeArea(
                expand=True,
                content=root,
            ),
        ],
    )
