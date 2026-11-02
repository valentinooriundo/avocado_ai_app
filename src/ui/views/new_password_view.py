import re

import flet as ft

from services.backend_recovery_service import recovery_reset_password
from services.settings_service import load_theme
from ui.state import get_state
from ui.views.recovery_views import (
    BRAND_GREEN,
    _bg_layer,
    _c_border,
    _c_card,
    _c_muted,
    _c_text,
    _card_shell,
    _input_capsule,
    _is_dark,
    _nav,
)

# route: /help/new-password


def create_new_password_view(page: ft.Page) -> ft.View:
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

    def go_login(_=None):
        _nav(page, "/login")

    BREAKPOINT_DESKTOP = 920
    FORM_WIDTH = 480
    LAYOUT_MAX_WIDTH = 980

    recovery_token = page.data.get("recovery_token")

    form_state = {
        "new_touched": False,
        "confirm_touched": False,
        "show_all": False,
        "saving": False,
    }

    # ---------------------------------------------------------
    # Encabezado
    # ---------------------------------------------------------

    back_btn = ft.IconButton(
        icon=ft.Icons.ARROW_BACK,
        tooltip=t(
            "new_password_back_tooltip",
            "Cancelar y volver al inicio de sesión",
        ),
        on_click=go_login,
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
    )

    security_badge = ft.Container(
        padding=ft.Padding(10, 6, 10, 6),
        border_radius=999,
        bgcolor=ft.Colors.with_opacity(
            0.08,
            BRAND_GREEN,
        ),
        content=ft.Row(
            tight=True,
            spacing=6,
            controls=[
                ft.Icon(
                    ft.Icons.VERIFIED_USER_OUTLINED,
                    size=14,
                    color=BRAND_GREEN,
                ),
                ft.Text(
                    t(
                        "new_password_secure_badge",
                        "Cambio protegido",
                    ),
                    size=11,
                    color=BRAND_GREEN,
                    weight=ft.FontWeight.W_700,
                ),
            ],
        ),
    )

    icon = ft.Container(
        width=64,
        height=64,
        border_radius=20,
        bgcolor=ft.Colors.with_opacity(
            0.10,
            BRAND_GREEN,
        ),
        alignment=ft.Alignment(0, 0),
        content=ft.Icon(
            ft.Icons.LOCK_RESET_OUTLINED,
            color=BRAND_GREEN,
            size=30,
        ),
    )

    title = ft.Text(
        t(
            "new_password_title",
            "Crea una nueva contraseña",
        ),
        size=25,
        weight=ft.FontWeight.W_900,
        color=_c_text(page),
        text_align=ft.TextAlign.CENTER,
    )

    subtitle = ft.Text(
        t(
            "new_password_subtitle",
            "Define una contraseña segura y diferente de las que utilizas en otros servicios.",
        ),
        size=13,
        color=_c_muted(page),
        text_align=ft.TextAlign.CENTER,
    )

    # ---------------------------------------------------------
    # Campos de contraseña
    # ---------------------------------------------------------

    new_pwd = ft.TextField(
        hint_text=t(
            "new_password_hint",
            "Ingresa tu nueva contraseña",
        ),
        border=ft.InputBorder.NONE,
        text_size=13,
        height=46,
        password=True,
        can_reveal_password=False,
        prefix_icon=ft.Icons.LOCK_OUTLINE,
        content_padding=ft.Padding(6, 10, 6, 10),
        autofocus=True,
    )

    confirm_pwd = ft.TextField(
        hint_text=t(
            "new_password_confirm_hint",
            "Repite la nueva contraseña",
        ),
        border=ft.InputBorder.NONE,
        text_size=13,
        height=46,
        password=True,
        can_reveal_password=False,
        prefix_icon=ft.Icons.LOCK_OUTLINE,
        content_padding=ft.Padding(6, 10, 6, 10),
    )

    new_pwd_shell = _input_capsule(
        page,
        new_pwd,
    )

    confirm_pwd_shell = _input_capsule(
        page,
        confirm_pwd,
    )

    def toggle_password(
        text_field: ft.TextField,
        button: ft.IconButton,
    ):
        text_field.password = not text_field.password

        button.icon = (
            ft.Icons.VISIBILITY_OFF
            if text_field.password
            else ft.Icons.VISIBILITY
        )

        button.tooltip = (
            t(
                "new_password_show_tooltip",
                "Mostrar contraseña",
            )
            if text_field.password
            else t(
                "new_password_hide_tooltip",
                "Ocultar contraseña",
            )
        )

        page.update()

    new_eye = ft.IconButton(
        icon=ft.Icons.VISIBILITY_OFF,
        icon_size=18,
        tooltip=t(
            "new_password_show_tooltip",
            "Mostrar contraseña",
        ),
    )

    confirm_eye = ft.IconButton(
        icon=ft.Icons.VISIBILITY_OFF,
        icon_size=18,
        tooltip=t(
            "new_password_show_tooltip",
            "Mostrar contraseña",
        ),
    )

    new_eye.on_click = lambda _: toggle_password(
        new_pwd,
        new_eye,
    )

    confirm_eye.on_click = lambda _: toggle_password(
        confirm_pwd,
        confirm_eye,
    )

    new_pwd.suffix = new_eye
    confirm_pwd.suffix = confirm_eye

    new_error_txt = ft.Text(
        "",
        size=10,
        color=ft.Colors.RED_400,
        weight=ft.FontWeight.W_600,
        visible=False,
    )

    confirm_error_txt = ft.Text(
        "",
        size=10,
        color=ft.Colors.RED_400,
        weight=ft.FontWeight.W_600,
        visible=False,
    )

    new_error_holder = ft.Container(
        height=17,
        alignment=ft.Alignment(-1, 0),
        content=new_error_txt,
    )

    confirm_error_holder = ft.Container(
        height=17,
        alignment=ft.Alignment(-1, 0),
        content=confirm_error_txt,
    )

    # ---------------------------------------------------------
    # Requisitos y nivel de seguridad
    # ---------------------------------------------------------

    def requirement_row(
        label: str,
    ) -> ft.Row:
        icon_control = ft.Icon(
            ft.Icons.RADIO_BUTTON_UNCHECKED,
            size=16,
            color=_c_muted(page),
        )

        text_control = ft.Text(
            label,
            size=11,
            color=_c_muted(page),
        )

        return ft.Row(
            spacing=8,
            controls=[
                icon_control,
                text_control,
            ],
        )

    req_min8 = requirement_row(
        t(
            "new_password_req_min8",
            "Mínimo 8 caracteres",
        )
    )

    req_lower = requirement_row(
        t(
            "new_password_req_lower",
            "Una letra minúscula",
        )
    )

    req_upper = requirement_row(
        t(
            "new_password_req_upper",
            "Una letra mayúscula",
        )
    )

    req_number = requirement_row(
        t(
            "new_password_req_number",
            "Al menos un número",
        )
    )

    req_special = requirement_row(
        t(
            "new_password_req_special",
            "Un símbolo, por ejemplo: ! @ #",
        )
    )

    requirement_rows = [
        req_min8,
        req_lower,
        req_upper,
        req_number,
        req_special,
    ]

    strength_label = ft.Text(
        t(
            "new_password_strength_empty",
            "Sin evaluar",
        ),
        size=11,
        color=_c_muted(page),
        weight=ft.FontWeight.W_800,
    )

    strength_segments = [
        ft.Container(
            expand=True,
            height=6,
            border_radius=999,
            bgcolor=ft.Colors.with_opacity(
                0.16,
                (
                    ft.Colors.WHITE
                    if _is_dark(page)
                    else ft.Colors.BLACK
                ),
            ),
        )
        for _ in range(5)
    ]

    strength_bar = ft.Row(
        spacing=5,
        controls=strength_segments,
    )

    requirements_card = ft.Container(
        padding=ft.Padding(15, 14, 15, 14),
        border_radius=16,
        bgcolor=ft.Colors.with_opacity(
            0.05,
            BRAND_GREEN,
        ),
        border=ft.Border.all(
            1,
            ft.Colors.with_opacity(
                0.18,
                BRAND_GREEN,
            ),
        ),
        content=ft.Column(
            spacing=9,
            controls=[
                ft.Text(
                    t(
                        "new_password_requirements_title",
                        "Requisitos de seguridad",
                    ),
                    size=11,
                    color=_c_text(page),
                    weight=ft.FontWeight.W_800,
                ),
                *requirement_rows,
            ],
        ),
    )

    match_status = ft.Row(
        spacing=7,
        visible=False,
        controls=[
            ft.Icon(
                ft.Icons.INFO_OUTLINE,
                size=15,
                color=_c_muted(page),
            ),
            ft.Text(
                "",
                size=10,
                color=_c_muted(page),
                weight=ft.FontWeight.W_600,
            ),
        ],
    )

    # ---------------------------------------------------------
    # Estados generales
    # ---------------------------------------------------------

    server_error_txt = ft.Text(
        "",
        size=10,
        color=ft.Colors.RED_400,
        weight=ft.FontWeight.W_600,
        visible=False,
        text_align=ft.TextAlign.CENTER,
    )

    token_alert = ft.Container(
        visible=not bool(recovery_token),
        padding=ft.Padding(13, 11, 13, 11),
        border_radius=14,
        bgcolor=ft.Colors.with_opacity(
            0.08,
            ft.Colors.RED_400,
        ),
        border=ft.Border.all(
            1,
            ft.Colors.with_opacity(
                0.30,
                ft.Colors.RED_400,
            ),
        ),
        content=ft.Row(
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.START,
            controls=[
                ft.Icon(
                    ft.Icons.ERROR_OUTLINE,
                    size=18,
                    color=ft.Colors.RED_400,
                ),
                ft.Text(
                    t(
                        "new_password_error_token",
                        "La sesión de recuperación no está disponible. Solicita un nuevo código para continuar.",
                    ),
                    size=10,
                    color=ft.Colors.RED_400,
                    expand=True,
                ),
            ],
        ),
    )

    save_btn_text = ft.Text(
        t(
            "new_password_button",
            "Actualizar contraseña",
        ),
        weight=ft.FontWeight.W_800,
        color=ft.Colors.WHITE,
        size=13,
    )

    save_btn = ft.Button(
        content=save_btn_text,
        height=52,
        style=ft.ButtonStyle(
            bgcolor=BRAND_GREEN,
            shape=ft.RoundedRectangleBorder(radius=15),
            elevation=2,
        ),
        on_click=lambda _: None,
        disabled=True,
    )

    save_btn.expand = True

    # ---------------------------------------------------------
    # Validación
    # ---------------------------------------------------------

    def password_rules(
        password: str,
    ) -> dict[str, bool]:
        return {
            "min8": len(password) >= 8,
            "lower": bool(
                re.search(r"[a-z]", password)
            ),
            "upper": bool(
                re.search(r"[A-Z]", password)
            ),
            "number": bool(
                re.search(r"\d", password)
            ),
            "special": bool(
                re.search(
                    r"[!@#$%&*()_\-+=\[\]{}:;,.?/]",
                    password,
                )
            ),
        }

    def mark_requirement(
        row: ft.Row,
        is_valid: bool,
    ):
        icon_control: ft.Icon = row.controls[0]
        text_control: ft.Text = row.controls[1]

        icon_control.name = (
            ft.Icons.CHECK_CIRCLE
            if is_valid
            else ft.Icons.RADIO_BUTTON_UNCHECKED
        )

        icon_control.color = (
            BRAND_GREEN
            if is_valid
            else _c_muted(page)
        )

        text_control.color = (
            BRAND_GREEN
            if is_valid
            else _c_muted(page)
        )

        text_control.weight = (
            ft.FontWeight.W_700
            if is_valid
            else ft.FontWeight.W_400
        )

    def update_strength(
        password: str,
        rules: dict[str, bool],
    ):
        score = sum(rules.values())

        inactive_color = ft.Colors.with_opacity(
            0.16,
            (
                ft.Colors.WHITE
                if _is_dark(page)
                else ft.Colors.BLACK
            ),
        )

        if score <= 2:
            active_color = ft.Colors.RED_400
            label = t(
                "new_password_strength_weak",
                "Débil",
            )
        elif score <= 4:
            active_color = ft.Colors.AMBER_700
            label = t(
                "new_password_strength_good",
                "Buena",
            )
        else:
            active_color = BRAND_GREEN
            label = t(
                "new_password_strength_strong",
                "Segura",
            )

        if not password:
            label = t(
                "new_password_strength_empty",
                "Sin evaluar",
            )
            active_color = inactive_color
            score = 0

        strength_label.value = label
        strength_label.color = (
            active_color
            if password
            else _c_muted(page)
        )

        for index, segment in enumerate(
            strength_segments
        ):
            segment.bgcolor = (
                active_color
                if index < score
                else inactive_color
            )

    def set_field_error(
        shell: ft.Container,
        error_control: ft.Text,
        message: str,
        should_show: bool,
    ):
        error_control.value = (
            message
            if should_show
            else ""
        )

        error_control.visible = should_show

        shell.border = ft.Border.all(
            1.4 if should_show else 1,
            (
                ft.Colors.RED_400
                if should_show
                else _c_border(page)
            ),
        )

    def clear_server_error():
        server_error_txt.value = ""
        server_error_txt.visible = False

    def validate(
        *,
        show_all: bool = False,
        update_page: bool = True,
    ) -> bool:
        if show_all:
            form_state["show_all"] = True
            form_state["new_touched"] = True
            form_state["confirm_touched"] = True

        password = new_pwd.value or ""
        confirmation = confirm_pwd.value or ""

        rules = password_rules(password)
        all_rules_valid = all(rules.values())

        for row, rule_value in zip(
            requirement_rows,
            rules.values(),
        ):
            mark_requirement(
                row,
                rule_value,
            )

        update_strength(
            password,
            rules,
        )

        new_error = ""

        if not password:
            new_error = t(
                "new_password_error_required",
                "Ingresa una nueva contraseña.",
            )
        elif not all_rules_valid:
            new_error = t(
                "new_password_error_requirements",
                "La contraseña todavía no cumple todos los requisitos.",
            )

        confirm_error = ""

        if not confirmation:
            confirm_error = t(
                "new_password_error_confirm_required",
                "Confirma la nueva contraseña.",
            )
        elif password != confirmation:
            confirm_error = t(
                "new_password_error_mismatch",
                "Las contraseñas no coinciden.",
            )

        show_new_error = bool(new_error) and (
            form_state["new_touched"]
            or form_state["show_all"]
        )

        show_confirm_error = bool(
            confirm_error
        ) and (
            form_state["confirm_touched"]
            or form_state["show_all"]
        )

        set_field_error(
            new_pwd_shell,
            new_error_txt,
            new_error,
            show_new_error,
        )

        set_field_error(
            confirm_pwd_shell,
            confirm_error_txt,
            confirm_error,
            show_confirm_error,
        )

        if confirmation:
            matches = (
                bool(password)
                and password == confirmation
            )

            match_icon: ft.Icon = (
                match_status.controls[0]
            )

            match_text: ft.Text = (
                match_status.controls[1]
            )

            match_status.visible = True

            match_icon.name = (
                ft.Icons.CHECK_CIRCLE_OUTLINE
                if matches
                else ft.Icons.ERROR_OUTLINE
            )

            match_icon.color = (
                BRAND_GREEN
                if matches
                else ft.Colors.RED_400
            )

            match_text.value = (
                t(
                    "new_password_match_ok",
                    "Las contraseñas coinciden.",
                )
                if matches
                else t(
                    "new_password_match_error",
                    "Las contraseñas no coinciden.",
                )
            )

            match_text.color = (
                BRAND_GREEN
                if matches
                else ft.Colors.RED_400
            )

        else:
            match_status.visible = False

        form_is_valid = (
            bool(recovery_token)
            and all_rules_valid
            and bool(confirmation)
            and password == confirmation
        )

        save_btn.disabled = (
            not form_is_valid
            or form_state["saving"]
        )

        if update_page:
            page.update()

        return form_is_valid

    def handle_new_change(_):
        form_state["new_touched"] = True
        clear_server_error()
        validate()

    def handle_confirm_change(_):
        form_state["confirm_touched"] = True
        clear_server_error()
        validate()

    new_pwd.on_change = handle_new_change
    confirm_pwd.on_change = handle_confirm_change

    new_pwd.on_blur = lambda _: validate()
    confirm_pwd.on_blur = lambda _: validate()

    # ---------------------------------------------------------
    # Actualización de contraseña
    # ---------------------------------------------------------

    def friendly_backend_error(
        exception: Exception,
    ) -> str:
        message = str(exception).upper()

        if (
            "EXPIRED" in message
            or "VENCIDO" in message
        ):
            return t(
                "new_password_error_expired",
                "La sesión de recuperación venció. Solicita un nuevo código.",
            )

        if (
            "WEAK_PASSWORD" in message
            or "CONTRASEÑA DÉBIL" in message
        ):
            return t(
                "new_password_error_weak",
                "La contraseña no cumple los requisitos de seguridad.",
            )

        if (
            "USED" in message
            or "UTILIZADO" in message
        ):
            return t(
                "new_password_error_used",
                "Esta sesión de recuperación ya fue utilizada.",
            )

        return t(
            "new_password_error_generic",
            "No pudimos actualizar la contraseña. Inténtalo nuevamente.",
        )

    def set_saving(
        value: bool,
    ):
        form_state["saving"] = value

        save_btn_text.value = (
            t(
                "new_password_saving",
                "Actualizando...",
            )
            if value
            else t(
                "new_password_button",
                "Actualizar contraseña",
            )
        )

        save_btn.disabled = (
            value
            or not validate(
                update_page=False
            )
        )

        page.update()

    def show_success():
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
                            "new_password_success",
                            "Contraseña actualizada correctamente. Ya puedes iniciar sesión.",
                        ),
                        color=ft.Colors.WHITE,
                        weight=ft.FontWeight.W_700,
                        expand=True,
                    ),
                ],
            ),
            bgcolor=BRAND_GREEN,
            show_close_icon=True,
            close_icon_color=ft.Colors.WHITE,
        )

        page.snack_bar.open = True
        page.update()

    def save_password(_=None):
        if form_state["saving"]:
            return

        if not validate(
            show_all=True
        ):
            return

        token = page.data.get(
            "recovery_token"
        )

        if not token:
            server_error_txt.value = t(
                "new_password_error_token",
                "La sesión de recuperación no está disponible. Solicita un nuevo código.",
            )
            server_error_txt.visible = True
            page.update()
            return

        password = new_pwd.value or ""

        set_saving(True)
        clear_server_error()

        try:
            recovery_reset_password(
                token,
                password,
            )

            new_pwd.value = ""
            confirm_pwd.value = ""

            page.data.pop(
                "recovery_token",
                None,
            )
            page.data.pop(
                "recover_mode",
                None,
            )
            page.data.pop(
                "recover_dest",
                None,
            )

            show_success()
            _nav(
                page,
                "/login",
            )

        except Exception as exception:
            set_saving(False)

            server_error_txt.value = (
                friendly_backend_error(
                    exception
                )
            )
            server_error_txt.visible = True
            page.update()

    save_btn.on_click = save_password
    confirm_pwd.on_submit = save_password

    back_login_btn = ft.TextButton(
        content=ft.Text(
            t(
                "new_password_back_login",
                "Volver al inicio de sesión",
            ),
            size=11,
            color=BRAND_GREEN,
            weight=ft.FontWeight.W_800,
        ),
        on_click=go_login,
        style=ft.ButtonStyle(
            padding=ft.Padding(0, 0, 0, 0),
        ),
    )

    # ---------------------------------------------------------
    # Formulario principal
    # ---------------------------------------------------------

    form_column = ft.Column(
        spacing=16,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    back_btn,
                    security_badge,
                ],
            ),
            icon,
            ft.Column(
                spacing=7,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    title,
                    subtitle,
                ],
            ),
            token_alert,
            ft.Divider(
                height=1,
                color=_c_border(page),
            ),
            ft.Column(
                spacing=7,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                controls=[
                    ft.Text(
                        t(
                            "new_password_label",
                            "Nueva contraseña",
                        ),
                        size=11,
                        color=_c_text(page),
                        weight=ft.FontWeight.W_800,
                    ),
                    new_pwd_shell,
                    new_error_holder,
                ],
            ),
            ft.Column(
                spacing=7,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text(
                                t(
                                    "new_password_strength_title",
                                    "Nivel de seguridad",
                                ),
                                size=10,
                                color=_c_muted(page),
                                weight=ft.FontWeight.W_700,
                            ),
                            strength_label,
                        ],
                    ),
                    strength_bar,
                ],
            ),
            requirements_card,
            ft.Column(
                spacing=7,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                controls=[
                    ft.Text(
                        t(
                            "new_password_confirm_label",
                            "Confirmar contraseña",
                        ),
                        size=11,
                        color=_c_text(page),
                        weight=ft.FontWeight.W_800,
                    ),
                    confirm_pwd_shell,
                    confirm_error_holder,
                    match_status,
                ],
            ),
            server_error_txt,
            ft.Row(
                controls=[save_btn],
            ),
            back_login_btn,
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
        icon_name,
        item_title: str,
        item_description: str,
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
                        0.09,
                        ft.Colors.WHITE,
                    ),
                    content=ft.Icon(
                        icon_name,
                        size=19,
                        color=ft.Colors.WHITE,
                    ),
                ),
                ft.Column(
                    spacing=3,
                    expand=True,
                    controls=[
                        ft.Text(
                            item_title,
                            size=12,
                            color=ft.Colors.WHITE,
                            weight=ft.FontWeight.W_800,
                        ),
                        ft.Text(
                            item_description,
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
        height=690,
        border_radius=28,
        padding=ft.Padding(32, 32, 32, 32),
        gradient=ft.LinearGradient(
            begin=ft.Alignment(-1, -1),
            end=ft.Alignment(1, 1),
            colors=[
                "#18382D",
                "#244A38",
                "#315E49",
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
                        0.09,
                        ft.Colors.WHITE,
                    ),
                    alignment=ft.Alignment(0, 0),
                    content=ft.Icon(
                        ft.Icons.SECURITY_OUTLINED,
                        size=32,
                        color=ft.Colors.WHITE,
                    ),
                ),
                ft.Column(
                    spacing=9,
                    controls=[
                        ft.Text(
                            t(
                                "new_password_side_title",
                                "Protege el acceso a tu cuenta",
                            ),
                            size=25,
                            weight=ft.FontWeight.W_900,
                            color=ft.Colors.WHITE,
                        ),
                        ft.Text(
                            t(
                                "new_password_side_description",
                                "Una contraseña sólida reduce el riesgo de accesos no autorizados y protege tu información agrícola.",
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
                    ft.Icons.PASSWORD_OUTLINED,
                    t(
                        "new_password_side_unique_title",
                        "Usa una contraseña única",
                    ),
                    t(
                        "new_password_side_unique_description",
                        "Evita reutilizar contraseñas de tu correo, redes sociales u otras aplicaciones.",
                    ),
                ),
                information_item(
                    ft.Icons.LOCK_OUTLINE,
                    t(
                        "new_password_side_combination_title",
                        "Combina distintos caracteres",
                    ),
                    t(
                        "new_password_side_combination_description",
                        "Incluye letras mayúsculas, minúsculas, números y símbolos.",
                    ),
                ),
                information_item(
                    ft.Icons.VERIFIED_USER_OUTLINED,
                    t(
                        "new_password_side_private_title",
                        "Manténla en privado",
                    ),
                    t(
                        "new_password_side_private_description",
                        "No compartas tu contraseña con otras personas ni la envíes por mensajes.",
                    ),
                ),
                ft.Container(expand=True),
                ft.Container(
                    padding=ft.Padding(14, 12, 14, 12),
                    border_radius=15,
                    bgcolor=ft.Colors.with_opacity(
                        0.08,
                        ft.Colors.WHITE,
                    ),
                    content=ft.Row(
                        spacing=10,
                        controls=[
                            ft.Icon(
                                ft.Icons.SHIELD_OUTLINED,
                                size=19,
                                color=ft.Colors.WHITE,
                            ),
                            ft.Text(
                                t(
                                    "new_password_side_footer",
                                    "Avoruna nunca te solicitará tu contraseña por correo, llamadas o redes sociales.",
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
            viewport_height = int(
                page.height or 820
            )

            panel_height = max(
                650,
                min(
                    760,
                    viewport_height - 70,
                ),
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
            min(
                450,
                int(width - 24),
            ),
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
                    padding=ft.Padding(
                        12,
                        18,
                        12,
                        24,
                    ),
                    content=ft.Column(
                        expand=True,
                        scroll=ft.ScrollMode.AUTO,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            layout_holder,
                        ],
                    ),
                ),
            ],
        ),
    )

    def on_resize(_):
        layout_holder.content = build_layout()
        page.update()

    page.on_resize = on_resize

    layout_holder.content = build_layout()
    validate(update_page=False)

    return ft.View(
        route="/help/new-password",
        controls=[
            ft.SafeArea(
                expand=True,
                content=root,
            )
        ],
    )
