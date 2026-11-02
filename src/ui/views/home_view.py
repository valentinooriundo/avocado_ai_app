# src/ui/views/home_view.py
import asyncio
import flet as ft

from services.settings_service import load_theme, save_theme
from ui.theme_tokens import BRAND_PRIMARY, BRAND_SOFT, text_color, muted_color, border_color, surface_color

BRAND_GREEN = BRAND_PRIMARY
BG_TINT = "#EAF8E5"


def _nav(page: ft.Page, route: str):
    asyncio.create_task(page.push_route(route))


def _is_dark(page: ft.Page) -> bool:
    return page.theme_mode == ft.ThemeMode.DARK


def _is_mobile(page: ft.Page) -> bool:
    w = page.width or 0
    return w != 0 and w < 720


def _c_bg(page: ft.Page):
    return "#0F1115" if _is_dark(page) else "#F7FBF5"


def _c_surface(page: ft.Page):
    return "#141922" if _is_dark(page) else "#FFFFFF"


def _c_text(page: ft.Page):
    return "#F3F4F6" if _is_dark(page) else "#111111"


def _c_muted(page: ft.Page):
    return "#A7B0C0" if _is_dark(page) else "#6B7280"


def _c_border(page: ft.Page):
    return "#2A3142" if _is_dark(page) else ft.Colors.GREY_200


def _shadow(page: ft.Page):
    return ft.BoxShadow(
        blur_radius=24,
        spread_radius=2,
        color=ft.Colors.with_opacity(0.20 if _is_dark(page) else 0.10, ft.Colors.BLACK),
        offset=ft.Offset(0, 8),
    )


def _bg_layer(page: ft.Page):
    return ft.Container(
        expand=True,
        bgcolor=_c_bg(page),
        content=ft.Stack(
            expand=True,
            controls=[
                ft.Container(expand=True, bgcolor=_c_bg(page)),
                ft.Container(expand=True, bgcolor=BG_TINT, opacity=0.10 if _is_dark(page) else 0.45),
            ],
        ),
    )


def _card(page: ft.Page, content: ft.Control, width=None, padding=18):
    return ft.Container(
        width=width,
        padding=ft.Padding(padding, padding, padding, padding),
        border_radius=22,
        bgcolor=_c_surface(page),
        border=ft.Border.all(1, _c_border(page)),
        shadow=_shadow(page),
        content=content,
    )


def _pill(label: str, color_bg, color_fg):
    return ft.Container(
        padding=ft.Padding(10, 6, 10, 6),
        border_radius=999,
        bgcolor=color_bg,
        content=ft.Text(label, size=10, weight=ft.FontWeight.W_800, color=color_fg),
    )


def _format_time(ts: str) -> str:
    try:
        t = (ts or "").split(".")[0]
        if " " in t:
            d, hhmmss = t.split(" ")
            hh, mm = hhmmss.split(":")[0], hhmmss.split(":")[1]
            return f"{d}, {hh}:{mm}"
        return t
    except Exception:
        return "HOY"


def create_home_view(page: ft.Page) -> ft.View:
    db = page.data.get("db")

    # ====== Sync theme from SQLite settings ======
    if db is not None:
        saved = load_theme(db)
        page.theme_mode = ft.ThemeMode.DARK if saved == "dark" else ft.ThemeMode.LIGHT

    # ====== Datos ======
    recent_items = []
    if db is not None:
        try:
            with db._conn() as conn:
                rows = conn.execute(
                    "SELECT created_at, maturity_percent, status, image_asset "
                    "FROM scans ORDER BY datetime(created_at) DESC LIMIT 2"
                ).fetchall()
            for r in rows:
                recent_items.append(
                    {
                        "time": _format_time(r["created_at"]),
                        "status": r["status"] or "Listo",
                        "pct": int(r["maturity_percent"] or 0),
                        "img": r["image_asset"] or "history_1.png",
                    }
                )
        except Exception:
            recent_items = []

    if not recent_items:
        recent_items = [
            {"time": "HOY, 10:45 AM", "status": "Listo", "pct": 85, "img": "history_1.png"},
            {"time": "AYER, 04:20 PM", "status": "Espera", "pct": 42, "img": "history_2.png"},
        ]

    # ====== Top actions ======
    notif_btn = ft.IconButton(icon=ft.Icons.NOTIFICATIONS_NONE)
    theme_btn = ft.IconButton(icon=ft.Icons.DARK_MODE)

    def refresh_top_icons():
        theme_btn.icon = ft.Icons.LIGHT_MODE if _is_dark(page) else ft.Icons.DARK_MODE
        theme_btn.icon_color = _c_muted(page)
        notif_btn.icon_color = _c_muted(page)

        theme_btn.bgcolor = ft.Colors.with_opacity(0.06, ft.Colors.BLACK if not _is_dark(page) else ft.Colors.WHITE)
        notif_btn.bgcolor = ft.Colors.with_opacity(0.06, ft.Colors.BLACK if not _is_dark(page) else ft.Colors.WHITE)

    # ====== Hosts ======
    bg_host = ft.Container(expand=True)
    content_host = ft.Container(expand=True)

    # ====== Action scan ======
    def open_scan(_=None):
        page.snack_bar = ft.SnackBar(ft.Text("Abriendo cámara..."))
        page.snack_bar.open = True
        page.update()
        _nav(page, "/camera")

    # ====== Cards ======
    def status_chip(status: str):
        if (status or "").lower() == "listo":
            return _pill("Listo", ft.Colors.with_opacity(0.18, ft.Colors.GREEN_400), BRAND_GREEN)
        return _pill("Espera", ft.Colors.with_opacity(0.18, ft.Colors.AMBER_400), ft.Colors.AMBER_700)

    def recent_card(item):
        return ft.Container(
            width=220 if not _is_mobile(page) else 170,
            padding=ft.Padding(12, 12, 12, 12),
            border_radius=18,
            border=ft.Border.all(1, _c_border(page)),
            bgcolor=_c_surface(page),
            content=ft.Column(
                spacing=8,
                controls=[
                    ft.Container(
                        height=92 if not _is_mobile(page) else 82,
                        border_radius=14,
                        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                        bgcolor=ft.Colors.with_opacity(0.10, ft.Colors.GREEN_400),
                        content=ft.Image(src=item["img"], fit="cover"),
                    ),
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Column(
                                spacing=2,
                                controls=[
                                    ft.Text(item["time"], size=9, color=_c_muted(page), weight=ft.FontWeight.W_700),
                                    status_chip(item["status"]),
                                ],
                            ),
                            ft.Column(
                                spacing=0,
                                horizontal_alignment=ft.CrossAxisAlignment.END,
                                controls=[
                                    ft.Text(
                                        f"{item['pct']}%",
                                        size=12,
                                        weight=ft.FontWeight.W_900,
                                        color=_c_text(page),
                                    ),
                                    ft.Text("MADUREZ", size=8, color=_c_muted(page), weight=ft.FontWeight.W_700),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
        )

    # ====== Toggle theme ======
    def toggle_theme(_):
        new_mode = ft.ThemeMode.LIGHT if _is_dark(page) else ft.ThemeMode.DARK
        page.theme_mode = new_mode
        if db is not None:
            save_theme(db, "dark" if new_mode == ft.ThemeMode.DARK else "light")
        build_layout()
        page.update()

    theme_btn.on_click = toggle_theme

    # ==========================================================
    # MOBILE LAYOUT (NO TOCAR) ✅
    # ==========================================================
    def mobile_layout():
        avatar = ft.CircleAvatar(
            radius=18,
            bgcolor=ft.Colors.with_opacity(0.12, ft.Colors.GREEN_400),
            content=ft.Text("V", weight=ft.FontWeight.W_900, color=_c_text(page)),
        )

        compact = (page.width or 0) < 380

        right_actions = ft.Container(
            width=92 if not compact else 46,
            alignment=ft.Alignment(1, 0),
            content=ft.Row(
                spacing=6,
                alignment=ft.MainAxisAlignment.END,
                controls=[notif_btn, theme_btn] if not compact else [theme_btn],
            ),
        )

        title_block = ft.Column(
            spacing=0,
            controls=[
                ft.Text(
                    "BIENVENIDO",
                    size=9,
                    color=_c_muted(page),
                    weight=ft.FontWeight.W_800,
                    max_lines=1,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
                ft.Text(
                    "Hola, Productor",
                    size=14,
                    color=_c_text(page),
                    weight=ft.FontWeight.W_900,
                    max_lines=1,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
            ],
        )

        header = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    icon_color=_c_muted(page),
                    on_click=lambda _: _nav(page, "/welcome"),
                    tooltip="Volver",
                ),
                avatar,
                ft.Container(expand=True, content=title_block),
                right_actions,
            ],
        )

        scan_circle = ft.Container(
            width=240,
            height=240,
            border_radius=120,
            bgcolor=BRAND_GREEN,
            alignment=ft.Alignment(0, 0),
            ink=True,
            on_click=open_scan,
            content=ft.Icon(ft.Icons.CENTER_FOCUS_STRONG, size=42, color=ft.Colors.WHITE),
        )

        system_pill = ft.Container(
            border_radius=999,
            bgcolor=_c_surface(page),
            padding=ft.Padding(14, 8, 14, 8),
            border=ft.Border.all(1, _c_border(page)),
            content=ft.Row(
                tight=True,
                spacing=8,
                controls=[
                    ft.Container(width=8, height=8, border_radius=99, bgcolor=BRAND_GREEN),
                    ft.Text("Sistema\nlisto", size=10, weight=ft.FontWeight.W_900, color=_c_text(page)),
                ],
            ),
        )

        open_cam_btn = ft.Button(
            "Abrir cámara",
            icon=ft.Icons.PHOTO_CAMERA,
            on_click=open_scan,
            style=ft.ButtonStyle(
                bgcolor={ft.ControlState.DEFAULT: BRAND_GREEN},
                color={ft.ControlState.DEFAULT: ft.Colors.WHITE},
                shape={ft.ControlState.DEFAULT: ft.RoundedRectangleBorder(radius=12)},
                padding={ft.ControlState.DEFAULT: ft.Padding(14, 10, 14, 10)},
            ),
        )

        hero = _card(
            page,
            content=ft.Column(
                spacing=14,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    header,
                    ft.Container(height=6),
                    ft.Stack(
                        width=260,
                        height=260,
                        controls=[
                            ft.Container(
                                width=260,
                                height=260,
                                border_radius=130,
                                bgcolor=ft.Colors.with_opacity(0.14, ft.Colors.GREEN_400),
                            ),
                            ft.Container(alignment=ft.Alignment(0, 0), content=scan_circle),
                            ft.Container(alignment=ft.Alignment(0, 0.58), content=system_pill),
                        ],
                    ),
                    open_cam_btn,
                    ft.Text("Escanear Aguacate", size=18, weight=ft.FontWeight.W_900, color=_c_text(page)),
                    ft.Text(
                        "Apunta la cámara al fruto para detectar el\nnivel de madurez en tiempo real.",
                        size=11,
                        color=_c_muted(page),
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
            ),
        )

        recent_hdr = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Text("Historial reciente", size=12, weight=ft.FontWeight.W_900, color=_c_text(page)),
                ft.TextButton(
                    content=ft.Text("Ver todo", size=11, color=BRAND_GREEN, weight=ft.FontWeight.W_900),
                    on_click=lambda _: _nav(page, "/history"),
                    style=ft.ButtonStyle(padding=ft.Padding(0, 0, 0, 0)),
                ),
            ],
        )

        recent_row = ft.Row(
            spacing=12,
            scroll=ft.ScrollMode.AUTO,
            controls=[recent_card(x) for x in recent_items],
        )

        nav_bar = ft.Container(
            padding=ft.Padding(14, 10, 14, 10),
            border_radius=18,
            bgcolor=_c_surface(page),
            border=ft.Border.all(1, _c_border(page)),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_AROUND,
                controls=[
                    ft.Column(
                        spacing=4,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Icon(ft.Icons.HOME, color=BRAND_GREEN, size=20),
                            ft.Text("Inicio", size=9, color=BRAND_GREEN, weight=ft.FontWeight.W_800),
                        ],
                    ),
                    ft.Column(
                        spacing=4,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Icon(ft.Icons.HISTORY, color=_c_muted(page), size=20),
                            ft.Text("Historial", size=9, color=_c_muted(page), weight=ft.FontWeight.W_800),
                        ],
                    ),
                    ft.Column(
                        spacing=4,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Icon(ft.Icons.SETTINGS, color=_c_muted(page), size=20),
                            ft.Text("Ajustes", size=9, color=_c_muted(page), weight=ft.FontWeight.W_800),
                        ],
                    ),
                ],
            ),
        )

        return ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=14,
            controls=[
                ft.Container(padding=ft.Padding(14, 14, 14, 0), content=hero),
                ft.Container(
                    padding=ft.Padding(14, 0, 14, 0),
                    content=ft.Column(spacing=10, controls=[recent_hdr, recent_row]),
                ),
                ft.Container(height=4),
                ft.Container(padding=ft.Padding(14, 0, 14, 14), content=nav_bar),
            ],
        )

    # ==========================================================
    # DESKTOP/WEB LAYOUT ✅
    # ==========================================================
    def desktop_web_layout():
        w = page.width or 1200
        compact_sidebar = w < 980

        avatar = ft.CircleAvatar(
            radius=18,
            bgcolor=ft.Colors.with_opacity(0.12, ft.Colors.GREEN_400),
            content=ft.Text("V", weight=ft.FontWeight.W_900, color=_c_text(page)),
        )

        header = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Column(
                    spacing=0,
                    controls=[
                        ft.Text("BIENVENIDO", size=9, color=_c_muted(page), weight=ft.FontWeight.W_800),
                        ft.Text("Hola, Productor", size=16, color=_c_text(page), weight=ft.FontWeight.W_900),
                    ],
                ),
                ft.Row(spacing=8, controls=[avatar, notif_btn, theme_btn]),
            ],
        )

        scan_circle = ft.Stack(
            width=220,
            height=220,
            controls=[
                ft.Container(
                    width=220,
                    height=220,
                    border_radius=110,
                    bgcolor=ft.Colors.with_opacity(0.18, ft.Colors.GREEN_400),
                ),
                ft.Container(
                    width=220,
                    height=220,
                    border_radius=110,
                    ink=True,
                    on_click=open_scan,
                    alignment=ft.Alignment(0, 0),
                    content=ft.Icon(ft.Icons.CENTER_FOCUS_STRONG, size=44, color=BRAND_GREEN),
                ),
            ],
        )

        start_btn = ft.Button(
            "Iniciar Análisis",
            icon=ft.Icons.PHOTO_CAMERA,
            on_click=open_scan,
            style=ft.ButtonStyle(
                bgcolor={ft.ControlState.DEFAULT: BRAND_GREEN},
                color={ft.ControlState.DEFAULT: ft.Colors.WHITE},
                shape={ft.ControlState.DEFAULT: ft.RoundedRectangleBorder(radius=12)},
                padding={ft.ControlState.DEFAULT: ft.Padding(16, 12, 16, 12)},
            ),
        )

        scan_card = _card(
            page,
            content=ft.Column(
                spacing=12,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    scan_circle,
                    ft.Text("Escanear Aguacate", size=22, weight=ft.FontWeight.W_900, color=_c_text(page)),
                    ft.Text(
                        "Apunta la cámara al fruto para detectar el\nnivel de madurez en tiempo real.",
                        size=11,
                        color=_c_muted(page),
                        text_align=ft.TextAlign.CENTER,
                    ),
                    start_btn,
                ],
            ),
            padding=20,
        )

        recent_block = _card(
            page,
            content=ft.Column(
                spacing=12,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text("Historial reciente", size=14, weight=ft.FontWeight.W_900, color=_c_text(page)),
                            ft.TextButton(
                                content=ft.Text("Ver todo >", size=11, color=BRAND_GREEN, weight=ft.FontWeight.W_900),
                                on_click=lambda _: _nav(page, "/history"),
                                style=ft.ButtonStyle(padding=ft.Padding(0, 0, 0, 0)),
                            ),
                        ],
                    ),
                    ft.Row(spacing=12, wrap=True, controls=[recent_card(x) for x in recent_items]),
                ],
            ),
            padding=18,
        )

        summary_card = _card(
            page,
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Column(
                        spacing=2,
                        controls=[
                            ft.Text("Resumen de cosecha", size=12, weight=ft.FontWeight.W_900, color=_c_text(page)),
                            ft.Text("24 aguacates analizados hoy", size=10, color=_c_muted(page), weight=ft.FontWeight.W_700),
                        ],
                    ),
                    ft.Row(
                        spacing=18,
                        controls=[
                            ft.Column(
                                spacing=0,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                controls=[
                                    ft.Text("18", size=18, weight=ft.FontWeight.W_900, color=BRAND_GREEN),
                                    ft.Text("LISTOS", size=8, color=_c_muted(page), weight=ft.FontWeight.W_800),
                                ],
                            ),
                            ft.Column(
                                spacing=0,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                controls=[
                                    ft.Text("6", size=18, weight=ft.FontWeight.W_900, color=ft.Colors.AMBER_700),
                                    ft.Text("EN PROCESO", size=8, color=_c_muted(page), weight=ft.FontWeight.W_800),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
            padding=18,
        )

        # ✅ SIN ft.Expanded -> usamos Container(expand=True)
        def quick_btn(text: str, icon, on_click=None):
            return ft.Container(
                col={"xs": 12, "sm": 6, "md": 6, "lg": 3, "xl": 3},
                padding=ft.Padding(14, 12, 14, 12),
                border_radius=18,
                bgcolor=_c_surface(page),
                border=ft.Border.all(1, _c_border(page)),
                ink=True,
                on_click=on_click,
                content=ft.Row(
                    spacing=10,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Icon(icon, size=18, color=BRAND_GREEN),
                        ft.Container(
                            expand=True,
                            content=ft.Text(
                                text,
                                size=11,
                                color=_c_text(page),
                                weight=ft.FontWeight.W_800,
                                max_lines=2,
                                overflow=ft.TextOverflow.CLIP,
                                no_wrap=False,
                            ),
                        ),
                    ],
                ),
            )

        quick_actions = _card(
            page,
            content=ft.Column(
                spacing=12,
                controls=[
                    ft.Text("Accesos rápidos", size=12, weight=ft.FontWeight.W_900, color=_c_text(page)),
                    ft.ResponsiveRow(
                        spacing=12,
                        run_spacing=12,
                        controls=[
                            quick_btn("Nuevo Lote", ft.Icons.ADD_BOX_OUTLINED, on_click=lambda _: None),
                            quick_btn("Sincronizar", ft.Icons.CLOUD_SYNC_OUTLINED, on_click=lambda _: None),
                            quick_btn("Exportar PDF", ft.Icons.PICTURE_AS_PDF_OUTLINED, on_click=lambda _: None),
                            quick_btn("Ayuda", ft.Icons.HELP_OUTLINE, on_click=lambda _: None),
                        ],
                    ),
                ],
            ),
            padding=18,
        )

        right_col = ft.Column(expand=True, spacing=14, controls=[recent_block, summary_card, quick_actions])

        if w < 1100:
            content_grid = ft.Column(spacing=14, controls=[scan_card, right_col])
        else:
            content_grid = ft.Row(
                spacing=14,
                vertical_alignment=ft.CrossAxisAlignment.START,
                controls=[ft.Container(width=420, content=scan_card), right_col],
            )

        def current_tab() -> str:
            r = (page.route or "").lower()
            if r.startswith("/history"):
                return "history"
            if r.startswith("/settings") or r.startswith("/ajustes"):
                return "settings"
            return "home"

        tab = current_tab()

        def nav_item(label: str, icon, route: str, active: bool):
            if compact_sidebar:
                return ft.Container(
                    height=44,
                    border_radius=14,
                    padding=ft.Padding(10, 0, 10, 0),
                    bgcolor=ft.Colors.with_opacity(0.12, ft.Colors.GREEN_400) if active else None,
                    ink=True,
                    on_click=lambda _: _nav(page, route),
                    alignment=ft.Alignment(-1, 0),
                    content=ft.Icon(icon, size=20, color=BRAND_GREEN if active else _c_muted(page)),
                    tooltip=label,
                )

            return ft.Container(
                height=44,
                border_radius=14,
                padding=ft.Padding(14, 0, 14, 0),
                bgcolor=ft.Colors.with_opacity(0.12, ft.Colors.GREEN_400) if active else None,
                ink=True,
                on_click=lambda _: _nav(page, route),
                alignment=ft.Alignment(-1, 0),
                content=ft.Row(
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Icon(icon, size=20, color=BRAND_GREEN if active else _c_muted(page)),
                        ft.Text(label, size=12, color=BRAND_GREEN if active else _c_text(page), weight=ft.FontWeight.W_800),
                    ],
                ),
            )

        sidebar_width = 72 if compact_sidebar else 240

        sidebar = ft.Container(
            width=sidebar_width,
            border_radius=22,
            bgcolor=_c_surface(page),
            border=ft.Border.all(1, _c_border(page)),
            padding=ft.Padding(12, 14, 12, 14),
            content=ft.Column(
                expand=True,
                spacing=12,
                horizontal_alignment=ft.CrossAxisAlignment.START,
                controls=[
                    ft.Row(
                        spacing=10,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Icon(ft.Icons.ECO, color=BRAND_GREEN, size=20),
                            ft.Text("Avoruna App", size=14, weight=ft.FontWeight.W_900, color=_c_text(page))
                            if not compact_sidebar
                            else ft.Container(),
                        ],
                    ),
                    ft.Container(height=6),

                    nav_item("Inicio", ft.Icons.HOME_OUTLINED, "/home", tab == "home"),
                    nav_item("Historial", ft.Icons.HISTORY_OUTLINED, "/history", tab == "history"),
                    nav_item("Ajustes", ft.Icons.SETTINGS_OUTLINED, "/settings", tab == "settings"),

                    ft.Container(expand=True),

                    # ✅ Botón Volver footer sidebar
                    ft.Container(
                        height=44,
                        border_radius=14,
                        padding=ft.Padding(12, 0, 12, 0),
                        border=ft.Border.all(1, _c_border(page)),
                        bgcolor=ft.Colors.with_opacity(0.04, ft.Colors.BLACK if not _is_dark(page) else ft.Colors.WHITE),
                        ink=True,
                        on_click=lambda _: _nav(page, "/welcome"),
                        alignment=ft.Alignment(-1, 0),
                        content=ft.Row(
                            spacing=10,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.Icon(ft.Icons.ARROW_BACK, size=18, color=_c_muted(page)),
                                ft.Text(
                                    "Volver" if not compact_sidebar else "",
                                    size=11,
                                    color=_c_muted(page),
                                    weight=ft.FontWeight.W_800,
                                ),
                            ],
                        ),
                        tooltip="Volver",
                    ),
                ],
            ),
        )

        main = ft.Container(
            expand=True,
            padding=ft.Padding(16, 16, 16, 16),
            content=ft.Column(expand=True, spacing=14, controls=[header, content_grid]),
        )

        shell = ft.Container(
            expand=True,
            alignment=ft.Alignment(0, 0),
            padding=ft.Padding(18, 18, 18, 18),
            content=ft.Row(
                spacing=14,
                alignment=ft.MainAxisAlignment.CENTER,
                vertical_alignment=ft.CrossAxisAlignment.START,
                controls=[
                    sidebar,
                    ft.Container(width=1200 if w > 1400 else None, expand=True, content=main),
                ],
            ),
        )
        return shell

    # ====== Build layout ======
    def build_layout(*_):
        refresh_top_icons()
        bg_host.content = _bg_layer(page)
        content_host.content = mobile_layout() if _is_mobile(page) else desktop_web_layout()
        page.update()

    page.on_resized = build_layout

    root = ft.Container(expand=True, content=ft.Stack(expand=True, controls=[bg_host, content_host]))
    build_layout()
    return ft.View(route="/home", controls=[ft.SafeArea(expand=True, content=root)])
