# src/ui/views/support_view.py
import asyncio
import flet as ft

from ui.components.app_shell import build_app_shell, BRAND_GREEN


def _nav(page: ft.Page, route: str):
    asyncio.create_task(page.push_route(route))


def create_support_view(page: ft.Page) -> ft.View:
    is_dark = page.theme_mode == ft.ThemeMode.DARK

    def c_surface():
        return "#141922" if is_dark else "#FFFFFF"

    def c_bg():
        return "#0F1115" if is_dark else "#F7FBF5"

    def c_text():
        return "#F3F4F6" if is_dark else "#111111"

    def c_muted():
        return "#A7B0C0" if is_dark else "#6B7280"

    def c_border():
        return "#2A3142" if is_dark else ft.Colors.GREY_200

    def c_soft():
        return ft.Colors.with_opacity(0.10, ft.Colors.GREEN_400)

    shadow = ft.BoxShadow(
        blur_radius=12,
        spread_radius=1,
        color=ft.Colors.with_opacity(0.12 if is_dark else 0.07, ft.Colors.BLACK),
        offset=ft.Offset(0, 5),
    )

    faqs = {
        "scan_error": {
            "title": "Error en el escaneo de fruta",
            "icon": ft.Icons.ERROR_OUTLINE,
            "icon_bg": "#FDECEC" if not is_dark else "#3A1F24",
            "icon_color": "#EF4444",
            "answer": (
                "Revisa que la palta esté completamente visible, sin sombras fuertes ni reflejos. "
                "Limpia el lente, mantén una distancia estable y evita mover el dispositivo durante la captura. "
                "Si el problema continúa, cierra y vuelve a abrir la cámara o reinicia el módulo de escaneo."
            ),
        },
        "sync": {
            "title": "Problemas de sincronización",
            "icon": ft.Icons.SYNC_PROBLEM_OUTLINED,
            "icon_bg": "#EEF4FF" if not is_dark else "#1F2A3D",
            "icon_color": "#3B82F6",
            "answer": (
                "Verifica tu conexión a internet y confirma que la app tenga permisos de red. "
                "Si trabajas en modo offline, los registros pueden quedar pendientes hasta recuperar señal. "
                "Luego entra nuevamente al módulo o actualiza la vista para forzar la sincronización."
            ),
        },
        "ios_camera": {
            "title": "Calibración de cámara iOS",
            "icon": ft.Icons.PHOTO_CAMERA_OUTLINED,
            "icon_bg": "#ECFDF3" if not is_dark else "#1B3225",
            "icon_color": BRAND_GREEN,
            "answer": (
                "En iPhone o iPad, usa buena iluminación natural o luz blanca uniforme. "
                "Evita zoom digital, mantén la fruta centrada y el equipo estable. "
                "Si notas cambios de exposición, repite la captura con fondo limpio."
            ),
        },
    }

    faq_answer_refs = {}
    faq_icon_refs = {}

    def bubble(text: str, is_user: bool) -> ft.Control:
        bubble_width = 300 if (page.width or 1200) > 900 else 220
        return ft.Row(
            alignment=ft.MainAxisAlignment.END if is_user else ft.MainAxisAlignment.START,
            controls=[
                ft.Container(
                    width=bubble_width,
                    padding=ft.Padding(10, 8, 10, 8),
                    border_radius=14,
                    bgcolor=BRAND_GREEN if is_user else ft.Colors.with_opacity(
                        0.07, ft.Colors.BLACK if not is_dark else ft.Colors.WHITE
                    ),
                    content=ft.Text(
                        text,
                        size=11,
                        color=ft.Colors.WHITE if is_user else c_text(),
                    ),
                )
            ],
        )

    def ai_response(user_text: str) -> str:
        t = (user_text or "").strip().lower()

        if any(x in t for x in ["hola", "buenas", "hello", "hi"]):
            return (
                "Hola. Soy el asistente de soporte de Avoruna. "
                "Puedo ayudarte con escaneo, sincronización, cámara, resultados y uso del sistema."
            )

        if any(x in t for x in ["escaneo", "scan", "camara", "cámara", "foto", "captura"]):
            return (
                "Para problemas de escaneo, revisa 4 puntos: lente limpio, buena iluminación, "
                "fruta centrada y dispositivo estable. También puedes abrir el Centro de Aprendizaje "
                "para ver la guía paso a paso."
            )

        if any(x in t for x in ["sincron", "nube", "historial", "subir", "guardar"]):
            return (
                "Si el historial no sincroniza, verifica conexión a internet, permisos de red "
                "y que tu sesión esté activa. Si trabajaste offline, los datos pueden quedar pendientes "
                "hasta recuperar señal."
            )

        if any(x in t for x in ["resultado", "madurez", "porcentaje", "interpretacion", "interpretación"]):
            return (
                "El porcentaje representa la cercanía al punto de consumo. "
                "No conviene evaluar solo el número; también debes considerar la recomendación operativa."
            )

        if any(x in t for x in ["ios", "iphone", "ipad"]):
            return (
                "En iOS, usa iluminación uniforme, evita reflejos sobre la cáscara "
                "y no uses zoom digital. Mantén la palta centrada y el equipo estable."
            )

        if any(x in t for x in ["aprender", "tutorial", "guia", "guía", "manual"]):
            return (
                "Puedes entrar al Centro de Aprendizaje desde esta misma pantalla. "
                "Ahí tienes tutoriales de escaneo, calibración de luz, interpretación de resultados y mantenimiento."
            )

        if any(x in t for x in ["soporte", "whatsapp", "correo", "contacto"]):
            return (
                "Tienes tres canales disponibles: chat interno, WhatsApp al 922196988 "
                "y correo a support@avoruna.com."
            )

        return (
            "Entendido. Puedo orientarte en escaneo, sincronización, cámara, resultados o uso general de Avoruna. "
            "Escríbeme el problema con más detalle."
        )

    chat_messages = ft.ListView(
        expand=True,
        spacing=8,
        auto_scroll=True,
    )

    def add_chat_message(text: str, is_user: bool):
        chat_messages.controls.append(bubble(text, is_user))

    chat_input = ft.TextField(
        hint_text="Escribe tu consulta...",
        expand=True,
        text_size=11,
        border_color=c_border(),
        focused_border_color=BRAND_GREEN,
        content_padding=10,
        on_submit=lambda e: send_message(),
    )

    def send_message():
        value = (chat_input.value or "").strip()
        if not value:
            return

        add_chat_message(value, True)
        chat_input.value = ""
        add_chat_message(ai_response(value), False)
        page.update()

    def close_chat(e=None):
        page.pop_dialog()
        page.update()

    chat_dialog = ft.AlertDialog(
        modal=True,
        bgcolor=c_surface(),
        title=ft.Row(
            spacing=8,
            controls=[
                ft.Container(
                    width=30,
                    height=30,
                    border_radius=15,
                    bgcolor=c_soft(),
                    alignment=ft.Alignment(0, 0),
                    content=ft.Icon(ft.Icons.SMART_TOY_OUTLINED, color=BRAND_GREEN, size=16),
                ),
                ft.Column(
                    spacing=0,
                    controls=[
                        ft.Text("Asistente IA Avoruna", size=14, weight=ft.FontWeight.W_800, color=c_text()),
                        ft.Text("Soporte conversacional", size=10, color=c_muted()),
                    ],
                ),
            ],
        ),
        content=ft.Container(
            width=500,
            height=380,
            content=ft.Column(
                spacing=10,
                controls=[
                    ft.Container(
                        expand=True,
                        border_radius=12,
                        bgcolor=ft.Colors.with_opacity(
                            0.03, ft.Colors.BLACK if not is_dark else ft.Colors.WHITE
                        ),
                        padding=10,
                        content=chat_messages,
                    ),
                    ft.Row(
                        spacing=8,
                        controls=[
                            chat_input,
                            ft.Button(
                                content=ft.Text("Enviar", size=11, weight=ft.FontWeight.W_700),
                                bgcolor=BRAND_GREEN,
                                color=ft.Colors.WHITE,
                                on_click=lambda e: send_message(),
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(radius=10),
                                    padding=ft.Padding(14, 12, 14, 12),
                                ),
                            ),
                        ],
                    ),
                ],
            ),
        ),
        actions=[
            ft.TextButton(
                content=ft.Text("Cerrar", size=11, color=c_muted()),
                on_click=close_chat,
            )
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    def open_chat(e=None):
        chat_messages.controls.clear()
        add_chat_message(
            "Hola. Soy el asistente de soporte de Avoruna. Cuéntame tu problema y te responderé con pasos concretos.",
            False,
        )
        chat_input.value = ""
        page.show_dialog(chat_dialog)
        page.update()

    def toggle_faq(key: str):
        answer = faq_answer_refs[key]
        icon = faq_icon_refs[key]
        answer.visible = not answer.visible
        icon.name = ft.Icons.KEYBOARD_ARROW_UP if answer.visible else ft.Icons.KEYBOARD_ARROW_DOWN
        page.update()

    def faq_item(key: str) -> ft.Control:
        data = faqs[key]

        answer = ft.Container(
            visible=False,
            padding=ft.Padding(40, 0, 6, 2),
            content=ft.Text(
                data["answer"],
                size=11,
                color=c_muted(),
            ),
        )
        faq_answer_refs[key] = answer

        arrow_icon = ft.Icon(ft.Icons.KEYBOARD_ARROW_DOWN, size=18, color=c_muted())
        faq_icon_refs[key] = arrow_icon

        return ft.Container(
            border_radius=14,
            bgcolor=c_surface(),
            border=ft.Border.all(1, c_border()),
            padding=ft.Padding(12, 10, 12, 10),
            ink=True,
            on_click=lambda e: toggle_faq(key),
            content=ft.Column(
                spacing=6,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Row(
                                spacing=10,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                controls=[
                                    ft.Container(
                                        width=24,
                                        height=24,
                                        border_radius=7,
                                        bgcolor=data["icon_bg"],
                                        alignment=ft.Alignment(0, 0),
                                        content=ft.Icon(data["icon"], size=14, color=data["icon_color"]),
                                    ),
                                    ft.Text(
                                        data["title"],
                                        size=12,
                                        weight=ft.FontWeight.W_700,
                                        color=c_text(),
                                    ),
                                ],
                            ),
                            arrow_icon,
                        ],
                    ),
                    answer,
                ],
            ),
        )

    def contact_card(
        title: str,
        subtitle: str,
        note: str,
        icon,
        icon_color: str,
        body: ft.Control,
    ) -> ft.Control:
        return ft.Container(
            col={"xs": 12, "sm": 6, "md": 4},
            border_radius=16,
            bgcolor=c_surface(),
            border=ft.Border.all(1, c_border()),
            shadow=shadow,
            padding=14,
            content=ft.Column(
                spacing=10,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Column(
                                spacing=2,
                                controls=[
                                    ft.Text(title, size=14, weight=ft.FontWeight.W_800, color=c_text()),
                                    ft.Text(subtitle, size=10, color=c_muted()),
                                ],
                            ),
                            ft.Icon(icon, size=17, color=icon_color),
                        ],
                    ),
                    ft.Text(note, size=10, color=c_muted()),
                    body,
                ],
            ),
        )

    chat_card = contact_card(
        "Chat en Vivo",
        "Respuesta en menos de 5 min",
        "Asistencia rápida para incidencias funcionales y operativas.",
        ft.Icons.CHAT_OUTLINED,
        BRAND_GREEN,
        ft.Button(
            content=ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=6,
                controls=[
                    ft.Icon(ft.Icons.PLAY_ARROW, size=15, color=ft.Colors.WHITE),
                    ft.Text("Iniciar Chat Ahora", size=11, weight=ft.FontWeight.W_800, color=ft.Colors.WHITE),
                ],
            ),
            bgcolor=BRAND_GREEN,
            color=ft.Colors.WHITE,
            on_click=open_chat,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10),
                padding=ft.Padding(12, 12, 12, 12),
            ),
        ),
    )

    whatsapp_url = "https://wa.me/51922196988"
    gmail_compose_url = "https://mail.google.com/mail/?view=cm&fs=1&to=support@avoruna.com&su=Soporte%20Avoruna"

    phone_card = contact_card(
        "Llamar a Soporte",
        "Lunes a Viernes, 8am - 6pm",
        "Al pulsar se abrirá tu WhatsApp con el canal de soporte.",
        ft.Icons.PHONE_OUTLINED,
        BRAND_GREEN,
        ft.OutlinedButton(
            content=ft.Column(
                spacing=2,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Text("+51 922 196 988", size=12, weight=ft.FontWeight.W_800),
                    ft.Text("Abrir WhatsApp", size=10),
                ],
            ),
            url=whatsapp_url,
            style=ft.ButtonStyle(
                side=ft.BorderSide(1, BRAND_GREEN),
                color=BRAND_GREEN,
                shape=ft.RoundedRectangleBorder(radius=10),
                padding=ft.Padding(14, 10, 14, 10),
            ),
        ),
    )

    email_card = contact_card(
        "Enviar Correo",
        "Soporte técnico especializado",
        "Se abrirá Gmail para redactar el mensaje.",
        ft.Icons.MAIL_OUTLINE,
        BRAND_GREEN,
        ft.Column(
            spacing=8,
            controls=[
                ft.Container(
                    padding=ft.Padding(9, 7, 9, 7),
                    border_radius=9,
                    bgcolor=ft.Colors.with_opacity(
                        0.06, ft.Colors.BLACK if not is_dark else ft.Colors.WHITE
                    ),
                    content=ft.Row(
                        spacing=8,
                        controls=[
                            ft.Icon(ft.Icons.OUTGOING_MAIL, size=13, color=c_muted()),
                            ft.Text("support@avoruna.com", size=11, weight=ft.FontWeight.W_700, color=c_text()),
                        ],
                    ),
                ),
                ft.Button(
                    content=ft.Text("Abrir en Gmail", size=11, weight=ft.FontWeight.W_700),
                    url=gmail_compose_url,
                    bgcolor=BRAND_GREEN,
                    color=ft.Colors.WHITE,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=10),
                        padding=ft.Padding(12, 11, 12, 11),
                    ),
                ),
            ],
        ),
    )

    learning_card = ft.Container(
        border_radius=16,
        bgcolor=ft.Colors.with_opacity(0.10, ft.Colors.GREEN_400),
        border=ft.Border.all(1, ft.Colors.with_opacity(0.20, ft.Colors.GREEN_500)),
        padding=14,
        ink=True,
        on_click=lambda e: _nav(page, "/learn"),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Row(
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Container(
                            width=40,
                            height=40,
                            border_radius=11,
                            bgcolor=BRAND_GREEN,
                            alignment=ft.Alignment(0, 0),
                            content=ft.Icon(ft.Icons.MENU_BOOK_OUTLINED, size=20, color=ft.Colors.WHITE),
                        ),
                        ft.Column(
                            spacing=2,
                            controls=[
                                ft.Text("Centro de Aprendizaje", size=14, weight=ft.FontWeight.W_800, color=c_text()),
                                ft.Text(
                                    "Explora tutoriales y manuales de uso detallados.",
                                    size=11,
                                    color=c_muted(),
                                ),
                            ],
                        ),
                    ],
                ),
                ft.Icon(ft.Icons.OPEN_IN_NEW, size=20, color=BRAND_GREEN),
            ],
        ),
    )

    main_column = ft.Column(
        spacing=12,
        scroll=ft.ScrollMode.AUTO,
        controls=[
            ft.Container(
                alignment=ft.Alignment(0, 0),
                content=ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=5,
                    controls=[
                        ft.Container(
                            width=48,
                            height=48,
                            border_radius=24,
                            bgcolor=c_soft(),
                            alignment=ft.Alignment(0, 0),
                            content=ft.Icon(ft.Icons.HELP_OUTLINE, size=24, color=BRAND_GREEN),
                        ),
                        ft.Text(
                            "¿En qué podemos ayudarte?",
                            size=20,
                            weight=ft.FontWeight.W_900,
                            color=c_text(),
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Text(
                            "Estamos aquí para optimizar tu cosecha. Selecciona una opción de contacto.",
                            size=11,
                            color=c_muted(),
                            text_align=ft.TextAlign.CENTER,
                        ),
                    ],
                ),
            ),
            ft.ResponsiveRow(
                run_spacing=10,
                spacing=10,
                controls=[chat_card, phone_card, email_card],
            ),
            ft.Column(
                spacing=8,
                controls=[
                    ft.Text("Preguntas Frecuentes", size=16, weight=ft.FontWeight.W_900, color=c_text()),
                    faq_item("scan_error"),
                    faq_item("sync"),
                    faq_item("ios_camera"),
                ],
            ),
            learning_card,
            ft.Container(height=4),
        ],
    )

    content = ft.Row(
        alignment=ft.MainAxisAlignment.CENTER,
        controls=[
            ft.Container(
                width=900,
                content=main_column,
            )
        ],
    )

    return ft.View(
        route="/support",
        bgcolor=c_bg(),
        padding=0,
        spacing=0,
        scroll=ft.ScrollMode.AUTO,
        controls=[
            build_app_shell(page, content),
        ],
    )
