import flet as ft


# =========================================================
# PALETA PRINCIPAL AVORUNA
# =========================================================

BRAND_GREEN = "#39D80C"

GREEN_DARK = "#216B38"
GREEN_DEEP = "#174C2A"
GREEN_SOFT = "#ECF9E8"

LIGHT_BACKGROUND = "#F5FAF2"
LIGHT_SURFACE = "#FFFFFF"
LIGHT_BORDER = "#E3ECE0"
LIGHT_TEXT = "#1B211D"
LIGHT_MUTED = "#6B746E"

DARK_BACKGROUND = "#0F1310"
DARK_SURFACE = "#141A16"
DARK_BORDER = "#29322C"
DARK_TEXT = "#F2F5F3"
DARK_MUTED = "#9CA8A0"


def build_app_shell(page: ft.Page, content: ft.Control) -> ft.Control:
    """
    Construye la estructura principal de Avoruna.

    - Sidebar fijo para escritorio.
    - Navegación horizontal para pantallas pequeñas.
    - Identificación automática de la ruta activa.
    - Compatibilidad con modo claro y oscuro.
    """

    is_dark = page.theme_mode == ft.ThemeMode.DARK
    page_width = page.width or 1200

    is_compact = page_width < 850

    # =====================================================
    # COLORES SEGÚN TEMA
    # =====================================================

    background_color = DARK_BACKGROUND if is_dark else LIGHT_BACKGROUND
    sidebar_color = DARK_SURFACE if is_dark else LIGHT_SURFACE
    border_color = DARK_BORDER if is_dark else LIGHT_BORDER
    text_color = DARK_TEXT if is_dark else LIGHT_TEXT
    muted_color = DARK_MUTED if is_dark else LIGHT_MUTED

    active_background = "#17321F" if is_dark else GREEN_SOFT
    active_text_color = "#8DEA73" if is_dark else GREEN_DEEP

    card_green = "#193522" if is_dark else "#F0F9ED"

    # =====================================================
    # NAVEGACIÓN
    # =====================================================

    def navigate(route: str):
        if page.route != route:
            page.run_task(page.push_route, route)

    def is_active(route: str) -> bool:
        current_route = page.route or "/dashboard"

        if route == "/dashboard":
            return current_route in (
                "/dashboard",
                "/home",
                "/",
            )

        return current_route.startswith(route)

    navigation_items = [
        {
            "label": "Inicio",
            "route": "/dashboard",
            "icon": ft.Icons.DASHBOARD_OUTLINED,
            "active_icon": ft.Icons.DASHBOARD_ROUNDED,
        },
        {
            "label": "Escaneo",
            "route": "/scan",
            "icon": ft.Icons.PHOTO_CAMERA_OUTLINED,
            "active_icon": ft.Icons.PHOTO_CAMERA,
        },
        {
            "label": "Historial",
            "route": "/history",
            "icon": ft.Icons.HISTORY,
            "active_icon": ft.Icons.HISTORY_ROUNDED,
        },
        {
            "label": "Reportes",
            "route": "/reports",
            "icon": ft.Icons.INSERT_CHART_OUTLINED,
            "active_icon": ft.Icons.INSERT_CHART_ROUNDED,
        },
        {
            "label": "Configuración",
            "route": "/settings",
            "icon": ft.Icons.SETTINGS_OUTLINED,
            "active_icon": ft.Icons.SETTINGS_ROUNDED,
        },
    ]

    # =====================================================
    # ELEMENTO DEL SIDEBAR
    # =====================================================

    def sidebar_item(item: dict) -> ft.Control:
        active = is_active(item["route"])

        icon_color = active_text_color if active else muted_color
        label_color = active_text_color if active else text_color

        return ft.Container(
            height=48,
            border_radius=12,
            bgcolor=active_background if active else None,
            border=(
                ft.Border(
                    left=ft.BorderSide(4, BRAND_GREEN),
                )
                if active
                else None
            ),
            padding=ft.Padding(
                10 if active else 14,
                0,
                12,
                0,
            ),
            ink=True,
            on_click=lambda _, route=item["route"]: navigate(route),
            content=ft.Row(
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Container(
                        width=32,
                        height=32,
                        border_radius=10,
                        alignment=ft.Alignment.CENTER,
                        bgcolor=(
                            ft.Colors.with_opacity(
                                0.13,
                                BRAND_GREEN,
                            )
                            if active
                            else None
                        ),
                        content=ft.Icon(
                            item["active_icon"] if active else item["icon"],
                            size=20,
                            color=icon_color,
                        ),
                    ),
                    ft.Text(
                        item["label"],
                        size=13,
                        weight=(
                            ft.FontWeight.W_800
                            if active
                            else ft.FontWeight.W_600
                        ),
                        color=label_color,
                    ),
                    ft.Container(expand=True),
                    (
                        ft.Icon(
                            ft.Icons.CHEVRON_RIGHT_ROUNDED,
                            size=17,
                            color=active_text_color,
                        )
                        if active
                        else ft.Container(width=17)
                    ),
                ],
            ),
        )

    # =====================================================
    # MARCA AVORUNA
    # =====================================================

    brand_header = ft.Container(
        padding=ft.Padding(20, 22, 18, 18),
        content=ft.Row(
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Container(
                    width=46,
                    height=46,
                    border_radius=14,
                    bgcolor=GREEN_SOFT if not is_dark else "#193522",
                    alignment=ft.Alignment.CENTER,
                    content=ft.Icon(
                        ft.Icons.ECO_OUTLINED,
                        size=25,
                        color=GREEN_DARK if not is_dark else BRAND_GREEN,
                    ),
                ),
                ft.Column(
                    expand=True,
                    spacing=2,
                    controls=[
                        ft.Text(
                            "Avoruna",
                            size=19,
                            weight=ft.FontWeight.W_900,
                            color=text_color,
                        ),
                        ft.Text(
                            "IA para palta Hass",
                            size=10,
                            weight=ft.FontWeight.W_600,
                            color=muted_color,
                        ),
                    ],
                ),
            ],
        ),
    )

    # =====================================================
    # ESTADO DEL SISTEMA
    # =====================================================

    system_status = ft.Container(
        border_radius=14,
        bgcolor=card_green,
        border=ft.Border.all(1, border_color),
        padding=ft.Padding(12, 11, 12, 11),
        content=ft.Row(
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Container(
                    width=10,
                    height=10,
                    border_radius=5,
                    bgcolor=BRAND_GREEN,
                ),
                ft.Column(
                    expand=True,
                    spacing=1,
                    controls=[
                        ft.Text(
                            "Sistema operativo",
                            size=10,
                            weight=ft.FontWeight.W_800,
                            color=text_color,
                        ),
                        ft.Text(
                            "Servicios disponibles",
                            size=9,
                            color=muted_color,
                        ),
                    ],
                ),
                ft.Icon(
                    ft.Icons.CLOUD_DONE_OUTLINED,
                    size=17,
                    color=GREEN_DARK if not is_dark else BRAND_GREEN,
                ),
            ],
        ),
    )

    # =====================================================
    # SIDEBAR DE ESCRITORIO
    # =====================================================

    desktop_sidebar = ft.Container(
        width=260,
        bgcolor=sidebar_color,
        border=ft.Border(
            right=ft.BorderSide(1, border_color),
        ),
        content=ft.Column(
            expand=True,
            spacing=0,
            controls=[
                brand_header,
                ft.Divider(
                    height=1,
                    thickness=1,
                    color=border_color,
                ),
                ft.Container(
                    padding=ft.Padding(18, 20, 18, 8),
                    content=ft.Text(
                        "MENÚ PRINCIPAL",
                        size=9,
                        weight=ft.FontWeight.W_800,
                        color=muted_color,
                    ),
                ),
                ft.Container(
                    padding=ft.Padding(12, 0, 12, 0),
                    content=ft.Column(
                        spacing=6,
                        controls=[
                            sidebar_item(item)
                            for item in navigation_items
                        ],
                    ),
                ),

                # Empuja el estado del sistema hacia abajo.
                ft.Container(expand=True),

                ft.Container(
                    padding=ft.Padding(14, 12, 14, 10),
                    content=system_status,
                ),
                ft.Container(
                    padding=ft.Padding(20, 0, 20, 18),
                    content=ft.Text(
                        "Avoruna · Sistema móvil inteligente",
                        size=8,
                        color=muted_color,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ),
            ],
        ),
    )

    # =====================================================
    # NAVEGACIÓN COMPACTA
    # =====================================================

    def compact_item(item: dict) -> ft.Control:
        active = is_active(item["route"])

        return ft.Container(
            border_radius=10,
            bgcolor=active_background if active else None,
            padding=ft.Padding(12, 9, 12, 9),
            ink=True,
            on_click=lambda _, route=item["route"]: navigate(route),
            content=ft.Row(
                tight=True,
                spacing=7,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Icon(
                        item["active_icon"] if active else item["icon"],
                        size=18,
                        color=active_text_color if active else muted_color,
                    ),
                    ft.Text(
                        item["label"],
                        size=11,
                        weight=(
                            ft.FontWeight.W_800
                            if active
                            else ft.FontWeight.W_600
                        ),
                        color=active_text_color if active else text_color,
                    ),
                ],
            ),
        )

    mobile_header = ft.Container(
        height=66,
        bgcolor=sidebar_color,
        border=ft.Border(
            bottom=ft.BorderSide(1, border_color),
        ),
        padding=ft.Padding(16, 0, 16, 0),
        content=ft.Row(
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Container(
                    width=38,
                    height=38,
                    border_radius=12,
                    bgcolor=GREEN_SOFT if not is_dark else "#193522",
                    alignment=ft.Alignment.CENTER,
                    content=ft.Icon(
                        ft.Icons.ECO_OUTLINED,
                        size=21,
                        color=GREEN_DARK if not is_dark else BRAND_GREEN,
                    ),
                ),
                ft.Column(
                    expand=True,
                    spacing=0,
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=[
                        ft.Text(
                            "Avoruna",
                            size=16,
                            weight=ft.FontWeight.W_900,
                            color=text_color,
                        ),
                        ft.Text(
                            "IA para palta Hass",
                            size=9,
                            color=muted_color,
                        ),
                    ],
                ),
                ft.Container(
                    padding=ft.Padding(9, 5, 9, 5),
                    border_radius=999,
                    bgcolor=card_green,
                    content=ft.Row(
                        tight=True,
                        spacing=5,
                        controls=[
                            ft.Container(
                                width=7,
                                height=7,
                                border_radius=4,
                                bgcolor=BRAND_GREEN,
                            ),
                            ft.Text(
                                "Activo",
                                size=9,
                                weight=ft.FontWeight.W_700,
                                color=GREEN_DARK if not is_dark else BRAND_GREEN,
                            ),
                        ],
                    ),
                ),
            ],
        ),
    )

    mobile_navigation = ft.Container(
        height=58,
        bgcolor=sidebar_color,
        border=ft.Border(
            bottom=ft.BorderSide(1, border_color),
        ),
        padding=ft.Padding(10, 7, 10, 7),
        content=ft.Row(
            spacing=7,
            scroll=ft.ScrollMode.AUTO,
            controls=[
                compact_item(item)
                for item in navigation_items
            ],
        ),
    )

    main_area = ft.Container(
        expand=True,
        bgcolor=background_color,
        content=content,
    )

    # =====================================================
    # ESTRUCTURA RESPONSIVA
    # =====================================================

    if is_compact:
        return ft.Column(
            expand=True,
            spacing=0,
            controls=[
                mobile_header,
                mobile_navigation,
                main_area,
            ],
        )

    return ft.Row(
        expand=True,
        spacing=0,
        vertical_alignment=ft.CrossAxisAlignment.STRETCH,
        controls=[
            desktop_sidebar,
            main_area,
        ],
    )
