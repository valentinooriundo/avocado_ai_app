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


def _metric_card(page: ft.Page, title: str, value: str, suffix: str = "", subtitle: str = "", accent=BRAND_GREEN, border_color=None):
    value_row_controls = [
        ft.Text(value, size=28, color=accent, weight=ft.FontWeight.W_900),
    ]
    if suffix:
        value_row_controls.append(
            ft.Text(suffix, size=15, color=_c_text(page), weight=ft.FontWeight.W_800)
        )

    return _card(
        page,
        ft.Column(
            spacing=10,
            controls=[
                ft.Text(title, size=10, color=_c_muted(page), weight=ft.FontWeight.W_900),
                ft.Row(
                    spacing=6,
                    vertical_alignment=ft.CrossAxisAlignment.END,
                    controls=value_row_controls,
                ),
                ft.Text(subtitle, size=10, color=_c_muted(page), weight=ft.FontWeight.W_700),
            ],
        ),
        padding=18,
        radius=18,
        border_color=border_color,
    )


def _progress_line(page: ft.Page, value: float, color: str = BRAND_GREEN):
    total = 180
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


def _badge(page: ft.Page, text: str, bg=None, color=None):
    return ft.Container(
        padding=ft.Padding(10, 4, 10, 4),
        border_radius=999,
        bgcolor=bg or ft.Colors.with_opacity(0.10, ft.Colors.GREEN_400),
        content=ft.Text(
            text,
            size=8,
            color=color or BRAND_GREEN,
            weight=ft.FontWeight.W_900,
        ),
    )


def _farm_card(page: ft.Page, title: str, subtitle: str, area: str, status: str, status_bg, status_color, maturity: int, image_style: str):
    if image_style == "gold":
        art = ft.Container(
            height=120,
            border_radius=14,
            bgcolor="#1C1A16",
            content=ft.Stack(
                controls=[
                    ft.Container(
                        width=44,
                        height=92,
                        border_radius=12,
                        bgcolor="#7A5A22",
                        left=26,
                        top=16,
                    ),
                    ft.Container(
                        width=32,
                        height=74,
                        border_radius=999,
                        bgcolor="#B99138",
                        left=32,
                        top=24,
                    ),
                    ft.Container(
                        width=18,
                        height=18,
                        border_radius=999,
                        bgcolor="#E6D18A",
                        left=39,
                        top=18,
                    ),
                ],
            ),
        )
    elif image_style == "church":
        art = ft.Container(
            height=120,
            border_radius=14,
            bgcolor="#2C3F52",
            content=ft.Stack(
                controls=[
                    ft.Container(
                        width=84,
                        height=52,
                        bgcolor="#D0A85E",
                        left=28,
                        top=48,
                    ),
                    ft.Container(
                        width=44,
                        height=72,
                        bgcolor="#9A7340",
                        left=48,
                        top=28,
                    ),
                    ft.Container(
                        width=18,
                        height=18,
                        bgcolor="#5C3B18",
                        left=61,
                        top=68,
                    ),
                    ft.Container(
                        width=0,
                        height=0,
                        left=38,
                        top=18,
                    ),
                ],
            ),
        )
    else:
        art = ft.Container(
            height=120,
            border_radius=14,
            bgcolor="#0F2230",
            content=ft.Stack(
                controls=[
                    ft.Container(
                        width=68,
                        height=68,
                        border_radius=999,
                        border=ft.Border.all(6, "#F4F4F2"),
                        left=44,
                        top=20,
                    ),
                    ft.Container(
                        width=18,
                        height=50,
                        bgcolor="#0F2230",
                        left=69,
                        top=54,
                    ),
                ],
            ),
        )

    return _card(
        page,
        ft.Column(
            spacing=10,
            controls=[
                ft.Stack(
                    controls=[
                        art,
                        ft.Container(
                            right=10,
                            top=10,
                            content=_badge(page, status, bg=status_bg, color=status_color),
                        ),
                    ],
                ),
                ft.Text(title, size=14, color=_c_text(page), weight=ft.FontWeight.W_900),
                ft.Row(
                    spacing=8,
                    controls=[
                        ft.Icon(ft.Icons.LOCATION_ON_OUTLINED, size=14, color=_c_muted(page)),
                        ft.Text(subtitle, size=10, color=_c_muted(page)),
                        ft.Text(area, size=10, color=_c_muted(page), weight=ft.FontWeight.W_700),
                    ],
                ),
                ft.Container(height=1, bgcolor=_c_border(page)),
                ft.Text("MADUREZ ACTUAL", size=9, color=_c_muted(page), weight=ft.FontWeight.W_900),
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        _progress_line(page, maturity / 100.0, color=status_color if status == "CRÍTICO" else BRAND_GREEN),
                        ft.Text(f"{maturity}%", size=18, color=status_color if status == "CRÍTICO" else _c_text(page), weight=ft.FontWeight.W_900),
                    ],
                ),
            ],
        ),
        padding=10,
        radius=18,
    )


def _heat_cell(color: str):
    return ft.Container(
        width=30,
        height=30,
        border_radius=4,
        bgcolor=color,
        border=ft.Border.all(1, ft.Colors.with_opacity(0.08, ft.Colors.BLACK)),
    )


def _legend_item(page: ft.Page, color: str, text: str):
    return ft.Row(
        spacing=6,
        controls=[
            ft.Container(width=8, height=8, border_radius=999, bgcolor=color),
            ft.Text(text, size=9, color=_c_muted(page)),
        ],
    )


def create_fincas_view(page: ft.Page) -> ft.View:
    db = page.data.get("db")
    if db is not None:
        saved = load_theme(db)
        page.theme_mode = ft.ThemeMode.DARK if saved == "dark" else ft.ThemeMode.LIGHT

    mode = _screen_mode(page)
    is_mobile = mode == "mobile"
    is_tablet = mode == "tablet"

    title_block = ft.Column(
        spacing=2,
        controls=[
            ft.Text("Gestión de Fincas y Parcelas", size=16 if is_mobile else 18, color=_c_text(page), weight=ft.FontWeight.W_900),
            ft.Text("Monitoreo en tiempo real de la vitalidad y madurez de su producción.", size=12, color=_c_muted(page)),
        ],
    )

    action_row = ft.Row(
        spacing=10,
        controls=[
            ft.Icon(ft.Icons.NOTIFICATIONS_NONE_OUTLINED, size=18, color=_c_text(page)),
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
            controls=[title_block, action_row],
        )
    else:
        header_block = ft.Column(
            spacing=10,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[title_block, action_row],
                )
            ],
        )

    top_cards = [
        _metric_card(
            page,
            "HECTÁREAS TOTALES",
            "1,240",
            "",
            "+ 12% vs año anterior",
            accent="#1C7C0D",
        ),
        _card(
            page,
            ft.Column(
                spacing=10,
                controls=[
                    ft.Text("MADUREZ PROMEDIO", size=10, color=_c_muted(page), weight=ft.FontWeight.W_900),
                    ft.Row(
                        spacing=4,
                        vertical_alignment=ft.CrossAxisAlignment.END,
                        controls=[
                            ft.Text("78", size=28, color=_c_text(page), weight=ft.FontWeight.W_900),
                            ft.Text("%", size=15, color=_c_text(page), weight=ft.FontWeight.W_800),
                        ],
                    ),
                    ft.Row(
                        spacing=10,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            _progress_line(page, 0.78, color=BRAND_GREEN),
                            ft.Text("Óptimo", size=10, color=_c_muted(page), weight=ft.FontWeight.W_700),
                        ],
                    ),
                ],
            ),
            padding=18,
            radius=18,
        ),
        _metric_card(
            page,
            "ALERTAS ACTIVAS",
            "04",
            "",
            "Requieren acción inmediata",
            accent=ACCENT_RED,
            border_color=ACCENT_RED if not _is_dark(page) else "#563145",
        ),
    ]

    if mode == "desktop":
        metrics_block = ft.Row(
            spacing=14,
            controls=[
                ft.Container(expand=True, content=top_cards[0]),
                ft.Container(expand=True, content=top_cards[1]),
                ft.Container(expand=True, content=top_cards[2]),
            ],
        )
    elif mode == "tablet":
        metrics_block = ft.Column(
            spacing=14,
            controls=[
                ft.Row(
                    spacing=14,
                    controls=[
                        ft.Container(expand=True, content=top_cards[0]),
                        ft.Container(expand=True, content=top_cards[1]),
                    ],
                ),
                top_cards[2],
            ],
        )
    else:
        metrics_block = ft.Column(
            spacing=14,
            controls=top_cards,
        )

    explore_header = ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Text("Explorar Unidades de Producción", size=15, color=_c_text(page), weight=ft.FontWeight.W_900),
            ft.Row(
                spacing=8,
                controls=[
                    ft.Icon(ft.Icons.GRID_VIEW, size=16, color=BRAND_GREEN),
                    ft.Icon(ft.Icons.VIEW_LIST, size=16, color=_c_muted(page)),
                ],
            ),
        ],
    )

    farm_cards = [
        _farm_card(
            page,
            "Chacra Piñeros",
            "Variedad: Hass",
            "450 ha",
            "ÓPTIMO",
            ft.Colors.with_opacity(0.12, ft.Colors.GREEN_400),
            BRAND_GREEN,
            82,
            "gold",
        ),
        _farm_card(
            page,
            "San José de los Molinos",
            "Variedad: Fuerte",
            "580 ha",
            "EN PROCESO",
            ft.Colors.with_opacity(0.14, ft.Colors.BLUE_300),
            "#6A7A8A",
            65,
            "church",
        ),
        _farm_card(
            page,
            "Parcela Norte",
            "Variedad: Hass",
            "210 ha",
            "CRÍTICO",
            ft.Colors.with_opacity(0.14, ft.Colors.PINK_200),
            ACCENT_RED,
            91,
            "drop",
        ),
    ]

    if mode == "desktop":
        farms_block = ft.Row(
            spacing=14,
            controls=[
                ft.Container(expand=True, content=farm_cards[0]),
                ft.Container(expand=True, content=farm_cards[1]),
                ft.Container(expand=True, content=farm_cards[2]),
            ],
        )
    else:
        farms_block = ft.Column(
            spacing=14,
            controls=farm_cards,
        )

    heat_grid = ft.Column(
        spacing=4,
        controls=[
            ft.Row(spacing=4, controls=[_heat_cell("#8DBF74"), _heat_cell("#B6C7A8"), _heat_cell("#76A861"), _heat_cell("#D3D9C9"), _heat_cell("#4DD91E"), _heat_cell("#CDD9C4"), _heat_cell("#8CB778"), _heat_cell("#B6C7A8")]),
            ft.Row(spacing=4, controls=[_heat_cell("#D2D8C8"), _heat_cell("#B882A2"), _heat_cell("#D9DECF"), _heat_cell("#A8C495"), _heat_cell("#3DAF1C"), _heat_cell("#C3D0B8"), _heat_cell("#BFD0B2"), _heat_cell("#89B56F")]),
            ft.Row(spacing=4, controls=[_heat_cell("#8CB778"), _heat_cell("#C8D4BF"), _heat_cell("#8FB77D"), _heat_cell("#D7DBCE"), _heat_cell("#8CB778"), _heat_cell("#D2D9CA"), _heat_cell("#BFD0B2"), _heat_cell("#D6DCD0")]),
            ft.Row(spacing=4, controls=[_heat_cell("#D8DDCF"), _heat_cell("#C2D2B6"), _heat_cell("#B1C59F"), _heat_cell("#D5B6C0"), _heat_cell("#3D9227"), _heat_cell("#D9DECF"), _heat_cell("#C8D4BF"), _heat_cell("#B1C59F")]),
            ft.Row(spacing=4, controls=[_heat_cell("#C0CFB7"), _heat_cell("#D8DDCF"), _heat_cell("#D5DCCD"), _heat_cell("#4D992D"), _heat_cell("#D9DECF"), _heat_cell("#B1C59F"), _heat_cell("#8CB778"), _heat_cell("#D2D9CA")]),
        ],
    )

    heat_left = ft.Column(
        spacing=12,
        controls=[
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Column(
                        spacing=2,
                        controls=[
                            ft.Text("Mapa de Calor de Madurez por Cuadrante", size=15, color=_c_text(page), weight=ft.FontWeight.W_900),
                            ft.Text("Distribución geoespacial basada en índices NDVI y muestreo directo.", size=11, color=_c_muted(page)),
                        ],
                    ),
                    ft.Row(
                        spacing=8,
                        controls=[
                            _badge(page, "Vista Satelital", bg=ft.Colors.with_opacity(0.10, ft.Colors.GREEN_400), color=BRAND_GREEN),
                            _badge(page, "Topográfico", bg=ft.Colors.with_opacity(0.06, ft.Colors.BLACK if not _is_dark(page) else ft.Colors.WHITE), color=_c_muted(page)),
                        ],
                    ),
                ],
            ),
            _soft_card(
                page,
                ft.Column(
                    spacing=12,
                    controls=[
                        heat_grid,
                        ft.Row(
                            spacing=16,
                            controls=[
                                _legend_item(page, "#8CB778", "ÓPTIMO"),
                                _legend_item(page, "#4DD91E", "COSECHA TEMPRANA"),
                                _legend_item(page, "#B882A2", "SOBREMADURO"),
                            ],
                        ),
                    ],
                ),
                padding=12,
                radius=16,
            ),
        ],
    )

    heat_right = ft.Column(
        spacing=12,
        controls=[
            _soft_card(
                page,
                ft.Column(
                    spacing=8,
                    controls=[
                        ft.Text("ZONA CRÍTICA", size=9, color=_c_muted(page), weight=ft.FontWeight.W_900),
                        ft.Text("Cuadrante N-12", size=14, color=_c_text(page), weight=ft.FontWeight.W_900),
                        ft.Text(
                            "Alta madurez detectada. Se recomienda iniciar recolección en las próximas 48 hs.",
                            size=10,
                            color=_c_muted(page),
                        ),
                        ft.Container(
                            height=34,
                            border_radius=10,
                            bgcolor=ft.Colors.with_opacity(0.08, ft.Colors.PINK_200),
                            alignment=ft.Alignment(0, 0),
                            content=ft.Text("Ver detalles", size=10, color=ACCENT_RED, weight=ft.FontWeight.W_800),
                        ),
                    ],
                ),
                padding=12,
                radius=14,
            ),
            _soft_card(
                page,
                ft.Column(
                    spacing=8,
                    controls=[
                        ft.Text("RENDIMIENTO PROYECTADO", size=9, color=_c_muted(page), weight=ft.FontWeight.W_900),
                        ft.Row(
                            spacing=4,
                            vertical_alignment=ft.CrossAxisAlignment.END,
                            controls=[
                                ft.Text("12.5", size=24, color="#1C7C0D", weight=ft.FontWeight.W_900),
                                ft.Text("TON/HA", size=10, color=_c_muted(page), weight=ft.FontWeight.W_800),
                            ],
                        ),
                    ],
                ),
                padding=12,
                radius=14,
            ),
        ],
    )

    if mode == "desktop":
        heatmap_block = ft.Row(
            spacing=14,
            vertical_alignment=ft.CrossAxisAlignment.START,
            controls=[
                ft.Container(expand=3, content=heat_left),
                ft.Container(expand=1, content=heat_right),
            ],
        )
    else:
        heatmap_block = ft.Column(
            spacing=14,
            controls=[heat_left, heat_right],
        )

    fincas_content = ft.Container(
        expand=True,
        content=ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=16,
            controls=[
                header_block,
                metrics_block,
                explore_header,
                farms_block,
                heatmap_block,
                ft.Container(height=18),
            ],
        ),
    )

    root = build_app_shell(page, fincas_content)

    return ft.View(
        route="/fincas",
        controls=[
            ft.SafeArea(expand=True, content=root),
        ],
    )
