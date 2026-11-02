# src/ui/views/recovery_views.py
import re
import asyncio
import flet as ft

from ui.state import get_state
from services.settings_service import load_theme

BRAND_GREEN = "#2F5D46"
BRAND_GREEN_DARK = "#244A38"
BG_TINT = "#EEF3ED"

EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
PHONE_RE = re.compile(r"^\+?\d[\d\s]{7,15}\d$")


# =========================
# Small helpers
# =========================
def _nav(page: ft.Page, route: str):
    asyncio.create_task(page.push_route(route))


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
                ft.Container(expand=True, bgcolor=BG_TINT, opacity=0.10 if _is_dark(page) else 0.55),
            ],
        ),
    )


def _card_shell(page: ft.Page, content: ft.Control, width: int = 420):
    return ft.Container(
        width=width,
        padding=ft.Padding(18, 16, 18, 18),
        border_radius=22,
        bgcolor=_c_card(page),
        border=ft.Border.all(1, _c_border(page)),
        shadow=ft.BoxShadow(
            blur_radius=18,
            spread_radius=2,
            color=ft.Colors.with_opacity(0.18 if _is_dark(page) else 0.10, ft.Colors.BLACK),
        ),
        content=content,
    )


def _input_capsule(page: ft.Page, control: ft.Control):
    return ft.Container(
        padding=ft.Padding(12, 6, 12, 6),
        border_radius=16,
        bgcolor=_c_card(page) if _is_dark(page) else ft.Colors.WHITE,
        border=ft.Border.all(1, _c_border(page)),
        content=control,
    )


def _primary_btn(text: str, on_click, height: int = 50):
    return ft.Button(
        content=ft.Text(text, weight=ft.FontWeight.W_900, color=ft.Colors.WHITE, size=13),
        height=height,
        style=ft.ButtonStyle(bgcolor=BRAND_GREEN, shape=ft.RoundedRectangleBorder(radius=16)),
        on_click=on_click,
    )


def _pill_segment(page: ft.Page, label: str, active: bool, on_click):
    # "activo" bien marcado: verde + texto blanco
    bg = BRAND_GREEN if active else (_c_card(page) if not _is_dark(page) else ft.Colors.with_opacity(0.04, ft.Colors.WHITE))
    txt = ft.Colors.WHITE if active else _c_muted(page)
    border = BRAND_GREEN if active else _c_divider(page)

    return ft.Container(
        expand=True,
        padding=ft.Padding(12, 10, 12, 10),
        border_radius=14,
        bgcolor=bg,
        border=ft.Border.all(1, border),
        alignment=ft.Alignment(0, 0),
        on_click=on_click,
        content=ft.Text(label, size=12, weight=ft.FontWeight.W_800, color=txt),
    )


def _normalize_phone(v: str) -> str:
    return re.sub(r"\s+", "", (v or "").strip())


def _looks_valid(mode: str, v: str) -> bool:
    v = (v or "").strip()
    if mode == "email":
        return bool(EMAIL_RE.match(v))
    return bool(PHONE_RE.match(v))


def _exists_in_db(db, mode: str, v: str) -> bool:
    """
    Requiere users.email y users.phone (mismo sqlite).
    """
    if db is None:
        return True  # fallback de desarrollo

    if mode == "email":
        row = db.fetchone("SELECT 1 FROM users WHERE email = ? LIMIT 1", (v.strip(),))
        return row is not None

    phone = _normalize_phone(v)
    row = db.fetchone("SELECT 1 FROM users WHERE phone = ? LIMIT 1", (phone,))
    return row is not None


# ==========================================================
# 1) RECOVER ACCOUNT VIEW  (/help)
# ==========================================================
def create_recover_account_view(page: ft.Page) -> ft.View:
    db = page.data.get("db")
    _ = get_state(page)  # por si luego lo i18n-izas

    if db is not None:
        saved = load_theme(db)
        page.theme_mode = ft.ThemeMode.DARK if saved == "dark" else ft.ThemeMode.LIGHT

    def back(_=None):
        _nav(page, "/login")

    mode = {"value": "email"}  # "email" | "phone"

    title = ft.Text("Te ayudaremos a volver a ingresar", size=22, weight=ft.FontWeight.W_900, color=_c_text(page))
    subtitle = ft.Text("Selecciona un método para recibir tu código de seguridad.", size=12, color=_c_muted(page))
    label_upper = ft.Text("CONFIRMACIÓN DE IDENTIDAD", size=10, weight=ft.FontWeight.W_800, color=_c_muted(page))

    contact_tf = ft.TextField(
        hint_text="ejemplo@avoruna.com",
        border=ft.InputBorder.NONE,
        text_size=13,
        height=44,
        prefix_icon=ft.Icons.MAIL_OUTLINE,
        content_padding=ft.Padding(6, 10, 6, 10),
    )

    error_txt = ft.Text("", size=11, color=ft.Colors.RED_400, visible=False)

    send_btn = _primary_btn("ENVIAR CÓDIGO", lambda _: None, height=50)
    send_btn.expand = True
    send_btn.disabled = True

    def pick_email(_=None):
        mode["value"] = "email"
        contact_tf.value = ""
        error_txt.visible = False
        send_btn.disabled = True
        refresh_ui()

    def pick_phone(_=None):
        mode["value"] = "phone"
        contact_tf.value = ""
        error_txt.visible = False
        send_btn.disabled = True
        refresh_ui()

    segments = ft.Row(
        spacing=10,
        controls=[
            _pill_segment(page, "Correo electrónico", True, pick_email),
            _pill_segment(page, "Teléfono", False, pick_phone),
        ],
    )

    def refresh_ui():
        title.color = _c_text(page)
        subtitle.color = _c_muted(page)
        label_upper.color = _c_muted(page)

        if mode["value"] == "email":
            contact_tf.prefix_icon = ft.Icons.MAIL_OUTLINE
            contact_tf.hint_text = "ejemplo@avoruna.com"
        else:
            contact_tf.prefix_icon = ft.Icons.PHONE_ANDROID_OUTLINED
            contact_tf.hint_text = "+51 9xx xxx xxx"

        segments.controls = [
            _pill_segment(page, "Correo electrónico", mode["value"] == "email", pick_email),
            _pill_segment(page, "Teléfono", mode["value"] == "phone", pick_phone),
        ]
        page.update()

    def validate():
        v = (contact_tf.value or "").strip()

        # formato
        if not _looks_valid(mode["value"], v):
            send_btn.disabled = True
            error_txt.visible = False
            page.update()
            return

        # existe en DB
        if not _exists_in_db(db, mode["value"], v):
            send_btn.disabled = True
            error_txt.value = "Este correo o teléfono no se encuentra registrado."
            error_txt.visible = True
            page.update()
            return

        error_txt.visible = False
        send_btn.disabled = False
        page.update()

    def send_code(_=None):
        v = (contact_tf.value or "").strip()
        if not _looks_valid(mode["value"], v):
            return
        if not _exists_in_db(db, mode["value"], v):
            error_txt.value = "Este correo o teléfono no se encuentra registrado."
            error_txt.visible = True
            send_btn.disabled = True
            page.update()
            return

        page.data["recover_mode"] = mode["value"]
        page.data["recover_dest"] = v if mode["value"] == "email" else _normalize_phone(v)

        # (demo) guardar código fijo para validar en /verify
        page.data["recover_code"] = "420820"
        _nav(page, "/help/verify")

    send_btn.on_click = send_code
    contact_tf.on_change = lambda e: validate()

    bottom_link = ft.TextButton(
        content=ft.Text("¿No tienes acceso a este correo/teléfono? Ver opciones", size=11, color=BRAND_GREEN, weight=ft.FontWeight.W_800),
        on_click=lambda _: None,
        style=ft.ButtonStyle(padding=ft.Padding(0, 0, 0, 0)),
    )

    card = _card_shell(
        page,
        ft.Column(
            spacing=12,
            controls=[
                ft.Row(controls=[ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=back)]),
                title,
                subtitle,
                ft.Container(height=6),
                segments,
                ft.Container(height=6),
                label_upper,
                _input_capsule(page, contact_tf),
                error_txt,
                ft.Container(height=8),
                ft.Row(controls=[send_btn]),
            ],
        ),
        width=420,
    )

    scroll_col = ft.Column(
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Container(width=420, margin=ft.Margin(0, 0, 0, 18), content=card),
            bottom_link,
            ft.Container(height=10),
        ],
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
                    padding=ft.Padding(16, 18, 16, 24),
                    content=scroll_col,
                ),
            ],
        ),
    )

    refresh_ui()
    validate()
    return ft.View(route="/help", controls=[ft.SafeArea(expand=True, content=root)])


# ==========================================================
# 2) VERIFY CODE VIEW  (/help/verify)
# ==========================================================
def create_verify_code_view(page: ft.Page) -> ft.View:
    db = page.data.get("db")
    if db is not None:
        saved = load_theme(db)
        page.theme_mode = ft.ThemeMode.DARK if saved == "dark" else ft.ThemeMode.LIGHT

    def back(_=None):
        _nav(page, "/help")

    dest = page.data.get("recover_dest", "")
    title = ft.Text("Verifica tu identidad", size=22, weight=ft.FontWeight.W_900, color=_c_text(page), text_align=ft.TextAlign.CENTER)
    subtitle = ft.Text(f"Ingresa el código de 6 dígitos enviado a: {dest}", size=12, color=_c_muted(page), text_align=ft.TextAlign.CENTER)

    boxes: list[ft.TextField] = []
    box_containers: list[ft.Container] = []

    status_txt = ft.Text("", size=11, color=ft.Colors.RED_400, text_align=ft.TextAlign.CENTER)

    def build_box(i: int):
        tf = ft.TextField(
            value="",
            max_length=1,
            keyboard_type=ft.KeyboardType.NUMBER,
            border=ft.InputBorder.NONE,
            text_size=16,
            text_align=ft.TextAlign.CENTER,
            content_padding=ft.Padding(0, 12, 0, 12),
            width=44,
        )
        c = ft.Container(
            width=44,
            border_radius=12,
            border=ft.Border.all(2, _c_border(page)),
            bgcolor=_c_card(page),
            alignment=ft.Alignment(0, 0),
            content=tf,
        )

        def on_change(e):
            v = (tf.value or "").strip()
            if len(v) > 1:
                tf.value = v[-1]
            if tf.value and i < 5:
                try:
                    boxes[i + 1].focus()
                except Exception:
                    pass
            validate_silent()

        tf.on_change = on_change
        boxes.append(tf)
        box_containers.append(c)

    for i in range(6):
        build_box(i)

    code_row = ft.Row(alignment=ft.MainAxisAlignment.CENTER, spacing=10, controls=box_containers)

    def get_code() -> str:
        return "".join([(b.value or "") for b in boxes])

    def validate_silent():
        for idx, c in enumerate(box_containers):
            has = bool((boxes[idx].value or "").strip())
            c.border = ft.Border.all(2, BRAND_GREEN if has else _c_border(page))
        status_txt.value = ""
        page.update()

    def show_invalid(msg="Código inválido"):
        for c in box_containers:
            c.border = ft.Border.all(2, ft.Colors.RED_400)
        status_txt.value = msg
        page.update()

    # Timer minimal
    timer_txt = ft.Text("", size=11, color=_c_muted(page), text_align=ft.TextAlign.CENTER)
    countdown = {"sec": 45}
    stop_timer = {"stop": False}

    async def run_timer():
        stop_timer["stop"] = False
        countdown["sec"] = 45
        while countdown["sec"] >= 0 and not stop_timer["stop"]:
            timer_txt.value = f"Reenviar en 00:{countdown['sec']:02d}"
            page.update()
            await asyncio.sleep(1)
            countdown["sec"] -= 1
        if not stop_timer["stop"]:
            timer_txt.value = "Puedes reenviar el código"
            page.update()

    def resend(_=None):
        asyncio.create_task(run_timer())

    resend_btn = ft.TextButton(
        content=ft.Text("Reenviar código", size=11, color=BRAND_GREEN, weight=ft.FontWeight.W_800),
        on_click=lambda _: resend(),
        style=ft.ButtonStyle(padding=ft.Padding(0, 0, 0, 0)),
    )

    def verify(_=None):
        code = get_code()
        if len(code) != 6:
            show_invalid("Completa los 6 dígitos")
            return

        expected = page.data.get("recover_code", "420820")
        if code != expected:
            show_invalid("Código inválido")
            return

        stop_timer["stop"] = True
        _nav(page, "/help/new-password")

    verify_btn = _primary_btn("VERIFICAR", verify, height=50)
    verify_btn.expand = True

    icon = ft.Container(
        width=44,
        height=44,
        border_radius=14,
        bgcolor=ft.Colors.with_opacity(0.16, ft.Colors.GREEN_400) if _is_dark(page) else ft.Colors.with_opacity(0.22, ft.Colors.GREEN_400),
        alignment=ft.Alignment(0, 0),
        content=ft.Icon(ft.Icons.SHIELD_OUTLINED, color=BRAND_GREEN, size=22),
    )

    card = _card_shell(
        page,
        ft.Column(
            spacing=12,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Row(controls=[ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=back)]),
                ft.Container(height=2),
                icon,
                title,
                subtitle,
                ft.Container(height=6),
                code_row,
                status_txt,
                ft.Container(height=2),
                timer_txt,
                resend_btn,
                ft.Container(height=24),
                ft.Row(controls=[verify_btn]),
            ],
        ),
        width=420,
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
                    padding=ft.Padding(16, 18, 16, 24),
                    content=ft.Column(
                        expand=True,
                        scroll=ft.ScrollMode.AUTO,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[ft.Container(width=420, content=card)],
                    ),
                ),
            ],
        ),
    )

    validate_silent()
    asyncio.create_task(run_timer())
    return ft.View(route="/help/verify", controls=[ft.SafeArea(expand=True, content=root)])


# ==========================================================
# 3) NEW PASSWORD VIEW  (/help/new-password)
# ==========================================================
def create_new_password_view(page: ft.Page) -> ft.View:
    db = page.data.get("db")
    if db is not None:
        saved = load_theme(db)
        page.theme_mode = ft.ThemeMode.DARK if saved == "dark" else ft.ThemeMode.LIGHT

    # Seguridad UX: NO permitir "volver" (flujo sensible)
    def go_login(_=None):
        _nav(page, "/login")

    title = ft.Text("Nueva contraseña", size=22, weight=ft.FontWeight.W_900, color=_c_text(page))
    subtitle = ft.Text("Elige una contraseña segura para tu cuenta de Avoruna.", size=12, color=_c_muted(page))

    new_pwd = ft.TextField(
        hint_text="••••••••",
        border=ft.InputBorder.NONE,
        text_size=13,
        height=44,
        password=True,
        can_reveal_password=False,
        prefix_icon=ft.Icons.LOCK_OUTLINE,
        content_padding=ft.Padding(6, 10, 6, 10),
    )
    eye1 = ft.IconButton(icon=ft.Icons.VISIBILITY_OFF, icon_size=18, tooltip="Mostrar/Ocultar")
    new_pwd.suffix = eye1

    confirm_pwd = ft.TextField(
        hint_text="••••••••",
        border=ft.InputBorder.NONE,
        text_size=13,
        height=44,
        password=True,
        can_reveal_password=False,
        prefix_icon=ft.Icons.LOCK_OUTLINE,
        content_padding=ft.Padding(6, 10, 6, 10),
    )
    eye2 = ft.IconButton(icon=ft.Icons.VISIBILITY_OFF, icon_size=18, tooltip="Mostrar/Ocultar")
    confirm_pwd.suffix = eye2

    def toggle(tf: ft.TextField, btn: ft.IconButton):
        tf.password = not tf.password
        btn.icon = ft.Icons.VISIBILITY_OFF if tf.password else ft.Icons.VISIBILITY
        page.update()

    eye1.on_click = lambda e: toggle(new_pwd, eye1)
    eye2.on_click = lambda e: toggle(confirm_pwd, eye2)

    # ---------------- Strength + requisitos (UI como mock) ----------------
    weak_txt = ft.Text("", size=11, color=ft.Colors.AMBER_600)  # “⚠ Contraseña débil”
    strength_pct_txt = ft.Text("0%", size=11, color=_c_muted(page), weight=ft.FontWeight.W_700)

    # barra (fondo gris + relleno verde)
    strength_fill = ft.Container(height=6, width=0, border_radius=6, bgcolor=BRAND_GREEN)
    strength_bar = ft.Container(
        height=6,
        border_radius=6,
        bgcolor=ft.Colors.with_opacity(0.25, ft.Colors.GREY_400) if not _is_dark(page) else ft.Colors.with_opacity(0.25, ft.Colors.WHITE),
        content=strength_fill,
    )

    req_title = ft.Text("REQUISITOS", size=10, weight=ft.FontWeight.W_800, color=_c_muted(page))

    def req_row(label: str):
        dot = ft.Icon(ft.Icons.CIRCLE, size=10, color=_c_muted(page))
        txt = ft.Text(label, size=11, color=_c_muted(page))
        return ft.Row(spacing=8, controls=[dot, txt])

    req_min8 = req_row("Mínimo 8 caracteres")
    req_upper = req_row("Una letra mayúscula")
    req_num = req_row("Al menos un número")
    req_spec = req_row("Un carácter especial (!@#)")

    # tarjeta gris/verde suave del bloque requisitos (como imagen)
    req_card = ft.Container(
        padding=ft.Padding(14, 12, 14, 12),
        border_radius=16,
        bgcolor=ft.Colors.with_opacity(0.10, ft.Colors.GREEN_400) if not _is_dark(page) else ft.Colors.with_opacity(0.10, ft.Colors.WHITE),
        border=ft.Border.all(1, ft.Colors.with_opacity(0.18, ft.Colors.GREY_400) if not _is_dark(page) else ft.Colors.with_opacity(0.14, ft.Colors.WHITE)),
        content=ft.Column(spacing=8, controls=[req_title, req_min8, req_upper, req_num, req_spec]),
    )

    def mark_req(row: ft.Row, ok: bool):
        icon: ft.Icon = row.controls[0]
        txt: ft.Text = row.controls[1]
        if ok:
            icon.name = ft.Icons.CHECK_CIRCLE
            icon.color = BRAND_GREEN
            txt.color = BRAND_GREEN
        else:
            icon.name = ft.Icons.CIRCLE
            icon.color = _c_muted(page)
            txt.color = _c_muted(page)

    def update_strength_and_requirements():
        p = (new_pwd.value or "")

        ok_min8 = len(p) >= 8
        ok_upper = any(ch.isupper() for ch in p)
        ok_num = any(ch.isdigit() for ch in p)
        ok_spec = any(ch in "!@#$%&*()_-+=[]{}:;,.?/" for ch in p)

        mark_req(req_min8, ok_min8)
        mark_req(req_upper, ok_upper)
        mark_req(req_num, ok_num)
        mark_req(req_spec, ok_spec)

        score = sum([ok_min8, ok_upper, ok_num, ok_spec])
        pct = int((score / 4) * 100)

        strength_pct_txt.value = f"{pct}%"
        weak_txt.value = "⚠ Contraseña débil" if pct < 50 else ""

        # ancho relleno según % (barra 240 aprox)
        max_w = 240
        strength_fill.width = int((pct / 100) * max_w)

        page.update()

    new_pwd.on_change = lambda e: update_strength_and_requirements()

    error_txt = ft.Text("", size=11, color=ft.Colors.RED_400)

    def save_pwd(_=None):
        p1 = (new_pwd.value or "")
        p2 = (confirm_pwd.value or "")
        if p1 != p2 or len(p1) == 0:
            error_txt.value = "Las contraseñas no coinciden."
            page.update()
            return
        if len(p1) < 8:
            error_txt.value = "La contraseña debe tener al menos 8 caracteres."
            page.update()
            return

        error_txt.value = ""
        _nav(page, "/help/success")

    save_btn = _primary_btn("GUARDAR Y ENTRAR", save_pwd, height=50)
    save_btn.expand = True

    # ---------------- Layout ----------------
    card = _card_shell(
        page,
        ft.Column(
            spacing=12,
            controls=[
                # Sin back para no volver al código
                ft.Row(controls=[ft.Text("Recuperación", size=12, color=_c_muted(page), weight=ft.FontWeight.W_800)]),
                title,
                subtitle,

                ft.Container(height=4),
                ft.Text("Nueva contraseña", size=11, color=_c_text(page), weight=ft.FontWeight.W_800),
                _input_capsule(page, new_pwd),

                # warning + barra + porcentaje (como el mock)
                weak_txt,
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Container(expand=True, content=strength_bar),
                        ft.Container(width=10),
                        strength_pct_txt,
                    ],
                ),
                ft.Text(
                    "Usa una mezcla de letras, números y símbolos\npara mayor seguridad.",
                    size=11,
                    color=_c_muted(page),
                ),

                ft.Container(height=4),
                ft.Text("Confirmar contraseña", size=11, color=_c_text(page), weight=ft.FontWeight.W_800),
                _input_capsule(page, confirm_pwd),

                error_txt,

                # requisitos visual (tarjeta)
                req_card,

                ft.Container(height=8),
                ft.Row(controls=[save_btn]),

                ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=6,
                    wrap=True,
                    controls=[
                        ft.Text("¿Necesitas ayuda?", size=11, color=_c_muted(page)),
                        ft.TextButton(
                            content=ft.Text("Contacta soporte", size=11, color=BRAND_GREEN, weight=ft.FontWeight.W_800),
                            on_click=lambda _: None,
                            style=ft.ButtonStyle(padding=ft.Padding(0, 0, 0, 0)),
                        ),
                    ],
                ),

                ft.TextButton(
                    content=ft.Text("Volver al inicio de sesión", size=11, color=BRAND_GREEN, weight=ft.FontWeight.W_800),
                    on_click=go_login,
                    style=ft.ButtonStyle(padding=ft.Padding(0, 0, 0, 0)),
                ),
            ],
        ),
        width=420,
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
                    padding=ft.Padding(16, 18, 16, 24),
                    content=ft.Column(
                        expand=True,
                        scroll=ft.ScrollMode.AUTO,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[ft.Container(width=420, content=card)],
                    ),
                ),
            ],
        ),
    )

    update_strength_and_requirements()
    return ft.View(route="/help/new-password", controls=[ft.SafeArea(expand=True, content=root)])

# ==========================================================
# 4) SUCCESS VIEW  (/help/success)
# ==========================================================
def create_recover_success_view(page: ft.Page) -> ft.View:
    db = page.data.get("db")
    if db is not None:
        saved = load_theme(db)
        page.theme_mode = ft.ThemeMode.DARK if saved == "dark" else ft.ThemeMode.LIGHT

    def go_home(_=None):
        _nav(page, "/login")

    title = ft.Text("¡Contraseña actualizada!", size=22, weight=ft.FontWeight.W_900, color=_c_text(page), text_align=ft.TextAlign.CENTER)
    subtitle = ft.Text("Tu cuenta está segura ahora. Ya puedes volver a ingresar.", size=12, color=_c_muted(page), text_align=ft.TextAlign.CENTER)

    big_circle = ft.Container(
        width=140,
        height=140,
        border_radius=70,
        bgcolor=ft.Colors.with_opacity(0.10, ft.Colors.GREEN_400) if _is_dark(page) else ft.Colors.with_opacity(0.18, ft.Colors.GREEN_400),
        alignment=ft.Alignment(0, 0),
        content=ft.Container(
            width=70,
            height=70,
            border_radius=35,
            bgcolor=BRAND_GREEN,
            alignment=ft.Alignment(0, 0),
            content=ft.Icon(ft.Icons.CHECK, size=34, color=ft.Colors.WHITE),
        ),
    )

    btn = _primary_btn("IR AL INICIO", go_home, height=50)
    btn.expand = True

    card = _card_shell(
        page,
        ft.Column(
            spacing=12,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Row(controls=[ft.Text("Recuperación", size=12, color=_c_muted(page), weight=ft.FontWeight.W_800)]),
                ft.Container(height=10),
                big_circle,
                title,
                subtitle,
                ft.Container(height=24),
                ft.Row(controls=[btn]),
            ],
        ),
        width=420,
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
                    padding=ft.Padding(16, 18, 16, 24),
                    content=ft.Column(
                        expand=True,
                        scroll=ft.ScrollMode.AUTO,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[ft.Container(width=420, content=card)],
                    ),
                ),
            ],
        ),
    )

    return ft.View(route="/help/success", controls=[ft.SafeArea(expand=True, content=root)])
