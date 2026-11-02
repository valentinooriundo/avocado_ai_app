import flet as ft

from services.settings_service import load_theme
from ui.components.app_shell import build_app_shell
from ui.theme_tokens import BRAND_PRIMARY, BRAND_SOFT, text_color, muted_color, border_color, surface_color

BRAND_GREEN = BRAND_PRIMARY
ACCENT_RED = "#B05A7A"


def _is_dark(page: ft.Page) -> bool:
    return page.theme_mode == ft.ThemeMode.DARK


def _screen_mode(page: ft.Page) -> str:
    w = page.width or 1200
    if w < 760:
        return "mobile"
    if w < 1080:
        return "tablet"
    return "desktop"


def _c_surface(page: ft.Page):
    return "#11161C" if _is_dark(page) else "#FFFFFF"


def _c_soft(page: ft.Page):
    return "#171E27" if _is_dark(page) else "#F4F8EF"


def _c_text(page: ft.Page):
    return "#F5F7FA" if _is_dark(page) else "#172018"


def _c_muted(page: ft.Page):
    return "#97A3B6" if _is_dark(page) else "#6B7280"


def _c_border(page: ft.Page):
    return "#253041" if _is_dark(page) else "#DFE8D7"


def _shadow(page: ft.Page):
    return ft.BoxShadow(
        blur_radius=24,
        spread_radius=1,
        color=ft.Colors.with_opacity(0.18 if _is_dark(page) else 0.08, ft.Colors.BLACK),
        offset=ft.Offset(0, 10),
    )


def _card(page: ft.Page, content: ft.Control, padding=16, radius=22, border_color=None):
    return ft.Container(
        padding=ft.Padding(padding, padding, padding, padding),
        border_radius=radius,
        bgcolor=_c_surface(page),
        border=ft.Border.all(1, border_color or _c_border(page)),
        shadow=_shadow(page),
        content=content,
    )


def _soft_card(page: ft.Page, content: ft.Control, padding=14, radius=16):
    return ft.Container(
        padding=ft.Padding(padding, padding, padding, padding),
        border_radius=radius,
        bgcolor=_c_soft(page),
        border=ft.Border.all(1, _c_border(page)),
        content=content,
    )


def _pill_btn(page: ft.Page, label: str, active=False, on_click=None, icon=None):
    row_controls = []
    if icon:
        row_controls.append(ft.Icon(icon, size=12, color=BRAND_GREEN if active else _c_muted(page)))
    row_controls.append(
        ft.Text(
            label,
            size=10,
            color=BRAND_GREEN if active else _c_text(page),
            weight=ft.FontWeight.W_800,
        )
    )

    return ft.Container(
        height=34,
        padding=ft.Padding(12, 0, 12, 0),
        border_radius=10,
        bgcolor=ft.Colors.with_opacity(0.10, ft.Colors.GREEN_400) if active else _c_soft(page),
        border=ft.Border.all(1, _c_border(page)),
        ink=True,
        on_click=on_click,
        alignment=ft.Alignment(0, 0),
        content=ft.Row(
            spacing=6,
            tight=True,
            controls=row_controls,
        ),
    )


def _metric_card(page: ft.Page, title: str, value: str, suffix: str = "", subtitle: str = "", accent=BRAND_GREEN, border_color=None):
    controls = [
        ft.Text(title, size=10, color=_c_muted(page), weight=ft.FontWeight.W_900),
        ft.Row(
            spacing=4,
            vertical_alignment=ft.CrossAxisAlignment.END,
            controls=[
                ft.Text(value, size=28, color=accent, weight=ft.FontWeight.W_900),
                ft.Text(suffix, size=14, color=_c_text(page), weight=ft.FontWeight.W_800) if suffix else ft.Container(),
            ],
        ),
        ft.Text(subtitle, size=10, color=_c_muted(page), weight=ft.FontWeight.W_700),
    ]

    return _card(
        page,
        ft.Column(spacing=10, controls=controls),
        padding=18,
        radius=18,
        border_color=border_color,
    )


def _progress_line(page: ft.Page, value: float, color: str = BRAND_GREEN, total=100):
    fill = max(8, int(total * max(0.0, min(1.0, value))))
    return ft.Stack(
        height=8,
        controls=[
            ft.Container(
                width=total,
                height=4,
                top=2,
                border_radius=999,
                bgcolor=ft.Colors.with_opacity(0.10, ft.Colors.BLACK if not _is_dark(page) else ft.Colors.WHITE),
            ),
            ft.Container(
                width=fill,
                height=4,
                top=2,
                border_radius=999,
                bgcolor=color,
            ),
        ],
    )


def _status_badge(page: ft.Page, label: str, kind: str):
    if kind == "good":
        bg = ft.Colors.with_opacity(0.12, ft.Colors.GREEN_400)
        color = BRAND_GREEN
    elif kind == "danger":
        bg = ft.Colors.with_opacity(0.12, ft.Colors.PINK_200)
        color = ACCENT_RED
    else:
        bg = ft.Colors.with_opacity(0.08, ft.Colors.GREY_300)
        color = _c_muted(page)

    return ft.Container(
        padding=ft.Padding(10, 4, 10, 4),
        border_radius=999,
        bgcolor=bg,
        content=ft.Text(
            label,
            size=8,
            color=color,
            weight=ft.FontWeight.W_900,
        ),
    )


def _parcel_row(page: ft.Page, lote: str, variedad: str, area: str, madurez: int, estado: str, estado_kind: str):
    bar_color = BRAND_GREEN if estado_kind == "good" else ACCENT_RED if estado_kind == "danger" else "#B8C5B0"

    return ft.Container(
        padding=ft.Padding(10, 12, 10, 12),
        border_radius=12,
        bgcolor=_c_surface(page),
        border=ft.Border.all(1, _c_border(page)),
        content=ft.Row(
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Container(
                    width=38,
                    content=ft.Text(
                        lote,
                        size=11,
                        color=_c_text(page),
                        weight=ft.FontWeight.W_800,
                    ),
                ),
                ft.Container(
                    width=74,
                    content=ft.Text(variedad, size=10, color=_c_muted(page), weight=ft.FontWeight.W_700),
                ),
                ft.Container(
                    width=56,
                    content=ft.Text(area, size=10, color=_c_text(page), weight=ft.FontWeight.W_700),
                ),
                ft.Container(
                    expand=True,
                    content=ft.Row(
                        spacing=10,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            _progress_line(page, madurez / 100.0, color=bar_color, total=76),
                            ft.Text(f"{madurez}%", size=10, color=_c_text(page), weight=ft.FontWeight.W_800),
                        ],
                    ),
                ),
                _status_badge(page, estado, estado_kind),
            ],
        ),
    )


def _heat_cell(color: str):
    return ft.Container(
        width=26,
        height=26,
        border_radius=4,
        bgcolor=color,
        border=ft.Border.all(1, ft.Colors.with_opacity(0.08, ft.Colors.BLACK)),
    )


def _map_pin(page: ft.Page, icon):
    return ft.Container(
        width=36,
        height=36,
        border_radius=999,
        bgcolor=_c_surface(page),
        border=ft.Border.all(1, _c_border(page)),
        alignment=ft.Alignment(0, 0),
        content=ft.Icon(icon, size=16, color=_c_muted(page)),
    )


def create_parcelas_view(page: ft.Page) -> ft.View:
    db = page.data.get("db")
    if db is not None:
        saved = load_theme(db)
        page.theme_mode = ft.ThemeMode.DARK if saved == "dark" else ft.ThemeMode.LIGHT

    mode = _screen_mode(page)
    is_mobile = mode == "mobile"

    active_variedad = {"value": "Variedad"}
    active_order = {"value": "Ordenar"}

    def show_message(msg: str):
        page.snack_bar = ft.SnackBar(ft.Text(msg))
        page.snack_bar.open = True
        page.update()

    search_tf = ft.TextField(
        hint_text="Buscar lote...",
        dense=True,
        height=38,
        width=200 if mode == "desktop" else None,
        expand=False if mode == "desktop" else True,
        border_radius=999,
        text_size=11,
        bgcolor=ft.Colors.with_opacity(0.06, ft.Colors.BLACK if not _is_dark(page) else ft.Colors.WHITE),
        border=ft.InputBorder.NONE,
        prefix_icon=ft.Icons.SEARCH,
    )

    title_block = ft.Column(
        spacing=2,
        controls=[
            ft.Text("Gestión de Parcelas", size=16 if is_mobile else 18, color=_c_text(page), weight=ft.FontWeight.W_900),
        ],
    )

    top_right = ft.Row(
        spacing=10,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            search_tf,
            ft.Icon(ft.Icons.NOTIFICATIONS_NONE_OUTLINED, size=18, color=_c_text(page)),
            ft.Text("7", size=10, color=BRAND_GREEN, weight=ft.FontWeight.W_900),
            ft.CircleAvatar(
                radius=14,
                bgcolor=ft.Colors.with_opacity(0.18, BRAND_GREEN),
                content=ft.Text("V", size=11, color=BRAND_GREEN, weight=ft.FontWeight.W_900),
            ),
        ],
    )

    if mode == "desktop":
        header_block = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[title_block, top_right],
        )
    else:
        header_block = ft.Column(
            spacing=10,
            controls=[
                title_block,
                search_tf,
                ft.Row(
                    alignment=ft.MainAxisAlignment.END,
                    controls=[
                        ft.Icon(ft.Icons.NOTIFICATIONS_NONE_OUTLINED, size=18, color=_c_text(page)),
                        ft.CircleAvatar(
                            radius=14,
                            bgcolor=ft.Colors.with_opacity(0.18, BRAND_GREEN),
                            content=ft.Text("V", size=11, color=BRAND_GREEN, weight=ft.FontWeight.W_900),
                        ),
                    ],
                ),
            ],
        )

    cards = [
        _metric_card(page, "TOTAL HECTARES", "142.5", "ha", "+ 2.4% este mes", accent=_c_text(page)),
        _card(
            page,
            ft.Column(
                spacing=10,
                controls=[
                    ft.Text("AVG RIPENESS", size=10, color=_c_muted(page), weight=ft.FontWeight.W_900),
                    ft.Row(
                        spacing=4,
                        vertical_alignment=ft.CrossAxisAlignment.END,
                        controls=[
                            ft.Text("68", size=28, color=_c_text(page), weight=ft.FontWeight.W_900),
                            ft.Text("%", size=14, color=_c_text(page), weight=ft.FontWeight.W_800),
                        ],
                    ),
                    _progress_line(page, 0.68, color=BRAND_GREEN, total=92),
                ],
            ),
            padding=18,
            radius=18,
        ),
        _metric_card(
            page,
            "CRITICAL ALERTS",
            "03",
            "",
            "Acción Requerida",
            accent=ACCENT_RED,
            border_color=ACCENT_RED if not _is_dark(page) else "#563145",
        ),
    ]

    if mode == "desktop":
        metrics_block = ft.Row(
            spacing=14,
            controls=[
                ft.Container(expand=True, content=cards[0]),
                ft.Container(expand=True, content=cards[1]),
                ft.Container(expand=True, content=cards[2]),
            ],
        )
    elif mode == "tablet":
        metrics_block = ft.Column(
            spacing=14,
            controls=[
                ft.Row(
                    spacing=14,
                    controls=[
                        ft.Container(expand=True, content=cards[0]),
                        ft.Container(expand=True, content=cards[1]),
                    ],
                ),
                cards[2],
            ],
        )
    else:
        metrics_block = ft.Column(
            spacing=14,
            controls=cards,
        )

    filter_row = ft.Row(
        spacing=8,
        controls=[
            _pill_btn(
                page,
                active_variedad["value"],
                active=False,
                icon=ft.Icons.FILTER_ALT_OUTLINED,
                on_click=lambda _: show_message("Filtro por variedad pendiente."),
            ),
            _pill_btn(
                page,
                active_order["value"],
                active=False,
                icon=ft.Icons.SWAP_VERT,
                on_click=lambda _: show_message("Ordenamiento pendiente."),
            ),
        ],
    )

    table_header = ft.Row(
        controls=[
            ft.Container(width=38, content=ft.Text("LOTE / ID", size=9, color=_c_muted(page), weight=ft.FontWeight.W_900)),
            ft.Container(width=74, content=ft.Text("VARIEDAD", size=9, color=_c_muted(page), weight=ft.FontWeight.W_900)),
            ft.Container(width=56, content=ft.Text("ÁREA", size=9, color=_c_muted(page), weight=ft.FontWeight.W_900)),
            ft.Container(expand=True, content=ft.Text("MADURACIÓN", size=9, color=_c_muted(page), weight=ft.FontWeight.W_900)),
            ft.Text("ESTADO", size=9, color=_c_muted(page), weight=ft.FontWeight.W_900),
        ],
    )

    table_rows = ft.Column(
        spacing=10,
        controls=[
            _parcel_row(page, "L1", "Hass", "24.5 ha", 85, "Saludable", "good"),
            _parcel_row(page, "L4", "Fuerte", "18.2 ha", 42, "Estado crítico", "danger"),
            _parcel_row(page, "L2", "Hass", "32.0 ha", 72, "Saludable", "good"),
            _parcel_row(page, "L9", "Hass", "15.8 ha", 16, "Reposo", "muted"),
        ],
    )

    left_block = _card(
        page,
        ft.Column(
            spacing=14,
            controls=[
                ft.Text("Active Parcels", size=15, color=_c_text(page), weight=ft.FontWeight.W_900),
                ft.Text("Monitoreo detallado de lotes en producción", size=11, color=_c_muted(page)),
                filter_row,
                ft.Container(height=1, bgcolor=_c_border(page)),
                table_header,
                table_rows,
            ],
        ),
        padding=16,
        radius=18,
    )

    heat_grid = ft.Column(
        spacing=4,
        controls=[
            ft.Row(spacing=4, controls=[_heat_cell("#47D61F"), _heat_cell("#54DF28"), _heat_cell("#39C714"), _heat_cell("#70E355"), _heat_cell("#93E982")]),
            ft.Row(spacing=4, controls=[_heat_cell("#4DD91E"), _heat_cell("#F1BED0"), _heat_cell("#E89DB9"), _heat_cell("#4DD91E"), _heat_cell("#86E772")]),
            ft.Row(spacing=4, controls=[_heat_cell("#39C714"), _heat_cell("#4DD91E"), _heat_cell("#70E355"), _heat_cell("#72E45A"), _heat_cell("#41C919")]),
            ft.Row(spacing=4, controls=[_heat_cell("#D8E8CF"), _heat_cell("#DCEBD5"), _heat_cell("#D2E5C8"), _heat_cell("#BCE0AF"), _heat_cell("#D8E8CF")]),
            ft.Row(spacing=4, controls=[_heat_cell("#DCEBD5"), _heat_cell("#E1EDD9"), _heat_cell("#D6E8CF"), _heat_cell("#C5E2B8"), _heat_cell("#E1EDD9")]),
        ],
    )

    right_block = _card(
        page,
        ft.Column(
            spacing=14,
            controls=[
                ft.Text("Ripeness Heat Map", size=15, color=_c_text(page), weight=ft.FontWeight.W_900),
                ft.Text("Vista satelital de maduración por cuadrante", size=11, color=_c_muted(page)),
                heat_grid,
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text("BAJA(0%)", size=8, color=_c_muted(page), weight=ft.FontWeight.W_800),
                        ft.Text("ALTA(100%)", size=8, color=_c_muted(page), weight=ft.FontWeight.W_800),
                    ],
                ),
                _progress_line(page, 0.70, color=BRAND_GREEN, total=110),
                ft.Container(height=1, bgcolor=_c_border(page)),
                ft.Row(
                    spacing=8,
                    controls=[
                        ft.Icon(ft.Icons.LOCATION_ON_OUTLINED, size=14, color=ACCENT_RED),
                        ft.Text("Agronomic Recommendation", size=10, color=ACCENT_RED, weight=ft.FontWeight.W_900),
                    ],
                ),
                ft.Text(
                    "Sector B2 / Lote Sur muestra niveles de maduración cercanos a índices de sobre-madurez. "
                    "Se recomienda activar cosecha 48 hrs.",
                    size=10,
                    color=_c_muted(page),
                ),
                ft.Container(
                    height=36,
                    border_radius=10,
                    bgcolor=ft.Colors.with_opacity(0.10, ft.Colors.GREEN_400),
                    alignment=ft.Alignment(0, 0),
                    content=ft.Text("Ver Reporte Térmico Completo", size=10, color=BRAND_GREEN, weight=ft.FontWeight.W_800),
                ),
            ],
        ),
        padding=16,
        radius=18,
    )

    if mode == "desktop":
        middle_block = ft.Row(
            spacing=14,
            vertical_alignment=ft.CrossAxisAlignment.START,
            controls=[
                ft.Container(expand=3, content=left_block),
                ft.Container(expand=2, content=right_block),
            ],
        )
    else:
        middle_block = ft.Column(
            spacing=14,
            controls=[left_block, right_block],
        )

    map_area = _card(
        page,
        ft.Stack(
            controls=[
                ft.Container(
                    height=320 if mode == "desktop" else 260,
                    border_radius=18,
                    bgcolor="#D9E4C6",
                    content=ft.Stack(
                        controls=[
                            ft.Container(width=560, height=220, left=0, top=0, bgcolor="#D8E2C3"),
                            ft.Container(width=460, height=180, left=110, top=28, border_radius=140, bgcolor="#9EB882"),
                            ft.Container(width=180, height=120, left=150, top=70, border_radius=80, bgcolor="#BFD0A6"),
                            ft.Container(width=52, height=52, left=250, top=94, border_radius=8, bgcolor="#59C2C8"),
                            ft.Container(width=220, height=4, left=30, top=44, bgcolor="#DAD3B0", rotate=0.4),
                            ft.Container(width=240, height=4, left=90, top=190, bgcolor="#CABD8D", rotate=-0.4),
                            ft.Container(width=180, height=4, left=280, top=150, bgcolor="#CFC596", rotate=0.6),
                        ],
                    ),
                ),
                ft.Container(
                    left=16,
                    bottom=16,
                    content=_soft_card(
                        page,
                        ft.Column(
                            spacing=6,
                            controls=[
                                ft.Text("Live Field Telemetry", size=11, color=_c_text(page), weight=ft.FontWeight.W_800),
                                ft.Row(
                                    spacing=18,
                                    controls=[
                                        ft.Column(
                                            spacing=2,
                                            controls=[
                                                ft.Text("HUMIDITY", size=8, color=_c_muted(page), weight=ft.FontWeight.W_900),
                                                ft.Text("64%", size=18, color=_c_text(page), weight=ft.FontWeight.W_900),
                                            ],
                                        ),
                                        ft.Column(
                                            spacing=2,
                                            controls=[
                                                ft.Text("WIND SPEED", size=8, color=_c_muted(page), weight=ft.FontWeight.W_900),
                                                ft.Text("12 km/h", size=18, color=_c_text(page), weight=ft.FontWeight.W_900),
                                            ],
                                        ),
                                    ],
                                ),
                            ],
                        ),
                        padding=12,
                        radius=14,
                    ),
                ),
                ft.Container(
                    right=16,
                    top=16,
                    width=46,
                    height=46,
                    border_radius=999,
                    bgcolor="#168F00",
                    alignment=ft.Alignment(0, 0),
                    content=ft.Icon(ft.Icons.ADD, size=20, color=ft.Colors.WHITE),
                ),
                ft.Container(
                    right=18,
                    bottom=18,
                    content=ft.Column(
                        spacing=10,
                        controls=[
                            _map_pin(page, ft.Icons.MY_LOCATION),
                            _map_pin(page, ft.Icons.SEARCH),
                        ],
                    ),
                ),
            ],
        ),
        padding=12,
        radius=18,
    )

    parcelas_content = ft.Container(
        expand=True,
        content=ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=16,
            controls=[
                header_block,
                metrics_block,
                middle_block,
                map_area,
                ft.Container(height=18),
            ],
        ),
    )

    root = build_app_shell(page, parcelas_content)

    return ft.View(
        route="/parcelas",
        controls=[
            ft.SafeArea(expand=True, content=root),
        ],
    )
