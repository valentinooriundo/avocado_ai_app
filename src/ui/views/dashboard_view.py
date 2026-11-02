# src/ui/views/dashboard_view.py
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

import flet as ft

from services.auth_session_service import (
    clear_auth_data,
    get_auth_data,
    is_authenticated,
)
from services.scan_flow_service import get_scan_history
from services.settings_service import load_theme
from ui.components.app_shell import BRAND_GREEN, build_app_shell


ACCENT_BLUE = "#2563EB"
ACCENT_VIOLET = "#7C3AED"
ACCENT_AMBER = "#D97706"
ACCENT_RED = "#DC4C64"
ACCENT_DARK_GREEN = "#237A12"


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None

    try:
        return datetime.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None


def _confidence(item: dict) -> float:
    try:
        value = float(item.get("confidence", 0.0) or 0.0)
    except (TypeError, ValueError):
        return 0.0

    if value > 1:
        value = value / 100.0

    return max(0.0, min(1.0, value))


def _category(item: dict) -> str:
    if not bool(item.get("is_reliable", False)):
        return "inconclusive"

    key = str(item.get("label_key", "") or "").strip().lower()

    if key == "lista_para_cosecha":
        return "ready"

    if key == "en_proceso":
        return "process"

    return "not_ready"


def _category_label(item: dict) -> str:
    category = _category(item)

    if category == "ready":
        return "Lista para cosecha"

    if category == "process":
        return "En proceso"

    if category == "not_ready":
        return "Aún no lista"

    return "Resultado no concluyente"


def _category_color(item: dict) -> str:
    category = _category(item)

    if category == "ready":
        return "#2E9D35"

    if category == "process":
        return ACCENT_AMBER

    if category == "not_ready":
        return ACCENT_RED

    return "#9A6700"


def _read_image_bytes(path_value: str | None) -> bytes | None:
    if not path_value:
        return None

    path = Path(str(path_value))

    if not path.exists() or not path.is_file():
        return None

    try:
        return path.read_bytes()
    except OSError:
        return None


def _demo_history() -> list[dict]:
    """
    Datos de respaldo visual para una instalación sin análisis.
    Cuando SQLite contiene registros, el panel usa únicamente datos reales.
    """

    now = datetime.now()

    demo_rows = [
        ("lista_para_cosecha", True, 0.92, 0),
        ("en_proceso", True, 0.81, 0),
        ("aun_no_lista", True, 0.89, 1),
        ("lista_para_cosecha", True, 0.87, 1),
        ("lista_para_cosecha", True, 0.94, 2),
        ("en_proceso", True, 0.76, 2),
        ("aun_no_lista", True, 0.84, 3),
        ("lista_para_cosecha", True, 0.91, 4),
        ("aun_no_lista", False, 0.43, 4),
        ("en_proceso", True, 0.79, 5),
        ("lista_para_cosecha", True, 0.88, 6),
        ("aun_no_lista", True, 0.86, 6),
    ]

    result: list[dict] = []

    for index, (label_key, reliable, confidence, days_ago) in enumerate(demo_rows):
        created_at = now - timedelta(
            days=days_ago,
            hours=(index * 2) % 10,
        )

        label_text = {
            "lista_para_cosecha": "Lista para cosecha",
            "en_proceso": "En proceso",
            "aun_no_lista": "Aún no lista",
        }[label_key]

        result.append(
            {
                "scan_id": f"demo-{index + 1}",
                "created_at": created_at.isoformat(timespec="seconds"),
                "label_key": label_key,
                "label_text": label_text,
                "confidence": confidence,
                "is_reliable": reliable,
                "inference_mode": "model",
                "recommended_action": (
                    "Programar la cosecha."
                    if label_key == "lista_para_cosecha"
                    else "Continuar con el seguimiento."
                ),
                "saved_image_path": "",
                "_demo": True,
            }
        )

    return result


def create_dashboard_view(page: ft.Page) -> ft.View:
    if not is_authenticated(page):
        page.run_task(page.push_route, "/login")
        return ft.View(
            route="/dashboard",
            controls=[ft.Container()],
        )

    if page.data is None:
        page.data = {}

    db = page.data.get("db") if isinstance(page.data, dict) else None

    if db is not None:
        try:
            saved_theme = load_theme(db)
            page.theme_mode = (
                ft.ThemeMode.DARK
                if saved_theme == "dark"
                else ft.ThemeMode.LIGHT
            )
        except Exception:
            pass

    auth_info = get_auth_data(page)
    full_name = str(
        auth_info.get("firebase_name")
        or "Productor"
    ).strip()
    user_email = str(
        auth_info.get("firebase_email")
        or ""
    ).strip()

    name_parts = [
        part
        for part in full_name.split()
        if part.strip()
    ]

    display_name = (
        " ".join(name_parts[:2])
        if name_parts
        else "Productor"
    )

    is_dark = page.theme_mode == ft.ThemeMode.DARK
    width = page.width or 1200
    is_mobile = width < 700
    is_tablet = 700 <= width < 1080

    page_padding = 12 if is_mobile else 18
    content_max_width = (
        None
        if is_mobile
        else (1040 if is_tablet else 1240)
    )
    card_radius = 18 if is_mobile else 22
    card_padding = 13 if is_mobile else 17

    def c_bg() -> str:
        return "#0E1217" if is_dark else "#F4F9F1"

    def c_surface() -> str:
        return "#151B24" if is_dark else "#FFFFFF"

    def c_surface_alt() -> str:
        return "#1B2330" if is_dark else "#F7FAF5"

    def c_text() -> str:
        return "#F5F7FA" if is_dark else "#172018"

    def c_muted() -> str:
        return "#9CA8B8" if is_dark else "#667085"

    def c_border() -> str:
        return "#2A3444" if is_dark else "#DDE7D7"

    def c_soft_green() -> str:
        return "#17331D" if is_dark else "#EAF7E5"

    def c_soft_blue() -> str:
        return "#192A44" if is_dark else "#EBF3FF"

    def c_soft_violet() -> str:
        return "#2A2040" if is_dark else "#F2ECFF"

    def c_soft_amber() -> str:
        return "#3B2C15" if is_dark else "#FFF5DE"

    def c_soft_red() -> str:
        return "#3A2027" if is_dark else "#FDEDEF"

    shadow = ft.BoxShadow(
        blur_radius=24 if not is_mobile else 14,
        spread_radius=1,
        color=ft.Colors.with_opacity(
            0.20 if is_dark else 0.07,
            ft.Colors.BLACK,
        ),
        offset=ft.Offset(0, 8),
    )

    state = {
        "period": "7 días",
        "history": [],
        "using_demo": False,
        "load_error": "",
    }

    def nav(route: str) -> None:
        page.run_task(
            page.push_route,
            route,
        )

    def logout(_=None) -> None:
        clear_auth_data(page)
        page.run_task(
            page.push_route,
            "/login",
        )

    def load_history() -> None:
        try:
            rows = get_scan_history(
                limit=500
            )
            state["history"] = list(rows or [])
            state["using_demo"] = not bool(rows)
            state["load_error"] = ""

            if not rows:
                state["history"] = _demo_history()

        except Exception as exception:
            state["history"] = _demo_history()
            state["using_demo"] = True
            state["load_error"] = str(exception)

    load_history()

    def card(
        content: ft.Control,
        *,
        padding: int | None = None,
        radius: int | None = None,
        bgcolor: str | None = None,
        border_color: str | None = None,
        on_click=None,
        ink: bool = False,
    ) -> ft.Container:
        return ft.Container(
            border_radius=radius or card_radius,
            bgcolor=bgcolor or c_surface(),
            border=ft.Border.all(
                1,
                border_color or c_border(),
            ),
            shadow=shadow,
            padding=(
                padding
                if padding is not None
                else card_padding
            ),
            ink=ink,
            on_click=on_click,
            content=content,
        )

    def icon_box(
        icon,
        *,
        color: str,
        background: str,
        size: int = 42,
    ) -> ft.Container:
        return ft.Container(
            width=size,
            height=size,
            border_radius=14,
            bgcolor=background,
            alignment=ft.Alignment.CENTER,
            content=ft.Icon(
                icon,
                color=color,
                size=21,
            ),
        )

    def period_button(
        label: str,
    ) -> ft.Container:
        active = (
            state["period"] == label
        )

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
                BRAND_GREEN
                if active
                else c_surface()
            ),
            border=ft.Border.all(
                1,
                BRAND_GREEN
                if active
                else c_border(),
            ),
            ink=True,
            on_click=lambda _, value=label: set_period(
                value
            ),
            alignment=ft.Alignment.CENTER,
            content=ft.Text(
                label,
                size=10,
                color=(
                    ft.Colors.WHITE
                    if active
                    else c_muted()
                ),
                weight=ft.FontWeight.W_900,
            ),
        )

    def filter_history(
        period: str,
    ) -> list[dict]:
        history = list(
            state["history"]
        )
        now = datetime.now()

        if period == "Todo":
            return history

        if period == "Hoy":
            return [
                item
                for item in history
                if (
                    _parse_datetime(
                        item.get("created_at")
                    )
                    and _parse_datetime(
                        item.get("created_at")
                    ).date()
                    == now.date()
                )
            ]

        days = (
            7
            if period == "7 días"
            else 30
        )

        cutoff = now - timedelta(
            days=days - 1
        )

        return [
            item
            for item in history
            if (
                _parse_datetime(
                    item.get("created_at")
                )
                and _parse_datetime(
                    item.get("created_at")
                )
                >= cutoff.replace(
                    hour=0,
                    minute=0,
                    second=0,
                    microsecond=0,
                )
            )
        ]

    def calculate_stats(
        rows: list[dict],
    ) -> dict:
        total = len(rows)

        ready = sum(
            1
            for item in rows
            if _category(item) == "ready"
        )
        process = sum(
            1
            for item in rows
            if _category(item) == "process"
        )
        not_ready = sum(
            1
            for item in rows
            if _category(item) == "not_ready"
        )
        inconclusive = sum(
            1
            for item in rows
            if _category(item) == "inconclusive"
        )
        reliable = sum(
            1
            for item in rows
            if bool(item.get("is_reliable", False))
        )
        model_real = sum(
            1
            for item in rows
            if str(
                item.get(
                    "inference_mode",
                    "",
                )
            ).lower()
            == "model"
        )

        confidence_values = [
            _confidence(item)
            for item in rows
        ]

        average_confidence = (
            sum(confidence_values)
            / len(confidence_values)
            if confidence_values
            else 0.0
        )

        return {
            "total": total,
            "ready": ready,
            "process": process,
            "not_ready": not_ready,
            "inconclusive": inconclusive,
            "reliable": reliable,
            "model_real": model_real,
            "avg_conf": average_confidence,
            "reliable_pct": (
                reliable / total
                if total
                else 0.0
            ),
            "model_pct": (
                model_real / total
                if total
                else 0.0
            ),
        }

    def build_activity_series(
        rows: list[dict],
    ) -> tuple[list[str], list[int], str]:
        now = datetime.now()
        period = state["period"]

        if period == "Hoy":
            labels = [
                "06h",
                "09h",
                "12h",
                "15h",
                "18h",
                "21h",
            ]
            values = [0] * len(labels)

            for item in rows:
                parsed = _parse_datetime(
                    item.get("created_at")
                )

                if not parsed:
                    continue

                hour = parsed.hour
                index = min(
                    max(
                        (hour - 6) // 3,
                        0,
                    ),
                    len(values) - 1,
                )
                values[index] += 1

            return (
                labels,
                values,
                "Escaneos distribuidos durante el día",
            )

        if period == "7 días":
            dates = [
                (
                    now
                    - timedelta(days=offset)
                ).date()
                for offset in range(
                    6,
                    -1,
                    -1,
                )
            ]

            counts = {
                date_value: 0
                for date_value in dates
            }

            for item in rows:
                parsed = _parse_datetime(
                    item.get("created_at")
                )

                if parsed and parsed.date() in counts:
                    counts[parsed.date()] += 1

            weekdays = [
                "L",
                "M",
                "M",
                "J",
                "V",
                "S",
                "D",
            ]

            labels = [
                weekdays[
                    date_value.weekday()
                ]
                for date_value in dates
            ]
            values = [
                counts[date_value]
                for date_value in dates
            ]

            return (
                labels,
                values,
                "Actividad registrada en los últimos 7 días",
            )

        if period == "30 días":
            labels = [
                "D1-5",
                "D6-10",
                "D11-15",
                "D16-20",
                "D21-25",
                "D26-30",
            ]
            values = [0] * 6
            start = (
                now
                - timedelta(days=29)
            ).replace(
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )

            for item in rows:
                parsed = _parse_datetime(
                    item.get("created_at")
                )

                if not parsed or parsed < start:
                    continue

                day_difference = (
                    parsed.date()
                    - start.date()
                ).days

                bucket = min(
                    day_difference // 5,
                    5,
                )
                values[bucket] += 1

            return (
                labels,
                values,
                "Actividad agrupada cada cinco días",
            )

        monthly_counts: dict[
            tuple[int, int],
            int,
        ] = defaultdict(int)

        for item in rows:
            parsed = _parse_datetime(
                item.get("created_at")
            )

            if parsed:
                monthly_counts[
                    (
                        parsed.year,
                        parsed.month,
                    )
                ] += 1

        months = sorted(
            monthly_counts.keys()
        )[-6:]

        month_names = [
            "Ene",
            "Feb",
            "Mar",
            "Abr",
            "May",
            "Jun",
            "Jul",
            "Ago",
            "Sep",
            "Oct",
            "Nov",
            "Dic",
        ]

        labels = [
            month_names[month - 1]
            for _, month in months
        ]
        values = [
            monthly_counts[key]
            for key in months
        ]

        if not labels:
            labels = [
                "Ene",
                "Feb",
                "Mar",
                "Abr",
                "May",
                "Jun",
            ]
            values = [0] * 6

        return (
            labels,
            values,
            "Evolución mensual del historial disponible",
        )

    def build_confidence_series(
        rows: list[dict],
    ) -> tuple[list[str], list[int]]:
        ordered = sorted(
            rows,
            key=lambda item: (
                _parse_datetime(
                    item.get("created_at")
                )
                or datetime.min
            ),
        )

        recent = ordered[-8:]

        labels = [
            f"A{index + 1}"
            for index in range(
                len(recent)
            )
        ]

        values = [
            int(
                round(
                    _confidence(item)
                    * 100
                )
            )
            for item in recent
        ]

        if not values:
            labels = [
                "A1",
                "A2",
                "A3",
                "A4",
                "A5",
                "A6",
            ]
            values = [0] * 6

        return labels, values

    def bar_chart(
        labels: list[str],
        values: list[int],
        *,
        color: str,
        height: int = 150,
        percentage: bool = False,
    ) -> ft.Control:
        maximum = max(
            values
            or [1]
        )

        if percentage:
            maximum = max(
                maximum,
                100,
            )

        bars: list[ft.Control] = []

        for index, value in enumerate(values):
            fill_height = max(
                7,
                int(
                    (
                        value
                        / maximum
                        if maximum
                        else 0
                    )
                    * (
                        height
                        - 44
                    )
                ),
            )

            bars.append(
                ft.Column(
                    expand=True,
                    spacing=5,
                    alignment=ft.MainAxisAlignment.END,
                    horizontal_alignment=(
                        ft.CrossAxisAlignment.CENTER
                    ),
                    controls=[
                        ft.Text(
                            (
                                f"{value}%"
                                if percentage
                                else str(value)
                            ),
                            size=8,
                            color=c_muted(),
                            weight=ft.FontWeight.W_800,
                        ),
                        ft.Container(
                            width=22 if not is_mobile else 16,
                            height=fill_height,
                            border_radius=ft.BorderRadius.only(
                                top_left=8,
                                top_right=8,
                                bottom_left=3,
                                bottom_right=3,
                            ),
                            gradient=ft.LinearGradient(
                                begin=ft.Alignment(
                                    0,
                                    -1,
                                ),
                                end=ft.Alignment(
                                    0,
                                    1,
                                ),
                                colors=[
                                    color,
                                    ft.Colors.with_opacity(
                                        0.52,
                                        color,
                                    ),
                                ],
                            ),
                        ),
                        ft.Text(
                            labels[index],
                            size=8,
                            color=c_muted(),
                            weight=ft.FontWeight.W_700,
                        ),
                    ],
                )
            )

        return ft.Container(
            height=height,
            padding=ft.Padding(
                4,
                8,
                4,
                0,
            ),
            content=ft.Row(
                spacing=6,
                vertical_alignment=(
                    ft.CrossAxisAlignment.END
                ),
                controls=bars,
            ),
        )

    def distribution_row(
        label: str,
        count: int,
        total: int,
        color: str,
        icon,
    ) -> ft.Control:
        percentage = (
            count / total
            if total
            else 0.0
        )

        return ft.Column(
            spacing=7,
            controls=[
                ft.Row(
                    alignment=(
                        ft.MainAxisAlignment
                        .SPACE_BETWEEN
                    ),
                    controls=[
                        ft.Row(
                            spacing=8,
                            controls=[
                                ft.Icon(
                                    icon,
                                    size=15,
                                    color=color,
                                ),
                                ft.Text(
                                    label,
                                    size=11,
                                    color=c_text(),
                                    weight=(
                                        ft.FontWeight
                                        .W_800
                                    ),
                                ),
                            ],
                        ),
                        ft.Text(
                            (
                                f"{count} · "
                                f"{percentage * 100:.0f}%"
                            ),
                            size=10,
                            color=color,
                            weight=ft.FontWeight.W_900,
                        ),
                    ],
                ),
                ft.ProgressBar(
                    value=percentage,
                    height=7,
                    border_radius=999,
                    color=color,
                    bgcolor=ft.Colors.with_opacity(
                        0.10,
                        color,
                    ),
                ),
            ],
        )

    def metric_card(
        title: str,
        value: str,
        subtitle: str,
        *,
        icon,
        accent: str,
        soft_background: str,
        col: dict | None = None,
    ) -> ft.Container:
        return ft.Container(
            col=(
                col
                or {
                    "xs": 6,
                    "sm": 6,
                    "md": 3,
                }
            ),
            content=card(
                ft.Column(
                    spacing=11,
                    controls=[
                        ft.Row(
                            alignment=(
                                ft.MainAxisAlignment
                                .SPACE_BETWEEN
                            ),
                            controls=[
                                icon_box(
                                    icon,
                                    color=accent,
                                    background=(
                                        soft_background
                                    ),
                                ),
                                ft.Container(
                                    padding=ft.Padding(
                                        8,
                                        4,
                                        8,
                                        4,
                                    ),
                                    border_radius=999,
                                    bgcolor=ft.Colors.with_opacity(
                                        0.08,
                                        accent,
                                    ),
                                    content=ft.Text(
                                        "ACTUAL",
                                        size=8,
                                        color=accent,
                                        weight=(
                                            ft.FontWeight
                                            .W_900
                                        ),
                                    ),
                                ),
                            ],
                        ),
                        ft.Text(
                            title,
                            size=10,
                            color=c_muted(),
                            weight=ft.FontWeight.W_800,
                        ),
                        ft.Text(
                            value,
                            size=25 if not is_mobile else 22,
                            color=c_text(),
                            weight=ft.FontWeight.W_900,
                        ),
                        ft.Text(
                            subtitle,
                            size=9,
                            color=accent,
                            weight=ft.FontWeight.W_700,
                        ),
                    ],
                )
            ),
        )

    def open_result(
        item: dict,
    ):
        def handler(_=None):
            if item.get("_demo"):
                show_message(
                    "Este es un registro de demostración. "
                    "Realiza un análisis para abrir un resultado real."
                )
                return

            page.data["scan_result"] = item
            page.data["last_scan_id"] = item.get(
                "scan_id"
            )

            image_bytes = _read_image_bytes(
                item.get(
                    "saved_image_path"
                )
            )

            if image_bytes:
                page.data[
                    "scan_image_bytes"
                ] = image_bytes
            else:
                page.data.pop(
                    "scan_image_bytes",
                    None,
                )

            nav("/result")

        return handler

    def recent_card(
        item: dict,
    ) -> ft.Control:
        image_bytes = _read_image_bytes(
            item.get(
                "saved_image_path"
            )
        )

        if image_bytes:
            preview = ft.Image(
                src=image_bytes,
                width=72,
                height=72,
                fit=ft.BoxFit.COVER,
                border_radius=15,
                gapless_playback=True,
            )
        else:
            preview = ft.Container(
                width=72,
                height=72,
                border_radius=15,
                gradient=ft.LinearGradient(
                    begin=ft.Alignment(
                        -1,
                        -1,
                    ),
                    end=ft.Alignment(
                        1,
                        1,
                    ),
                    colors=[
                        "#2D6A2D",
                        "#70C85A",
                    ],
                ),
                alignment=ft.Alignment.CENTER,
                content=ft.Icon(
                    ft.Icons.ECO_OUTLINED,
                    size=30,
                    color=ft.Colors.WHITE,
                ),
            )

        parsed = _parse_datetime(
            item.get("created_at")
        )
        formatted_date = (
            parsed.strftime(
                "%d/%m/%Y · %H:%M"
            )
            if parsed
            else "Fecha no disponible"
        )
        result_color = _category_color(
            item
        )

        return ft.Container(
            col={
                "xs": 12,
                "md": 4,
            },
            content=card(
                ft.Row(
                    spacing=12,
                    vertical_alignment=(
                        ft.CrossAxisAlignment
                        .CENTER
                    ),
                    controls=[
                        preview,
                        ft.Column(
                            expand=True,
                            spacing=5,
                            controls=[
                                ft.Text(
                                    _category_label(
                                        item
                                    ),
                                    size=13,
                                    color=result_color,
                                    weight=(
                                        ft.FontWeight
                                        .W_900
                                    ),
                                    max_lines=1,
                                    overflow=(
                                        ft.TextOverflow
                                        .ELLIPSIS
                                    ),
                                ),
                                ft.Text(
                                    formatted_date,
                                    size=9,
                                    color=c_muted(),
                                ),
                                ft.Row(
                                    spacing=6,
                                    wrap=True,
                                    controls=[
                                        ft.Container(
                                            padding=ft.Padding(
                                                7,
                                                3,
                                                7,
                                                3,
                                            ),
                                            border_radius=999,
                                            bgcolor=ft.Colors.with_opacity(
                                                0.10,
                                                result_color,
                                            ),
                                            content=ft.Text(
                                                (
                                                    f"Confianza "
                                                    f"{_confidence(item) * 100:.1f}%"
                                                ),
                                                size=8,
                                                color=result_color,
                                                weight=(
                                                    ft.FontWeight
                                                    .W_800
                                                ),
                                            ),
                                        ),
                                        ft.Container(
                                            padding=ft.Padding(
                                                7,
                                                3,
                                                7,
                                                3,
                                            ),
                                            border_radius=999,
                                            bgcolor=c_soft_violet(),
                                            content=ft.Text(
                                                "IA",
                                                size=8,
                                                color=ACCENT_VIOLET,
                                                weight=(
                                                    ft.FontWeight
                                                    .W_900
                                                ),
                                            ),
                                        ),
                                    ],
                                ),
                            ],
                        ),
                        ft.Icon(
                            ft.Icons.CHEVRON_RIGHT,
                            size=18,
                            color=c_muted(),
                        ),
                    ],
                ),
                ink=True,
                on_click=open_result(
                    item
                ),
            ),
        )

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
                    weight=ft.FontWeight.W_700,
                ),
                bgcolor=(
                    ACCENT_RED
                    if error
                    else "#2F5D46"
                ),
                show_close_icon=True,
                duration=ft.Duration(
                    seconds=4
                ),
            )
        )

    period_row = ft.Row(
        spacing=8,
        wrap=True,
    )
    dashboard_host = ft.Column(
        spacing=14,
    )

    def set_period(
        value: str,
    ) -> None:
        state["period"] = value
        rebuild_dashboard(
            update=True
        )

    def refresh_dashboard(_=None) -> None:
        load_history()
        rebuild_dashboard(
            update=True
        )
        show_message(
            "Dashboard actualizado con los últimos análisis."
        )

    def quick_action(
        title: str,
        subtitle: str,
        *,
        icon,
        accent: str,
        soft_background: str,
        route: str,
    ) -> ft.Control:
        return ft.Container(
            col={
                "xs": 12,
                "sm": 4,
            },
            content=card(
                ft.Row(
                    spacing=12,
                    controls=[
                        icon_box(
                            icon,
                            color=accent,
                            background=soft_background,
                            size=46,
                        ),
                        ft.Column(
                            expand=True,
                            spacing=3,
                            controls=[
                                ft.Text(
                                    title,
                                    size=12,
                                    color=c_text(),
                                    weight=(
                                        ft.FontWeight
                                        .W_900
                                    ),
                                ),
                                ft.Text(
                                    subtitle,
                                    size=9,
                                    color=c_muted(),
                                    max_lines=2,
                                    overflow=(
                                        ft.TextOverflow
                                        .ELLIPSIS
                                    ),
                                ),
                            ],
                        ),
                        ft.Icon(
                            ft.Icons.ARROW_FORWARD_IOS,
                            size=13,
                            color=c_muted(),
                        ),
                    ],
                ),
                ink=True,
                on_click=lambda _: nav(
                    route
                ),
            ),
        )

    def rebuild_dashboard(
        *,
        update: bool,
    ) -> None:
        rows = filter_history(
            state["period"]
        )
        stats = calculate_stats(
            rows
        )

        period_row.controls = [
            period_button("Hoy"),
            period_button("7 días"),
            period_button("30 días"),
            period_button("Todo"),
        ]

        activity_labels, activity_values, activity_caption = (
            build_activity_series(
                rows
            )
        )
        confidence_labels, confidence_values = (
            build_confidence_series(
                rows
            )
        )

        sorted_recent = sorted(
            rows,
            key=lambda item: (
                _parse_datetime(
                    item.get("created_at")
                )
                or datetime.min
            ),
            reverse=True,
        )[:3]

        ready_ratio = (
            stats["ready"]
            / stats["total"]
            if stats["total"]
            else 0.0
        )

        confidence_percent = (
            stats["avg_conf"]
            * 100
        )

        priority_ready = stats["ready"]
        priority_review = (
            stats["inconclusive"]
            + sum(
                1
                for item in rows
                if _confidence(item) < 0.60
            )
        )

        demo_notice = (
            ft.Container(
                padding=ft.Padding(
                    12,
                    9,
                    12,
                    9,
                ),
                border_radius=13,
                bgcolor=c_soft_amber(),
                border=ft.Border.all(
                    1,
                    ft.Colors.with_opacity(
                        0.30,
                        ACCENT_AMBER,
                    ),
                ),
                content=ft.Row(
                    spacing=9,
                    controls=[
                        ft.Icon(
                            ft.Icons.SCIENCE_OUTLINED,
                            size=17,
                            color=ACCENT_AMBER,
                        ),
                        ft.Text(
                            (
                                "Modo demostración activo: no se encontraron "
                                "análisis locales. El panel muestra datos de ejemplo."
                            ),
                            size=10,
                            color=ACCENT_AMBER,
                            weight=ft.FontWeight.W_800,
                        ),
                    ],
                ),
            )
            if state["using_demo"]
            else ft.Container(
                height=0
            )
        )

        system_message = (
            "SQLite local operativo"
            if not state["load_error"]
            else "Datos de respaldo activos"
        )

        top_banner = ft.Container(
            border_radius=24,
            padding=(
                18
                if is_mobile
                else 22
            ),
            gradient=ft.LinearGradient(
                begin=ft.Alignment(
                    -1,
                    -1,
                ),
                end=ft.Alignment(
                    1,
                    1,
                ),
                colors=(
                    [
                        "#17351E",
                        "#10271A",
                    ]
                    if is_dark
                    else [
                        "#E9F8E4",
                        "#F8FCF5",
                    ]
                ),
            ),
            border=ft.Border.all(
                1,
                c_border(),
            ),
            shadow=shadow,
            content=(
                ft.Column(
                    spacing=14,
                    controls=[
                        ft.Column(
                            spacing=5,
                            controls=[
                                ft.Text(
                                    (
                                        f"Hola, "
                                        f"{display_name}"
                                    ),
                                    size=21,
                                    color=c_text(),
                                    weight=(
                                        ft.FontWeight
                                        .W_900
                                    ),
                                ),
                                ft.Text(
                                    (
                                        "Panel inteligente para supervisar "
                                        "la madurez de la palta Hass."
                                    ),
                                    size=11,
                                    color=c_muted(),
                                ),
                            ],
                        ),
                        ft.Row(
                            spacing=8,
                            wrap=True,
                            controls=[
                                ft.FilledButton(
                                    adaptive=False,
                                    content=ft.Text(
                                        "NUEVO ANÁLISIS",
                                        size=10,
                                        weight=(
                                            ft.FontWeight
                                            .W_900
                                        ),
                                    ),
                                    icon=ft.Icons.PHOTO_CAMERA,
                                    height=42,
                                    style=ft.ButtonStyle(
                                        bgcolor=BRAND_GREEN,
                                        color=ft.Colors.WHITE,
                                        shape=ft.RoundedRectangleBorder(
                                            radius=12
                                        ),
                                    ),
                                    on_click=lambda _: nav(
                                        "/scan"
                                    ),
                                ),
                                ft.OutlinedButton(
                                    adaptive=False,
                                    content=ft.Text(
                                        "HISTORIAL",
                                        size=10,
                                        weight=(
                                            ft.FontWeight
                                            .W_900
                                        ),
                                    ),
                                    icon=ft.Icons.HISTORY,
                                    height=42,
                                    style=ft.ButtonStyle(
                                        color=c_text(),
                                        side=ft.BorderSide(
                                            1,
                                            c_border(),
                                        ),
                                        shape=ft.RoundedRectangleBorder(
                                            radius=12
                                        ),
                                    ),
                                    on_click=lambda _: nav(
                                        "/history"
                                    ),
                                ),
                            ],
                        ),
                    ],
                )
                if is_mobile
                else ft.Row(
                    alignment=(
                        ft.MainAxisAlignment
                        .SPACE_BETWEEN
                    ),
                    vertical_alignment=(
                        ft.CrossAxisAlignment
                        .CENTER
                    ),
                    controls=[
                        ft.Column(
                            expand=True,
                            spacing=5,
                            controls=[
                                ft.Row(
                                    spacing=8,
                                    controls=[
                                        ft.Text(
                                            (
                                                f"Hola, "
                                                f"{display_name}"
                                            ),
                                            size=24,
                                            color=c_text(),
                                            weight=(
                                                ft.FontWeight
                                                .W_900
                                            ),
                                        ),
                                        ft.Container(
                                            padding=ft.Padding(
                                                9,
                                                4,
                                                9,
                                                4,
                                            ),
                                            border_radius=999,
                                            bgcolor=c_soft_green(),
                                            content=ft.Text(
                                                "SISTEMA OPERATIVO",
                                                size=8,
                                                color=BRAND_GREEN,
                                                weight=(
                                                    ft.FontWeight
                                                    .W_900
                                                ),
                                            ),
                                        ),
                                    ],
                                ),
                                ft.Text(
                                    (
                                        "Monitorea los análisis de madurez, "
                                        "la confiabilidad del modelo y las "
                                        "prioridades de cosecha."
                                    ),
                                    size=11,
                                    color=c_muted(),
                                ),
                                ft.Text(
                                    user_email,
                                    size=9,
                                    color=c_muted(),
                                ),
                            ],
                        ),
                        ft.Row(
                            spacing=8,
                            controls=[
                                ft.IconButton(
                                    icon=ft.Icons.REFRESH,
                                    tooltip="Actualizar dashboard",
                                    on_click=refresh_dashboard,
                                ),
                                ft.FilledButton(
                                    adaptive=False,
                                    content=ft.Text(
                                        "NUEVO ANÁLISIS",
                                        size=10,
                                        weight=(
                                            ft.FontWeight
                                            .W_900
                                        ),
                                    ),
                                    icon=ft.Icons.PHOTO_CAMERA,
                                    height=42,
                                    style=ft.ButtonStyle(
                                        bgcolor=BRAND_GREEN,
                                        color=ft.Colors.WHITE,
                                        shape=ft.RoundedRectangleBorder(
                                            radius=12
                                        ),
                                    ),
                                    on_click=lambda _: nav(
                                        "/scan"
                                    ),
                                ),
                                ft.OutlinedButton(
                                    adaptive=False,
                                    content=ft.Text(
                                        "SALIR",
                                        size=10,
                                        weight=(
                                            ft.FontWeight
                                            .W_900
                                        ),
                                    ),
                                    icon=ft.Icons.LOGOUT,
                                    height=42,
                                    style=ft.ButtonStyle(
                                        color=ACCENT_RED,
                                        side=ft.BorderSide(
                                            1,
                                            ft.Colors.with_opacity(
                                                0.40,
                                                ACCENT_RED,
                                            ),
                                        ),
                                        shape=ft.RoundedRectangleBorder(
                                            radius=12
                                        ),
                                    ),
                                    on_click=logout,
                                ),
                            ],
                        ),
                    ],
                )
            ),
        )

        context_bar = card(
            (
                ft.Column(
                    spacing=10,
                    controls=[
                        ft.Column(
                            spacing=2,
                            controls=[
                                ft.Text(
                                    "Periodo de análisis",
                                    size=12,
                                    color=c_text(),
                                    weight=(
                                        ft.FontWeight
                                        .W_900
                                    ),
                                ),
                                ft.Text(
                                    (
                                        "Los indicadores y gráficos "
                                        "se actualizan automáticamente."
                                    ),
                                    size=9,
                                    color=c_muted(),
                                ),
                            ],
                        ),
                        period_row,
                    ],
                )
                if is_mobile
                else ft.Row(
                    alignment=(
                        ft.MainAxisAlignment
                        .SPACE_BETWEEN
                    ),
                    vertical_alignment=(
                        ft.CrossAxisAlignment
                        .CENTER
                    ),
                    controls=[
                        ft.Column(
                            spacing=2,
                            controls=[
                                ft.Text(
                                    "Periodo de análisis",
                                    size=12,
                                    color=c_text(),
                                    weight=(
                                        ft.FontWeight
                                        .W_900
                                    ),
                                ),
                                ft.Text(
                                    (
                                        "Dashboard calculado desde "
                                        "el historial local de SQLite."
                                    ),
                                    size=9,
                                    color=c_muted(),
                                ),
                            ],
                        ),
                        period_row,
                    ],
                )
            ),
            padding=13,
        )

        status_row = ft.ResponsiveRow(
            spacing=10,
            run_spacing=10,
            controls=[
                ft.Container(
                    col={
                        "xs": 12,
                        "sm": 4,
                    },
                    content=card(
                        ft.Row(
                            spacing=10,
                            controls=[
                                icon_box(
                                    ft.Icons.STORAGE_OUTLINED,
                                    color=BRAND_GREEN,
                                    background=c_soft_green(),
                                    size=38,
                                ),
                                ft.Column(
                                    spacing=2,
                                    controls=[
                                        ft.Text(
                                            "Almacenamiento",
                                            size=9,
                                            color=c_muted(),
                                        ),
                                        ft.Text(
                                            system_message,
                                            size=10,
                                            color=c_text(),
                                            weight=(
                                                ft.FontWeight
                                                .W_900
                                            ),
                                        ),
                                    ],
                                ),
                            ],
                        ),
                        padding=11,
                    ),
                ),
                ft.Container(
                    col={
                        "xs": 12,
                        "sm": 4,
                    },
                    content=card(
                        ft.Row(
                            spacing=10,
                            controls=[
                                icon_box(
                                    ft.Icons.PSYCHOLOGY_ALT_OUTLINED,
                                    color=ACCENT_BLUE,
                                    background=c_soft_blue(),
                                    size=38,
                                ),
                                ft.Column(
                                    spacing=2,
                                    controls=[
                                        ft.Text(
                                            "Motor de análisis",
                                            size=9,
                                            color=c_muted(),
                                        ),
                                        ft.Text(
                                            (
                                                f"{stats['model_pct'] * 100:.0f}% "
                                                "con modelo real"
                                            ),
                                            size=10,
                                            color=c_text(),
                                            weight=(
                                                ft.FontWeight
                                                .W_900
                                            ),
                                        ),
                                    ],
                                ),
                            ],
                        ),
                        padding=11,
                    ),
                ),
                ft.Container(
                    col={
                        "xs": 12,
                        "sm": 4,
                    },
                    content=card(
                        ft.Row(
                            spacing=10,
                            controls=[
                                icon_box(
                                    ft.Icons.VERIFIED_OUTLINED,
                                    color=ACCENT_VIOLET,
                                    background=c_soft_violet(),
                                    size=38,
                                ),
                                ft.Column(
                                    spacing=2,
                                    controls=[
                                        ft.Text(
                                            "Confiabilidad",
                                            size=9,
                                            color=c_muted(),
                                        ),
                                        ft.Text(
                                            (
                                                f"{stats['reliable_pct'] * 100:.0f}% "
                                                "de resultados válidos"
                                            ),
                                            size=10,
                                            color=c_text(),
                                            weight=(
                                                ft.FontWeight
                                                .W_900
                                            ),
                                        ),
                                    ],
                                ),
                            ],
                        ),
                        padding=11,
                    ),
                ),
            ],
        )

        metrics = ft.ResponsiveRow(
            spacing=12,
            run_spacing=12,
            controls=[
                metric_card(
                    "ANÁLISIS REALIZADOS",
                    str(stats["total"]),
                    (
                        f"Periodo: "
                        f"{state['period']}"
                    ),
                    icon=ft.Icons.ANALYTICS_OUTLINED,
                    accent=BRAND_GREEN,
                    soft_background=c_soft_green(),
                ),
                metric_card(
                    "LISTAS PARA COSECHA",
                    str(stats["ready"]),
                    (
                        f"{ready_ratio * 100:.0f}% "
                        "del periodo"
                    ),
                    icon=ft.Icons.TASK_ALT,
                    accent=ACCENT_DARK_GREEN,
                    soft_background=c_soft_green(),
                ),
                metric_card(
                    "CONFIANZA PROMEDIO",
                    f"{confidence_percent:.1f}%",
                    (
                        "Evaluación acumulada "
                        "del modelo"
                    ),
                    icon=ft.Icons.VERIFIED_USER_OUTLINED,
                    accent=ACCENT_VIOLET,
                    soft_background=c_soft_violet(),
                ),
                metric_card(
                    "POR REVISAR",
                    str(priority_review),
                    (
                        "No concluyentes o "
                        "confianza baja"
                    ),
                    icon=ft.Icons.WARNING_AMBER_ROUNDED,
                    accent=ACCENT_RED,
                    soft_background=c_soft_red(),
                ),
            ],
        )

        activity_card = ft.Container(
            col={
                "xs": 12,
                "md": 8,
            },
            content=card(
                ft.Column(
                    spacing=10,
                    controls=[
                        ft.Row(
                            alignment=(
                                ft.MainAxisAlignment
                                .SPACE_BETWEEN
                            ),
                            controls=[
                                ft.Column(
                                    spacing=2,
                                    controls=[
                                        ft.Text(
                                            "Actividad de análisis",
                                            size=15,
                                            color=c_text(),
                                            weight=(
                                                ft.FontWeight
                                                .W_900
                                            ),
                                        ),
                                        ft.Text(
                                            activity_caption,
                                            size=9,
                                            color=c_muted(),
                                        ),
                                    ],
                                ),
                                ft.Container(
                                    padding=ft.Padding(
                                        9,
                                        4,
                                        9,
                                        4,
                                    ),
                                    border_radius=999,
                                    bgcolor=c_soft_green(),
                                    content=ft.Text(
                                        (
                                            f"{sum(activity_values)} "
                                            "escaneos"
                                        ),
                                        size=8,
                                        color=BRAND_GREEN,
                                        weight=(
                                            ft.FontWeight
                                            .W_900
                                        ),
                                    ),
                                ),
                            ],
                        ),
                        bar_chart(
                            activity_labels,
                            activity_values,
                            color=BRAND_GREEN,
                            height=172,
                        ),
                    ],
                )
            ),
        )

        gauge_size = (
            132
            if not is_mobile
            else 118
        )

        confidence_gauge = ft.Container(
            col={
                "xs": 12,
                "md": 4,
            },
            content=card(
                ft.Column(
                    spacing=12,
                    horizontal_alignment=(
                        ft.CrossAxisAlignment
                        .CENTER
                    ),
                    controls=[
                        ft.Row(
                            alignment=(
                                ft.MainAxisAlignment
                                .SPACE_BETWEEN
                            ),
                            controls=[
                                ft.Column(
                                    spacing=2,
                                    controls=[
                                        ft.Text(
                                            "Salud del modelo",
                                            size=15,
                                            color=c_text(),
                                            weight=(
                                                ft.FontWeight
                                                .W_900
                                            ),
                                        ),
                                        ft.Text(
                                            "Confiabilidad promedio",
                                            size=9,
                                            color=c_muted(),
                                        ),
                                    ],
                                ),
                                ft.Icon(
                                    ft.Icons.AUTO_GRAPH,
                                    color=ACCENT_VIOLET,
                                    size=20,
                                ),
                            ],
                        ),
                        ft.Stack(
                            width=gauge_size,
                            height=gauge_size,
                            controls=[
                                ft.ProgressRing(
                                    value=stats["avg_conf"],
                                    width=gauge_size,
                                    height=gauge_size,
                                    stroke_width=11,
                                    color=ACCENT_VIOLET,
                                    bgcolor=ft.Colors.with_opacity(
                                        0.10,
                                        ACCENT_VIOLET,
                                    ),
                                ),
                                ft.Container(
                                    width=gauge_size,
                                    height=gauge_size,
                                    alignment=ft.Alignment.CENTER,
                                    content=ft.Column(
                                        tight=True,
                                        spacing=0,
                                        horizontal_alignment=(
                                            ft.CrossAxisAlignment
                                            .CENTER
                                        ),
                                        controls=[
                                            ft.Text(
                                                f"{confidence_percent:.1f}%",
                                                size=23,
                                                color=c_text(),
                                                weight=(
                                                    ft.FontWeight
                                                    .W_900
                                                ),
                                            ),
                                            ft.Text(
                                                "CONFIANZA",
                                                size=8,
                                                color=c_muted(),
                                                weight=(
                                                    ft.FontWeight
                                                    .W_900
                                                ),
                                            ),
                                        ],
                                    ),
                                ),
                            ],
                        ),
                        ft.Container(
                            padding=ft.Padding(
                                11,
                                8,
                                11,
                                8,
                            ),
                            border_radius=13,
                            bgcolor=c_soft_violet(),
                            content=ft.Row(
                                alignment=(
                                    ft.MainAxisAlignment
                                    .CENTER
                                ),
                                spacing=7,
                                controls=[
                                    ft.Icon(
                                        ft.Icons.INSIGHTS_OUTLINED,
                                        size=15,
                                        color=ACCENT_VIOLET,
                                    ),
                                    ft.Text(
                                        (
                                            "Modelo preparado para "
                                            "evaluación en campo"
                                        ),
                                        size=9,
                                        color=ACCENT_VIOLET,
                                        weight=(
                                            ft.FontWeight
                                            .W_800
                                        ),
                                    ),
                                ],
                            ),
                        ),
                    ],
                )
            ),
        )

        confidence_chart = ft.Container(
            col={
                "xs": 12,
                "md": 7,
            },
            content=card(
                ft.Column(
                    spacing=10,
                    controls=[
                        ft.Column(
                            spacing=2,
                            controls=[
                                ft.Text(
                                    "Confianza de análisis recientes",
                                    size=15,
                                    color=c_text(),
                                    weight=(
                                        ft.FontWeight
                                        .W_900
                                    ),
                                ),
                                ft.Text(
                                    (
                                        "Porcentaje de confianza de "
                                        "los últimos resultados disponibles"
                                    ),
                                    size=9,
                                    color=c_muted(),
                                ),
                            ],
                        ),
                        bar_chart(
                            confidence_labels,
                            confidence_values,
                            color=ACCENT_VIOLET,
                            height=165,
                            percentage=True,
                        ),
                    ],
                )
            ),
        )

        distribution_card = ft.Container(
            col={
                "xs": 12,
                "md": 5,
            },
            content=card(
                ft.Column(
                    spacing=15,
                    controls=[
                        ft.Column(
                            spacing=2,
                            controls=[
                                ft.Text(
                                    "Distribución de madurez",
                                    size=15,
                                    color=c_text(),
                                    weight=(
                                        ft.FontWeight
                                        .W_900
                                    ),
                                ),
                                ft.Text(
                                    (
                                        "Clasificación actual de "
                                        "los análisis seleccionados"
                                    ),
                                    size=9,
                                    color=c_muted(),
                                ),
                            ],
                        ),
                        distribution_row(
                            "Lista para cosecha",
                            stats["ready"],
                            stats["total"],
                            "#2E9D35",
                            ft.Icons.TASK_ALT,
                        ),
                        distribution_row(
                            "En proceso",
                            stats["process"],
                            stats["total"],
                            ACCENT_AMBER,
                            ft.Icons.TIMELAPSE,
                        ),
                        distribution_row(
                            "Aún no lista",
                            stats["not_ready"],
                            stats["total"],
                            ACCENT_RED,
                            ft.Icons.HOURGLASS_BOTTOM,
                        ),
                        distribution_row(
                            "No concluyente",
                            stats["inconclusive"],
                            stats["total"],
                            "#9A6700",
                            ft.Icons.HELP_OUTLINE,
                        ),
                    ],
                )
            ),
        )

        priorities = ft.Container(
            col={
                "xs": 12,
                "md": 5,
            },
            content=card(
                ft.Column(
                    spacing=13,
                    controls=[
                        ft.Row(
                            alignment=(
                                ft.MainAxisAlignment
                                .SPACE_BETWEEN
                            ),
                            controls=[
                                ft.Column(
                                    spacing=2,
                                    controls=[
                                        ft.Text(
                                            "Prioridades operativas",
                                            size=15,
                                            color=c_text(),
                                            weight=(
                                                ft.FontWeight
                                                .W_900
                                            ),
                                        ),
                                        ft.Text(
                                            "Acciones sugeridas por el panel",
                                            size=9,
                                            color=c_muted(),
                                        ),
                                    ],
                                ),
                                ft.Icon(
                                    ft.Icons.NOTIFICATIONS_ACTIVE_OUTLINED,
                                    color=ACCENT_RED,
                                    size=20,
                                ),
                            ],
                        ),
                        ft.Container(
                            padding=12,
                            border_radius=14,
                            bgcolor=c_soft_green(),
                            content=ft.Row(
                                spacing=10,
                                controls=[
                                    icon_box(
                                        ft.Icons.AGRICULTURE_OUTLINED,
                                        color=BRAND_GREEN,
                                        background=c_surface(),
                                        size=40,
                                    ),
                                    ft.Column(
                                        expand=True,
                                        spacing=3,
                                        controls=[
                                            ft.Text(
                                                (
                                                    f"{priority_ready} "
                                                    "análisis listos"
                                                ),
                                                size=11,
                                                color=c_text(),
                                                weight=(
                                                    ft.FontWeight
                                                    .W_900
                                                ),
                                            ),
                                            ft.Text(
                                                (
                                                    "Revisar y programar "
                                                    "la cosecha según el campo."
                                                ),
                                                size=9,
                                                color=c_muted(),
                                            ),
                                        ],
                                    ),
                                ],
                            ),
                        ),
                        ft.Container(
                            padding=12,
                            border_radius=14,
                            bgcolor=c_soft_red(),
                            content=ft.Row(
                                spacing=10,
                                controls=[
                                    icon_box(
                                        ft.Icons.RULE_OUTLINED,
                                        color=ACCENT_RED,
                                        background=c_surface(),
                                        size=40,
                                    ),
                                    ft.Column(
                                        expand=True,
                                        spacing=3,
                                        controls=[
                                            ft.Text(
                                                (
                                                    f"{priority_review} "
                                                    "resultados por revisar"
                                                ),
                                                size=11,
                                                color=c_text(),
                                                weight=(
                                                    ft.FontWeight
                                                    .W_900
                                                ),
                                            ),
                                            ft.Text(
                                                (
                                                    "Repetir fotografía "
                                                    "si la confianza es baja."
                                                ),
                                                size=9,
                                                color=c_muted(),
                                            ),
                                        ],
                                    ),
                                ],
                            ),
                        ),
                        ft.OutlinedButton(
                            adaptive=False,
                            content=ft.Text(
                                "ABRIR HISTORIAL COMPLETO",
                                size=10,
                                weight=ft.FontWeight.W_900,
                            ),
                            icon=ft.Icons.HISTORY,
                            height=42,
                            style=ft.ButtonStyle(
                                color=BRAND_GREEN,
                                side=ft.BorderSide(
                                    1,
                                    BRAND_GREEN,
                                ),
                                shape=ft.RoundedRectangleBorder(
                                    radius=12
                                ),
                            ),
                            on_click=lambda _: nav(
                                "/history"
                            ),
                        ),
                    ],
                )
            ),
        )

        quick_panel = ft.Container(
            col={
                "xs": 12,
                "md": 7,
            },
            content=card(
                ft.Column(
                    spacing=13,
                    controls=[
                        ft.Column(
                            spacing=2,
                            controls=[
                                ft.Text(
                                    "Accesos rápidos",
                                    size=15,
                                    color=c_text(),
                                    weight=(
                                        ft.FontWeight
                                        .W_900
                                    ),
                                ),
                                ft.Text(
                                    "Módulos principales de Avoruna",
                                    size=9,
                                    color=c_muted(),
                                ),
                            ],
                        ),
                        ft.ResponsiveRow(
                            spacing=10,
                            run_spacing=10,
                            controls=[
                                quick_action(
                                    "Escanear",
                                    "Analizar una nueva palta Hass",
                                    icon=ft.Icons.PHOTO_CAMERA_OUTLINED,
                                    accent=BRAND_GREEN,
                                    soft_background=c_soft_green(),
                                    route="/scan",
                                ),
                                quick_action(
                                    "Historial",
                                    "Buscar y revisar resultados",
                                    icon=ft.Icons.HISTORY,
                                    accent=ACCENT_BLUE,
                                    soft_background=c_soft_blue(),
                                    route="/history",
                                ),
                                quick_action(
                                    "Reportes",
                                    "Ver indicadores consolidados",
                                    icon=ft.Icons.INSERT_CHART_OUTLINED,
                                    accent=ACCENT_VIOLET,
                                    soft_background=c_soft_violet(),
                                    route="/reports",
                                ),
                            ],
                        ),
                    ],
                )
            ),
        )

        recent_section = ft.Column(
            spacing=10,
            controls=[
                ft.Row(
                    alignment=(
                        ft.MainAxisAlignment
                        .SPACE_BETWEEN
                    ),
                    controls=[
                        ft.Column(
                            spacing=2,
                            controls=[
                                ft.Text(
                                    "Análisis recientes",
                                    size=16,
                                    color=c_text(),
                                    weight=(
                                        ft.FontWeight
                                        .W_900
                                    ),
                                ),
                                ft.Text(
                                    (
                                        "Últimos resultados registrados "
                                        "en el dispositivo"
                                    ),
                                    size=9,
                                    color=c_muted(),
                                ),
                            ],
                        ),
                        ft.TextButton(
                            content=ft.Text(
                                "Ver todos",
                                size=10,
                                color=BRAND_GREEN,
                                weight=ft.FontWeight.W_900,
                            ),
                            on_click=lambda _: nav(
                                "/history"
                            ),
                        ),
                    ],
                ),
                (
                    ft.ResponsiveRow(
                        spacing=12,
                        run_spacing=12,
                        controls=[
                            recent_card(item)
                            for item in sorted_recent
                        ],
                    )
                    if sorted_recent
                    else card(
                        ft.Column(
                            horizontal_alignment=(
                                ft.CrossAxisAlignment
                                .CENTER
                            ),
                            spacing=8,
                            controls=[
                                ft.Icon(
                                    ft.Icons.HISTORY_TOGGLE_OFF,
                                    size=42,
                                    color=BRAND_GREEN,
                                ),
                                ft.Text(
                                    "No hay análisis en este periodo",
                                    size=13,
                                    color=c_text(),
                                    weight=(
                                        ft.FontWeight
                                        .W_900
                                    ),
                                ),
                                ft.Text(
                                    (
                                        "Selecciona otro periodo o "
                                        "realiza un nuevo análisis."
                                    ),
                                    size=9,
                                    color=c_muted(),
                                ),
                            ],
                        )
                    )
                ),
            ],
        )

        dashboard_host.controls = [
            top_banner,
            demo_notice,
            context_bar,
            status_row,
            metrics,
            ft.ResponsiveRow(
                spacing=12,
                run_spacing=12,
                controls=[
                    activity_card,
                    confidence_gauge,
                ],
            ),
            ft.ResponsiveRow(
                spacing=12,
                run_spacing=12,
                controls=[
                    confidence_chart,
                    distribution_card,
                ],
            ),
            ft.ResponsiveRow(
                spacing=12,
                run_spacing=12,
                controls=[
                    priorities,
                    quick_panel,
                ],
            ),
            recent_section,
            ft.Container(
                height=20
            ),
        ]

        if update:
            page.update()

    rebuild_dashboard(
        update=False
    )

    main_column = ft.Column(
        spacing=14,
        scroll=ft.ScrollMode.AUTO,
        controls=[
            dashboard_host,
        ],
    )

    centered_content = ft.Row(
        alignment=ft.MainAxisAlignment.CENTER,
        controls=[
            ft.Container(
                expand=True,
                width=content_max_width,
                padding=ft.Padding(
                    page_padding,
                    page_padding,
                    page_padding,
                    page_padding,
                ),
                content=main_column,
            )
        ],
    )

    root = build_app_shell(
        page,
        centered_content,
    )

    return ft.View(
        route="/dashboard",
        bgcolor=c_bg(),
        padding=0,
        spacing=0,
        controls=[
            ft.SafeArea(
                expand=True,
                content=root,
            ),
        ],
    )
