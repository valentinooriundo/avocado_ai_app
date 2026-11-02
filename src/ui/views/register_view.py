import re
import flet as ft

from ui.state import get_state
from services.settings_service import load_theme
from services.firebase_email_auth_service import (
    register_with_email_password,
    FirebaseEmailAuthError,
    map_firebase_auth_error,
)
from services.auth_session_service import save_auth_data
from services.backend_profile_service import upsert_user_profile_backend

BRAND_GREEN = "#2F5D46"
BRAND_GREEN_DARK = "#244A38"
BG_TINT = "#EEF3ED"

EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
PHONE_RE = re.compile(r"^\+?\d[\d\s]{7,15}\d$")


def _nav(page: ft.Page, route: str):
    page.run_task(page.push_route, route)


def _is_dark(page: ft.Page) -> bool:
    return page.theme_mode == ft.ThemeMode.DARK


def _c_bg(page: ft.Page):
    return "#0F1115" if _is_dark(page) else "#FFFFFF"


def _c_card(page: ft.Page):
    return "#151922" if _is_dark(page) else "#FFFFFF"


def _c_text(page: ft.Page):
    return "#F3F4F6" if _is_dark(page) else "#111111"


def _c_muted(page: ft.Page):
    return "#A7B0C0" if _is_dark(page) else "#6B7280"


def _c_border(page: ft.Page):
    return "#2A3142" if _is_dark(page) else ft.Colors.GREY_200


def _c_divider(page: ft.Page):
    return "#2A3142" if _is_dark(page) else ft.Colors.GREY_300


def _bg_layer(page: ft.Page):
    return ft.Container(
        expand=True,
        bgcolor=_c_bg(page),
        content=ft.Stack(
            expand=True,
            controls=[
                ft.Container(expand=True, bgcolor=_c_bg(page)),
                ft.Container(
                    expand=True,
                    bgcolor=BG_TINT,
                    opacity=0.10 if _is_dark(page) else 0.55,
                ),
            ],
        ),
    )


def _card_shell(page: ft.Page, content: ft.Control, width: int = 420):
    return ft.Container(
        width=width,
        padding=ft.Padding(30, 26, 30, 28),
        border_radius=28,
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        bgcolor=_c_card(page),
        border=ft.Border.all(1, _c_border(page)),
        shadow=ft.BoxShadow(
            blur_radius=32,
            spread_radius=0,
            color=ft.Colors.with_opacity(
                0.20 if _is_dark(page) else 0.08,
                ft.Colors.BLACK,
            ),
            offset=ft.Offset(0, 10),
        ),
        content=content,
    )


def _input_capsule(page: ft.Page, control: ft.Control):
    return ft.Container(
        padding=ft.Padding(12, 5, 12, 5),
        border_radius=15,
        bgcolor="#101722" if _is_dark(page) else "#FFFFFF",
        border=ft.Border.all(1, _c_border(page)),
        content=control,
    )


def _primary_btn(text: str, on_click, height: int = 50):
    return ft.Button(
        content=ft.Text(
            text,
            weight=ft.FontWeight.W_800,
            color=ft.Colors.WHITE,
            size=14,
        ),
        height=height,
        style=ft.ButtonStyle(
            bgcolor=BRAND_GREEN,
            overlay_color=ft.Colors.with_opacity(
                0.08,
                ft.Colors.WHITE,
            ),
            shape=ft.RoundedRectangleBorder(radius=15),
            elevation=2,
        ),
        on_click=on_click,
    )


def _register_hero_panel(
    page: ft.Page,
    t,
    panel_height: int = 760,
) -> ft.Container:
    return ft.Container(
        expand=True,
        height=panel_height,
        border_radius=30,
        padding=ft.Padding(34, 34, 34, 34),
        gradient=ft.LinearGradient(
            begin=ft.Alignment(-1, -1),
            end=ft.Alignment(1, 1),
            colors=["#1F4D39", "#2F5D46", "#4C8C6A"],
        ),
        content=ft.Column(
            expand=True,
            spacing=18,
            controls=[
                ft.Container(
                    padding=ft.Padding(12, 8, 12, 8),
                    border_radius=999,
                    bgcolor=ft.Colors.with_opacity(0.12, ft.Colors.WHITE),
                    content=ft.Row(
                        tight=True,
                        spacing=8,
                        controls=[
                            ft.Icon(
                                ft.Icons.ECO_OUTLINED,
                                size=16,
                                color=ft.Colors.WHITE,
                            ),
                            ft.Text(
                                t("register_hero_badge", "Registro en Avoruna"),
                                size=12,
                                weight=ft.FontWeight.W_700,
                                color=ft.Colors.WHITE,
                            ),
                        ],
                    ),
                ),
                ft.Column(
                    spacing=8,
                    controls=[
                        ft.Text(
                            t("register_hero_title", "Crea tu cuenta y gestiona tu cultivo con mayor facilidad"),
                            size=28,
                            weight=ft.FontWeight.W_900,
                            color=ft.Colors.WHITE,
                        ),
                        ft.Text(
                            t("register_hero_subtitle", "Regístrate para acceder a análisis, historial y seguimiento de la madurez de la palta Hass desde cualquier lugar."),
                            size=13,
                            color=ft.Colors.with_opacity(0.88, ft.Colors.WHITE),
                        ),
                    ],
                ),
                ft.Container(height=6),
                ft.Column(
                    spacing=10,
                    controls=[
                        ft.Row(
                            spacing=10,
                            controls=[
                                ft.Icon(
                                    ft.Icons.CHECK_CIRCLE_OUTLINE,
                                    size=18,
                                    color=ft.Colors.WHITE,
                                ),
                                ft.Text(
                                    t("register_benefit_fast", "Registro rápido y ordenado"),
                                    size=13,
                                    color=ft.Colors.WHITE,
                                ),
                            ],
                        ),
                        ft.Row(
                            spacing=10,
                            controls=[
                                ft.Icon(
                                    ft.Icons.CHECK_CIRCLE_OUTLINE,
                                    size=18,
                                    color=ft.Colors.WHITE,
                                ),
                                ft.Text(
                                    t("register_benefit_history", "Acceso a historial y resultados"),
                                    size=13,
                                    color=ft.Colors.WHITE,
                                ),
                            ],
                        ),
                        ft.Row(
                            spacing=10,
                            controls=[
                                ft.Icon(
                                    ft.Icons.CHECK_CIRCLE_OUTLINE,
                                    size=18,
                                    color=ft.Colors.WHITE,
                                ),
                                ft.Text(
                                    t("register_benefit_field", "Diseñado para uso en campo"),
                                    size=13,
                                    color=ft.Colors.WHITE,
                                ),
                            ],
                        ),
                    ],
                ),
                ft.Container(expand=True),
                ft.Container(
                    height=355,
                    border_radius=28,
                    clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                    bgcolor=ft.Colors.with_opacity(0.12, ft.Colors.WHITE),
                    padding=ft.Padding(18, 18, 18, 10),
                    content=ft.Stack(
                        expand=True,
                        controls=[
                            ft.Container(
                                alignment=ft.Alignment(0, 1),
                                padding=ft.Padding(0, 0, 0, 8),
                                content=ft.Container(
                                    width=210,
                                    height=24,
                                    border_radius=999,
                                    bgcolor=ft.Colors.with_opacity(
                                        0.18, ft.Colors.BLACK
                                    ),
                                ),
                            ),
                            ft.Container(
                                expand=True,
                                alignment=ft.Alignment(0, 1),
                                content=ft.Image(
                                    src="register_hero.png",
                                    fit=ft.BoxFit.CONTAIN,
                                ),
                            ),
                        ],
                    ),
                ),
            ],
        ),
    )


def create_register_view(page: ft.Page) -> ft.View:
    db = page.data.get("db")
    state = get_state(page)

    if db is not None:
        saved = load_theme(db)
        page.theme_mode = ft.ThemeMode.DARK if saved == "dark" else ft.ThemeMode.LIGHT

    def t(
        key: str,
        fallback: str | None = None,
        **values,
    ) -> str:
        value = state.t(key)

        if value is None or value == key:
            value = fallback if fallback is not None else key

        if values:
            try:
                return value.format(**values)
            except (KeyError, ValueError):
                return value

        return value

    def back(_=None):
        _nav(page, "/login")

    BREAKPOINT_DESKTOP = 980
    FORM_MAX_W = 520
    MOBILE_MAX_W = 460
    LAYOUT_MAX_W = 1180

    def _form_width() -> int:
        w = page.width or 420

        if w >= BREAKPOINT_DESKTOP:
            return FORM_MAX_W

        return max(320, min(MOBILE_MAX_W, int(w - 32)))

    full_name_tf = ft.TextField(
        hint_text=t("register_name_hint", "Nombres y apellidos"),
        border=ft.InputBorder.NONE,
        text_size=13,
        height=44,
        prefix_icon=ft.Icons.PERSON_OUTLINE,
        content_padding=ft.Padding(6, 10, 6, 10),
    )

    email_tf = ft.TextField(
        hint_text=t("register_email_hint", "nombre@avoruna.com"),
        border=ft.InputBorder.NONE,
        text_size=13,
        height=44,
        prefix_icon=ft.Icons.MAIL_OUTLINE,
        keyboard_type=ft.KeyboardType.EMAIL,
        content_padding=ft.Padding(6, 10, 6, 10),
    )

    phone_tf = ft.TextField(
        hint_text=t("register_phone_hint", "+51 9xx xxx xxx"),
        border=ft.InputBorder.NONE,
        text_size=13,
        height=44,
        prefix_icon=ft.Icons.PHONE_ANDROID_OUTLINED,
        keyboard_type=ft.KeyboardType.PHONE,
        content_padding=ft.Padding(6, 10, 6, 10),
    )

    farm_tf = ft.TextField(
        hint_text=t("register_farm_hint", "Departamento y distrito"),
        border=ft.InputBorder.NONE,
        text_size=13,
        height=44,
        prefix_icon=ft.Icons.LOCATION_ON_OUTLINED,
        content_padding=ft.Padding(6, 10, 6, 10),
    )

    variety_dd = ft.TextField(
        value="Hass",
        read_only=True,
        border=ft.InputBorder.NONE,
        text_size=13,
        height=46,
        prefix_icon=ft.Icons.ECO_OUTLINED,
        content_padding=ft.Padding(6, 10, 6, 10),
    )

    pwd_tf = ft.TextField(
        hint_text=t("register_password_hint", "Mínimo 8 caracteres"),
        border=ft.InputBorder.NONE,
        text_size=13,
        height=44,
        password=True,
        can_reveal_password=False,
        prefix_icon=ft.Icons.LOCK_OUTLINE,
        content_padding=ft.Padding(6, 10, 6, 10),
    )
    eye_btn = ft.IconButton(
        icon=ft.Icons.VISIBILITY_OFF,
        icon_size=18,
        tooltip=t("register_password_toggle", "Mostrar u ocultar contraseña"),
    )
    pwd_tf.suffix = eye_btn

    def toggle_pwd(_):
        pwd_tf.password = not pwd_tf.password
        eye_btn.icon = (
            ft.Icons.VISIBILITY_OFF if pwd_tf.password else ft.Icons.VISIBILITY
        )
        page.update()

    eye_btn.on_click = toggle_pwd

    accept_cb = ft.Checkbox(value=False)

    # Error general: Firebase, backend o problemas de conexión.
    err_txt = ft.Text(
        "",
        size=11,
        color=ft.Colors.RED_400,
        visible=False,
    )

    # Referencias visuales de cada campo.
    field_errors: dict[str, ft.Text] = {}
    field_shells: dict[str, ft.Container] = {}

    # Controla qué campos ya fueron utilizados por el usuario.
    touched = {
        "name": False,
        "email": False,
        "phone": False,
        "farm": False,
        "password": False,
    }

    validation_state = {
        "show_all": False,
        "terms_touched": False,
    }

    terms_error = ft.Text(
        "",
        size=10,
        color=ft.Colors.RED_400,
        visible=False,
    )

    def _normalize_phone(v: str) -> str:
        return re.sub(r"\s+", "", (v or "").strip())

    def _email_ok(v: str) -> bool:
        return bool(EMAIL_RE.match((v or "").strip()))

    def _phone_ok(v: str) -> bool:
        return bool(PHONE_RE.match((v or "").strip()))

    def _pwd_ok(v: str) -> bool:
        return len(v or "") >= 8

    create_btn = _primary_btn(
        t("register_create_button", "Crear cuenta"),
        lambda e: None,
        height=52,
    )
    create_btn.expand = True
    create_btn.disabled = True

    def _set_field_error(key: str, message: str):
        """
        Muestra el mensaje debajo del campo y cambia su borde.
        """

        error_control = field_errors.get(key)
        field_shell = field_shells.get(key)

        # Durante la creación inicial del formulario todavía
        # podrían no haberse registrado los controles.
        if error_control is None or field_shell is None:
            return

        should_show = bool(message) and (
            touched.get(key, False) or validation_state["show_all"]
        )

        error_control.value = message if should_show else ""
        error_control.visible = should_show

        field_shell.border = ft.Border.all(
            1.4 if should_show else 1,
            (ft.Colors.RED_400 if should_show else _c_border(page)),
        )

    def validate(_=None, *, show_all: bool = False) -> bool:
        """
        Valida todos los campos y devuelve True cuando
        el formulario está completamente correcto.
        """

        if show_all:
            validation_state["show_all"] = True

            for key in touched:
                touched[key] = True

            validation_state["terms_touched"] = True

        # El error general se oculta cuando el usuario vuelve a editar.
        err_txt.visible = False
        err_txt.value = ""

        name = (full_name_tf.value or "").strip()
        email = (email_tf.value or "").strip()
        phone = (phone_tf.value or "").strip()
        farm = (farm_tf.value or "").strip()
        pwd = pwd_tf.value or ""

        # Nombre completo
        if not name:
            name_error = t("register_error_name_required", "Ingresa tus nombres y apellidos.")
        elif len(name) < 3:
            name_error = t("register_error_name_min", "El nombre debe contener al menos 3 caracteres.")
        elif len(name.split()) < 2:
            name_error = t("register_error_name_full", "Ingresa al menos un nombre y un apellido.")
        else:
            name_error = ""

        # Correo electrónico
        if not email:
            email_error = t("register_error_email_required", "Ingresa tu correo electrónico.")
        elif not _email_ok(email):
            email_error = t(
                "register_error_email_invalid",
                "Ingresa un correo válido, por ejemplo: usuario@correo.com.",
            )
        else:
            email_error = ""

        # Número de teléfono
        if not phone:
            phone_error = t("register_error_phone_required", "Ingresa tu número de teléfono.")
        elif not _phone_ok(phone):
            phone_error = t(
                "register_error_phone_invalid",
                "Ingresa un número válido, por ejemplo: +51 987 654 321.",
            )
        else:
            phone_error = ""

        # Ubicación de la finca
        if not farm:
            farm_error = t("register_error_farm_required", "Ingresa el departamento y distrito de la chacra.")
        elif len(farm) < 4:
            farm_error = t("register_error_farm_min", "Especifica mejor la ubicación de la chacra.")
        else:
            farm_error = ""

        # Contraseña
        if not pwd:
            password_error = t("register_error_password_required", "Ingresa una contraseña.")
        elif not _pwd_ok(pwd):
            missing = 8 - len(pwd)

            if missing == 1:
                password_error = t("register_error_password_missing_one", "Falta 1 carácter para completar el mínimo de 8.")
            else:
                password_error = t(
                    "register_error_password_missing_many",
                    "Faltan {count} caracteres para completar el mínimo de 8.",
                    count=missing,
                )
        else:
            password_error = ""

        errors = {
            "name": name_error,
            "email": email_error,
            "phone": phone_error,
            "farm": farm_error,
            "password": password_error,
        }

        for key, message in errors.items():
            _set_field_error(key, message)

        fields_are_valid = not any(errors.values())
        terms_are_valid = bool(accept_cb.value)

        # Muestra el error de términos cuando el usuario interactúa
        # con la casilla o cuando los demás campos ya están correctos.
        show_terms_error = not terms_are_valid and (
            validation_state["terms_touched"]
            or validation_state["show_all"]
            or fields_are_valid
        )

        terms_error.value = (
            t(
                "register_error_terms",
                "Debes aceptar los términos y condiciones para continuar.",
            )
            if show_terms_error
            else ""
        )
        terms_error.visible = show_terms_error

        form_is_valid = fields_are_valid and terms_are_valid
        create_btn.disabled = not form_is_valid

        page.update()
        return form_is_valid

    def _bind_field_validation(
        key: str,
        control: ft.TextField,
    ):
        def handle_change(_):
            touched[key] = True
            validate()

        def handle_blur(_):
            touched[key] = True
            validate()

        control.on_change = handle_change
        control.on_blur = handle_blur

    _bind_field_validation("name", full_name_tf)
    _bind_field_validation("email", email_tf)
    _bind_field_validation("phone", phone_tf)
    _bind_field_validation("farm", farm_tf)
    _bind_field_validation("password", pwd_tf)

    def handle_terms_change(_):
        validation_state["terms_touched"] = True
        validate()

    accept_cb.on_change = handle_terms_change

    def firebase_register_error(ex: Exception) -> str:
        raw_error = str(ex)
        normalized = raw_error.upper()

        if "EMAIL_EXISTS" in normalized:
            return t(
                "register_error_email_exists",
                "Este correo ya está registrado.",
            )

        if "INVALID_EMAIL" in normalized:
            return t(
                "register_error_email_invalid",
                "Ingresa un correo válido, por ejemplo: usuario@correo.com.",
            )

        if "WEAK_PASSWORD" in normalized:
            return t(
                "register_error_password_weak",
                "La contraseña es demasiado débil.",
            )

        if "TOO_MANY_ATTEMPTS" in normalized:
            return t(
                "register_error_too_many_attempts",
                "Se realizaron demasiados intentos. Inténtalo más tarde.",
            )

        if "OPERATION_NOT_ALLOWED" in normalized:
            return t(
                "register_error_operation_not_allowed",
                "El registro con correo y contraseña no está habilitado.",
            )

        localized_fallback = map_firebase_auth_error(raw_error)

        if state.lang == "es":
            return localized_fallback

        return t(
            "register_error_firebase_generic",
            "Firebase could not create the account. Please try again.",
        )

    def create_account(_=None):
        if not validate(show_all=True):
            return

        name = (full_name_tf.value or "").strip()
        email = (email_tf.value or "").strip().lower()
        phone = _normalize_phone(phone_tf.value or "")
        farm = (farm_tf.value or "").strip()
        variety = (variety_dd.value or "").strip()
        pwd = pwd_tf.value or ""

        try:
            firebase_session = register_with_email_password(email, pwd)

            auth_payload = {
                "firebase_id_token": firebase_session.get("idToken"),
                "firebase_refresh_token": firebase_session.get("refreshToken"),
                "firebase_expires_in": firebase_session.get("expiresIn"),
                "firebase_local_id": firebase_session.get("localId"),
                "firebase_uid": firebase_session.get("localId"),
                "firebase_email": firebase_session.get("email"),
                "firebase_name": name,
                "auth_provider": "password",
            }

            # save_auth_data(page, auth_payload)

            phone_e164 = phone if phone.startswith("+") else f"+51{phone}"

            upsert_user_profile_backend(
                uid=auth_payload["firebase_uid"],
                full_name=name,
                email=email,
                phone_e164=phone_e164,
                farm_location=farm,
                avocado_variety=variety,
                auth_provider="password",
                firebase_id_token=auth_payload.get("firebase_id_token"),
            )

            page.data["reg_name"] = name
            page.data["reg_farm"] = farm
            page.data["reg_email"] = email
            page.data["reg_phone"] = phone_e164
            page.data["reg_variety"] = variety

            # Permite mostrar el toast una sola vez
            page.data["register_success_pending"] = True

            _nav(page, "/register/success")

        except FirebaseEmailAuthError as ex:
            err_txt.value = firebase_register_error(ex)
            err_txt.visible = True
            page.update()
        except Exception as ex:
            err_txt.value = t(
                "register_error_create",
                "No se pudo crear la cuenta. {error}",
                error=str(ex),
            )
            err_txt.visible = True
            page.update()

    create_btn.on_click = create_account

    top_title = ft.Text(
        t("register_title", "Crear una cuenta"),
        size=25,
        weight=ft.FontWeight.W_900,
        color=_c_text(page),
    )

    top_sub = ft.Text(
        t("register_subtitle", "Registra tus datos para acceder a las funciones de Avoruna."),
        size=13,
        color=_c_muted(page),
    )

    security_badge = ft.Container(
        padding=ft.Padding(10, 6, 10, 6),
        border_radius=999,
        bgcolor=ft.Colors.with_opacity(0.08, BRAND_GREEN),
        content=ft.Row(
            tight=True,
            spacing=6,
            controls=[
                ft.Icon(
                    ft.Icons.LOCK_OUTLINE,
                    size=14,
                    color=BRAND_GREEN,
                ),
                ft.Text(
                    t("register_secure", "Registro seguro"),
                    size=11,
                    weight=ft.FontWeight.W_700,
                    color=BRAND_GREEN,
                ),
            ],
        ),
    )

    def form_field(
        key: str | None,
        label: str,
        control: ft.Control,
        col: dict | int = 12,
    ) -> ft.Container:
        input_shell = _input_capsule(page, control)

        controls: list[ft.Control] = [
            ft.Text(
                label,
                size=11,
                color=_c_text(page),
                weight=ft.FontWeight.W_700,
            ),
            input_shell,
        ]

        if key is not None:
            error_message = ft.Text(
                "",
                size=10,
                color=ft.Colors.RED_400,
                visible=False,
                weight=ft.FontWeight.W_500,
            )

            field_errors[key] = error_message
            field_shells[key] = input_shell

            # Reserva espacio para evitar que el formulario
            # salte cuando aparece el mensaje.
            controls.append(
                ft.Container(
                    height=16,
                    alignment=ft.Alignment(-1, 0),
                    content=error_message,
                )
            )
        else:
            # Campo sin validación, como la variedad fija Hass.
            controls.append(ft.Container(height=16))

        return ft.Container(
            col=col,
            content=ft.Column(
                spacing=6,
                controls=controls,
            ),
        )

    # google_btn = ft.OutlinedButton(
    #     content=ft.Row(
    #         alignment=ft.MainAxisAlignment.CENTER,
    #         spacing=10,
    #         controls=[
    #             ft.Image(src="google.png", width=18, height=18),
    #             ft.Text(
    #                 "Continuar con Google",
    #                 size=12,
    #                 weight=ft.FontWeight.W_800,
    #                 color=_c_text(page),
    #             ),
    #         ],
    #     ),
    #     height=46,
    #     style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=14)),
    #     on_click=lambda _: _nav(page, "/login"),
    # )
    # google_btn.expand = True

    # divider = ft.Row(
    #     vertical_alignment=ft.CrossAxisAlignment.CENTER,
    #     spacing=10,
    #     controls=[
    #         ft.Container(height=1, bgcolor=_c_divider(page), expand=True),
    #         ft.Text(
    #             "O USA TUS DATOS",
    #             size=10,
    #             weight=ft.FontWeight.W_800,
    #             color=_c_muted(page),
    #         ),
    #         ft.Container(height=1, bgcolor=_c_divider(page), expand=True),
    #     ],
    # )

    terms_row = ft.Row(
        spacing=10,
        vertical_alignment=ft.CrossAxisAlignment.START,
        controls=[
            accept_cb,
            ft.Container(
                expand=True,
                content=ft.Column(
                    spacing=2,
                    controls=[
                        ft.Row(
                            spacing=4,
                            wrap=True,
                            controls=[
                                ft.Text(
                                    t("register_terms_prefix", "Acepto los"),
                                    size=10,
                                    color=_c_muted(page),
                                ),
                                ft.TextButton(
                                    content=ft.Text(
                                        t("register_terms_link", "términos y condiciones"),
                                        size=10,
                                        color=BRAND_GREEN,
                                        weight=ft.FontWeight.W_800,
                                    ),
                                    on_click=lambda _: None,
                                    style=ft.ButtonStyle(
                                        padding=ft.Padding(0, 0, 0, 0)
                                    ),
                                ),
                                ft.Text(
                                    t("register_terms_suffix", "de privacidad y uso agrícola de Avoruna."),
                                    size=10,
                                    color=_c_muted(page),
                                    overflow=ft.TextOverflow.VISIBLE,
                                ),
                            ],
                        ),
                    ],
                ),
            ),
        ],
    )

    bottom_login = ft.Row(
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=6,
        wrap=True,
        controls=[
            ft.Text(
                t("register_have_account", "¿Ya tienes una cuenta?"),
                size=11,
                color=_c_muted(page),
            ),
            ft.TextButton(
                content=ft.Text(
                    t("register_sign_in", "Inicia sesión"),
                    size=11,
                    color=BRAND_GREEN,
                    weight=ft.FontWeight.W_800,
                ),
                on_click=lambda _: _nav(page, "/login"),
                style=ft.ButtonStyle(padding=ft.Padding(0, 0, 0, 0)),
            ),
        ],
    )

    card = _card_shell(
        page,
        ft.Column(
            spacing=18,
            controls=[
                # Navegación superior
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.IconButton(
                            icon=ft.Icons.ARROW_BACK,
                            tooltip=t("register_back_tooltip", "Volver al inicio de sesión"),
                            on_click=back,
                            style=ft.ButtonStyle(
                                bgcolor=ft.Colors.with_opacity(
                                    0.07,
                                    (
                                        ft.Colors.WHITE
                                        if _is_dark(page)
                                        else ft.Colors.BLACK
                                    ),
                                ),
                                shape=ft.RoundedRectangleBorder(radius=14),
                            ),
                        ),
                        security_badge,
                    ],
                ),
                # Encabezado
                ft.Column(
                    spacing=7,
                    controls=[
                        top_title,
                        top_sub,
                    ],
                ),
                ft.Divider(
                    height=1,
                    color=_c_divider(page),
                ),
                # Sección: información personal
                ft.Column(
                    spacing=4,
                    controls=[
                        ft.Text(
                            t("register_personal_title", "Información personal"),
                            size=14,
                            weight=ft.FontWeight.W_800,
                            color=_c_text(page),
                        ),
                        ft.Text(
                            t("register_personal_subtitle", "Datos necesarios para identificar y contactar al usuario."),
                            size=11,
                            color=_c_muted(page),
                        ),
                    ],
                ),
                ft.ResponsiveRow(
                    spacing=14,
                    run_spacing=14,
                    controls=[
                        form_field(
                            "name",
                            t("register_name_label", "Nombre completo"),
                            full_name_tf,
                            {"xs": 12, "sm": 12, "md": 12},
                        ),
                        form_field(
                            "email",
                            t("register_email_label", "Correo electrónico"),
                            email_tf,
                            {"xs": 12, "sm": 12, "md": 6},
                        ),
                        form_field(
                            "phone",
                            t("register_phone_label", "Número de teléfono"),
                            phone_tf,
                            {"xs": 12, "sm": 12, "md": 6},
                        ),
                    ],
                ),
                # Sección: información agrícola
                ft.Column(
                    spacing=4,
                    controls=[
                        ft.Text(
                            t("register_agricultural_title", "Información agrícola"),
                            size=14,
                            weight=ft.FontWeight.W_800,
                            color=_c_text(page),
                        ),
                        ft.Text(
                            t("register_agricultural_subtitle", "Información relacionada con la chacra y el cultivo."),
                            size=11,
                            color=_c_muted(page),
                        ),
                    ],
                ),
                ft.ResponsiveRow(
                    spacing=14,
                    run_spacing=14,
                    controls=[
                        form_field(
                            "farm",
                            t("register_farm_label", "Ubicación de la chacra"),
                            farm_tf,
                            {"xs": 12, "sm": 12, "md": 6},
                        ),
                        form_field(
                            None,
                            t("register_variety_label", "Variedad de palta"),
                            variety_dd,
                            {"xs": 12, "sm": 12, "md": 6},
                        ),
                    ],
                ),
                # Sección: seguridad
                ft.Column(
                    spacing=4,
                    controls=[
                        ft.Text(
                            t("register_security_title", "Seguridad de la cuenta"),
                            size=14,
                            weight=ft.FontWeight.W_800,
                            color=_c_text(page),
                        ),
                        ft.Text(
                            t("register_security_subtitle", "Utiliza una contraseña de ocho caracteres como mínimo."),
                            size=11,
                            color=_c_muted(page),
                        ),
                    ],
                ),
                form_field(
                    "password",
                    t("register_password_label", "Contraseña"),
                    pwd_tf,
                    12,
                ),
                terms_row,
                ft.Container(
                    height=18,
                    padding=ft.Padding(48, 0, 0, 0),
                    alignment=ft.Alignment(-1, 0),
                    content=terms_error,
                ),
                # Este queda reservado para errores de Firebase o backend.
                err_txt,
                ft.Container(height=2),
                ft.Row(
                    controls=[create_btn],
                ),
                bottom_login,
            ],
        ),
        width=_form_width(),
    )

    form_column = card.content

    layout_holder = ft.Container()

    def _build_register_layout():
        is_desktop = (page.width or 0) >= BREAKPOINT_DESKTOP

        form_width = _form_width()
        card.width = form_width

        if is_desktop:
            viewport_height = int(page.height or 900)

            panel_height = max(
                720,
                min(860, viewport_height - 80),
            )

            # Las dos columnas tendrán exactamente la misma altura.
            card.height = panel_height
            card.clip_behavior = ft.ClipBehavior.ANTI_ALIAS

            # El formulario tendrá desplazamiento interno.
            form_column.expand = True
            form_column.scroll = ft.ScrollMode.AUTO

            total_width = min(
                LAYOUT_MAX_W,
                int((page.width or LAYOUT_MAX_W) - 40),
            )

            return ft.Container(
                width=total_width,
                height=panel_height,
                content=ft.Row(
                    spacing=24,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                    controls=[
                        ft.Container(
                            expand=True,
                            height=panel_height,
                            content=_register_hero_panel(
                                page,
                                t,
                                panel_height,
                            ),
                        ),
                        ft.Container(
                            width=form_width,
                            height=panel_height,
                            content=card,
                        ),
                    ],
                ),
            )

        # En móvil, la tarjeta recupera su altura automática.
        card.height = None
        form_column.expand = False
        form_column.scroll = None

        return ft.Container(
            width=form_width,
            content=card,
        )

    root = ft.Container(
        expand=True,
        content=ft.Stack(
            expand=True,
            controls=[
                _bg_layer(page),
                ft.Container(
                    expand=True,
                    padding=ft.Padding(20, 24, 20, 24),
                    alignment=ft.Alignment(0, 0),
                    content=ft.Column(
                        expand=True,
                        scroll=ft.ScrollMode.AUTO,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[layout_holder],
                    ),
                ),
            ],
        ),
    )

    def _on_resize(_):
        layout_holder.content = _build_register_layout()
        page.update()

    page.on_resize = _on_resize
    layout_holder.content = _build_register_layout()

    validate()

    return ft.View(
        route="/register",
        controls=[
            ft.SafeArea(
                expand=True,
                content=root,
            )
        ],
    )


def create_register_success_view(page: ft.Page) -> ft.View:
    db = page.data.get("db")
    state = get_state(page)

    def t(
        key: str,
        fallback: str | None = None,
        **values,
    ) -> str:
        value = state.t(key)

        if value is None or value == key:
            value = fallback if fallback is not None else key

        if values:
            try:
                return value.format(**values)
            except (KeyError, ValueError):
                return value

        return value

    if db is not None:
        saved = load_theme(db)
        page.theme_mode = ft.ThemeMode.DARK if saved == "dark" else ft.ThemeMode.LIGHT

    def go_dashboard(_=None):
        _nav(page, "/dashboard")

    def go_login(_=None):
        _nav(page, "/login")

    name = page.data.get("reg_name", t("register_success_default_user", "Usuario"))
    farm = page.data.get("reg_farm", t("register_success_default_farm", "Chacra no registrada"))

    success_icon = ft.Container(
        width=86,
        height=86,
        border_radius=43,
        bgcolor=ft.Colors.with_opacity(0.12, BRAND_GREEN),
        alignment=ft.Alignment(0, 0),
        content=ft.Container(
            width=58,
            height=58,
            border_radius=29,
            bgcolor=BRAND_GREEN,
            alignment=ft.Alignment(0, 0),
            content=ft.Icon(
                ft.Icons.CHECK_ROUNDED,
                size=32,
                color=ft.Colors.WHITE,
            ),
        ),
    )

    profile_card = ft.Container(
        padding=ft.Padding(16, 14, 16, 14),
        border_radius=16,
        border=ft.Border.all(1, _c_border(page)),
        bgcolor=_c_card(page),
        content=ft.Row(
            spacing=12,
            controls=[
                ft.CircleAvatar(
                    radius=20,
                    bgcolor=ft.Colors.with_opacity(0.10, BRAND_GREEN),
                    content=ft.Icon(
                        ft.Icons.PERSON_OUTLINE,
                        color=BRAND_GREEN,
                        size=22,
                    ),
                ),
                ft.Column(
                    spacing=3,
                    expand=True,
                    controls=[
                        ft.Text(
                            name,
                            size=13,
                            weight=ft.FontWeight.W_800,
                            color=_c_text(page),
                        ),
                        ft.Text(
                            farm,
                            size=11,
                            color=_c_muted(page),
                        ),
                    ],
                ),
                ft.Icon(
                    ft.Icons.ECO_OUTLINED,
                    color=BRAND_GREEN,
                    size=22,
                ),
            ],
        ),
    )

    dashboard_btn = _primary_btn(
        t("register_success_sign_in", "Iniciar sesión"),
        go_login,
        height=50,
    )
    dashboard_btn.expand = True

    card = _card_shell(
        page,
        ft.Column(
            spacing=18,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.END,
                    controls=[
                        ft.IconButton(
                            icon=ft.Icons.CLOSE,
                            tooltip=t("register_success_close", "Cerrar"),
                            on_click=go_login,
                        ),
                    ],
                ),
                success_icon,
                ft.Text(
                    t("register_success_title", "¡Cuenta creada con éxito!"),
                    size=23,
                    weight=ft.FontWeight.W_900,
                    color=_c_text(page),
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text(
                    t(
                        "register_success_message",
                        "Bienvenido, {name}. Tu cuenta de Avoruna ya está lista para comenzar.",
                        name=name,
                    ),
                    size=12,
                    color=_c_muted(page),
                    text_align=ft.TextAlign.CENTER,
                ),
                profile_card,
                ft.Container(height=2),
                ft.Row(
                    controls=[dashboard_btn],
                ),
                ft.TextButton(
                    content=ft.Text(
                        t("register_success_back_login", "Volver al inicio de sesión"),
                        size=11,
                        color=BRAND_GREEN,
                        weight=ft.FontWeight.W_700,
                    ),
                    on_click=go_login,
                ),
            ],
        ),
        width=460,
    )

    root = ft.Container(
        expand=True,
        content=ft.Stack(
            expand=True,
            controls=[
                _bg_layer(page),
                ft.Container(
                    expand=True,
                    alignment=ft.Alignment(0, 0),
                    padding=ft.Padding(16, 20, 16, 24),
                    content=ft.Column(
                        expand=True,
                        scroll=ft.ScrollMode.AUTO,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        alignment=ft.MainAxisAlignment.CENTER,
                        controls=[card],
                    ),
                ),
            ],
        ),
    )

    return ft.View(
        route="/register/success",
        controls=[
            ft.SafeArea(
                expand=True,
                content=root,
            )
        ],
    )
