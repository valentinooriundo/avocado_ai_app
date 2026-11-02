# src/ui/views/learning_view.py
import asyncio
import flet as ft
import flet_video as ftv

from ui.components.app_shell import build_app_shell, BRAND_GREEN


def create_learning_view(page: ft.Page) -> ft.View:
    is_dark = page.theme_mode == ft.ThemeMode.DARK

    def c_surface():
        return "#141922" if is_dark else "#FFFFFF"

    def c_text():
        return "#F3F4F6" if is_dark else "#111111"

    def c_muted():
        return "#A7B0C0" if is_dark else "#6B7280"

    def c_border():
        return "#2A3142" if is_dark else ft.Colors.GREY_200

    def soft_bg():
        return "#0F1115" if is_dark else "#F7FBF5"

    def green_soft():
        return ft.Colors.with_opacity(0.10, ft.Colors.GREEN_400)

    shadow = ft.BoxShadow(
        blur_radius=16,
        spread_radius=1,
        color=ft.Colors.with_opacity(0.14 if is_dark else 0.08, ft.Colors.BLACK),
        offset=ft.Offset(0, 6),
    )

    def make_vtt(lines):
        parts = ["WEBVTT", ""]
        for timerange, text in lines:
            parts.append(timerange)
            parts.append(text)
            parts.append("")
        return "\n".join(parts)

    tutorials = {
        "scan": {
            "title": "Guía rápida: domina el análisis",
            "category": "TUTORIAL DESTACADO",
            "duration": "2:23",
            "description": "Aprende el flujo correcto para capturar una imagen limpia y estable del fruto.",
            "video_url": "https://user-images.githubusercontent.com/28951144/229373720-14d69157-1a56-4a78-a2f4-d7a134d7c3e9.mp4",
            "external_url": "https://www.youtube.com/watch?v=aqz-KE-bpKQ",
            "tip": "Limpia el lente de la cámara antes de cada análisis para mejorar la precisión.",
            "card_title": "Cómo\nEscanear",
            "icon": ft.Icons.CAMERA_ALT_OUTLINED,
            "subtitles": {
                "es": make_vtt([
                    ("00:00.000 --> 00:03.000", "Bienvenido al tutorial de escaneo en Avoruna."),
                    ("00:03.100 --> 00:07.000", "Ubica la palta en una zona iluminada y estable."),
                    ("00:07.100 --> 00:11.000", "Evita sombras fuertes y mueve la cámara lentamente."),
                    ("00:11.100 --> 00:15.000", "Cuando el fruto esté centrado, inicia el análisis."),
                ]),
                "en": make_vtt([
                    ("00:00.000 --> 00:03.000", "Welcome to the scanning tutorial in Avoruna."),
                    ("00:03.100 --> 00:07.000", "Place the avocado in a stable and well-lit area."),
                    ("00:07.100 --> 00:11.000", "Avoid strong shadows and move the camera slowly."),
                    ("00:11.100 --> 00:15.000", "Once the fruit is centered, start the analysis."),
                ]),
                "qu": make_vtt([
                    ("00:00.000 --> 00:03.000", "Avorunapi escaneo yachachiyta qallarisun."),
                    ("00:03.100 --> 00:07.000", "Paltata allin k'anchaypi churay."),
                    ("00:07.100 --> 00:11.000", "Ancha llanthu ama kananchu, camaratapas allinta muyuchiy."),
                    ("00:11.100 --> 00:15.000", "Chawpipi kaptin análisis qallariy."),
                ]),
                "ay": make_vtt([
                    ("00:00.000 --> 00:03.000", "Akax Avorunan escaneo yatichäwiwa."),
                    ("00:03.100 --> 00:07.000", "Paltax suma qhanan chiqan uchaña."),
                    ("00:07.100 --> 00:11.000", "Janiw ch'amaka llanthux utjañapäkiti, camara k'achata muyuyam."),
                    ("00:11.100 --> 00:15.000", "Chikaru purini ukhaxa análisis qalltam."),
                ]),
            },
        },
        "light": {
            "title": "Calibración de luz para resultados consistentes",
            "category": "TUTORIAL TÉCNICO",
            "duration": "3:11",
            "description": "Configura la iluminación para reducir ruido visual y obtener lecturas más estables.",
            "video_url": "https://user-images.githubusercontent.com/28951144/229373718-86ce5e1d-d195-45d5-baa6-ef94041d0b90.mp4",
            "external_url": "https://www.youtube.com/watch?v=aqz-KE-bpKQ",
            "tip": "Prefiere luz natural difusa o una fuente LED blanca uniforme.",
            "card_title": "Calibración de\nLuz",
            "icon": ft.Icons.WB_SUNNY_OUTLINED,
            "subtitles": {
                "es": make_vtt([
                    ("00:00.000 --> 00:03.000", "Este tutorial explica cómo calibrar la luz."),
                    ("00:03.100 --> 00:07.000", "Evita reflejos directos sobre la cáscara."),
                    ("00:07.100 --> 00:11.000", "Usa una iluminación uniforme en todo el encuadre."),
                    ("00:11.100 --> 00:15.000", "Eso mejora la precisión del análisis."),
                ]),
                "en": make_vtt([
                    ("00:00.000 --> 00:03.000", "This tutorial explains how to calibrate light."),
                    ("00:03.100 --> 00:07.000", "Avoid direct reflections on the peel."),
                    ("00:07.100 --> 00:11.000", "Use uniform lighting across the frame."),
                    ("00:11.100 --> 00:15.000", "This improves analysis accuracy."),
                ]),
                "qu": make_vtt([
                    ("00:00.000 --> 00:03.000", "Kay yachachiyqa k'anchay ajustemanta willan."),
                    ("00:03.100 --> 00:07.000", "Karapi q'illaykunata ama saqeychu."),
                    ("00:07.100 --> 00:11.000", "Tukuy encuadrepi kikillan k'anchayta churay."),
                    ("00:11.100 --> 00:15.000", "Chaymi precisiónta allinyachin."),
                ]),
                "ay": make_vtt([
                    ("00:00.000 --> 00:03.000", "Aka yatichäwix qhana askichañatakiwa."),
                    ("00:03.100 --> 00:07.000", "Janiw qhantati uñnaqanakax cáscara patxaru puriñapäkiti."),
                    ("00:07.100 --> 00:11.000", "Pachpa qhanawa taqpach encuadren utjañapa."),
                    ("00:11.100 --> 00:15.000", "Ukax precisión juk'amp sumaptayi."),
                ]),
            },
        },
        "results": {
            "title": "Interpretación de resultados y madurez",
            "category": "LECTURA DE RESULTADOS",
            "duration": "4:05",
            "description": "Comprende cómo leer porcentajes, estados y recomendaciones del sistema.",
            "video_url": "https://user-images.githubusercontent.com/28951144/229373716-76da0a4e-225a-44e4-9ee7-3e9006dbc3e3.mp4",
            "external_url": "https://www.youtube.com/watch?v=aqz-KE-bpKQ",
            "tip": "No evalúes solo el porcentaje; revisa también la recomendación operativa.",
            "card_title": "Interpretación\nde Resultados",
            "icon": ft.Icons.INSIGHTS_OUTLINED,
            "subtitles": {
                "es": make_vtt([
                    ("00:00.000 --> 00:03.000", "Aquí aprenderás a interpretar el resultado."),
                    ("00:03.100 --> 00:07.000", "El porcentaje refleja la cercanía al punto de consumo."),
                    ("00:07.100 --> 00:11.000", "La recomendación final te guía en la decisión."),
                    ("00:11.100 --> 00:15.000", "Usa ambos datos en conjunto."),
                ]),
                "en": make_vtt([
                    ("00:00.000 --> 00:03.000", "Here you will learn how to interpret the result."),
                    ("00:03.100 --> 00:07.000", "The percentage reflects closeness to ripeness."),
                    ("00:07.100 --> 00:11.000", "The final recommendation guides your decision."),
                    ("00:11.100 --> 00:15.000", "Use both values together."),
                ]),
                "qu": make_vtt([
                    ("00:00.000 --> 00:03.000", "Kaypi resultadota imaynata hamut'anapaq yachanki."),
                    ("00:03.100 --> 00:07.000", "Porcentajeqa mayqin grado madurezman qayllayta rikuchin."),
                    ("00:07.100 --> 00:11.000", "Recomendaciónqa allin akllayta yanapan."),
                    ("00:11.100 --> 00:15.000", "Iskayninta kuska qhawariy."),
                ]),
                "ay": make_vtt([
                    ("00:00.000 --> 00:03.000", "Akanxa resultado amuyañ yatiqäta."),
                    ("00:03.100 --> 00:07.000", "Porcentaje ukax madurez ukar jak'achasiñ uñacht'ayi."),
                    ("00:07.100 --> 00:11.000", "Qhipa amuyt'awix amtäwimaruw irpxaruwayi."),
                    ("00:11.100 --> 00:15.000", "Pä yatiyawinak mayacht'asis uñtam."),
                ]),
            },
        },
        "maintenance": {
            "title": "Mantenimiento preventivo del módulo",
            "category": "MANTENIMIENTO",
            "duration": "2:48",
            "description": "Conserva la cámara y el flujo de análisis en condiciones óptimas.",
            "video_url": "https://user-images.githubusercontent.com/28951144/229373695-22f88f13-d18f-4288-9bf1-c3e078d83722.mp4",
            "external_url": "https://www.youtube.com/watch?v=aqz-KE-bpKQ",
            "tip": "Revisa enfoque, batería y conectividad antes de iniciar una jornada larga.",
            "card_title": "Mantenimiento",
            "icon": ft.Icons.BUILD_OUTLINED,
            "subtitles": {
                "es": make_vtt([
                    ("00:00.000 --> 00:03.000", "Este tutorial cubre el mantenimiento preventivo."),
                    ("00:03.100 --> 00:07.000", "Limpia el lente antes de cada jornada."),
                    ("00:07.100 --> 00:11.000", "Revisa estabilidad, batería y conectividad."),
                    ("00:11.100 --> 00:15.000", "Eso reduce fallos durante el análisis."),
                ]),
                "en": make_vtt([
                    ("00:00.000 --> 00:03.000", "This tutorial covers preventive maintenance."),
                    ("00:03.100 --> 00:07.000", "Clean the lens before each session."),
                    ("00:07.100 --> 00:11.000", "Check stability, battery, and connectivity."),
                    ("00:11.100 --> 00:15.000", "This reduces failures during analysis."),
                ]),
                "qu": make_vtt([
                    ("00:00.000 --> 00:03.000", "Kay yachachiyqa mantenimiento preventivomanta."),
                    ("00:03.100 --> 00:07.000", "Sapa jornadaman lente limpiay."),
                    ("00:07.100 --> 00:11.000", "Estabilidad, batería, conectividad qhaway."),
                    ("00:11.100 --> 00:15.000", "Chayqa análisispi pantaykunata pisiyachin."),
                ]),
                "ay": make_vtt([
                    ("00:00.000 --> 00:03.000", "Aka yatichäwix mantenimiento preventivot uñacht'ayi."),
                    ("00:03.100 --> 00:07.000", "Sapa irnaqäw nayraqat lente q'umacham."),
                    ("00:07.100 --> 00:11.000", "Estabilidad, batería ukat conectividad uñakipt'am."),
                    ("00:11.100 --> 00:15.000", "Ukax análisisan pantjasiwinak jisk'achayi."),
                ]),
            },
        },
    }

    current_key = "scan"
    cards_map = {}

    def subtitle_track_for(tutorial_key: str, lang: str):
        if lang == "none":
            return ftv.VideoSubtitleTrack.none()

        tutorial = tutorials[tutorial_key]
        raw_subtitle = tutorial["subtitles"].get(lang, tutorial["subtitles"]["es"])

        lang_titles = {
            "es": "Español",
            "en": "English",
            "qu": "Quechua",
            "ay": "Aymara",
        }

        return ftv.VideoSubtitleTrack(
            src=raw_subtitle,
            title=lang_titles.get(lang, "Español"),
            language=lang,
        )

    tutorial_title = ft.Text(
        tutorials[current_key]["title"],
        size=22,
        weight=ft.FontWeight.W_900,
        color=c_text(),
    )

    tutorial_desc = ft.Text(
        tutorials[current_key]["description"],
        size=12,
        color=c_muted(),
    )

    tutorial_category = ft.Text(
        tutorials[current_key]["category"],
        size=10,
        color=BRAND_GREEN,
        weight=ft.FontWeight.W_900,
    )

    tutorial_duration = ft.Text(
        f"Duración: {tutorials[current_key]['duration']}",
        size=10,
        color=c_muted(),
        weight=ft.FontWeight.W_700,
    )

    tip_title = ft.Text(
        "CONSEJO DEL DÍA",
        size=10,
        weight=ft.FontWeight.W_900,
        color=BRAND_GREEN,
    )

    tip_text = ft.Text(
        tutorials[current_key]["tip"],
        size=12,
        color=c_muted(),
    )

    language_dd = ft.Dropdown(
        width=170,
        height=40,
        dense=True,
        value="es",
        text_size=12,
        border_color=c_border(),
        focused_border_color=BRAND_GREEN,
        bgcolor=c_surface(),
        content_padding=10,
        options=[
            ft.dropdown.Option(key="es", text="Español"),
            ft.dropdown.Option(key="en", text="English"),
            ft.dropdown.Option(key="qu", text="Quechua"),
            ft.dropdown.Option(key="ay", text="Aymara"),
            ft.dropdown.Option(key="none", text="Sin subtítulos"),
        ],
    )

    status_text = ft.Text(
        "Selecciona un tutorial para cambiar el video principal y el idioma de subtítulos.",
        size=10,
        color=c_muted(),
    )

    video = ftv.Video(
        playlist=[
            ftv.VideoMedia(tutorials[current_key]["video_url"]),
        ],
        aspect_ratio=16 / 9,
        autoplay=False,
        show_controls=True,
        volume=100,
        fit=ft.BoxFit.COVER,
        fill_color=ft.Colors.BLACK,
        filter_quality=ft.FilterQuality.MEDIUM,
        subtitle_configuration=ftv.VideoSubtitleConfiguration(
            visible=True,
            text_scale_factor=0.72,
            text_align=ft.TextAlign.CENTER,
            text_style=ft.TextStyle(
                size=16,
                color=ft.Colors.WHITE,
                weight=ft.FontWeight.W_700,
                bgcolor=ft.Colors.with_opacity(0.65, ft.Colors.BLACK),
            ),
            padding=ft.Padding(left=12, top=0, right=12, bottom=12),
        ),
        subtitle_track=subtitle_track_for(current_key, "es"),
        on_error=lambda e: print("Video error:", e.data),
    )

    external_button = ft.OutlinedButton(
        content=ft.Text(
            "Abrir externo",
            size=11,
            weight=ft.FontWeight.W_700,
        ),
        icon=ft.Icons.OPEN_IN_NEW,
        url=tutorials[current_key]["external_url"],
        height=40,
        style=ft.ButtonStyle(
            side=ft.BorderSide(1, BRAND_GREEN),
            color=BRAND_GREEN,
            shape=ft.RoundedRectangleBorder(radius=12),
            padding=ft.Padding(12, 0, 12, 0),
        ),
    )

    def refresh_cards():
        for key, card in cards_map.items():
            active = key == current_key
            card.bgcolor = green_soft() if active else c_surface()
            card.border = ft.Border.all(1.2, BRAND_GREEN if active else c_border())
            card.shadow = shadow if active else None

    async def change_tutorial(key: str):
        nonlocal current_key
        current_key = key
        data = tutorials[key]

        tutorial_title.value = data["title"]
        tutorial_desc.value = data["description"]
        tutorial_category.value = data["category"]
        tutorial_duration.value = f"Duración: {data['duration']}"
        tip_text.value = data["tip"]
        external_button.url = data["external_url"]

        try:
            await video.stop()
        except Exception:
            pass

        video.playlist = [ftv.VideoMedia(data["video_url"])]
        video.subtitle_track = subtitle_track_for(key, language_dd.value or "es")

        refresh_cards()
        page.update()

        await asyncio.sleep(0.10)

        try:
            await video.play()
        except Exception as ex:
            print("No se pudo reproducir el video:", ex)

    def on_language_change(e: ft.ControlEvent):
        selected = e.control.value or "es"
        video.subtitle_track = subtitle_track_for(current_key, selected)
        page.update()

    language_dd.on_change = on_language_change

    def tutorial_card(key: str):
        data = tutorials[key]

        card = ft.Container(
            col={"xs": 12, "sm": 6, "md": 3},
            padding=12,
            border_radius=18,
            bgcolor=c_surface(),
            border=ft.Border.all(1, c_border()),
            ink=True,
            on_click=lambda _: asyncio.create_task(change_tutorial(key)),
            content=ft.Column(
                spacing=10,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Container(
                        width=42,
                        height=42,
                        border_radius=14,
                        bgcolor=ft.Colors.with_opacity(0.12, ft.Colors.GREEN_400),
                        alignment=ft.Alignment(0, 0),
                        content=ft.Icon(data["icon"], color=BRAND_GREEN, size=22),
                    ),
                    ft.Text(
                        data["card_title"],
                        text_align=ft.TextAlign.CENTER,
                        size=14,
                        weight=ft.FontWeight.W_800,
                        color=c_text(),
                    ),
                    ft.Text(
                        data["duration"],
                        size=10,
                        color=c_muted(),
                        weight=ft.FontWeight.W_700,
                    ),
                ],
            ),
        )

        cards_map[key] = card
        return card

    cards_row = ft.ResponsiveRow(
        run_spacing=10,
        spacing=10,
        controls=[
            tutorial_card("scan"),
            tutorial_card("light"),
            tutorial_card("results"),
            tutorial_card("maintenance"),
        ],
    )

    refresh_cards()

    actions_block = ft.ResponsiveRow(
        run_spacing=8,
        spacing=8,
        controls=[
            ft.Container(
                col={"xs": 12, "sm": 4, "md": 3},
                content=ft.Container(
                    height=40,
                    padding=ft.Padding(10, 0, 10, 0),
                    border_radius=999,
                    bgcolor=ft.Colors.with_opacity(0.10, ft.Colors.GREEN_400),
                    alignment=ft.Alignment(-1, 0),
                    content=tutorial_duration,
                ),
            ),
            ft.Container(
                col={"xs": 12, "sm": 4, "md": 4},
                content=language_dd,
            ),
            ft.Container(
                col={"xs": 12, "sm": 4, "md": 3},
                content=external_button,
            ),
        ],
    )

    content = ft.Column(
        expand=True,
        spacing=12,
        scroll=ft.ScrollMode.AUTO,
        controls=[
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Column(
                        spacing=2,
                        controls=[
                            ft.Text(
                                "Avoruna Learning Center",
                                size=24,
                                weight=ft.FontWeight.W_900,
                                color=c_text(),
                            ),
                            ft.Text(
                                "Centro de aprendizaje interactivo.",
                                size=12,
                                color=c_muted(),
                            ),
                        ],
                    ),
                    ft.Container(
                        width=42,
                        height=42,
                        border_radius=21,
                        bgcolor=ft.Colors.with_opacity(0.12, ft.Colors.AMBER_300),
                        alignment=ft.Alignment(0, 0),
                        content=ft.Icon(
                            ft.Icons.PLAY_CIRCLE_FILL,
                            color=BRAND_GREEN,
                            size=22,
                        ),
                    ),
                ],
            ),

            tutorial_category,

            ft.Container(
                border_radius=22,
                bgcolor=c_surface(),
                border=ft.Border.all(1, c_border()),
                shadow=shadow,
                clip_behavior=ft.ClipBehavior.HARD_EDGE,
                content=ft.Column(
                    spacing=0,
                    controls=[
                        ft.Container(
                            bgcolor=ft.Colors.BLACK,
                            content=video,
                        ),
                        ft.Container(
                            padding=14,
                            content=ft.Column(
                                spacing=8,
                                controls=[
                                    tutorial_title,
                                    tutorial_desc,
                                    actions_block,
                                    status_text,
                                ],
                            ),
                        ),
                    ],
                ),
            ),

            ft.Column(
                spacing=8,
                controls=[
                    ft.Text(
                        "Tutoriales y guías",
                        size=18,
                        weight=ft.FontWeight.W_900,
                        color=c_text(),
                    ),
                    cards_row,
                ],
            ),

            ft.Container(
                border_radius=18,
                padding=14,
                bgcolor=ft.Colors.with_opacity(0.10, ft.Colors.GREEN_400),
                border=ft.Border(
                    left=ft.BorderSide(4, BRAND_GREEN),
                    top=ft.BorderSide(1, ft.Colors.TRANSPARENT),
                    right=ft.BorderSide(1, ft.Colors.TRANSPARENT),
                    bottom=ft.BorderSide(1, ft.Colors.TRANSPARENT),
                ),
                content=ft.Row(
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                    controls=[
                        ft.Container(
                            width=36,
                            height=36,
                            border_radius=18,
                            bgcolor=BRAND_GREEN,
                            alignment=ft.Alignment(0, 0),
                            content=ft.Icon(
                                ft.Icons.LIGHTBULB,
                                color=ft.Colors.WHITE,
                                size=18,
                            ),
                        ),
                        ft.Column(
                            expand=True,
                            spacing=4,
                            controls=[
                                tip_title,
                                tip_text,
                            ],
                        ),
                    ],
                ),
            ),

            ft.Container(height=4),
        ],
    )

    return ft.View(
        route="/learn",
        bgcolor=soft_bg(),
        padding=0,
        spacing=0,
        scroll=ft.ScrollMode.AUTO,
        controls=[
            build_app_shell(page, content),
        ],
    )
