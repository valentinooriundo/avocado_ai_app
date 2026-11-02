# src/ui/views/alerts_view.py
import flet as ft
from services.settings_service import load_theme
from ui.components.app_shell import build_app_shell, BRAND_GREEN


def _is_dark(page: ft.Page) -> bool:
    return page.theme_mode == ft.ThemeMode.DARK


def create_alerts_view(page: ft.Page) -> ft.View:
    db = page.data.get("db")

    # Sync theme
    if db is not None:
        saved = load_theme(db)
        page.theme_mode = ft.ThemeMode.DARK if saved == "dark" else ft.ThemeMode.LIGHT

    # ---- helpers
    def c_surface():
        return "#141922" if _is_dark(page) else "#FFFFFF"

    def c_text():
        return "#F3F4F6" if _is_dark(page) else "#111111"

    def c_muted():
        return "#A7B0C0" if _is_dark(page) else "#6B7280"

    def c_border():
        return "#2A3142" if _is_dark(page) else ft.Colors.GREY_200

    def shadow():
        return ft.BoxShadow(
            blur_radius=24,
            spread_radius=2,
            color=ft.Colors.with_opacity(0.20 if _is_dark(page) else 0.10, ft.Colors.BLACK),
            offset=ft.Offset(0, 8),
        )

    def card(content: ft.Control, padding=18, radius=22):
        return ft.Container(
            padding=ft.Padding(padding, padding, padding, padding),
            border_radius=radius,
            bgcolor=c_surface(),
            border=ft.Border.all(1, c_border()),
            shadow=shadow(),
            content=content,
        )

    def pill(text: str, bg, fg):
        return ft.Container(
            padding=ft.Padding(10, 4, 10, 4),
            border_radius=999,
            bgcolor=bg,
            content=ft.Text(text, size=9, weight=ft.FontWeight.W_900, color=fg),
        )

    def snack(msg: str):
        page.snack_bar = ft.SnackBar(ft.Text(msg))
        page.snack_bar.open = True
        page.update()

    # ---- Breakpoints
    def layout_mode() -> str:
        w = page.width or 1200
        if w >= 1280:
            return "3col"
        if w >= 900:
            return "2col"
        return "1col"

    # ---- components
    def header_bar():
        return ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Column(
                    spacing=2,
                    controls=[
                        ft.Text("Panel de Alertas", size=22, weight=ft.FontWeight.W_900, color=c_text()),
                        ft.Text(
                            "Estado crítico de monitoreo para cultivos de aguacate",
                            size=10,
                            weight=ft.FontWeight.W_700,
                            color=c_muted(),
                        ),
                    ],
                ),
                ft.Row(
                    spacing=10,
                    controls=[
                        ft.IconButton(
                            icon=ft.Icons.REFRESH,
                            icon_color=c_muted(),
                            tooltip="Actualizar (mock)",
                            on_click=lambda _: snack("Actualizando… (mock)"),
                        ),
                        ft.CircleAvatar(
                            radius=16,
                            bgcolor=ft.Colors.with_opacity(0.12, ft.Colors.GREEN_400),
                            content=ft.Text("JD", size=10, weight=ft.FontWeight.W_900, color=c_text()),
                        ),
                    ],
                ),
            ],
        )

    def weather_card():
        return card(
            ft.Column(
                spacing=14,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Column(
                                spacing=2,
                                controls=[
                                    ft.Text("CLIMA\nACTUAL", size=8, color=c_muted(), weight=ft.FontWeight.W_900),
                                    pill("BAJO\nRIESGO", ft.Colors.with_opacity(0.12, ft.Colors.GREEN_400), BRAND_GREEN),
                                ],
                            ),
                            ft.Icon(ft.Icons.CLOUD_OUTLINED, color=BRAND_GREEN),
                        ],
                    ),
                    ft.Row(
                        vertical_alignment=ft.CrossAxisAlignment.END,
                        controls=[
                            ft.Text("24", size=44, weight=ft.FontWeight.W_900, color=c_text()),
                            ft.Text("°C", size=14, weight=ft.FontWeight.W_900, color=c_muted()),
                        ],
                    ),
                    ft.Text("Cielos\ndespejados", size=12, weight=ft.FontWeight.W_800, color=c_text()),
                    ft.Divider(height=1, color=c_border()),
                    ft.ResponsiveRow(
                        spacing=10,
                        run_spacing=10,
                        controls=[
                            ft.Container(
                                col={"xs": 6},
                                content=card(
                                    ft.Column(
                                        spacing=2,
                                        controls=[
                                            ft.Row(
                                                spacing=6,
                                                controls=[
                                                    ft.Icon(ft.Icons.WATER_DROP_OUTLINED, size=16, color=BRAND_GREEN),
                                                    ft.Text("HUMEDAD", size=8, color=c_muted(), weight=ft.FontWeight.W_900),
                                                ],
                                            ),
                                            ft.Text("65%", size=14, weight=ft.FontWeight.W_900, color=c_text()),
                                        ],
                                    ),
                                    padding=12,
                                    radius=16,
                                ),
                            ),
                            ft.Container(
                                col={"xs": 6},
                                content=card(
                                    ft.Column(
                                        spacing=2,
                                        controls=[
                                            ft.Row(
                                                spacing=6,
                                                controls=[
                                                    ft.Icon(ft.Icons.AIR_OUTLINED, size=16, color=BRAND_GREEN),
                                                    ft.Text("VIENTO", size=8, color=c_muted(), weight=ft.FontWeight.W_900),
                                                ],
                                            ),
                                            ft.Text("12 km/h", size=14, weight=ft.FontWeight.W_900, color=c_text()),
                                        ],
                                    ),
                                    padding=12,
                                    radius=16,
                                ),
                            ),
                        ],
                    ),
                ],
            ),
            padding=18,
        )

    # ✅ FIX: acción con wrap (no se corta)
    def action_box(text: str):
        return ft.Container(
            padding=ft.Padding(12, 10, 12, 10),
            border_radius=16,
            bgcolor=ft.Colors.with_opacity(0.12, ft.Colors.GREEN_400),
            content=ft.Row(
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.START,
                controls=[
                    ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE, size=18, color=BRAND_GREEN),
                    ft.Container(
                        expand=True,  # ✅ ocupa el ancho disponible
                        content=ft.Text(
                            text,
                            size=10,
                            color=BRAND_GREEN,
                            weight=ft.FontWeight.W_900,
                            no_wrap=False,  # ✅ permite varias líneas
                        ),
                    ),
                ],
            ),
        )

    def impact_box(text: str):
        return ft.Container(
            padding=ft.Padding(12, 10, 12, 10),
            border_radius=16,
            border=ft.Border.all(1, c_border()),
            bgcolor=ft.Colors.with_opacity(0.04, ft.Colors.BLACK if not _is_dark(page) else ft.Colors.WHITE),
            content=ft.Column(
                spacing=6,
                controls=[
                    ft.Text("IMPACTO EN CULTIVO", size=8, color=c_muted(), weight=ft.FontWeight.W_900),
                    ft.Text(text, size=10, color=c_text(), weight=ft.FontWeight.W_700),
                ],
            ),
        )

    def alert_card(title: str, tag_text: str, tag_bg, tag_fg, icon, when: str, impact: str, action: str):
        return card(
            ft.Column(
                spacing=12,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Row(
                                spacing=10,
                                controls=[
                                    ft.Container(
                                        width=34,
                                        height=34,
                                        border_radius=999,
                                        bgcolor=ft.Colors.with_opacity(
                                            0.12, ft.Colors.RED_400 if "CRÍT" in tag_text else ft.Colors.AMBER_400
                                        ),
                                        alignment=ft.Alignment(0, 0),
                                        content=ft.Icon(icon, size=18, color=ft.Colors.RED_400 if "CRÍT" in tag_text else ft.Colors.AMBER_700),
                                    ),
                                    ft.Column(
                                        spacing=2,
                                        controls=[
                                            ft.Text(title, size=12, weight=ft.FontWeight.W_900, color=c_text()),
                                            ft.Text(when, size=9, weight=ft.FontWeight.W_700, color=c_muted()),
                                        ],
                                    ),
                                ],
                            ),
                            pill(tag_text, tag_bg, tag_fg),
                        ],
                    ),
                    impact_box(impact),
                    action_box(action),
                ],
            ),
            padding=16,
        )

    def active_alerts_panel():
        top = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Text("Alertas Activas", size=14, weight=ft.FontWeight.W_900, color=c_text()),
                pill("2 CRÍTICAS", ft.Colors.with_opacity(0.12, ft.Colors.RED_400), ft.Colors.RED_400),
            ],
        )
        a1 = alert_card(
            title="Riesgo de Helada",
            tag_text="CRÍTICO",
            tag_bg=ft.Colors.with_opacity(0.12, ft.Colors.RED_400),
            tag_fg=ft.Colors.RED_400,
            icon=ft.Icons.AC_UNIT_OUTLINED,
            when="Desciende a 2°C prevista hoy a las 03:00 AM",
            impact="Muerte de tejidos en floración y quemadura de brotes jóvenes del aguacate.",
            action="Acción: Activar riego por aspersión preventivo para elevar la temperatura del dosel.",
        )
        a2 = alert_card(
            title="Alta Radiación UV",
            tag_text="ADVERTENCIA",
            tag_bg=ft.Colors.with_opacity(0.14, ft.Colors.AMBER_400),
            tag_fg=ft.Colors.AMBER_700,
            icon=ft.Icons.WB_SUNNY_OUTLINED,
            when="Índice UV 11+ proyectado para mediodía",
            impact="Deshidratación severa de hojas y posible “golpe de sol” en la fruta expuesta.",
            action="Acción: Aumentar frecuencia de riego un 15% para mantener turgencia celular.",
        )
        return ft.Column(spacing=14, controls=[top, a1, a2])

    def forecast_card(title: str, today: str, tomorrow: str, thu: str):
        def row(day: str, icon, temp: str):
            return ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Row(spacing=8, controls=[ft.Icon(icon, size=18, color=BRAND_GREEN),
                                                ft.Text(day, size=10, color=c_muted(), weight=ft.FontWeight.W_800)]),
                    ft.Text(temp, size=10, color=c_text(), weight=ft.FontWeight.W_900),
                ],
            )

        return card(
            ft.Column(
                spacing=10,
                controls=[
                    ft.Text(title, size=11, weight=ft.FontWeight.W_900, color=c_text()),
                    ft.Divider(height=1, color=c_border()),
                    row("Hoy", ft.Icons.WB_SUNNY_OUTLINED, today),
                    row("Mañ", ft.Icons.CLOUD_OUTLINED, tomorrow),
                    row("Jue", ft.Icons.BEACH_ACCESS_OUTLINED, thu),
                ],
            ),
            padding=14,
            radius=18,
        )

    def forecast_panel():
        return ft.Column(
            spacing=12,
            controls=[
                ft.Text("Pronóstico por\nParcela", size=14, weight=ft.FontWeight.W_900, color=c_text()),
                forecast_card("• Parcela Norte", "26° / 14°", "18° / 2°", "22° / 8°"),
                forecast_card("• Lote Sur", "28° / 15°", "19° / 4°", "17° / 9°"),
            ],
        )

    # ---- Build responsive content
    content_host = ft.Container(expand=True)

    def build_content():
        mode = layout_mode()

        # anchos variables (para no romper en pantallas chicas/medias)
        w = page.width or 1200
        side_w = 280 if w >= 1400 else 260 if w >= 1200 else 240

        weather = ft.Container(width=side_w if mode != "1col" else None, content=weather_card())
        forecast = ft.Container(width=side_w if mode == "3col" else None, content=forecast_panel())
        center = ft.Container(expand=True, content=ft.Column(spacing=14, controls=[header_bar(), active_alerts_panel()]))

        if mode == "3col":
            return ft.Row(
                spacing=14,
                vertical_alignment=ft.CrossAxisAlignment.START,
                controls=[weather, center, forecast],
            )

        if mode == "2col":
            # 2 col: arriba header+alertas (full), abajo weather + forecast (2 columnas)
            return ft.Column(
                spacing=14,
                controls=[
                    header_bar(),
                    active_alerts_panel(),
                    ft.ResponsiveRow(
                        spacing=14,
                        run_spacing=14,
                        controls=[
                            ft.Container(col={"xs": 12, "md": 6}, content=weather_card()),
                            ft.Container(col={"xs": 12, "md": 6}, content=forecast_panel()),
                        ],
                    ),
                    ft.Container(height=60),
                ],
            )

        # 1 col: todo apilado
        return ft.Column(
            spacing=14,
            controls=[
                header_bar(),
                weather_card(),
                active_alerts_panel(),
                forecast_panel(),
                ft.Container(height=60),
            ],
        )

    def rebuild(*_):
        content_host.content = build_content()
        page.update()

    page.on_resized = rebuild
    rebuild()

    root = build_app_shell(page, content_host)

    return ft.View(
        route="/alerts",
        scroll=ft.ScrollMode.ALWAYS,
        controls=[ft.SafeArea(expand=True, content=root)],
    )
