import asyncio
import re

import flet as ft

from services.backend_recovery_service import recovery_check, recovery_start
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
    _is_dark,
    _nav,
)

# route: /help/verify


def create_verify_otp_view(page: ft.Page) -> ft.View:
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
        _nav(page, "/help")

    BREAKPOINT_DESKTOP = 920
    FORM_WIDTH = 470
    LAYOUT_MAX_WIDTH = 980
    OTP_LENGTH = 6
    RESEND_SECONDS = 45

    destination = str(page.data.get("recover_dest", "") or "").strip()
    mode = str(page.data.get("recover_mode", "email") or "email").strip()

    form_state = {
        "active_index": 0,
        "has_error": False,
        "verifying": False,
        "resending": False,
    }

    timer_state = {
        "generation": 0,
    }

    def mask_destination(value: str, selected_mode: str) -> str:
        if not value:
            return t(
                "verify_destination_missing",
                "Destino no disponible",
            )

        if selected_mode == "email" and "@" in value:
            local, domain = value.split("@", 1)
            visible = local[:2] if len(local) >= 2 else local[:1]
            return f"{visible}***@{domain}"

        digits = re.sub(r"\D+", "", value)

        if len(digits) >= 4:
            country = f"+{digits[:2]} " if value.startswith("+") else ""
            return f"{country}••• ••• {digits[-4:]}"

        return value

    masked_destination = mask_destination(destination, mode)

    def show_snackbar(message: str, *, success: bool = True):
        page.snack_bar = ft.SnackBar(
            content=ft.Row(
                spacing=10,
                controls=[
                    ft.Icon(
                        (
                            ft.Icons.CHECK_CIRCLE_OUTLINE
                            if success
                            else ft.Icons.ERROR_OUTLINE
                        ),
                        color=ft.Colors.WHITE,
                    ),
                    ft.Text(
                        message,
                        color=ft.Colors.WHITE,
                        weight=ft.FontWeight.W_700,
                        expand=True,
                    ),
                ],
            ),
            bgcolor=(
                BRAND_GREEN
                if success
                else ft.Colors.RED_700
            ),
            show_close_icon=True,
            close_icon_color=ft.Colors.WHITE,
        )
        page.snack_bar.open = True
        page.update()

    # ---------------------------------------------------------
    # Encabezado del formulario
    # ---------------------------------------------------------

    back_btn = ft.IconButton(
        icon=ft.Icons.ARROW_BACK,
        tooltip=t(
            "verify_back_tooltip",
            "Volver al método de recuperación",
        ),
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
                    ft.Icons.VERIFIED_USER_OUTLINED,
                    size=14,
                    color=BRAND_GREEN,
                ),
                ft.Text(
                    t(
                        "verify_secure_badge",
                        "Verificación segura",
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
            ft.Icons.SHIELD_OUTLINED,
            color=BRAND_GREEN,
            size=30,
        ),
    )

    title = ft.Text(
        t(
            "verify_title",
            "Verifica tu identidad",
        ),
        size=25,
        weight=ft.FontWeight.W_900,
        color=_c_text(page),
        text_align=ft.TextAlign.CENTER,
    )

    subtitle = ft.Text(
        t(
            "verify_subtitle",
            "Ingresa el código de 6 dígitos que enviamos al medio registrado.",
        ),
        size=13,
        color=_c_muted(page),
        text_align=ft.TextAlign.CENTER,
    )

    destination_chip = ft.Container(
        padding=ft.Padding(13, 9, 13, 9),
        border_radius=13,
        border=ft.Border.all(1, _c_border(page)),
        bgcolor=ft.Colors.with_opacity(0.04, BRAND_GREEN),
        content=ft.Row(
            tight=True,
            spacing=8,
            controls=[
                ft.Icon(
                    (
                        ft.Icons.MAIL_OUTLINE
                        if mode == "email"
                        else ft.Icons.PHONE_ANDROID_OUTLINED
                    ),
                    size=17,
                    color=BRAND_GREEN,
                ),
                ft.Text(
                    masked_destination,
                    size=12,
                    color=_c_text(page),
                    weight=ft.FontWeight.W_700,
                ),
            ],
        ),
    )

    code_label = ft.Text(
        t(
            "verify_code_label",
            "Código de verificación",
        ),
        size=11,
        color=_c_text(page),
        weight=ft.FontWeight.W_700,
    )

    code_helper = ft.Text(
        t(
            "verify_code_helper",
            "Puedes escribir o pegar el código completo.",
        ),
        size=10,
        color=_c_muted(page),
        text_align=ft.TextAlign.CENTER,
    )

    # ---------------------------------------------------------
    # Casillas OTP
    # ---------------------------------------------------------

    boxes: list[ft.TextField] = []
    box_containers: list[ft.Container] = []

    status_txt = ft.Text(
        "",
        size=10,
        color=ft.Colors.RED_400,
        text_align=ft.TextAlign.CENTER,
        weight=ft.FontWeight.W_600,
        visible=False,
    )

    status_holder = ft.Container(
        height=18,
        alignment=ft.Alignment(0, 0),
        content=status_txt,
    )

    verify_btn_text = ft.Text(
        t(
            "verify_button",
            "Verificar código",
        ),
        weight=ft.FontWeight.W_800,
        color=ft.Colors.WHITE,
        size=13,
    )

    verify_btn = ft.Button(
        content=verify_btn_text,
        height=52,
        style=ft.ButtonStyle(
            bgcolor=BRAND_GREEN,
            shape=ft.RoundedRectangleBorder(radius=15),
            elevation=2,
        ),
        on_click=lambda _: None,
        disabled=True,
    )
    verify_btn.expand = True

    def get_code() -> str:
        return "".join(
            (box.value or "").strip()
            for box in boxes
        )

    def refresh_box_styles():
        for index, container in enumerate(box_containers):
            has_value = bool((boxes[index].value or "").strip())
            is_active = form_state["active_index"] == index

            if form_state["has_error"]:
                border_color = ft.Colors.RED_400
                border_width = 1.5
            elif is_active:
                border_color = BRAND_GREEN
                border_width = 1.6
            elif has_value:
                border_color = ft.Colors.with_opacity(
                    0.70,
                    BRAND_GREEN,
                )
                border_width = 1.4
            else:
                border_color = _c_border(page)
                border_width = 1

            container.border = ft.Border.all(
                border_width,
                border_color,
            )

    def clear_error():
        form_state["has_error"] = False
        status_txt.value = ""
        status_txt.visible = False

    def show_invalid(message: str):
        form_state["has_error"] = True
        status_txt.value = message
        status_txt.visible = True
        refresh_box_styles()
        page.update()

    def validate_code(*, update_page: bool = True) -> bool:
        code = get_code()
        is_complete = (
            len(code) == OTP_LENGTH
            and code.isdigit()
        )

        verify_btn.disabled = (
            not is_complete
            or form_state["verifying"]
        )

        if form_state["has_error"] and code:
            clear_error()

        refresh_box_styles()

        if update_page:
            page.update()

        return is_complete

    def focus_box(index: int):
        if not boxes:
            return

        safe_index = max(
            0,
            min(index, OTP_LENGTH - 1),
        )

        form_state["active_index"] = safe_index

        try:
            boxes[safe_index].focus()
        except Exception:
            pass

    def distribute_digits(
        digits: str,
        start_index: int = 0,
    ):
        clean_digits = "".join(
            char
            for char in digits
            if char.isdigit()
        )

        if not clean_digits:
            return

        write_index = start_index

        for digit in clean_digits:
            if write_index >= OTP_LENGTH:
                break

            boxes[write_index].value = digit
            write_index += 1

        focus_box(
            min(write_index, OTP_LENGTH - 1)
        )
        validate_code()

    def build_box(index: int):
        text_field = ft.TextField(
            value="",
            keyboard_type=ft.KeyboardType.NUMBER,
            border=ft.InputBorder.NONE,
            text_size=19,
            text_align=ft.TextAlign.CENTER,
            content_padding=ft.Padding(0, 13, 0, 13),
            width=38,
            height=52,
            autofocus=index == 0,
        )

        container = ft.Container(
            width=38,
            height=54,
            border_radius=12,
            border=ft.Border.all(
                1,
                _c_border(page),
            ),
            bgcolor=_c_card(page),
            alignment=ft.Alignment(0, 0),
            content=text_field,
        )

        def on_focus(_):
            form_state["active_index"] = index
            refresh_box_styles()
            page.update()

        def on_blur(_):
            refresh_box_styles()
            page.update()

        def on_change(_):
            original_value = text_field.value or ""
            digits = "".join(
                char
                for char in original_value
                if char.isdigit()
            )

            clear_error()

            # Permite pegar varios dígitos, incluso el código completo.
            if len(digits) > 1:
                text_field.value = ""
                distribute_digits(
                    digits,
                    start_index=index,
                )
                return

            if digits:
                text_field.value = digits[-1]

                if index < OTP_LENGTH - 1:
                    focus_box(index + 1)
            else:
                text_field.value = ""

                # Solo retrocede cuando el usuario realmente borró
                # el contenido, no cuando escribió un carácter inválido.
                if original_value == "" and index > 0:
                    focus_box(index - 1)

            validate_code()

        text_field.on_focus = on_focus
        text_field.on_blur = on_blur
        text_field.on_change = on_change

        boxes.append(text_field)
        box_containers.append(container)

    for box_index in range(OTP_LENGTH):
        build_box(box_index)

    code_row = ft.Row(
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=6,
        controls=box_containers,
    )

    def clear_code():
        for box in boxes:
            box.value = ""

        clear_error()
        focus_box(0)
        validate_code()

    # ---------------------------------------------------------
    # Reenvío y temporizador
    # ---------------------------------------------------------

    resend_text = ft.Text(
        "",
        size=11,
        color=BRAND_GREEN,
        weight=ft.FontWeight.W_800,
    )

    resend_btn = ft.TextButton(
        content=resend_text,
        on_click=lambda _: None,
        disabled=True,
        style=ft.ButtonStyle(
            padding=ft.Padding(4, 4, 4, 4),
        ),
    )

    resend_question = ft.Text(
        t(
            "verify_resend_question",
            "¿No recibiste el código?",
        ),
        size=11,
        color=_c_muted(page),
    )

    def format_countdown(seconds: int) -> str:
        minutes, remaining_seconds = divmod(
            max(0, seconds),
            60,
        )
        return f"{minutes:02d}:{remaining_seconds:02d}"

    def start_countdown():
        timer_state["generation"] += 1
        generation = timer_state["generation"]

        async def run_timer():
            resend_btn.disabled = True

            for seconds in range(
                RESEND_SECONDS,
                -1,
                -1,
            ):
                if generation != timer_state["generation"]:
                    return

                resend_text.value = t(
                    "verify_resend_countdown",
                    "Reenviar en {time}",
                ).format(
                    time=format_countdown(seconds)
                )

                page.update()
                await asyncio.sleep(1)

            if generation == timer_state["generation"]:
                resend_text.value = t(
                    "verify_resend_button",
                    "Reenviar código",
                )
                resend_btn.disabled = False
                page.update()

        page.run_task(run_timer)

    def friendly_recovery_error(
        exception: Exception,
    ) -> str:
        message = str(exception).upper()

        if (
            "EXPIRED" in message
            or "VENCIDO" in message
        ):
            return t(
                "verify_error_expired",
                "El código venció. Solicita uno nuevo para continuar.",
            )

        if (
            "INVALID" in message
            or "INCORRECT" in message
            or "INVÁLIDO" in message
        ):
            return t(
                "verify_error_invalid",
                "El código ingresado no es correcto. Revísalo e inténtalo nuevamente.",
            )

        if (
            "TOO_MANY" in message
            or "MUCHOS INTENTOS" in message
        ):
            return t(
                "verify_error_attempts",
                "Se realizaron demasiados intentos. Espera unos minutos antes de continuar.",
            )

        return t(
            "verify_error_generic",
            "No pudimos verificar el código. Inténtalo nuevamente.",
        )

    def resend_code(_=None):
        if (
            resend_btn.disabled
            or form_state["resending"]
            or not destination
        ):
            return

        form_state["resending"] = True
        resend_btn.disabled = True
        resend_text.value = t(
            "verify_resending",
            "Enviando nuevo código...",
        )
        page.update()

        try:
            recovery_start(
                mode,
                destination,
            )

            clear_code()
            start_countdown()

            show_snackbar(
                t(
                    "verify_resend_success",
                    "Enviamos un nuevo código de verificación.",
                )
            )

        except Exception as exception:
            resend_btn.disabled = False
            resend_text.value = t(
                "verify_resend_button",
                "Reenviar código",
            )

            show_snackbar(
                friendly_recovery_error(exception),
                success=False,
            )

        finally:
            form_state["resending"] = False
            page.update()

    resend_btn.on_click = resend_code

    resend_row = ft.Row(
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=4,
        wrap=True,
        controls=[
            resend_question,
            resend_btn,
        ],
    )

    # ---------------------------------------------------------
    # Verificación
    # ---------------------------------------------------------

    def set_verifying(value: bool):
        form_state["verifying"] = value

        verify_btn_text.value = (
            t(
                "verify_checking",
                "Verificando...",
            )
            if value
            else t(
                "verify_button",
                "Verificar código",
            )
        )

        verify_btn.disabled = (
            value
            or not (
                len(get_code()) == OTP_LENGTH
                and get_code().isdigit()
            )
        )

        page.update()

    def verify(_=None):
        if form_state["verifying"]:
            return

        if not validate_code():
            show_invalid(
                t(
                    "verify_error_incomplete",
                    "Completa los 6 dígitos para continuar.",
                )
            )
            return

        code = get_code()
        set_verifying(True)

        try:
            result = recovery_check(
                mode,
                destination,
                code,
            )

            recovery_token = result.get(
                "recovery_token"
            )

            if not recovery_token:
                raise RuntimeError(
                    "RECOVERY_TOKEN_MISSING"
                )

            page.data["recovery_token"] = recovery_token

            # Detiene cualquier temporizador activo.
            timer_state["generation"] += 1

            _nav(
                page,
                "/help/new-password",
            )

        except Exception as exception:
            set_verifying(False)
            show_invalid(
                friendly_recovery_error(exception)
            )

    verify_btn.on_click = verify

    for text_field in boxes:
        text_field.on_submit = verify

    change_method_btn = ft.TextButton(
        content=ft.Text(
            t(
                "verify_change_method",
                "Cambiar método de recuperación",
            ),
            size=11,
            color=BRAND_GREEN,
            weight=ft.FontWeight.W_700,
        ),
        on_click=back,
        style=ft.ButtonStyle(
            padding=ft.Padding(0, 0, 0, 0),
        ),
    )

    # ---------------------------------------------------------
    # Formulario
    # ---------------------------------------------------------

    form_column = ft.Column(
        spacing=17,
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
            destination_chip,
            ft.Divider(
                height=1,
                color=_c_border(page),
            ),
            ft.Column(
                spacing=8,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    code_label,
                    code_row,
                    code_helper,
                    status_holder,
                ],
            ),
            ft.Row(
                controls=[verify_btn],
            ),
            resend_row,
            change_method_btn,
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
        height=610,
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
                        ft.Icons.VERIFIED_USER_OUTLINED,
                        size=32,
                        color=ft.Colors.WHITE,
                    ),
                ),
                ft.Column(
                    spacing=9,
                    controls=[
                        ft.Text(
                            t(
                                "verify_side_title",
                                "Confirma que eres tú",
                            ),
                            size=25,
                            weight=ft.FontWeight.W_900,
                            color=ft.Colors.WHITE,
                        ),
                        ft.Text(
                            t(
                                "verify_side_description",
                                "Utiliza el código temporal que enviamos al medio registrado para continuar con la recuperación.",
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
                        "verify_side_code_title",
                        "Código de 6 dígitos",
                    ),
                    t(
                        "verify_side_code_description",
                        "Escribe o pega el código exactamente como aparece en el mensaje.",
                    ),
                ),
                information_item(
                    ft.Icons.SCHEDULE_OUTLINED,
                    t(
                        "verify_side_expiration_title",
                        "Vigencia limitada",
                    ),
                    t(
                        "verify_side_expiration_description",
                        "El código vence después de 10 minutos por motivos de seguridad.",
                    ),
                ),
                information_item(
                    ft.Icons.LOCK_OUTLINE,
                    t(
                        "verify_side_security_title",
                        "Información confidencial",
                    ),
                    t(
                        "verify_side_security_description",
                        "No compartas este código con otras personas.",
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
                                    "verify_side_footer",
                                    "Avoruna nunca solicitará este código por llamadas o redes sociales.",
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
                590,
                min(690, viewport_height - 80),
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
            min(450, int(width - 24)),
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
                    padding=ft.Padding(12, 18, 12, 24),
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

    def on_resize(_):
        layout_holder.content = build_layout()
        page.update()

    page.on_resize = on_resize

    layout_holder.content = build_layout()
    validate_code(update_page=False)
    start_countdown()

    return ft.View(
        route="/help/verify",
        controls=[
            ft.SafeArea(
                expand=True,
                content=root,
            )
        ],
    )
