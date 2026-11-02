# src/ui/views/profile_view.py
import flet as ft
from services.settings_service import load_theme
from ui.components.app_shell import build_app_shell, BRAND_GREEN


def _is_dark(page: ft.Page) -> bool:
    return page.theme_mode == ft.ThemeMode.DARK


def create_profile_view(page: ft.Page) -> ft.View:
    db = page.data.get("db")

    # sync theme
    if db is not None:
        saved = load_theme(db)
        page.theme_mode = ft.ThemeMode.DARK if saved == "dark" else ft.ThemeMode.LIGHT

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

    def card(content: ft.Control, padding=18, radius=22, width=None):
        return ft.Container(
            width=width,  # ✅ clave: forzar ancho cuando haga falta
            padding=ft.Padding(padding, padding, padding, padding),
            border_radius=radius,
            bgcolor=c_surface(),
            border=ft.Border.all(1, c_border()),
            shadow=shadow(),
            content=content,
        )

    def section_label(txt: str):
        return ft.Text(txt.upper(), size=9, weight=ft.FontWeight.W_900, color=c_muted())

    def snack(msg: str):
        page.snack_bar = ft.SnackBar(ft.Text(msg))
        page.snack_bar.open = True
        page.update()

    def list_item(icon, title: str, on_click=None, danger=False):
        return ft.Container(
            border_radius=16,
            border=ft.Border.all(1, c_border()),
            bgcolor=c_surface(),
            padding=ft.Padding(14, 12, 14, 12),
            ink=True,
            on_click=on_click,
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Row(
                        spacing=10,
                        controls=[
                            ft.Container(
                                width=32,
                                height=32,
                                border_radius=12,
                                bgcolor=ft.Colors.with_opacity(0.12, ft.Colors.RED_400 if danger else ft.Colors.GREEN_400),
                                alignment=ft.Alignment(0, 0),
                                content=ft.Icon(icon, size=18, color=ft.Colors.RED_400 if danger else BRAND_GREEN),
                            ),
                            ft.Text(
                                title,
                                size=11,
                                weight=ft.FontWeight.W_900,
                                color=ft.Colors.RED_400 if danger else c_text(),
                            ),
                        ],
                    ),
                    ft.Icon(ft.Icons.CHEVRON_RIGHT, color=c_muted()),
                ],
            ),
        )

    def metric_card(label: str, value: str, icon):
        return card(
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Column(
                        spacing=2,
                        controls=[
                            ft.Text(label.upper(), size=8, color=c_muted(), weight=ft.FontWeight.W_900),
                            ft.Text(value, size=18, color=c_text(), weight=ft.FontWeight.W_900),
                        ],
                    ),
                    ft.Container(
                        width=40,
                        height=40,
                        border_radius=14,
                        bgcolor=ft.Colors.with_opacity(0.12, ft.Colors.GREEN_400),
                        alignment=ft.Alignment(0, 0),
                        content=ft.Icon(icon, color=BRAND_GREEN),
                    ),
                ],
            ),
            padding=14,
            radius=18,
        )

    # ✅ Header usuario FULL WIDTH (forzado)
    def user_header(width=None):
        return card(
            ft.Column(
                spacing=10,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Stack(
                        width=88,
                        height=88,
                        controls=[
                            ft.CircleAvatar(
                                radius=42,
                                bgcolor=ft.Colors.with_opacity(0.12, ft.Colors.GREEN_400),
                                content=ft.Icon(ft.Icons.PERSON, size=40, color=BRAND_GREEN),
                            ),
                            ft.Container(
                                alignment=ft.Alignment(0.78, 0.78),
                                content=ft.Container(
                                    width=22,
                                    height=22,
                                    border_radius=999,
                                    bgcolor=BRAND_GREEN,
                                    border=ft.Border.all(3, c_surface()),
                                    alignment=ft.Alignment(0, 0),
                                    content=ft.Icon(ft.Icons.CHECK, size=14, color=ft.Colors.WHITE),
                                ),
                            ),
                        ],
                    ),
                    ft.Text("Valentino Oriundo", size=16, weight=ft.FontWeight.W_900, color=c_text()),
                    ft.Text("PRODUCTOR VERIFICADO", size=9, weight=ft.FontWeight.W_900, color=BRAND_GREEN),
                    ft.Text("ID Agro: AV-29481", size=9, weight=ft.FontWeight.W_700, color=c_muted()),
                ],
            ),
            padding=18,
            radius=22,
            width=width,  # ✅ aquí ya no se queda “angosta”
        )

    def build_content():
        w = page.width or 1200
        narrow = w < 980

        # ancho del contenido en desktop, como tu referencia
        content_width = 820 if not narrow else None

        metrics = ft.ResponsiveRow(
            spacing=14,
            run_spacing=14,
            controls=[
                ft.Container(col={"xs": 12, "md": 6}, content=metric_card("Parcelas", "4", ft.Icons.GRID_VIEW)),
                ft.Container(col={"xs": 12, "md": 6}, content=metric_card("Análisis", "156", ft.Icons.QUERY_STATS)),
            ],
        )

        account_box = ft.Column(
            spacing=10,
            controls=[
                section_label("Cuenta"),
                card(
                    ft.Column(
                        spacing=10,
                        controls=[
                            list_item(ft.Icons.EDIT_OUTLINED, "Editar Perfil", on_click=lambda _: snack("Editar perfil (mock)")),
                            list_item(ft.Icons.LOCK_OUTLINE, "Seguridad", on_click=lambda _: snack("Seguridad (mock)")),
                        ],
                    ),
                    padding=12,
                    radius=18,
                ),
            ],
        )

        prefs_box = ft.Column(
            spacing=10,
            controls=[
                section_label("Preferencias"),
                card(
                    ft.Column(
                        spacing=10,
                        controls=[
                            list_item(ft.Icons.CLOUD_OUTLINED, "Notificaciones climáticas", on_click=lambda _: snack("Notificaciones (mock)")),
                            list_item(ft.Icons.STRAIGHTEN, "Unidad de medida", on_click=lambda _: snack("Unidades (mock)")),
                        ],
                    ),
                    padding=12,
                    radius=18,
                ),
            ],
        )

        support_box = ft.Column(
            spacing=10,
            controls=[
                section_label("Soporte"),
                card(
                    ft.Column(
                        spacing=10,
                        controls=[
                            list_item(ft.Icons.HELP_OUTLINE, "Centro de Ayuda", on_click=lambda _: snack("Centro de ayuda (mock)")),
                            list_item(ft.Icons.DESCRIPTION_OUTLINED, "Términos y condiciones", on_click=lambda _: snack("Términos (mock)")),
                        ],
                    ),
                    padding=12,
                    radius=18,
                ),
            ],
        )

        logout = list_item(ft.Icons.LOGOUT, "Cerrar sesión", on_click=lambda _: snack("Cerrar sesión (mock)"), danger=True)

        column = ft.Column(
            spacing=14,
            controls=[
                user_header(width=content_width),  # ✅ full width como la imagen 2
                metrics,
                account_box,
                prefs_box,
                support_box,
                logout,
                ft.Container(height=40),
            ],
        )

        if not narrow:
            return ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                controls=[ft.Container(width=content_width, content=column)],
            )

        return column

    content_host = ft.Container(expand=True)

    def rebuild(*_):
        content_host.content = build_content()
        page.update()

    page.on_resized = rebuild
    rebuild()

    root = build_app_shell(page, content_host)
    return ft.View(route="/profile", scroll=ft.ScrollMode.ALWAYS, controls=[ft.SafeArea(expand=True, content=root)])
