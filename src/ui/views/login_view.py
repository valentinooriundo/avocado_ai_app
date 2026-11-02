import asyncio
import requests
import flet as ft

from ui.state import get_state
from services.settings_service import load_theme
from services.google_auth_service import get_google_provider
from services.firebase_auth_service import (
    sign_in_with_firebase_custom_token,
    get_backend_auth_url,
)
from services.firebase_email_auth_service import (
    login_with_email_password,
    FirebaseEmailAuthError,
    map_firebase_auth_error,
)
from services.auth_session_service import save_auth_data
from services.backend_profile_service import upsert_user_profile_backend


def create_login_view(page: ft.Page) -> ft.View:
    db = page.data.get("db")
    state = get_state(page)
    google_provider = get_google_provider()

    APP_LOGO_SRC = "avocado.png"
    GOOGLE_LOGO_SRC = "google.png"
    SLIDE_1_SRC = "slide1-login.png"
    SLIDE_2_SRC = "slide2-login.png"
    SLIDE_3_SRC = "slide3-login.png"

    def t(key: str, fallback: str | None = None):
        value = state.t(key)
        if value is None:
            return fallback if fallback is not None else key
        return value

    def nav(route: str):
        page.run_task(page.push_route, route)

    def back(_=None):
        nav("/welcome")

    if db is not None:
        saved_theme = load_theme(db)
        page.theme_mode = (
            ft.ThemeMode.DARK if saved_theme == "dark" else ft.ThemeMode.LIGHT
        )

    def is_dark() -> bool:
        return page.theme_mode == ft.ThemeMode.DARK

    def c_bg():
        return "#0F1115" if is_dark() else "#F6F8F4"

    def c_card_soft():
        return "#151C2C" if is_dark() else "#FFFFFF"

    def c_text():
        return "#F3F4F6" if is_dark() else "#111827"

    def c_muted():
        return "#9CA3AF" if is_dark() else "#6B7280"

    def c_border():
        return "#243046" if is_dark() else "#E5E7EB"

    def c_divider():
        return "#263143" if is_dark() else "#E5E7EB"

    def c_input_bg():
        return "#0E1626" if is_dark() else "#FFFFFF"

    BRAND_GREEN = "#2F5D46"
    BG_TOP = "#EEF3ED"
    BG_BASE = "#FAFBF8"

    # =========================
    # Modern toast custom
    # =========================
    toast_icon = ft.Icon(ft.Icons.INFO, size=20, color=ft.Colors.WHITE)
    toast_title = ft.Text(
        "",
        size=13,
        weight=ft.FontWeight.W_800,
        color=ft.Colors.WHITE,
    )
    toast_message = ft.Text(
        "",
        size=11,
        color=ft.Colors.WHITE,
        max_lines=2,
    )
    toast_bar = ft.Container(width=5, border_radius=8)
    toast_close = ft.IconButton(
        icon=ft.Icons.CLOSE,
        icon_size=16,
        icon_color=ft.Colors.WHITE,
        style=ft.ButtonStyle(padding=0),
    )

    toast_card = ft.Container(
        visible=False,
        opacity=0,
        animate_opacity=200,
        right=18,
        top=18,
        width=340,
        border_radius=16,
        bgcolor="#1F2937",
        shadow=ft.BoxShadow(
            blur_radius=18,
            spread_radius=0,
            color=ft.Colors.with_opacity(0.18, ft.Colors.BLACK),
            offset=ft.Offset(0, 6),
        ),
        content=ft.Row(
            spacing=0,
            controls=[
                toast_bar,
                ft.Container(
                    expand=True,
                    padding=ft.Padding(14, 12, 14, 12),
                    content=ft.Row(
                        vertical_alignment=ft.CrossAxisAlignment.START,
                        controls=[
                            ft.Container(
                                margin=ft.Margin(0, 2, 10, 0),
                                content=toast_icon,
                            ),
                            ft.Column(
                                expand=True,
                                spacing=2,
                                controls=[toast_title, toast_message],
                            ),
                            toast_close,
                        ],
                    ),
                ),
            ],
        ),
    )

    async def hide_toast_after(delay: float = 2.8):
        await asyncio.sleep(delay)
        toast_card.opacity = 0
        page.update()
        await asyncio.sleep(0.22)
        toast_card.visible = False
        page.update()

    def show_toast(message: str, kind: str = "info", title: str | None = None):
        if toast_card not in page.overlay:
            page.overlay.append(toast_card)

        if kind == "success":
            toast_card.bgcolor = "#FFFFFF" if not is_dark() else "#1D2A22"
            toast_bar.bgcolor = "#2ECC71"
            toast_icon.name = ft.Icons.CHECK_CIRCLE
            toast_icon.color = "#2ECC71"
            toast_title.value = title or "Success"
            toast_title.color = "#111827" if not is_dark() else "#F9FAFB"
            toast_message.color = "#6B7280" if not is_dark() else "#D1D5DB"
            toast_message.value = message
            toast_close.icon_color = "#6B7280" if not is_dark() else "#D1D5DB"
        elif kind == "error":
            toast_card.bgcolor = "#FFFFFF" if not is_dark() else "#2A1D1F"
            toast_bar.bgcolor = "#FF3B5C"
            toast_icon.name = ft.Icons.CANCEL
            toast_icon.color = "#FF3B5C"
            toast_title.value = title or "Error"
            toast_title.color = "#111827" if not is_dark() else "#F9FAFB"
            toast_message.color = "#6B7280" if not is_dark() else "#D1D5DB"
            toast_message.value = message
            toast_close.icon_color = "#6B7280" if not is_dark() else "#D1D5DB"
        elif kind == "warning":
            toast_card.bgcolor = "#FFFFFF" if not is_dark() else "#2C281A"
            toast_bar.bgcolor = "#F4B400"
            toast_icon.name = ft.Icons.WARNING_AMBER_ROUNDED
            toast_icon.color = "#F4B400"
            toast_title.value = title or "Warning"
            toast_title.color = "#111827" if not is_dark() else "#F9FAFB"
            toast_message.color = "#6B7280" if not is_dark() else "#D1D5DB"
            toast_message.value = message
            toast_close.icon_color = "#6B7280" if not is_dark() else "#D1D5DB"
        else:
            toast_card.bgcolor = "#FFFFFF" if not is_dark() else "#1F2937"
            toast_bar.bgcolor = "#3B82F6"
            toast_icon.name = ft.Icons.INFO
            toast_icon.color = "#3B82F6"
            toast_title.value = title or "Info"
            toast_title.color = "#111827" if not is_dark() else "#F9FAFB"
            toast_message.color = "#6B7280" if not is_dark() else "#D1D5DB"
            toast_message.value = message
            toast_close.icon_color = "#6B7280" if not is_dark() else "#D1D5DB"

        def close_now(_=None):
            toast_card.opacity = 0
            page.update()

        toast_close.on_click = close_now

        toast_card.visible = True
        toast_card.opacity = 1
        page.update()
        page.run_task(hide_toast_after)

    def show_error(message: str):
        show_toast(message, "error", "Error")

    def show_success(message: str):
        show_toast(message, "success", "Success")

    def input_container(control: ft.Control) -> ft.Container:
        return ft.Container(
            padding=ft.Padding(12, 4, 12, 4),
            border_radius=18,
            bgcolor=c_input_bg(),
            border=ft.Border.all(1, c_border()),
            content=control,
        )

    def divider_with_text(label: str) -> ft.Row:
        return ft.Row(
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
            controls=[
                ft.Container(height=1, bgcolor=c_divider(), expand=True),
                ft.Text(label, size=12, color=c_muted()),
                ft.Container(height=1, bgcolor=c_divider(), expand=True),
            ],
        )

    async def do_google_login():
        await page.login(
            provider=google_provider,
            fetch_user=True,
        )

    def login_with_google(_):
        try:
            page.run_task(do_google_login)
        except Exception as ex:
            show_error(f"No se pudo iniciar Google OAuth: {ex}")

    def login_with_email(_=None):
        email = (email_tf.value or "").strip().lower()
        password = (pwd_tf.value or "").strip()

        if not email:
            show_error("Ingresa tu correo electrónico.")
            try:
                email_tf.focus()
            except Exception:
                pass
            return

        if not password:
            show_error("Ingresa tu contraseña.")
            try:
                pwd_tf.focus()
            except Exception:
                pass
            return

        continue_btn.disabled = True
        continue_btn.content.value = "INGRESANDO..."
        page.update()

        try:
            firebase_session = login_with_email_password(email, password)

            auth_payload = {
                "firebase_id_token": firebase_session.get("idToken"),
                "firebase_refresh_token": firebase_session.get("refreshToken"),
                "firebase_expires_in": firebase_session.get("expiresIn"),
                "firebase_local_id": firebase_session.get("localId"),
                "firebase_uid": firebase_session.get("localId"),
                "firebase_email": firebase_session.get("email"),
                "firebase_name": firebase_session.get("displayName", ""),
                "auth_provider": "password",
            }

            save_auth_data(page, auth_payload)
            show_success("Inicio de sesión correcto.")
            page.run_task(page.push_route, "/dashboard")

        except FirebaseEmailAuthError as ex:
            show_error(map_firebase_auth_error(str(ex)))
        except Exception as ex:
            show_error(f"No se pudo iniciar sesión: {ex}")
        finally:
            continue_btn.disabled = False
            continue_btn.content.value = t("login_continue", "CONTINUAR")
            page.update()

    def on_login(e):
        if getattr(e, "error", None):
            show_error(f"Error al iniciar con Google: {e.error}")
            return

        async def finish_login_flow():
            google_btn.disabled = True
            page.update()

            try:
                auth_data = getattr(page, "auth", None)
                user_data = getattr(auth_data, "user", None) if auth_data else None

                if not user_data:
                    raise ValueError("No se recibió perfil de usuario de Google.")

                backend_url = get_backend_auth_url()

                response = requests.post(
                    f"{backend_url}/auth/google/flet",
                    json={
                        "sub": user_data.get("sub"),
                        "email": user_data.get("email"),
                        "name": user_data.get("name", ""),
                        "given_name": user_data.get("given_name", ""),
                        "family_name": user_data.get("family_name", ""),
                        "picture": user_data.get("picture", ""),
                        "email_verified": user_data.get("email_verified", False),
                    },
                    timeout=20,
                )
                response.raise_for_status()
                backend_data = response.json()

                firebase_session = sign_in_with_firebase_custom_token(
                    backend_data["custom_token"]
                )

                auth_payload = {
                    "firebase_id_token": firebase_session.get("idToken"),
                    "firebase_refresh_token": firebase_session.get("refreshToken"),
                    "firebase_expires_in": firebase_session.get("expiresIn"),
                    "firebase_local_id": firebase_session.get("localId"),
                    "firebase_uid": backend_data.get("uid"),
                    "firebase_email": backend_data.get("email"),
                    "firebase_name": backend_data.get("name"),
                    "auth_provider": "google",
                }

                save_auth_data(page, auth_payload)

                try:
                    existing_phone = page.data.get("reg_phone", "")
                    existing_farm = page.data.get("reg_farm", "")
                    existing_variety = page.data.get("reg_variety", "")

                    if existing_phone:
                        upsert_user_profile_backend(
                            uid=auth_payload["firebase_uid"],
                            full_name=auth_payload.get("firebase_name")
                            or backend_data.get("name")
                            or "Usuario",
                            email=auth_payload.get("firebase_email")
                            or backend_data.get("email"),
                            phone_e164=existing_phone,
                            farm_location=existing_farm,
                            avocado_variety=existing_variety,
                            auth_provider="google",
                            firebase_id_token=auth_payload.get("firebase_id_token"),
                        )
                except Exception:
                    pass

                await asyncio.sleep(0.15)
                show_success("Inicio de sesión con Google correcto.")
                await page.push_route("/dashboard")

            except requests.HTTPError as ex:
                detail = ""
                try:
                    detail = ex.response.text
                except Exception:
                    detail = str(ex)
                show_error(f"Error HTTP en autenticación: {detail}")
            except Exception as ex:
                show_error(f"Error en autenticación Firebase: {ex}")
            finally:
                google_btn.disabled = False
                page.update()

        page.run_task(finish_login_flow)

    page.on_login = on_login

    email_tf = ft.TextField(
        hint_text="nombre@avoruna.com",
        border=ft.InputBorder.NONE,
        text_size=13,
        height=42,
        content_padding=ft.Padding(6, 10, 6, 10),
        prefix_icon=ft.Icons.MAIL_OUTLINE,
        keyboard_type=ft.KeyboardType.EMAIL,
        on_submit=login_with_email,
    )

    pwd_tf = ft.TextField(
        hint_text="Ingresa tu contraseña",
        border=ft.InputBorder.NONE,
        text_size=13,
        height=42,
        password=True,
        can_reveal_password=False,
        content_padding=ft.Padding(6, 10, 6, 10),
        prefix_icon=ft.Icons.LOCK_OUTLINE,
        on_submit=login_with_email,
    )

    eye_btn = ft.IconButton(
        icon=ft.Icons.VISIBILITY_OFF,
        tooltip="Mostrar/Ocultar",
        icon_size=18,
    )

    def toggle_pwd(_):
        pwd_tf.password = not pwd_tf.password
        eye_btn.icon = (
            ft.Icons.VISIBILITY_OFF if pwd_tf.password else ft.Icons.VISIBILITY
        )
        page.update()

    eye_btn.on_click = toggle_pwd
    pwd_tf.suffix = eye_btn

    title_txt = ft.Text(
        "",
        size=24,
        weight=ft.FontWeight.W_900,
        color=c_text(),
        text_align=ft.TextAlign.LEFT,
    )
    subtitle_txt = ft.Text(
        "",
        size=13,
        color=c_muted(),
        text_align=ft.TextAlign.LEFT,
    )

    email_label_txt = ft.Text(
        "",
        size=11,
        color=c_text(),
        weight=ft.FontWeight.W_700,
    )
    pwd_label_txt = ft.Text(
        "",
        size=11,
        color=c_text(),
        weight=ft.FontWeight.W_700,
    )

    forgot_pwd_link = ft.TextButton(
        content=ft.Text(
            "",
            size=11,
            color=BRAND_GREEN,
            weight=ft.FontWeight.W_800,
        ),
        on_click=lambda _: nav("/help"),
        style=ft.ButtonStyle(padding=ft.Padding(0, 0, 0, 0)),
    )

    continue_btn = ft.Button(
        adaptive=False,
        content=ft.Text(
            "",
            weight=ft.FontWeight.W_800,
            color=ft.Colors.WHITE,
            size=13,
        ),
        bgcolor=BRAND_GREEN,
        color=ft.Colors.WHITE,
        height=46,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=16),
            padding=ft.Padding.symmetric(horizontal=20, vertical=12),
        ),
        on_click=login_with_email,
    )

    continue_btn.expand = True

    google_btn_text = ft.Text(
        "",
        weight=ft.FontWeight.W_700,
        color=c_text(),
        size=12,
    )

    google_btn = ft.OutlinedButton(
        adaptive=False,
        content=ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10,
            controls=[
                ft.Image(
                    src=GOOGLE_LOGO_SRC,
                    width=18,
                    height=18,
                ),
                google_btn_text,
            ],
        ),
        height=46,
        style=ft.ButtonStyle(
            color=c_text(),
            shape=ft.RoundedRectangleBorder(radius=16),
            side=ft.BorderSide(
                width=1,
                color=c_border(),
            ),
        ),
        on_click=login_with_google,
    )

    google_btn.expand = True

    no_account_txt = ft.Text("", size=12, color=c_muted())

    register_link = ft.TextButton(
        content=ft.Text(
            "",
            color=BRAND_GREEN,
            weight=ft.FontWeight.W_800,
            size=12,
        ),
        on_click=lambda _: nav("/register"),
        style=ft.ButtonStyle(padding=ft.Padding(0, 0, 0, 0)),
    )

    forgot_access_txt = ft.Text(
        "",
        size=12,
        color=c_muted(),
        text_align=ft.TextAlign.CENTER,
    )

    help_btn = ft.TextButton(
        content=ft.Text(
            "",
            color=BRAND_GREEN,
            weight=ft.FontWeight.W_800,
            size=12,
        ),
        on_click=lambda _: nav("/help"),
        style=ft.ButtonStyle(padding=ft.Padding(0, 0, 0, 0)),
    )

    logo_badge = ft.Container(
        width=48,
        height=48,
        border_radius=24,
        bgcolor=ft.Colors.with_opacity(0.18, ft.Colors.GREEN_400),
        alignment=ft.Alignment(0, 0),
        content=ft.Image(src=APP_LOGO_SRC, width=26, height=26),
    )

    mini_badge = ft.Container(
        padding=ft.Padding(10, 6, 10, 6),
        border_radius=999,
        bgcolor=ft.Colors.with_opacity(0.08, ft.Colors.GREEN_400),
        content=ft.Row(
            spacing=6,
            tight=True,
            controls=[
                ft.Icon(ft.Icons.ECO_OUTLINED, size=14, color=BRAND_GREEN),
                ft.Text(
                    "Acceso seguro",
                    size=11,
                    color=BRAND_GREEN,
                    weight=ft.FontWeight.W_700,
                ),
            ],
        ),
    )

    pwd_header_row = ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        wrap=True,
        controls=[pwd_label_txt, forgot_pwd_link],
    )

    divider_row = divider_with_text("")
    divider_mid_text = divider_row.controls[1]

    form_block = ft.Column(
        spacing=10,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        controls=[
            mini_badge,
            logo_badge,
            title_txt,
            subtitle_txt,
            ft.Container(height=2),
            email_label_txt,
            input_container(email_tf),
            pwd_header_row,
            input_container(pwd_tf),
            ft.Container(height=2),
            ft.Row(controls=[continue_btn]),
            divider_row,
            ft.Row(controls=[google_btn]),
            ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=6,
                wrap=True,
                controls=[no_account_txt, register_link],
            ),
            ft.Column(
                spacing=2,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[forgot_access_txt, help_btn],
            ),
        ],
    )

    back_row = ft.Row(
        alignment=ft.MainAxisAlignment.START,
        controls=[
            ft.IconButton(
                icon=ft.Icons.ARROW_BACK,
                on_click=back,
                style=ft.ButtonStyle(
                    bgcolor=ft.Colors.with_opacity(
                        0.08,
                        ft.Colors.WHITE if is_dark() else ft.Colors.BLACK,
                    ),
                    shape=ft.RoundedRectangleBorder(radius=14),
                ),
            )
        ],
    )

    login_card = ft.Container(
        width=450,
        padding=ft.Padding(18, 16, 18, 18),
        border_radius=28,
        bgcolor=c_card_soft(),
        border=ft.Border.all(1, c_border()),
        shadow=ft.BoxShadow(
            blur_radius=28,
            spread_radius=0,
            color=ft.Colors.with_opacity(
                0.22 if is_dark() else 0.10,
                ft.Colors.BLACK,
            ),
            offset=ft.Offset(0, 8),
        ),
        content=ft.Column(
            spacing=10,
            controls=[
                back_row,
                form_block,
            ],
        ),
        opacity=0,
        animate_opacity=250,
        scale=0.98,
        animate_scale=250,
    )

    async def animate_in():
        await asyncio.sleep(0.03)
        login_card.opacity = 1
        login_card.scale = 1
        page.update()

    asyncio.create_task(animate_in())

    background = ft.Container(
        expand=True,
        gradient=ft.LinearGradient(
            begin=ft.Alignment(-1, -1),
            end=ft.Alignment(1, 1),
            colors=(
                ["#101713", "#17231D", "#0F1115"]
                if is_dark()
                else [BG_TOP, BG_BASE, "#FFFFFF"]
            ),
            stops=[0.0, 0.55, 1.0],
        ),
        content=ft.Stack(
            expand=True,
            controls=[
                # Resplandor superior derecho
                ft.Container(
                    right=-130,
                    top=-130,
                    width=310,
                    height=310,
                    border_radius=155,
                    bgcolor=ft.Colors.with_opacity(
                        0.08 if is_dark() else 0.06,
                        BRAND_GREEN,
                    ),
                ),
                # Resplandor inferior izquierdo
                ft.Container(
                    left=-100,
                    bottom=-100,
                    width=250,
                    height=250,
                    border_radius=125,
                    bgcolor=ft.Colors.with_opacity(
                        0.06 if is_dark() else 0.04,
                        BRAND_GREEN,
                    ),
                ),
            ],
        ),
    )

    def build_slides():
        return [
            {
                "title": t("carousel_fast_title", "Diagnóstico rápido"),
                "desc": t(
                    "carousel_fast_desc",
                    "Evalúa la madurez en segundos, incluso en campo.",
                ),
                "img": SLIDE_1_SRC,
                "icon": ft.Icons.SPEED,
            },
            {
                "title": t("carousel_offline_title", "Trabajo sin conexión"),
                "desc": t(
                    "carousel_offline_desc",
                    "Opera offline y sincroniza cuando la conectividad vuelva.",
                ),
                "img": SLIDE_2_SRC,
                "icon": ft.Icons.WIFI_OFF,
            },
            {
                "title": t("carousel_simple_title", "Uso simple"),
                "desc": t(
                    "carousel_simple_desc",
                    "Una experiencia clara para operarios, capataces y supervisores.",
                ),
                "img": SLIDE_3_SRC,
                "icon": ft.Icons.INSIGHTS,
            },
        ]

    slides = build_slides()
    slide_idx = {"i": 0}

    slide_title = ft.Text(
        "",
        size=24,
        weight=ft.FontWeight.W_900,
        text_align=ft.TextAlign.LEFT,
        color=c_text(),
    )
    slide_desc = ft.Text(
        "",
        size=13,
        color=c_muted(),
        text_align=ft.TextAlign.LEFT,
    )

    SLIDE_WIDTH = 520
    SLIDE_HEIGHT = 292
    SLIDE_RADIUS = 22

    slide_media = ft.Container(
        width=SLIDE_WIDTH,
        height=SLIDE_HEIGHT,
        border_radius=SLIDE_RADIUS,
        bgcolor="#E7F1E8",
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        border=ft.Border.all(
            1,
            ft.Colors.with_opacity(
                0.06,
                ft.Colors.WHITE if is_dark() else ft.Colors.BLACK,
            ),
        ),
        shadow=ft.BoxShadow(
            blur_radius=14,
            spread_radius=0,
            color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK),
            offset=ft.Offset(0, 5),
        ),
        alignment=ft.Alignment(0, 0),
        content=ft.Icon(
            ft.Icons.SPEED,
            size=72,
            color=BRAND_GREEN,
        ),
        opacity=1,
        animate_opacity=220,
        scale=1,
        animate_scale=220,
    )

    dots = ft.Row(alignment=ft.MainAxisAlignment.START, spacing=6)

    def set_dot_active(active_index: int):
        dots.controls = []
        for k in range(len(slides)):
            dots.controls.append(
                ft.Container(
                    width=22 if k == active_index else 8,
                    height=8,
                    border_radius=8,
                    bgcolor=BRAND_GREEN if k == active_index else c_divider(),
                    animate=ft.Animation(200, "easeOut"),
                )
            )

    def media_control_for(s):
        if s.get("img"):
            return ft.Image(
                src=s["img"],
                width=SLIDE_WIDTH,
                height=SLIDE_HEIGHT,
                fit=ft.BoxFit.COVER,
                border_radius=ft.BorderRadius.all(SLIDE_RADIUS),
                filter_quality=ft.FilterQuality.HIGH,
                gapless_playback=True,
                anti_alias=True,
            )

        return ft.Icon(
            s["icon"],
            size=72,
            color=BRAND_GREEN,
        )

    def render_slide(i: int):
        s = slides[i]
        slide_title.value = s["title"]
        slide_desc.value = s["desc"]

        slide_media.opacity = 0
        slide_media.scale = 0.98
        page.update()

        async def apply_after_delay():
            await asyncio.sleep(0.06)
            slide_media.content = media_control_for(s)
            slide_media.opacity = 1
            slide_media.scale = 1
            set_dot_active(i)
            page.update()

        asyncio.create_task(apply_after_delay())

    def next_slide(_=None):
        slide_idx["i"] = (slide_idx["i"] + 1) % len(slides)
        render_slide(slide_idx["i"])

    def prev_slide(_=None):
        slide_idx["i"] = (slide_idx["i"] - 1) % len(slides)
        render_slide(slide_idx["i"])

    hero_card = ft.Container(
        width=620,
        padding=ft.Padding(20, 20, 20, 20),
        border_radius=30,
        bgcolor=c_card_soft(),
        border=ft.Border.all(1, c_border()),
        shadow=ft.BoxShadow(
            blur_radius=28,
            spread_radius=0,
            color=ft.Colors.with_opacity(
                0.20 if is_dark() else 0.08,
                ft.Colors.BLACK,
            ),
            offset=ft.Offset(0, 8),
        ),
        content=ft.Column(
            spacing=14,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text(
                            state.app_name,
                            size=18,
                            weight=ft.FontWeight.W_900,
                            color=BRAND_GREEN,
                        ),
                        ft.Row(
                            spacing=4,
                            controls=[
                                ft.IconButton(
                                    icon=ft.Icons.CHEVRON_LEFT,
                                    on_click=prev_slide,
                                    icon_size=18,
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.CHEVRON_RIGHT,
                                    on_click=next_slide,
                                    icon_size=18,
                                ),
                            ],
                        ),
                    ],
                ),
                slide_media,
                slide_title,
                slide_desc,
                dots,
            ],
        ),
    )

    render_slide(0)

    auto_task = {"t": None}

    async def autoplay():
        while True:
            await asyncio.sleep(4)
            if page.route == "/login" and (page.width or 0) >= 980:
                next_slide()

    def ensure_autoplay_running():
        if auto_task["t"] is None:
            auto_task["t"] = asyncio.create_task(autoplay())

    ensure_autoplay_running()

    root = ft.Container(expand=True)

    def refresh_texts_and_theme():
        title_txt.value = t("login_welcome_title", "Bienvenido a Avoruna")
        subtitle_txt.value = t(
            "login_welcome_subtitle",
            "Accede con tu correo y contraseña o continúa con Google.",
        )
        email_label_txt.value = t(
            "login_email_label",
            "Dirección de correo electrónico",
        )
        pwd_label_txt.value = t(
            "login_password_label",
            "Contraseña",
        )
        email_tf.hint_text = t("login_email_hint", "nombre@avoruna.com")
        pwd_tf.hint_text = t("login_password_hint", "Ingresa tu contraseña")
        forgot_pwd_link.content.value = t(
            "login_forgot_password",
            "¿Olvidaste tu contraseña?",
        )
        continue_btn.content.value = t("login_continue", "CONTINUAR")
        forgot_access_txt.value = t(
            "login_forgot_access",
            "¿Has olvidado tus datos de acceso?",
        )
        help_btn.content.value = t("login_help", "Recuperar cuenta")
        divider_mid_text.value = t("login_or_continue_with", "o continuar con")
        google_btn_text.value = t("login_google", "Iniciar sesión con Google")
        no_account_txt.value = t("login_no_account", "¿No tienes una cuenta?")
        register_link.content.value = t("login_register", "Regístrate")

        title_txt.color = c_text()
        subtitle_txt.color = c_muted()
        email_label_txt.color = c_text()
        pwd_label_txt.color = c_text()
        no_account_txt.color = c_muted()
        forgot_access_txt.color = c_muted()

        login_card.bgcolor = c_card_soft()
        login_card.border = ft.Border.all(1, c_border())

        hero_card.bgcolor = c_card_soft()
        hero_card.border = ft.Border.all(1, c_border())

        google_btn.style = ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=16),
            side=ft.BorderSide(1, c_border()),
        )

        nonlocal slides
        slides = build_slides()
        render_slide(slide_idx["i"])

        page.update()

    def build_layout():
        w = page.width or 0
        h = page.height or 0

        if w < 700:
            SIDE_MARGIN = 18
            TOP_MARGIN = 16
            BOTTOM_MARGIN = 24

            # Deja 18 px de espacio a cada costado
            login_card.width = min(
                max(w - (SIDE_MARGIN * 2), 280),
                430,
            )

            root.content = ft.Stack(
                expand=True,
                controls=[
                    background,
                    ft.Container(
                        expand=True,
                        padding=ft.Padding(
                            SIDE_MARGIN,      # izquierda
                            TOP_MARGIN,       # arriba
                            SIDE_MARGIN,      # derecha
                            BOTTOM_MARGIN,    # abajo
                        ),
                        content=ft.Column(
                            expand=True,
                            scroll=ft.ScrollMode.AUTO,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.Container(height=4),
                                login_card,
                                ft.Container(height=12),
                            ],
                        ),
                    ),
                ],
            )

        elif w < 980:
            login_card.width = min(520, w - 40)
            hero_card.width = min(w - 40, 620)

            root.content = ft.Stack(
                expand=True,
                controls=[
                    background,
                    ft.Container(
                        expand=True,
                        padding=ft.Padding(20, 20, 22, 22),
                        content=ft.Column(
                            expand=True,
                            scroll=ft.ScrollMode.AUTO,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                login_card,
                                ft.Container(height=12),
                                hero_card,
                            ],
                        ),
                    ),
                ],
            )

        else:
            login_card.width = min(470, int(w * 0.33))
            hero_card.width = min(680, int(w * 0.44))

            left_panel = ft.Container(
                width=login_card.width,
                height=min(max(h - 56, 520), 760),
                content=ft.Column(
                    expand=True,
                    scroll=ft.ScrollMode.AUTO,
                    controls=[login_card],
                ),
            )

            root.content = ft.Stack(
                expand=True,
                controls=[
                    background,
                    ft.Container(
                        expand=True,
                        padding=ft.Padding(24, 24, 24, 24),
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.CENTER,
                            vertical_alignment=ft.CrossAxisAlignment.START,
                            spacing=24,
                            controls=[
                                left_panel,
                                hero_card,
                            ],
                        ),
                    ),
                ],
            )

        refresh_texts_and_theme()

    page.on_resize = lambda e: build_layout()
    build_layout()

    return ft.View(route="/login", controls=[ft.SafeArea(expand=True, content=root)])
