import flet as ft

from services.backend_recovery_service import recovery_start
from services.settings_service import load_theme
from ui.state import get_state
from ui.views.recovery_views import (
    BRAND_GREEN,
    _bg_layer,
    _c_muted,
    _c_text,
    _card_shell,
    _input_capsule,
    _looks_valid,
    _nav,
    _pill_segment,
)


def create_forgot_password_view(page: ft.Page) -> ft.View:
    db = page.data.get("db")
    state = get_state(page)

    if db is not None:
        saved = load_theme(db)
        page.theme_mode = (
            ft.ThemeMode.DARK
            if saved == "dark"
            else ft.ThemeMode.LIGHT
        )

    def t(key: str, fallback: str) -> str:
        value = state.t(key)

        if value is None or value == key:
            return fallback

        return value

    def back(_=None):
        _nav(page, "/login")

    BREAKPOINT_DESKTOP = 920
    FORM_WIDTH = 480
    LAYOUT_MAX_WIDTH = 980

    mode = {"value": "email"}
    state_form = {
        "touched": False,
        "sending": False,
    }

    # ---------------------------------------------------------
    # Encabezado
    # ---------------------------------------------------------

    back_btn = ft.IconButton(
        icon=ft.Icons.ARROW_BACK,
        tooltip=t(
            "recovery_back_tooltip",
            "Volver al inicio de sesión",
        ),
        on_click=back,
        style=ft.ButtonStyle(
            bgcolor=ft.Colors.with_opacity(
                0.07,
                (
                    ft.Colors.WHITE
                    if page.theme_mode == ft.ThemeMode.DARK
                    else ft.Colors.BLACK
                ),
            ),
            shape=ft.RoundedRectangleBorder(radius=14),
        ),
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
                    t(
                        "recovery_secure_process",
                        "Proceso seguro",
                    ),
                    size=11,
                    color=BRAND_GREEN,
                    weight=ft.FontWeight.W_700,
                ),
            ],
        ),
    )

    title = ft.Text(
        t(
            "recovery_title",
            "Recupera el acceso a tu cuenta",
        ),
        size=25,
        weight=ft.FontWeight.W_900,
        color=_c_text(page),
    )

    subtitle = ft.Text(
        t(
            "recovery_subtitle",
            (
                "Elige cómo recibir el código de verificación "
                "para confirmar tu identidad."
            ),
        ),
        size=13,
        color=_c_muted(page),
    )

    # ---------------------------------------------------------
    # Selector del método
    # ---------------------------------------------------------

    method_title = ft.Text(
        t(
            "recovery_method_title",
            "Método de recuperación",
        ),
        size=14,
        weight=ft.FontWeight.W_800,
        color=_c_text(page),
    )

    method_description = ft.Text(
        t(
            "recovery_method_description",
            "Selecciona el medio asociado a tu cuenta de Avoruna.",
        ),
        size=11,
        color=_c_muted(page),
    )

    segments = ft.Row(
        spacing=10,
    )

    # ---------------------------------------------------------
    # Campo de contacto
    # ---------------------------------------------------------

    contact_label = ft.Text(
        "",
        size=11,
        weight=ft.FontWeight.W_700,
        color=_c_text(page),
    )

    contact_tf = ft.TextField(
        hint_text="nombre@avoruna.com",
        border=ft.InputBorder.NONE,
        text_size=13,
        height=46,
        prefix_icon=ft.Icons.MAIL_OUTLINE,
        keyboard_type=ft.KeyboardType.EMAIL,
        content_padding=ft.Padding(6, 10, 6, 10),
        autofocus=True,
    )

    contact_shell = _input_capsule(page, contact_tf)

    helper_txt = ft.Text(
        "",
        size=10,
        color=_c_muted(page),
    )

    error_txt = ft.Text(
        "",
        size=10,
        color=ft.Colors.RED_400,
        weight=ft.FontWeight.W_500,
        visible=False,
    )

    error_holder = ft.Container(
        height=18,
        alignment=ft.Alignment(-1, 0),
        content=error_txt,
    )

    # ---------------------------------------------------------
    # Aviso de seguridad
    # ---------------------------------------------------------

    security_notice = ft.Container(
        padding=ft.Padding(13, 11, 13, 11),
        border_radius=14,
        bgcolor=ft.Colors.with_opacity(0.06, BRAND_GREEN),
        content=ft.Row(
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.START,
            controls=[
                ft.Icon(
                    ft.Icons.INFO_OUTLINE,
                    size=18,
                    color=BRAND_GREEN,
                ),
                ft.Text(
                    t(
                        "recovery_security_notice",
                        (
                            "Te enviaremos un código de un solo uso. "
                            "Por seguridad, no lo compartas con otras personas."
                        ),
                    ),
                    size=10,
                    color=_c_muted(page),
                    expand=True,
                ),
            ],
        ),
    )

    # ---------------------------------------------------------
    # Botón principal
    # ---------------------------------------------------------

    send_btn_text = ft.Text(
        t(
            "recovery_send_button",
            "Enviar código de verificación",
        ),
        weight=ft.FontWeight.W_800,
        color=ft.Colors.WHITE,
        size=13,
    )

    send_btn = ft.Button(
        content=send_btn_text,
        height=52,
        style=ft.ButtonStyle(
            bgcolor=BRAND_GREEN,
            shape=ft.RoundedRectangleBorder(radius=15),
            elevation=2,
        ),
        on_click=lambda _: None,
    )

    send_btn.expand = True
    send_btn.disabled = True

    # ---------------------------------------------------------
    # Validación
    # ---------------------------------------------------------

    def clear_error():
        error_txt.value = ""
        error_txt.visible = False

        contact_shell.border = ft.Border.all(
            1,
            (
                "#2A3142"
                if page.theme_mode == ft.ThemeMode.DARK
                else ft.Colors.GREY_200
            ),
        )

    def show_error(message: str):
        error_txt.value = message
        error_txt.visible = True

        contact_shell.border = ft.Border.all(
            1.4,
            ft.Colors.RED_400,
        )

    def validation_message(value: str) -> str:
        if mode["value"] == "email":
            if not value:
                return t(
                    "recovery_email_required",
                    "Ingresa el correo electrónico registrado.",
                )

            return t(
                "recovery_email_invalid",
                (
                    "Ingresa un correo válido, por ejemplo: "
                    "nombre@avoruna.com."
                ),
            )

        if not value:
            return t(
                "recovery_phone_required",
                "Ingresa el número de teléfono registrado.",
            )

        return t(
            "recovery_phone_invalid",
            (
                "Ingresa un número válido, por ejemplo: "
                "+51 987 654 321."
            ),
        )

    def validate(
        _=None,
        *,
        show_message: bool = False,
    ) -> bool:
        value = (contact_tf.value or "").strip()

        is_valid = _looks_valid(
            mode["value"],
            value,
        )

        send_btn.disabled = (
            not is_valid
            or state_form["sending"]
        )

        if is_valid:
            clear_error()

        elif show_message or state_form["touched"]:
            show_error(validation_message(value))

        else:
            clear_error()

        page.update()
        return is_valid

    # ---------------------------------------------------------
    # Cambio de método
    # ---------------------------------------------------------

    def rebuild_segments():
        segments.controls = [
            ft.Container(
                expand=True,
                content=_pill_segment(
                    page,
                    t(
                        "recovery_email_option",
                        "Correo electrónico",
                    ),
                    mode["value"] == "email",
                    pick_email,
                ),
            ),
            ft.Container(
                expand=True,
                content=_pill_segment(
                    page,
                    t(
                        "recovery_phone_option",
                        "Teléfono",
                    ),
                    mode["value"] == "phone",
                    pick_phone,
                ),
            ),
        ]

    def refresh_contact_field():
        if mode["value"] == "email":
            contact_label.value = t(
                "recovery_email_label",
                "Correo electrónico registrado",
            )

            contact_tf.prefix_icon = ft.Icons.MAIL_OUTLINE
            contact_tf.hint_text = "nombre@avoruna.com"
            contact_tf.keyboard_type = ft.KeyboardType.EMAIL

            helper_txt.value = t(
                "recovery_email_helper",
                (
                    "Utiliza el mismo correo con el que creaste "
                    "tu cuenta."
                ),
            )

        else:
            contact_label.value = t(
                "recovery_phone_label",
                "Número de teléfono registrado",
            )

            contact_tf.prefix_icon = (
                ft.Icons.PHONE_ANDROID_OUTLINED
            )
            contact_tf.hint_text = "+51 9xx xxx xxx"
            contact_tf.keyboard_type = ft.KeyboardType.PHONE

            helper_txt.value = t(
                "recovery_phone_helper",
                (
                    "Ingresa el número asociado a tu cuenta, "
                    "incluyendo el código del país."
                ),
            )

    def refresh_ui():
        rebuild_segments()
        refresh_contact_field()
        page.update()

    def reset_contact():
        contact_tf.value = ""
        state_form["touched"] = False
        send_btn.disabled = True
        clear_error()

    def pick_email(_=None):
        mode["value"] = "email"
        reset_contact()
        refresh_ui()

    def pick_phone(_=None):
        mode["value"] = "phone"
        reset_contact()
        refresh_ui()

    # ---------------------------------------------------------
    # Envío del código
    # ---------------------------------------------------------

    def set_sending(value: bool):
        state_form["sending"] = value

        if value:
            send_btn.disabled = True
            send_btn_text.value = t(
                "recovery_sending_button",
                "Enviando código...",
            )
        else:
            send_btn_text.value = t(
                "recovery_send_button",
                "Enviar código de verificación",
            )

            send_btn.disabled = not _looks_valid(
                mode["value"],
                (contact_tf.value or "").strip(),
            )

        page.update()

    def friendly_backend_error(exception: Exception) -> str:
        message = str(exception).strip()
        message_upper = message.upper()

        if "NOT_FOUND" in message_upper or "NO EXISTE" in message_upper:
            return t(
                "recovery_account_not_found",
                (
                    "No encontramos una cuenta asociada "
                    "a los datos ingresados."
                ),
            )

        if (
            "TOO_MANY" in message_upper
            or "MUCHOS INTENTOS" in message_upper
        ):
            return t(
                "recovery_too_many_attempts",
                (
                    "Se realizaron demasiados intentos. "
                    "Espera unos minutos antes de volver a intentarlo."
                ),
            )

        return t(
            "recovery_generic_error",
            (
                "No pudimos enviar el código en este momento. "
                "Verifica tus datos e inténtalo nuevamente."
            ),
        )

    def send_code(_=None):
        if state_form["sending"]:
            return

        state_form["touched"] = True

        if not validate(show_message=True):
            return

        value = (contact_tf.value or "").strip()

        set_sending(True)

        try:
            recovery_start(
                mode["value"],
                value,
            )

            page.data["recover_mode"] = mode["value"]
            page.data["recover_dest"] = value

            page.snack_bar = ft.SnackBar(
                content=ft.Row(
                    spacing=10,
                    controls=[
                        ft.Icon(
                            ft.Icons.CHECK_CIRCLE_OUTLINE,
                            color=ft.Colors.WHITE,
                        ),
                        ft.Text(
                            t(
                                "recovery_code_sent",
                                (
                                    "Código enviado correctamente. "
                                    "Revisa tu correo o teléfono."
                                ),
                            ),
                            color=ft.Colors.WHITE,
                            weight=ft.FontWeight.W_700,
                        ),
                    ],
                ),
                bgcolor=BRAND_GREEN,
                show_close_icon=True,
                close_icon_color=ft.Colors.WHITE,
            )

            page.snack_bar.open = True
            page.update()

            _nav(page, "/help/verify")

        except Exception as ex:
            show_error(friendly_backend_error(ex))
            set_sending(False)

    def contact_changed(_):
        state_form["touched"] = True
        validate()

    contact_tf.on_change = contact_changed
    contact_tf.on_blur = lambda _: validate(show_message=True)
    contact_tf.on_submit = send_code
    send_btn.on_click = send_code

    # ---------------------------------------------------------
    # Pie del formulario
    # ---------------------------------------------------------

    bottom_text = ft.Text(
        t(
            "recovery_remembered",
            "¿Recordaste tu contraseña?",
        ),
        size=11,
        color=_c_muted(page),
    )

    bottom_link = ft.TextButton(
        content=ft.Text(
            t(
                "recovery_back_login",
                "Volver a iniciar sesión",
            ),
            size=11,
            color=BRAND_GREEN,
            weight=ft.FontWeight.W_800,
        ),
        on_click=back,
        style=ft.ButtonStyle(
            padding=ft.Padding(0, 0, 0, 0),
        ),
    )

    bottom_row = ft.Row(
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=5,
        wrap=True,
        controls=[
            bottom_text,
            bottom_link,
        ],
    )

    # ---------------------------------------------------------
    # Formulario principal
    # ---------------------------------------------------------

    form_column = ft.Column(
        spacing=17,
        controls=[
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    back_btn,
                    security_badge,
                ],
            ),
            ft.Column(
                spacing=7,
                controls=[
                    title,
                    subtitle,
                ],
            ),
            ft.Divider(
                height=1,
                color=(
                    "#2A3142"
                    if page.theme_mode == ft.ThemeMode.DARK
                    else ft.Colors.GREY_300
                ),
            ),
            ft.Column(
                spacing=4,
                controls=[
                    method_title,
                    method_description,
                ],
            ),
            segments,
            ft.Column(
                spacing=7,
                controls=[
                    contact_label,
                    contact_shell,
                    helper_txt,
                    error_holder,
                ],
            ),
            security_notice,
            ft.Row(
                controls=[send_btn],
            ),
            bottom_row,
        ],
    )

    card = _card_shell(
        page,
        form_column,
        width=FORM_WIDTH,
    )

    # ---------------------------------------------------------
    # Panel informativo de escritorio
    # ---------------------------------------------------------

    def information_item(
        icon,
        title_text: str,
        description_text: str,
    ) -> ft.Row:
        return ft.Row(
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.START,
            controls=[
                ft.Container(
                    width=38,
                    height=38,
                    border_radius=12,
                    alignment=ft.Alignment(0, 0),
                    bgcolor=ft.Colors.with_opacity(
                        0.12,
                        ft.Colors.WHITE,
                    ),
                    content=ft.Icon(
                        icon,
                        size=19,
                        color=ft.Colors.WHITE,
                    ),
                ),
                ft.Column(
                    spacing=3,
                    expand=True,
                    controls=[
                        ft.Text(
                            title_text,
                            size=12,
                            color=ft.Colors.WHITE,
                            weight=ft.FontWeight.W_800,
                        ),
                        ft.Text(
                            description_text,
                            size=10,
                            color=ft.Colors.with_opacity(
                                0.82,
                                ft.Colors.WHITE,
                            ),
                        ),
                    ],
                ),
            ],
        )

    left_panel = ft.Container(
        expand=True,
        height=620,
        border_radius=28,
        padding=ft.Padding(32, 32, 32, 32),
        gradient=ft.LinearGradient(
            begin=ft.Alignment(-1, -1),
            end=ft.Alignment(1, 1),
            colors=[
                "#1F4D39",
                "#2F5D46",
                "#4C8C6A",
            ],
        ),
        content=ft.Column(
            expand=True,
            spacing=22,
            controls=[
                ft.Container(
                    width=62,
                    height=62,
                    border_radius=20,
                    bgcolor=ft.Colors.with_opacity(
                        0.14,
                        ft.Colors.WHITE,
                    ),
                    alignment=ft.Alignment(0, 0),
                    content=ft.Icon(
                        ft.Icons.LOCK_RESET_OUTLINED,
                        size=32,
                        color=ft.Colors.WHITE,
                    ),
                ),
                ft.Column(
                    spacing=9,
                    controls=[
                        ft.Text(
                            t(
                                "recovery_side_title",
                                "Recupera tu cuenta de forma segura",
                            ),
                            size=25,
                            weight=ft.FontWeight.W_900,
                            color=ft.Colors.WHITE,
                        ),
                        ft.Text(
                            t(
                                "recovery_side_description",
                                (
                                    "Confirma tu identidad y establece "
                                    "una nueva contraseña mediante un "
                                    "proceso rápido y protegido."
                                ),
                            ),
                            size=12,
                            color=ft.Colors.with_opacity(
                                0.86,
                                ft.Colors.WHITE,
                            ),
                        ),
                    ],
                ),
                ft.Container(height=4),
                information_item(
                    ft.Icons.CONTACT_MAIL_OUTLINED,
                    t(
                        "recovery_side_step1_title",
                        "1. Confirma tus datos",
                    ),
                    t(
                        "recovery_side_step1_description",
                        (
                            "Utiliza el correo o teléfono registrado "
                            "en tu cuenta."
                        ),
                    ),
                ),
                information_item(
                    ft.Icons.MARK_EMAIL_READ_OUTLINED,
                    t(
                        "recovery_side_step2_title",
                        "2. Recibe tu código",
                    ),
                    t(
                        "recovery_side_step2_description",
                        (
                            "Te enviaremos un código temporal "
                            "para verificar tu identidad."
                        ),
                    ),
                ),
                information_item(
                    ft.Icons.PASSWORD_OUTLINED,
                    t(
                        "recovery_side_step3_title",
                        "3. Crea una nueva contraseña",
                    ),
                    t(
                        "recovery_side_step3_description",
                        (
                            "Define una contraseña segura y recupera "
                            "el acceso a Avoruna."
                        ),
                    ),
                ),
                ft.Container(expand=True),
                ft.Container(
                    padding=ft.Padding(14, 12, 14, 12),
                    border_radius=15,
                    bgcolor=ft.Colors.with_opacity(
                        0.10,
                        ft.Colors.WHITE,
                    ),
                    content=ft.Row(
                        spacing=10,
                        controls=[
                            ft.Icon(
                                ft.Icons.VERIFIED_USER_OUTLINED,
                                size=19,
                                color=ft.Colors.WHITE,
                            ),
                            ft.Text(
                                t(
                                    "recovery_side_footer",
                                    (
                                        "Tus datos se procesan de manera "
                                        "segura y confidencial."
                                    ),
                                ),
                                size=10,
                                expand=True,
                                color=ft.Colors.with_opacity(
                                    0.88,
                                    ft.Colors.WHITE,
                                ),
                            ),
                        ],
                    ),
                ),
            ],
        ),
    )

    # ---------------------------------------------------------
    # Diseño responsive
    # ---------------------------------------------------------

    layout_holder = ft.Container()

    def build_layout():
        width = page.width or 420
        is_desktop = width >= BREAKPOINT_DESKTOP

        if is_desktop:
            viewport_height = int(page.height or 800)
            panel_height = max(
                600,
                min(700, viewport_height - 80),
            )

            card.width = FORM_WIDTH
            card.height = panel_height

            form_column.expand = True
            form_column.scroll = ft.ScrollMode.AUTO

            left_panel.height = panel_height

            total_width = min(
                LAYOUT_MAX_WIDTH,
                int(width - 40),
            )

            return ft.Container(
                width=total_width,
                height=panel_height,
                content=ft.Row(
                    spacing=22,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                    controls=[
                        ft.Container(
                            expand=True,
                            height=panel_height,
                            content=left_panel,
                        ),
                        ft.Container(
                            width=FORM_WIDTH,
                            height=panel_height,
                            content=card,
                        ),
                    ],
                ),
            )

        mobile_width = max(
            320,
            min(460, int(width - 32)),
        )

        card.width = mobile_width
        card.height = None

        form_column.expand = False
        form_column.scroll = None

        return ft.Container(
            width=mobile_width,
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
                    alignment=ft.Alignment(0, 0),
                    padding=ft.Padding(16, 20, 16, 24),
                    content=ft.Column(
                        expand=True,
                        scroll=ft.ScrollMode.AUTO,
                        horizontal_alignment=(
                            ft.CrossAxisAlignment.CENTER
                        ),
                        controls=[layout_holder],
                    ),
                ),
            ],
        ),
    )

    def on_resize(_):
        layout_holder.content = build_layout()
        page.update()

    page.on_resize = on_resize

    rebuild_segments()
    refresh_contact_field()
    layout_holder.content = build_layout()
    validate()

    return ft.View(
        route="/help",
        controls=[
            ft.SafeArea(
                expand=True,
                content=root,
            )
        ],
    )