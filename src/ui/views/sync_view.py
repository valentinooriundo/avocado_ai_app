# src/ui/views/sync_view.py
import flet as ft
from services.settings_service import load_theme
from ui.components.app_shell import build_app_shell, BRAND_GREEN


ACCENT_RED = "#D93C3C"


def _is_dark(page: ft.Page) -> bool:
    return page.theme_mode == ft.ThemeMode.DARK


def _screen_mode(page: ft.Page) -> str:
    w = page.width or 1200
    if w >= 1400:
        return "xl"
    if w >= 1100:
        return "lg"
    if w >= 850:
        return "md"
    if w >= 620:
        return "sm"
    return "xs"


def create_sync_view(page: ft.Page) -> ft.View:
    db = page.data.get("db")
    if db is not None:
        saved = load_theme(db)
        page.theme_mode = ft.ThemeMode.DARK if saved == "dark" else ft.ThemeMode.LIGHT

    def c_surface():
        return "#141922" if _is_dark(page) else "#FFFFFF"

    def c_soft():
        return "#19212B" if _is_dark(page) else "#EEF6E8"

    def c_bg():
        return "#0F1115" if _is_dark(page) else "#F7FBF5"

    def c_text():
        return "#F3F4F6" if _is_dark(page) else "#111111"

    def c_muted():
        return "#A7B0C0" if _is_dark(page) else "#6B7280"

    def c_border():
        return "#2A3142" if _is_dark(page) else "#E5E7EB"

    def c_green_soft():
        return ft.Colors.with_opacity(0.10, ft.Colors.GREEN_400)

    def shadow():
        return ft.BoxShadow(
            blur_radius=18,
            spread_radius=1,
            color=ft.Colors.with_opacity(
                0.14 if _is_dark(page) else 0.08,
                ft.Colors.BLACK,
            ),
            offset=ft.Offset(0, 6),
        )

    def snack(msg: str):
        page.snack_bar = ft.SnackBar(ft.Text(msg))
        page.snack_bar.open = True
        page.update()

    def card(content: ft.Control, padding=16, radius=20, height=None, border_color=None):
        return ft.Container(
            height=height,
            padding=ft.Padding(padding, padding, padding, padding),
            border_radius=radius,
            bgcolor=c_surface(),
            border=ft.Border.all(1, border_color or c_border()),
            shadow=shadow(),
            content=content,
        )

    def section_icon(icon, bg=None, color=None, size=20):
        return ft.Container(
            width=40,
            height=40,
            border_radius=12,
            bgcolor=bg or c_green_soft(),
            alignment=ft.Alignment(0, 0),
            content=ft.Icon(icon, size=size, color=color or BRAND_GREEN),
        )

    def metric_card(title: str, main: str, sub: str, icon, accent=BRAND_GREEN, border_color=None):
        return card(
            ft.Column(
                spacing=12,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Text(
                                title,
                                size=11,
                                color=c_muted(),
                                weight=ft.FontWeight.W_900,
                            ),
                            section_icon(
                                icon,
                                bg=ft.Colors.with_opacity(0.12, ft.Colors.GREEN_400) if accent == BRAND_GREEN else ft.Colors.with_opacity(0.12, ft.Colors.RED_400),
                                color=accent,
                                size=18,
                            ),
                        ],
                    ),
                    ft.Text(
                        main,
                        size=18,
                        color=accent if accent == ACCENT_RED else c_text(),
                        weight=ft.FontWeight.W_900,
                    ),
                    ft.Text(
                        sub,
                        size=10,
                        color=accent if accent == BRAND_GREEN else c_muted(),
                        weight=ft.FontWeight.W_700,
                    ),
                ],
            ),
            padding=18,
            radius=18,
            height=128,
            border_color=border_color,
        )

    def primary_button(label: str, on_click=None, icon=None):
        return ft.Container(
            height=42,
            border_radius=12,
            bgcolor=BRAND_GREEN,
            ink=True,
            on_click=on_click,
            alignment=ft.Alignment(0, 0),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=8,
                controls=[
                    ft.Icon(icon, size=16, color=ft.Colors.WHITE) if icon else ft.Container(),
                    ft.Text(
                        label,
                        size=11,
                        weight=ft.FontWeight.W_800,
                        color=ft.Colors.WHITE,
                    ),
                ],
            ),
        )

    sync_items = [
        {
            "name": "Scan_AV_2304",
            "time": "Hoy, 09:12 AM",
            "location": "Lote Norte-02",
            "size": "42.5 MB",
            "state": "Subiendo...",
            "state_kind": "progress",
            "thumb": "avocado",
        },
        {
            "name": "Scan_AV_2305",
            "time": "Ayer, 18:45 PM",
            "location": "Lote Sur-15",
            "size": "18.2 MB",
            "state": "PENDIENTE",
            "state_kind": "pending",
            "thumb": "cluster",
        },
        {
            "name": "Scan_AV_2306",
            "time": "Ayer, 17:20 PM",
            "location": "Huerto Este-C",
            "size": "89.1 MB",
            "state": "PENDIENTE",
            "state_kind": "pending",
            "thumb": "field",
        },
    ]

    logs = [
        {
            "title": "Sync Completa: Lote Central",
            "time": "10:45 AM",
            "desc": "Se sincronizaron 240 imágenes de alta resolución exitosamente.",
            "id": "ID: #99281-S",
            "kind": "ok",
        },
        {
            "title": "Reporte Generado",
            "time": "09:15 AM",
            "desc": "Índice de madurez calculado para Sector 2: 78% Promedio.",
            "id": "",
            "kind": "ok",
        },
        {
            "title": "Fallo de Conexión",
            "time": "08:02 AM",
            "desc": "Pérdida de señal en Sector 4 durante la subida de datos.",
            "id": "",
            "kind": "error",
        },
        {
            "title": "Cola Reanudada",
            "time": "07:41 AM",
            "desc": "La cola de sincronización retomó envíos en segundo plano.",
            "id": "",
            "kind": "ok",
        },
    ]

    def thumb(kind: str):
        if kind == "avocado":
            return ft.Container(
                width=34,
                height=34,
                border_radius=10,
                bgcolor="#202824",
                content=ft.Stack(
                    controls=[
                        ft.Container(
                            width=22,
                            height=22,
                            border_radius=999,
                            bgcolor="#7DA44F",
                            left=6,
                            top=6,
                        ),
                        ft.Container(
                            width=12,
                            height=12,
                            border_radius=999,
                            bgcolor="#D8E59B",
                            left=11,
                            top=11,
                        ),
                        ft.Container(
                            width=6,
                            height=6,
                            border_radius=999,
                            bgcolor="#6A4326",
                            left=14,
                            top=14,
                        ),
                    ]
                ),
            )
        if kind == "cluster":
            return ft.Container(
                width=34,
                height=34,
                border_radius=10,
                bgcolor="#2D3A22",
                content=ft.Stack(
                    controls=[
                        ft.Container(width=10, height=14, border_radius=999, bgcolor="#7DA44F", left=6, top=10),
                        ft.Container(width=10, height=14, border_radius=999, bgcolor="#6D9741", left=14, top=6),
                        ft.Container(width=10, height=14, border_radius=999, bgcolor="#83AB54", left=18, top=14),
                    ]
                ),
            )
        return ft.Container(
            width=34,
            height=34,
            border_radius=10,
            bgcolor="#36502F",
            content=ft.Stack(
                controls=[
                    ft.Container(width=24, height=4, bgcolor="#A8C98C", left=5, top=10, rotate=0.25),
                    ft.Container(width=16, height=16, border_radius=999, bgcolor="#88B45D", left=9, top=14),
                ]
            ),
        )

    def state_badge(kind: str, label: str):
        if kind == "progress":
            return ft.Column(
                spacing=4,
                horizontal_alignment=ft.CrossAxisAlignment.END,
                controls=[
                    ft.Text(
                        label,
                        size=8,
                        color=BRAND_GREEN,
                        weight=ft.FontWeight.W_900,
                    ),
                    ft.Stack(
                        width=88,
                        height=6,
                        controls=[
                            ft.Container(
                                width=88,
                                height=4,
                                top=1,
                                border_radius=999,
                                bgcolor=ft.Colors.with_opacity(
                                    0.10,
                                    ft.Colors.BLACK if not _is_dark(page) else ft.Colors.WHITE,
                                ),
                            ),
                            ft.Container(
                                width=52,
                                height=4,
                                top=1,
                                border_radius=999,
                                bgcolor=BRAND_GREEN,
                            ),
                        ],
                    ),
                ],
            )

        return ft.Container(
            padding=ft.Padding(10, 4, 10, 4),
            border_radius=999,
            bgcolor=ft.Colors.with_opacity(
                0.10,
                ft.Colors.GREEN_400 if kind == "pending" else ft.Colors.GREY_400,
            ),
            content=ft.Text(
                label,
                size=8,
                color=BRAND_GREEN if kind == "pending" else c_muted(),
                weight=ft.FontWeight.W_900,
            ),
        )

    def sync_row(item):
        return ft.Container(
            padding=ft.Padding(8, 10, 8, 10),
            border_radius=12,
            bgcolor=c_surface(),
            content=ft.Row(
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    thumb(item["thumb"]),
                    ft.Container(width=10),
                    ft.Container(
                        width=124,
                        content=ft.Column(
                            spacing=2,
                            controls=[
                                ft.Text(item["name"], size=11, color=c_text(), weight=ft.FontWeight.W_800),
                                ft.Text(item["time"], size=9, color=c_muted()),
                            ],
                        ),
                    ),
                    ft.Container(
                        width=92,
                        content=ft.Text(item["location"], size=10, color=c_text(), weight=ft.FontWeight.W_700),
                    ),
                    ft.Container(
                        width=70,
                        content=ft.Text(item["size"], size=10, color=c_muted()),
                    ),
                    ft.Container(
                        expand=True,
                        alignment=ft.Alignment(1, 0),
                        content=state_badge(item["state_kind"], item["state"]),
                    ),
                ],
            ),
        )

    def log_item(item):
        point_color = BRAND_GREEN if item["kind"] == "ok" else ACCENT_RED
        line_color = ft.Colors.with_opacity(
            0.25,
            ft.Colors.GREEN_400 if item["kind"] == "ok" else ft.Colors.RED_400,
        )

        return ft.Row(
            vertical_alignment=ft.CrossAxisAlignment.START,
            controls=[
                ft.Column(
                    spacing=0,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Container(
                            width=10,
                            height=10,
                            border_radius=999,
                            bgcolor=point_color,
                        ),
                        ft.Container(
                            width=2,
                            height=84,
                            bgcolor=line_color,
                        ),
                    ],
                ),
                ft.Container(width=10),
                ft.Container(
                    expand=True,
                    content=ft.Column(
                        spacing=4,
                        controls=[
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                vertical_alignment=ft.CrossAxisAlignment.START,
                                controls=[
                                    ft.Container(
                                        expand=True,
                                        content=ft.Text(
                                            item["title"],
                                            size=11,
                                            color=c_text(),
                                            weight=ft.FontWeight.W_800,
                                        ),
                                    ),
                                    ft.Text(
                                        item["time"],
                                        size=9,
                                        color=c_muted(),
                                        weight=ft.FontWeight.W_700,
                                    ),
                                ],
                            ),
                            ft.Text(
                                item["desc"],
                                size=10,
                                color=c_muted(),
                            ),
                            ft.Text(
                                item["id"],
                                size=9,
                                color=BRAND_GREEN,
                                weight=ft.FontWeight.W_800,
                            ) if item["id"] else ft.Container(),
                        ],
                    ),
                ),
            ],
        )

    def build_header(mode: str):
        title = ft.Column(
            spacing=4,
            controls=[
                ft.Row(
                    spacing=10,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Text(
                            "Sincronización de Datos",
                            size=18 if mode in ("xl", "lg", "md") else 16,
                            color=c_text(),
                            weight=ft.FontWeight.W_900,
                        ),
                        ft.Container(
                            padding=ft.Padding(10, 4, 10, 4),
                            border_radius=999,
                            bgcolor=ft.Colors.with_opacity(0.12, ft.Colors.RED_400),
                            content=ft.Text(
                                "OFFLINE (Ica Sector 4)",
                                size=8,
                                color=ACCENT_RED,
                                weight=ft.FontWeight.W_900,
                            ),
                        ),
                    ],
                ),
            ],
        )

        search = ft.TextField(
            hint_text="Buscar registros...",
            dense=True,
            height=36,
            width=240 if mode in ("xl", "lg") else 200 if mode == "md" else None,
            expand=False if mode in ("xl", "lg", "md") else True,
            border_radius=999,
            text_size=10,
            bgcolor=ft.Colors.with_opacity(
                0.04,
                ft.Colors.BLACK if not _is_dark(page) else ft.Colors.WHITE,
            ),
            border=ft.InputBorder.NONE,
            prefix_icon=ft.Icons.SEARCH,
        )

        if mode in ("xl", "lg"):
            return ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[title, search],
            )

        return ft.Column(
            spacing=10,
            controls=[title, search],
        )

    def build_metrics(mode: str):
        card1 = metric_card(
            "ESCANEOS PENDIENTES",
            "14",
            "+2 nuevos hoy",
            ft.Icons.INVENTORY_2_OUTLINED,
            accent=BRAND_GREEN,
            border_color=BRAND_GREEN,
        )

        card2 = metric_card(
            "ÚLTIMA SINCRONIZACIÓN",
            "Hoy 10:45 AM",
            "Hace 2 horas",
            ft.Icons.SYNC,
            accent=BRAND_GREEN,
            border_color=BRAND_GREEN,
        )

        card3 = metric_card(
            "ESTADO CONEXIÓN",
            "Offline",
            "Sector 4 - Ica, PE",
            ft.Icons.PORTABLE_WIFI_OFF_OUTLINED,
            accent=ACCENT_RED,
            border_color=ACCENT_RED,
        )

        if mode in ("xl", "lg"):
            return ft.Row(
                spacing=14,
                controls=[
                    ft.Container(expand=True, content=card1),
                    ft.Container(expand=True, content=card2),
                    ft.Container(expand=True, content=card3),
                ],
            )

        if mode == "md":
            return ft.Column(
                spacing=14,
                controls=[
                    ft.Row(
                        spacing=14,
                        controls=[
                            ft.Container(expand=True, content=card1),
                            ft.Container(expand=True, content=card2),
                        ],
                    ),
                    card3,
                ],
            )

        return ft.Column(
            spacing=14,
            controls=[card1, card2, card3],
        )

    content_host = ft.Container(expand=True)

    def build_content():
        mode = _screen_mode(page)
        max_width = 1120 if mode == "xl" else 980 if mode == "lg" else 860 if mode == "md" else 680 if mode == "sm" else None

        queue_card = card(
            ft.Column(
                spacing=12,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Text(
                                "Cola de Sincronización",
                                size=16,
                                color=c_text(),
                                weight=ft.FontWeight.W_900,
                            ),
                            ft.Container(
                                width=138,
                                content=primary_button(
                                    "Sincronizar Ahora",
                                    on_click=lambda e: snack("Sincronización manual iniciada."),
                                    icon=ft.Icons.SYNC,
                                ),
                            ),
                        ],
                    ),
                    ft.Container(height=1, bgcolor=c_border()),
                    ft.Row(
                        controls=[
                            ft.Container(width=44, content=ft.Text("ESCANEO", size=9, color=c_muted(), weight=ft.FontWeight.W_900)),
                            ft.Container(width=134, content=ft.Text("", size=9)),
                            ft.Container(width=92, content=ft.Text("UBICACIÓN", size=9, color=c_muted(), weight=ft.FontWeight.W_900)),
                            ft.Container(width=70, content=ft.Text("TAMAÑO", size=9, color=c_muted(), weight=ft.FontWeight.W_900)),
                            ft.Container(expand=True, content=ft.Text("ESTADO", size=9, color=c_muted(), weight=ft.FontWeight.W_900)),
                        ],
                    ),
                    ft.Column(
                        spacing=8,
                        controls=[sync_row(item) for item in sync_items],
                    ),
                    ft.Container(
                        alignment=ft.Alignment(0, 0),
                        padding=ft.Padding(0, 6, 0, 0),
                        content=ft.Text(
                            "Ver todos los escaneos (14)",
                            size=10,
                            color=BRAND_GREEN,
                            weight=ft.FontWeight.W_800,
                        ),
                    ),
                ],
            ),
            padding=16,
            radius=18,
        )

        log_card = card(
            ft.Column(
                spacing=12,
                controls=[
                    ft.Text(
                        "Log de Actividad",
                        size=16,
                        color=c_text(),
                        weight=ft.FontWeight.W_900,
                    ),
                    ft.Container(
                        height=360 if mode in ("xl", "lg", "md") else 300,
                        content=ft.ListView(
                            spacing=10,
                            controls=[log_item(item) for item in logs],
                        ),
                    ),
                ],
            ),
            padding=16,
            radius=18,
        )

        if mode in ("xl", "lg"):
            middle = ft.Row(
                spacing=14,
                vertical_alignment=ft.CrossAxisAlignment.START,
                controls=[
                    ft.Container(expand=3, content=queue_card),
                    ft.Container(expand=2, content=log_card),
                ],
            )
        else:
            middle = ft.Column(
                spacing=14,
                controls=[queue_card, log_card],
            )

        main_column = ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=14,
            controls=[
                build_header(mode),
                build_metrics(mode),
                middle,
                ft.Container(height=20),
            ],
        )

        return ft.Container(
            expand=True,
            alignment=ft.Alignment(0, -1),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                controls=[
                    ft.Container(
                        width=max_width,
                        expand=(max_width is None),
                        content=main_column,
                    )
                ],
            ),
        )

    def rebuild(*_):
        content_host.content = build_content()
        page.update()

    page.on_resized = rebuild
    rebuild()

    root = build_app_shell(page, content_host)

    return ft.View(
        route="/sync",
        bgcolor=c_bg(),
        padding=0,
        spacing=0,
        controls=[
            ft.SafeArea(expand=True, content=root),
        ],
    )
