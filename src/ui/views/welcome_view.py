import asyncio

import flet as ft

from services.settings_service import load_theme, save_language, save_theme
from ui.state import get_state


def create_welcome_view(page: ft.Page) -> ft.View:
    db = page.data["db"]
    state = get_state(page)

    BRAND_GREEN = "#2F5D46"

    LIGHT_BG_TOP = "#EAF0EB"
    LIGHT_BG_MIDDLE = "#F6F8F5"
    LIGHT_BG_BOTTOM = "#FFFFFF"

    DARK_BG_TOP = "#101713"
    DARK_BG_MIDDLE = "#17231D"
    DARK_BG_BOTTOM = "#0F1115"

    def nav(route: str):
        asyncio.create_task(page.push_route(route))

    def lang_label(code: str) -> str:
        labels = {
            "es": state.t("language_name_es"),
            "qu": state.t("language_name_qu"),
            "ay": state.t("language_name_ay"),
            "en": state.t("language_name_en"),
        }
        return labels.get(code, labels["es"])

    # ---------------- Theme helpers ----------------
    saved_theme = load_theme(db)
    page.theme_mode = (
        ft.ThemeMode.DARK if saved_theme == "dark" else ft.ThemeMode.LIGHT
    )

    def is_dark() -> bool:
        return page.theme_mode == ft.ThemeMode.DARK

    def card_bg():
        return "#1E1F22" if is_dark() else ft.Colors.WHITE

    def text_primary():
        return ft.Colors.WHITE if is_dark() else ft.Colors.BLACK

    def text_secondary():
        return ft.Colors.GREY_300 if is_dark() else ft.Colors.GREY_700

    def border_color(selected: bool):
        if selected:
            return ft.Colors.GREEN_300
        return ft.Colors.GREY_700 if is_dark() else ft.Colors.GREY_200

    def item_bg(selected: bool):
        if selected:
            return (
                ft.Colors.with_opacity(0.18, ft.Colors.GREEN_400)
                if is_dark()
                else ft.Colors.GREEN_50
            )
        return "#2A2C31" if is_dark() else ft.Colors.WHITE

    def overlay_bg():
        return (
            ft.Colors.with_opacity(0.65, ft.Colors.BLACK)
            if is_dark()
            else ft.Colors.with_opacity(0.45, ft.Colors.BLACK)
        )

    def page_gradient():
        colors = (
            [DARK_BG_TOP, DARK_BG_MIDDLE, DARK_BG_BOTTOM]
            if is_dark()
            else [LIGHT_BG_TOP, LIGHT_BG_MIDDLE, LIGHT_BG_BOTTOM]
        )

        return ft.LinearGradient(
            begin=ft.Alignment(-1, -1),
            end=ft.Alignment(1, 1),
            colors=colors,
            stops=[0.0, 0.55, 1.0],
        )

    # ---------------- UI base ----------------
    title = ft.Text(
        "",
        size=26,
        weight=ft.FontWeight.W_800,
        color=text_primary(),
        text_align=ft.TextAlign.CENTER,
    )

    subtitle = ft.Text(
        "",
        size=13,
        color=text_secondary(),
        text_align=ft.TextAlign.CENTER,
    )

    offline_note = ft.Text(
        "",
        size=12,
        color=text_secondary(),
        text_align=ft.TextAlign.CENTER,
    )

    def start_as_guest(_):
        current_db = page.data.get("db")
        if current_db:
            current_db.execute(
                """
                UPDATE session
                SET username = ?, is_active = 1, is_guest = 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = 1
                """,
                ("guest",),
            )

        nav("/scan")

    start_btn = ft.FilledButton(
        adaptive=False,
        content="",
        height=56,
        width=160,
        style=ft.ButtonStyle(
            bgcolor=BRAND_GREEN,
            color=ft.Colors.WHITE,
            shape=ft.RoundedRectangleBorder(radius=14),
            text_style=ft.TextStyle(
                size=18,
                weight=ft.FontWeight.W_600,
            ),
            elevation=2,
        ),
        on_click=start_as_guest,
    )

    have_account = ft.Text(
        "",
        size=12,
        color=text_secondary(),
        text_align=ft.TextAlign.CENTER,
    )

    login_link = ft.TextButton(
        adaptive=False,
        content="",
        on_click=lambda _: nav("/login"),
        style=ft.ButtonStyle(
            color=BRAND_GREEN,
            padding=ft.Padding(0, 0, 0, 0),
        ),
    )

    # ---------------- Theme toggle ----------------
    theme_btn = ft.IconButton(
        adaptive=False,
        icon=ft.Icons.DARK_MODE,
        tooltip="",
    )

    def refresh_theme_icon():
        theme_btn.icon = ft.Icons.LIGHT_MODE if is_dark() else ft.Icons.DARK_MODE

    def toggle_theme(_):
        new_mode = ft.ThemeMode.LIGHT if is_dark() else ft.ThemeMode.DARK
        page.theme_mode = new_mode
        save_theme(db, "dark" if new_mode == ft.ThemeMode.DARK else "light")

        apply_theme_to_controls()
        refresh_theme_icon()
        rebuild_language_items()
        page.update()

    theme_btn.on_click = toggle_theme

    # ---------------- Text refresh ----------------
    current_lang_label = ft.Text("", size=12, color=text_secondary())

    def refresh_texts():
        title.value = state.t("welcome_title").format(app=state.app_name)
        subtitle.value = state.t("welcome_subtitle")
        start_btn.content = state.t("start_button")
        offline_note.value = state.t("offline_note")
        have_account.value = state.t("have_account")
        login_link.content = state.t("login")

        hdr_title.value = state.t("language_modal_title")
        current_lang_label.value = state.t("language_current").format(
            language=lang_label(state.lang)
        )

        close_btn.tooltip = state.t("language_close")
        language_btn.tooltip = state.t("language_change_tooltip")
        theme_btn.tooltip = state.t("theme_change_tooltip")

        page.update()

    def apply_theme_to_controls():
        # Fondo dinámico
        background.gradient = page_gradient()

        # Logo
        hero_icon.bgcolor = ft.Colors.with_opacity(
            0.18 if is_dark() else 0.10,
            BRAND_GREEN,
        )

        # Textos principales
        title.color = text_primary()
        subtitle.color = text_secondary()
        offline_note.color = text_secondary()
        have_account.color = text_secondary()
        current_lang_label.color = text_secondary()

        # Overlay y tarjeta del selector de idioma
        modal_overlay.bgcolor = overlay_bg()
        modal_card.bgcolor = card_bg()

        # Encabezado e íconos del selector
        hdr_icon.color = text_secondary()
        hdr_title.color = text_primary()
        close_btn.icon_color = text_secondary()

        # Divisor
        divider.color = (
            ft.Colors.GREY_700 if is_dark() else ft.Colors.GREY_300
        )

    # ---------------- Modal idioma ----------------
    modal_overlay = ft.Container(
        visible=False,
        expand=True,
        bgcolor=overlay_bg(),
        alignment=ft.Alignment(0, 0),
        content=None,
    )

    def hide_modal(_=None):
        modal_overlay.visible = False
        page.update()

    def show_modal(_=None):
        rebuild_language_items()
        modal_overlay.visible = True
        page.update()

    def set_language(lang_code: str):
        state.lang = lang_code
        save_language(db, lang_code)

        rebuild_language_items()
        refresh_texts()
        apply_theme_to_controls()
        page.update()

    lang_items_col = ft.Column(tight=True, spacing=10)

    def option_item(label: str, code: str):
        selected = state.lang == code

        return ft.Container(
            border_radius=14,
            padding=ft.Padding(left=12, top=12, right=12, bottom=12),
            border=ft.Border.all(1, border_color(selected)),
            bgcolor=item_bg(selected),
            on_click=lambda e: set_language(code),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Row(
                        spacing=10,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Icon(
                                (
                                    ft.Icons.CHECK_CIRCLE
                                    if selected
                                    else ft.Icons.RADIO_BUTTON_UNCHECKED
                                ),
                                size=20,
                                color=(
                                    ft.Colors.GREEN_300
                                    if selected
                                    else (
                                        ft.Colors.GREY_400
                                        if is_dark()
                                        else ft.Colors.GREY_500
                                    )
                                ),
                            ),
                            ft.Text(
                                label,
                                size=15,
                                color=(
                                    text_primary()
                                    if selected
                                    else text_secondary()
                                ),
                                weight=(
                                    ft.FontWeight.W_700
                                    if selected
                                    else ft.FontWeight.W_600
                                ),
                            ),
                        ],
                    ),
                    ft.Icon(
                        ft.Icons.CHEVRON_RIGHT,
                        size=18,
                        color=text_secondary(),
                    ),
                ],
            ),
        )

    def rebuild_language_items():
        lang_items_col.controls = [
            option_item(lang_label("es"), "es"),
            option_item(lang_label("qu"), "qu"),
            option_item(lang_label("ay"), "ay"),
            option_item(lang_label("en"), "en"),
        ]

        current_lang_label.value = state.t("language_current").format(
            language=lang_label(state.lang)
        )

    # Controles del encabezado del modal
    hdr_icon = ft.Icon(
        ft.Icons.LANGUAGE,
        size=20,
        color=text_secondary(),
    )

    hdr_title = ft.Text(
        "",
        size=16,
        weight=ft.FontWeight.W_800,
        color=text_primary(),
    )

    close_btn = ft.IconButton(
        adaptive=False,
        icon=ft.Icons.CLOSE,
        tooltip="",
        on_click=hide_modal,
        icon_color=text_secondary(),
    )

    divider = ft.Divider(height=1)

    modal_card = ft.Container(
        width=380,
        border_radius=18,
        bgcolor=card_bg(),
        padding=ft.Padding(left=16, top=14, right=16, bottom=16),
        content=ft.Column(
            tight=True,
            spacing=12,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Row(
                            spacing=8,
                            controls=[hdr_icon, hdr_title],
                        ),
                        close_btn,
                    ],
                ),
                current_lang_label,
                divider,
                lang_items_col,
            ],
        ),
    )

    modal_overlay.on_click = hide_modal
    modal_overlay.content = ft.Container(
        alignment=ft.Alignment(0, 0),
        padding=ft.Padding(18, 18, 18, 18),
        content=modal_card,
    )

    # ---------------- Top bar ----------------
    language_btn = ft.IconButton(
        adaptive=False,
        icon=ft.Icons.LANGUAGE,
        tooltip="",
        on_click=show_modal,
    )

    top_bar = ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        controls=[
            ft.Container(),
            ft.Row(
                spacing=6,
                controls=[
                    theme_btn,
                    language_btn,
                ],
            ),
        ],
    )

    # ---------------- Hero ----------------
    hero_icon = ft.Container(
        width=78,
        height=78,
        border_radius=22,
        bgcolor=(
            ft.Colors.with_opacity(0.15, ft.Colors.GREEN_400)
            if is_dark()
            else ft.Colors.GREEN_50
        ),
        alignment=ft.Alignment(0, 0),
        content=ft.Image(
            src="avocado.png",
            width=48,
            height=48,
            fit=ft.BoxFit.CONTAIN,
        ),
    )

    background = ft.Container(
        expand=True,
        gradient=page_gradient(),
        content=ft.Stack(
            expand=True,
            controls=[
                ft.Container(
                    right=-150,
                    top=-150,
                    width=340,
                    height=340,
                    border_radius=170,
                    bgcolor=ft.Colors.with_opacity(
                        0.07 if is_dark() else 0.05,
                        BRAND_GREEN,
                    ),
                ),
                ft.Container(
                    left=-120,
                    bottom=-120,
                    width=280,
                    height=280,
                    border_radius=140,
                    bgcolor=ft.Colors.with_opacity(
                        0.05 if is_dark() else 0.035,
                        BRAND_GREEN,
                    ),
                ),
            ],
        ),
    )

    # Fila final: "¿Ya tienes una cuenta? Iniciar sesión"
    account_row = ft.Row(
        alignment=ft.MainAxisAlignment.CENTER,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=6,
        wrap=True,
        controls=[
            have_account,
            login_link,
        ],
    )

    # Bloque que se centra en celular desde el logo hasta iniciar sesión.
    hero_content = ft.Column(
        tight=True,
        width=420,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=18,
        controls=[
            hero_icon,
            ft.Column(
                tight=True,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=6,
                controls=[
                    title,
                    subtitle,
                ],
            ),
            ft.Container(height=8),
            start_btn,
            offline_note,
            ft.Container(height=10),
            account_row,
        ],
    )

    # Su contenido cambia según el ancho de la pantalla.
    base_content = ft.Container(expand=True)

    root = ft.Stack(
        expand=True,
        controls=[
            background,
            base_content,
            modal_overlay,
        ],
    )

    def build_layout(update_page: bool = True):
        width = page.width or 390

        # =========================
        # CELULAR
        # =========================
        if width < 700:
            side_margin = 18
            top_margin = 14
            bottom_margin = 20

            hero_content.width = min(
                max(width - (side_margin * 2), 280),
                390,
            )

            base_content.alignment = None
            base_content.padding = ft.Padding(
                side_margin,
                top_margin,
                side_margin,
                bottom_margin,
            )

            base_content.content = ft.Stack(
                expand=True,
                controls=[
                    # Tema e idioma permanecen arriba.
                    ft.Container(
                        left=0,
                        top=0,
                        right=0,
                        content=top_bar,
                    ),
                    # Desde el logo hasta iniciar sesión queda centrado.
                    ft.Container(
                        left=0,
                        top=54,
                        right=0,
                        bottom=0,
                        alignment=ft.Alignment(0, 0),
                        content=hero_content,
                    ),
                ],
            )

        # =========================
        # TABLET, WEB Y ESCRITORIO
        # =========================
        else:
            hero_content.width = 420

            base_content.alignment = ft.Alignment(0, 0)
            base_content.padding = ft.Padding(
                left=18,
                top=20,
                right=18,
                bottom=20,
            )

            # Conserva una distribución similar a la versión original.
            base_content.content = ft.Column(
                width=420,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=18,
                controls=[
                    top_bar,
                    ft.Container(height=6),
                    hero_content,
                ],
            )

        if update_page:
            page.update()

    def on_resize(_):
        build_layout(update_page=True)

    # ---------------- Init ----------------
    page.on_resize = on_resize

    build_layout(update_page=False)
    refresh_theme_icon()
    rebuild_language_items()
    apply_theme_to_controls()
    refresh_texts()

    return ft.View(
        route="/welcome",
        controls=[
            ft.SafeArea(
                expand=True,
                content=root,
            )
        ],
    )
