import flet as ft
from services.settings_service import load_theme
from ui.components.app_shell import build_app_shell, BRAND_GREEN


ACCENT_BLUE = "#2E7CF6"


def _is_dark(page: ft.Page) -> bool:
    return page.theme_mode == ft.ThemeMode.DARK


def _screen_mode(page: ft.Page) -> str:
    w = page.width or 1200
    if w < 760:
        return "mobile"
    if w < 1080:
        return "tablet"
    return "desktop"


def create_team_view(page: ft.Page) -> ft.View:
    db = page.data.get("db")

    if db is not None:
        saved = load_theme(db)
        page.theme_mode = ft.ThemeMode.DARK if saved == "dark" else ft.ThemeMode.LIGHT

    def c_surface():
        return "#141922" if _is_dark(page) else "#FFFFFF"

    def c_soft():
        return "#18202B" if _is_dark(page) else "#EEF6E8"

    def c_banner():
        return "#172016" if _is_dark(page) else "#DDE8CE"

    def c_text():
        return "#F3F4F6" if _is_dark(page) else "#111111"

    def c_muted():
        return "#A7B0C0" if _is_dark(page) else "#5F6B60"

    def c_border():
        return "#2A3142" if _is_dark(page) else "#DCE7D2"

    def c_button_green():
        return "#198A00" if _is_dark(page) else "#178400"

    def c_button_green_2():
        return "#2DD40F" if _is_dark(page) else "#2FD40F"

    def shadow():
        return ft.BoxShadow(
            blur_radius=24,
            spread_radius=2,
            color=ft.Colors.with_opacity(0.20 if _is_dark(page) else 0.10, ft.Colors.BLACK),
            offset=ft.Offset(0, 8),
        )

    def card(content: ft.Control, padding=18, radius=22, bgcolor=None):
        return ft.Container(
            padding=ft.Padding(padding, padding, padding, padding),
            border_radius=radius,
            bgcolor=bgcolor or c_surface(),
            border=ft.Border.all(1, c_border()),
            shadow=shadow(),
            content=content,
        )

    def snack(msg: str):
        page.snack_bar = ft.SnackBar(ft.Text(msg))
        page.snack_bar.open = True
        page.update()

    def primary_cta(label: str, on_click=None):
        return ft.Container(
            height=44,
            border_radius=12,
            ink=True,
            on_click=on_click,
            content=ft.Stack(
                controls=[
                    ft.Container(
                        expand=True,
                        border_radius=12,
                        bgcolor=c_button_green(),
                    ),
                    ft.Container(
                        width=110,
                        right=0,
                        top=0,
                        bottom=0,
                        border_radius=12,
                        bgcolor=ft.Colors.with_opacity(0.14, c_button_green_2()),
                    ),
                    ft.Container(
                        expand=True,
                        alignment=ft.Alignment(0, 0),
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=8,
                            controls=[
                                ft.Text(
                                    label,
                                    size=11,
                                    color=ft.Colors.WHITE,
                                    weight=ft.FontWeight.W_900,
                                ),
                                ft.Icon(
                                    ft.Icons.ARROW_FORWARD,
                                    size=16,
                                    color=ft.Colors.WHITE,
                                ),
                            ],
                        ),
                    ),
                ],
            ),
        )

    def outline_cta(label: str, on_click=None):
        return ft.Container(
            height=44,
            border_radius=12,
            border=ft.Border.all(1, c_border()),
            bgcolor=ft.Colors.with_opacity(
                0.03,
                ft.Colors.BLACK if not _is_dark(page) else ft.Colors.WHITE,
            ),
            ink=True,
            on_click=on_click,
            alignment=ft.Alignment(0, 0),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=8,
                controls=[
                    ft.Text(
                        label,
                        size=11,
                        color=c_button_green(),
                        weight=ft.FontWeight.W_900,
                    ),
                    ft.Icon(
                        ft.Icons.LINK,
                        size=14,
                        color=c_button_green(),
                    ),
                ],
            ),
        )

    def section_icon(icon, bg_color=None, fg_color=None):
        return ft.Container(
            width=44,
            height=44,
            border_radius=12,
            bgcolor=bg_color or ft.Colors.with_opacity(0.14, ft.Colors.GREEN_400),
            alignment=ft.Alignment(0, 0),
            content=ft.Icon(
                icon,
                size=20,
                color=fg_color or BRAND_GREEN,
            ),
        )

    # ==========================================================
    # MODAL 1: CREAR EQUIPO
    # ==========================================================
    create_dialog = ft.AlertDialog(modal=True)

    name_tf = ft.TextField(
        label="Nombre del Equipo",
        hint_text="Ej. Cuadrilla de Cosecha Ica",
        border_radius=12,
        text_size=11,
    )

    location_dd = ft.Dropdown(
        label="Ubicación / Chacra",
        value=None,
        options=[
            ft.dropdown.Option("pineros", "Chacra Piñeiros"),
            ft.dropdown.Option("molinos", "San José de los Molinos"),
            ft.dropdown.Option("sunampe", "Sunampe"),
        ],
        border_radius=12,
        text_size=11,
    )

    variety_dd = ft.Dropdown(
        label="Variedad de Palta",
        value="hass",
        options=[
            ft.dropdown.Option("hass", "Hass (Exportación)"),
            ft.dropdown.Option("fuerte", "Fuerte (Mercado local)"),
        ],
        border_radius=12,
        text_size=11,
    )

    desc_tf = ft.TextField(
        label="Descripción del Grupo",
        hint_text="Añada notas sobre el equipo, objetivos o requisitos específicos.",
        multiline=True,
        min_lines=3,
        max_lines=5,
        border_radius=12,
        text_size=11,
    )

    offline_sw = ft.Switch(value=True)
    daily_sw = ft.Switch(value=False)

    def switch_tile(icon, title: str, subtitle: str, control: ft.Switch):
        return ft.Container(
            padding=ft.Padding(14, 12, 14, 12),
            border_radius=16,
            border=ft.Border.all(1, c_border()),
            bgcolor=ft.Colors.with_opacity(
                0.04,
                ft.Colors.BLACK if not _is_dark(page) else ft.Colors.WHITE,
            ),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Row(
                        spacing=10,
                        controls=[
                            ft.Container(
                                width=34,
                                height=34,
                                border_radius=12,
                                bgcolor=ft.Colors.with_opacity(0.12, ft.Colors.GREEN_400),
                                alignment=ft.Alignment(0, 0),
                                content=ft.Icon(icon, color=BRAND_GREEN, size=18),
                            ),
                            ft.Container(
                                expand=True,
                                content=ft.Column(
                                    spacing=2,
                                    controls=[
                                        ft.Text(
                                            title,
                                            size=11,
                                            weight=ft.FontWeight.W_900,
                                            color=c_text(),
                                        ),
                                        ft.Text(
                                            subtitle,
                                            size=9,
                                            weight=ft.FontWeight.W_700,
                                            color=c_muted(),
                                        ),
                                    ],
                                ),
                            ),
                        ],
                    ),
                    control,
                ],
            ),
        )

    def close_create_dialog(_=None):
        create_dialog.open = False
        page.update()

    def submit_create(_=None):
        if not (name_tf.value or "").strip():
            snack("Ingresa un nombre de equipo.")
            return
        if not location_dd.value:
            snack("Selecciona una ubicación.")
            return
        snack("Equipo creado (mock). Generando código…")
        close_create_dialog()

    create_list = ft.ListView(
        spacing=14,
        padding=ft.Padding(0, 0, 0, 0),
        controls=[
            name_tf,
            location_dd,
            variety_dd,
            desc_tf,
            ft.Divider(height=1, color=c_border()),
            ft.Text(
                "Configuración Inicial",
                size=12,
                weight=ft.FontWeight.W_900,
                color=c_text(),
            ),
            switch_tile(
                ft.Icons.NO_CELL_OUTLINED,
                "Permitir escaneo offline",
                "Sincroniza cuando haya conexión disponible.",
                offline_sw,
            ),
            switch_tile(
                ft.Icons.NOTIFICATIONS_ACTIVE_OUTLINED,
                "Notificar reportes diarios",
                "Envía resumen operativo al administrador.",
                daily_sw,
            ),
            primary_cta("CREAR EQUIPO Y GENERAR CÓDIGO", on_click=submit_create),
            ft.Text(
                "Se generará un código único para que los trabajadores se unan al equipo.",
                size=8,
                color=c_muted(),
                weight=ft.FontWeight.W_700,
                text_align=ft.TextAlign.CENTER,
            ),
            ft.Container(height=6),
        ],
    )

    create_dialog.bgcolor = c_surface()
    create_dialog.inset_padding = ft.Padding(18, 18, 18, 18)
    create_dialog.actions = []
    create_dialog.content = ft.Container(
        width=640,
        height=560,
        padding=ft.Padding(18, 18, 18, 18),
        content=ft.Column(
            spacing=12,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Column(
                            spacing=2,
                            controls=[
                                ft.Text(
                                    "Crear Nuevo Equipo",
                                    size=16,
                                    weight=ft.FontWeight.W_900,
                                    color=c_text(),
                                ),
                                ft.Text(
                                    "Configure los datos base de la nueva cuadrilla.",
                                    size=9,
                                    weight=ft.FontWeight.W_700,
                                    color=c_muted(),
                                ),
                            ],
                        ),
                        ft.IconButton(
                            icon=ft.Icons.CLOSE,
                            icon_color=c_muted(),
                            tooltip="Cerrar",
                            on_click=close_create_dialog,
                        ),
                    ],
                ),
                ft.Divider(height=1, color=c_border()),
                ft.Container(expand=True, content=create_list),
            ],
        ),
    )

    if create_dialog not in page.overlay:
        page.overlay.append(create_dialog)

    def open_create_team_modal(_=None):
        ww = page.width or 1200
        modal_w = 640 if ww >= 1100 else 560 if ww >= 900 else 460 if ww >= 700 else 360
        modal_h = 560 if ww >= 700 else 520
        create_dialog.content.width = modal_w
        create_dialog.content.height = modal_h
        create_dialog.open = True
        page.update()

    # ==========================================================
    # MODAL 2: UNIRSE A EQUIPO
    # ==========================================================
    join_dialog = ft.AlertDialog(modal=True)
    otp_boxes: list[ft.TextField] = []

    def close_join_dialog(_=None):
        join_dialog.open = False
        page.update()

    def otp_value() -> str:
        return "".join([(b.value or "") for b in otp_boxes]).strip().upper()

    def verify_code(_=None):
        code = otp_value()
        if len(code) != 6:
            snack("Ingresa los 6 caracteres del código.")
            return
        snack(f"Código verificado: {code} (mock)")
        close_join_dialog()

    def build_otp_box(i: int) -> ft.TextField:
        tf = ft.TextField(
            value="",
            width=44,
            height=48,
            text_size=14,
            text_align=ft.TextAlign.CENTER,
            border_radius=10,
            max_length=1,
            bgcolor=ft.Colors.with_opacity(
                0.02,
                ft.Colors.BLACK if not _is_dark(page) else ft.Colors.WHITE,
            ),
        )

        def on_change(e: ft.ControlEvent):
            v = (e.control.value or "").upper()
            if len(v) > 1:
                v = v[-1]
            e.control.value = v
            if v and i < len(otp_boxes) - 1:
                try:
                    otp_boxes[i + 1].focus()
                except Exception:
                    pass
            page.update()

        def on_submit(_):
            if len(otp_value()) == 6:
                verify_code()

        tf.on_change = on_change
        tf.on_submit = on_submit
        return tf

    otp_boxes = [build_otp_box(i) for i in range(6)]

    join_dialog.bgcolor = c_surface()
    join_dialog.inset_padding = ft.Padding(18, 18, 18, 18)
    join_dialog.actions = []
    join_dialog.content = ft.Container(
        width=420,
        padding=ft.Padding(18, 18, 18, 18),
        content=ft.Column(
            spacing=14,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.END,
                    controls=[
                        ft.IconButton(
                            icon=ft.Icons.CLOSE,
                            icon_color=c_muted(),
                            tooltip="Cerrar",
                            on_click=close_join_dialog,
                        )
                    ],
                ),
                section_icon(ft.Icons.GROUP_ADD_OUTLINED),
                ft.Text(
                    "Unirse a un Equipo",
                    size=18,
                    weight=ft.FontWeight.W_900,
                    color=c_text(),
                ),
                ft.Text(
                    "Ingresa el código de 6 caracteres proporcionado por tu supervisor para comenzar.",
                    size=10,
                    weight=ft.FontWeight.W_700,
                    color=c_muted(),
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Row(
                    spacing=10,
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=otp_boxes,
                ),
                primary_cta("VERIFICAR CÓDIGO", on_click=verify_code),
                ft.Divider(height=1, color=c_border()),
                ft.Column(
                    spacing=10,
                    controls=[
                        ft.Text(
                            "¿QUÉ OBTENDRÁS AL UNIRTE?",
                            size=9,
                            weight=ft.FontWeight.W_900,
                            color=c_muted(),
                        ),
                        ft.Row(
                            spacing=10,
                            controls=[
                                ft.Icon(ft.Icons.QR_CODE_2, size=18, color=BRAND_GREEN),
                                ft.Container(
                                    expand=True,
                                    content=ft.Text(
                                        "Acceso a escaneos compartidos y base de datos agrícola.",
                                        size=10,
                                        color=c_text(),
                                        weight=ft.FontWeight.W_700,
                                    ),
                                ),
                            ],
                        ),
                        ft.Row(
                            spacing=10,
                            controls=[
                                ft.Icon(ft.Icons.INSERT_CHART_OUTLINED, size=18, color=BRAND_GREEN),
                                ft.Container(
                                    expand=True,
                                    content=ft.Text(
                                        "Reportes en tiempo real sobre productividad de campo.",
                                        size=10,
                                        color=c_text(),
                                        weight=ft.FontWeight.W_700,
                                    ),
                                ),
                            ],
                        ),
                        ft.Row(
                            spacing=10,
                            controls=[
                                ft.Icon(ft.Icons.FORUM_OUTLINED, size=18, color=BRAND_GREEN),
                                ft.Container(
                                    expand=True,
                                    content=ft.Text(
                                        "Comunicación directa con los miembros de tu equipo.",
                                        size=10,
                                        color=c_text(),
                                        weight=ft.FontWeight.W_700,
                                    ),
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        ),
    )

    if join_dialog not in page.overlay:
        page.overlay.append(join_dialog)

    def open_join_team_modal(_=None):
        for b in otp_boxes:
            b.value = ""
        ww = page.width or 1200
        join_dialog.content.width = 460 if ww >= 900 else 420 if ww >= 600 else 340
        join_dialog.open = True
        page.update()
        try:
            otp_boxes[0].focus()
        except Exception:
            pass

    # ==========================================================
    # HERO
    # ==========================================================
    def hero_banner():
        mode = _screen_mode(page)
        is_mobile = mode == "mobile"
        banner_h = 250 if not is_mobile else 270

        title = ft.Column(
            spacing=10,
            controls=[
                ft.Container(
                    padding=ft.Padding(10, 4, 10, 4),
                    border_radius=999,
                    bgcolor=ft.Colors.with_opacity(0.18, BRAND_GREEN),
                    content=ft.Text(
                        "ICA, PERÚ",
                        size=8,
                        color="#0D4D00",
                        weight=ft.FontWeight.W_900,
                    ),
                ),
                ft.Text(
                    "Optimiza tu cosecha\nen equipo.",
                    size=30 if not is_mobile else 24,
                    color=c_text(),
                    weight=ft.FontWeight.W_900,
                ),
                ft.Container(
                    width=420 if not is_mobile else None,
                    content=ft.Text(
                        "Gestiona colaboradores, monitorea la madurez de los frutos y coordina la logística de transporte desde una sola plataforma científica.",
                        size=12,
                        color=c_text() if _is_dark(page) else "#2D382B",
                        weight=ft.FontWeight.W_500,
                    ),
                ),
            ],
        )

        avocado_cluster = ft.Stack(
            controls=[
                ft.Container(
                    width=76,
                    height=112,
                    border_radius=999,
                    bgcolor="#789B47",
                    right=16,
                    top=8,
                ),
                ft.Container(
                    width=64,
                    height=98,
                    border_radius=999,
                    bgcolor="#6B8F3B",
                    right=88,
                    top=20,
                ),
                ft.Container(
                    width=60,
                    height=92,
                    border_radius=999,
                    bgcolor="#7DA44F",
                    right=144,
                    top=0,
                ),
                ft.Container(
                    width=56,
                    height=86,
                    border_radius=999,
                    bgcolor="#5D7F33",
                    right=36,
                    top=94,
                ),
                ft.Container(
                    width=64,
                    height=98,
                    border_radius=999,
                    bgcolor="#89AF5C",
                    right=118,
                    top=88,
                ),
            ]
        )

        bg_layer = ft.Stack(
            controls=[
                ft.Container(
                    expand=True,
                    border_radius=24,
                    bgcolor=c_banner(),
                ),
                ft.Container(
                    expand=True,
                    border_radius=24,
                    bgcolor=ft.Colors.with_opacity(0.18, ft.Colors.WHITE),
                ),
                ft.Container(
                    width=420,
                    height=banner_h,
                    left=-40,
                    top=0,
                    bgcolor=ft.Colors.with_opacity(0.08, ft.Colors.WHITE),
                    border_radius=120,
                ),
                ft.Container(
                    width=360,
                    height=180,
                    left=160,
                    top=44,
                    bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.BLACK),
                    border_radius=100,
                ),
                ft.Container(
                    width=280,
                    height=160,
                    right=0,
                    top=10,
                    content=avocado_cluster,
                ),
            ]
        )

        if mode == "desktop":
            content = ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Container(expand=3, content=title),
                    ft.Container(expand=2),
                ],
            )
        else:
            content = ft.Column(
                spacing=14,
                controls=[
                    title,
                ],
            )

        return ft.Container(
            height=banner_h,
            border_radius=24,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            content=ft.Stack(
                controls=[
                    bg_layer,
                    ft.Container(
                        expand=True,
                        padding=ft.Padding(20, 20, 20, 20),
                        content=content,
                    ),
                ],
            ),
        )

    # ==========================================================
    # ACTION CARDS
    # ==========================================================
    def action_card(
        title: str,
        desc: str,
        cta_label: str,
        icon,
        top_label: str,
        accent_bg,
        accent_fg,
        on_click,
        outlined=False,
    ):
        watermark = ft.Container(
            right=6,
            bottom=-8,
            content=ft.Icon(
                ft.Icons.GROUPS_2_OUTLINED if hasattr(ft.Icons, "GROUPS_2_OUTLINED") else ft.Icons.GROUP_OUTLINED,
                size=72,
                color=ft.Colors.with_opacity(0.05, ft.Colors.BLACK if not _is_dark(page) else ft.Colors.WHITE),
            ),
        )

        cta = outline_cta(cta_label, on_click=on_click) if outlined else primary_cta(cta_label, on_click=on_click)

        return card(
            ft.Stack(
                controls=[
                    watermark,
                    ft.Column(
                        spacing=16,
                        controls=[
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                controls=[
                                    section_icon(icon, bg_color=accent_bg, fg_color=accent_fg),
                                    ft.Text(
                                        top_label,
                                        size=10,
                                        color=c_muted(),
                                        weight=ft.FontWeight.W_700,
                                    ),
                                ],
                            ),
                            ft.Text(
                                title,
                                size=16,
                                weight=ft.FontWeight.W_900,
                                color=c_text(),
                            ),
                            ft.Text(
                                desc,
                                size=11,
                                color=c_muted(),
                                weight=ft.FontWeight.W_600,
                            ),
                            ft.Container(height=4),
                            cta,
                        ],
                    ),
                ],
            ),
            padding=20,
            radius=22,
            bgcolor=c_surface() if not outlined else c_soft(),
        )

    def build_content():
        mode = _screen_mode(page)
        is_mobile = mode == "mobile"

        create_team = action_card(
            title="Crear un equipo",
            desc="Inicia una nueva red de trabajo para tu parcela. Podrás asignar roles, gestionar turnos y recibir reportes en tiempo real de tus técnicos.",
            cta_label="Comenzar ahora",
            icon=ft.Icons.PERSON_ADD_ALT_1_OUTLINED,
            top_label="Liderazgo",
            accent_bg=ft.Colors.with_opacity(0.14, ft.Colors.GREEN_400),
            accent_fg=BRAND_GREEN,
            on_click=open_create_team_modal,
            outlined=False,
        )

        join_team = action_card(
            title="Unirme a un equipo",
            desc="Ingresa el código de invitación proporcionado por tu supervisor para comenzar a reportar datos de campo y ver tus tareas asignadas.",
            cta_label="Ingresar código",
            icon=ft.Icons.GROUP_ADD_OUTLINED,
            top_label="Colaboración",
            accent_bg=ft.Colors.with_opacity(0.14, ft.Colors.GREEN_400),
            accent_fg=BRAND_GREEN,
            on_click=open_join_team_modal,
            outlined=True,
        )

        if mode == "desktop":
            actions = ft.Row(
                spacing=16,
                controls=[
                    ft.Container(expand=True, content=create_team),
                    ft.Container(expand=True, content=join_team),
                ],
            )
        else:
            actions = ft.Column(
                spacing=14,
                controls=[create_team, join_team],
            )

        return ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=18,
            controls=[
                hero_banner(),
                actions,
                ft.Container(height=24 if is_mobile else 36),
            ],
        )

    content_host = ft.Container(expand=True)

    def rebuild(*_):
        content_host.content = build_content()
        page.update()

    page.on_resized = rebuild
    rebuild()

    root = build_app_shell(page, content_host)

    return ft.View(
        route="/team",
        controls=[ft.SafeArea(expand=True, content=root)],
    )
