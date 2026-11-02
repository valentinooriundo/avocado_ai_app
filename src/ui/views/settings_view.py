# src/ui/views/settings_view.py
import asyncio
import flet as ft

from services.settings_service import load_theme, save_theme
from ui.components.app_shell import build_app_shell, BRAND_GREEN


def _nav(page: ft.Page, route: str):
    asyncio.create_task(page.push_route(route))


async def _cs_get(page: ft.Page, key: str, default):
    try:
        v = await page.client_storage.get_async(key)
        return default if v is None else v
    except Exception:
        return default


async def _cs_set(page: ft.Page, key: str, value):
    try:
        await page.client_storage.set_async(key, value)
    except Exception:
        pass


def create_settings_view(page: ft.Page) -> ft.View:
    db = page.data.get("db")

    # ===== Sync theme from DB =====
    if db is not None:
        saved = load_theme(db)
        page.theme_mode = ft.ThemeMode.DARK if saved == "dark" else ft.ThemeMode.LIGHT

    # ===== Helpers =====
    def _snack(msg: str):
        page.snack_bar = ft.SnackBar(ft.Text(msg))
        page.snack_bar.open = True
        page.update()

    def _is_dark() -> bool:
        return page.theme_mode == ft.ThemeMode.DARK

    def _c_surface():
        return "#141922" if _is_dark() else "#FFFFFF"

    def _c_text():
        return "#F3F4F6" if _is_dark() else "#111111"

    def _c_muted():
        return "#A7B0C0" if _is_dark() else "#6B7280"

    def _c_border():
        return "#2A3142" if _is_dark() else ft.Colors.GREY_200

    def _shadow():
        return ft.BoxShadow(
            blur_radius=24,
            spread_radius=2,
            color=ft.Colors.with_opacity(0.20 if _is_dark() else 0.10, ft.Colors.BLACK),
            offset=ft.Offset(0, 8),
        )

    def _card(content: ft.Control, padding=18):
        return ft.Container(
            padding=ft.Padding(padding, padding, padding, padding),
            border_radius=22,
            bgcolor=_c_surface(),
            border=ft.Border.all(1, _c_border()),
            shadow=_shadow(),
            content=content,
        )

    def section_title(text: str):
        return ft.Text(text, size=10, color=_c_muted(), weight=ft.FontWeight.W_900)

    # ===== STATE =====
    sync_switch = ft.Switch(value=False)
    flash_switch = ft.Switch(value=True)
    precise_switch = ft.Switch(value=False)
    share_anon_switch = ft.Switch(value=True)
    darkmode_switch = ft.Switch(value=_is_dark())

    text_slider = ft.Slider(min=12, max=18, value=14, divisions=6)
    quality_slider = ft.Slider(min=0, max=2, value=2, divisions=2)
    quality_text = ft.Text("Alta (HD)", size=10, color=BRAND_GREEN, weight=ft.FontWeight.W_900)

    # Fuente de imagen (puede seguir con Dropdown, no es tan feo como el de variedad)
    image_source_dd = ft.Dropdown(
        value="native",
        options=[
            ft.dropdown.Option("native", "Cámara nativa (Recomendado)"),
            ft.dropdown.Option("fletcam", "Flet Camera (Web)"),
            ft.dropdown.Option("upload", "Subir imagen (archivos)"),
            ft.dropdown.Option("url", "Pegar URL de imagen"),
        ],
        border_radius=14,
        bgcolor=ft.Colors.with_opacity(0.02, ft.Colors.BLACK if not _is_dark() else ft.Colors.WHITE),
    )

    # Idioma (lo dejamos Dropdown porque no te estaba molestando; si quieres lo paso también al selector custom)
    lang_dd = ft.Dropdown(
        value="es",
        options=[
            ft.dropdown.Option("es", "Español"),
            ft.dropdown.Option("qu", "Quechua"),
            ft.dropdown.Option("ay", "Aymara"),
            ft.dropdown.Option("en", "English"),
        ],
        border_radius=14,
        bgcolor=ft.Colors.with_opacity(0.02, ft.Colors.BLACK if not _is_dark() else ft.Colors.WHITE),
    )

    # Modelo IA (Dropdown OK)
    model_dd = ft.Dropdown(
        value="hass_v1",
        options=[
            ft.dropdown.Option("hass_v1", "Hass v1 (Optimizado offline)"),
            ft.dropdown.Option("hass_v2", "Hass v2 (Más preciso)"),
        ],
        border_radius=14,
        bgcolor=ft.Colors.with_opacity(0.02, ft.Colors.BLACK if not _is_dark() else ft.Colors.WHITE),
    )

    # ✅ Variedad: NO Dropdown (para evitar el menú plomo/feo)
    variety_value = {"key": "hass"}  # estado simple
    variety_labels = {
        "hass": "Hass (Exportación)",
        "fuerte": "Fuerte (Mercado local)",
    }

    variety_text = ft.Text(variety_labels[variety_value["key"]], size=12, color=_c_text(), weight=ft.FontWeight.W_800)

    variety_box = ft.Container(
        height=46,
        border_radius=14,
        border=ft.Border.all(1, _c_border()),
        bgcolor=_c_surface(),
        padding=ft.Padding(14, 0, 14, 0),
        alignment=ft.Alignment(-1, 0),
        ink=True,
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                variety_text,
                ft.Icon(ft.Icons.ARROW_DROP_DOWN, color=_c_muted()),
            ],
        ),
    )

    def open_variety_dialog(_=None):
        def pick(k: str):
            variety_value["key"] = k
            variety_text.value = variety_labels[k]
            asyncio.create_task(_cs_set(page, "settings.variety", k))
            page.dialog.open = False
            page.update()

        items = []
        for k, label in variety_labels.items():
            active = (k == variety_value["key"])
            items.append(
                ft.Container(
                    border_radius=14,
                    padding=ft.Padding(14, 10, 14, 10),
                    bgcolor=ft.Colors.with_opacity(0.10, ft.Colors.GREEN_400) if active else None,
                    ink=True,
                    on_click=lambda e, kk=k: pick(kk),
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text(label, size=12, weight=ft.FontWeight.W_900, color=_c_text()),
                            ft.Icon(ft.Icons.CHECK, color=BRAND_GREEN) if active else ft.Container(width=24, height=24),
                        ],
                    ),
                )
            )

        page.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Selecciona la variedad", weight=ft.FontWeight.W_900),
            content=ft.Container(
                width=420,
                content=ft.Column(spacing=10, tight=True, controls=items),
            ),
            actions=[
                ft.TextButton("Cerrar", on_click=lambda _: (setattr(page.dialog, "open", False), page.update())),
            ],
        )
        page.dialog.open = True
        page.update()

    variety_box.on_click = open_variety_dialog

    # ===== Helpers =====
    def _quality_label():
        v = int(quality_slider.value or 2)
        return {0: "Baja", 1: "Media", 2: "Alta (HD)"}.get(v, "Alta (HD)")

    def _quality_changed(_):
        quality_text.value = _quality_label()
        page.update()

    def _toggle_theme(_):
        page.theme_mode = ft.ThemeMode.DARK if darkmode_switch.value else ft.ThemeMode.LIGHT
        if db is not None:
            save_theme(db, "dark" if page.theme_mode == ft.ThemeMode.DARK else "light")

        # ✅ IMPORTANT: re-render completo para que fondo + app_shell + cards cambien
        page.go(page.route)

    darkmode_switch.on_change = _toggle_theme

    # ===== Persistence binding =====
    def bind_persistence():
        sync_switch.on_change = lambda e: asyncio.create_task(_cs_set(page, "settings.sync", bool(e.control.value)))
        flash_switch.on_change = lambda e: asyncio.create_task(_cs_set(page, "settings.flash", bool(e.control.value)))
        precise_switch.on_change = lambda e: asyncio.create_task(_cs_set(page, "settings.precise", bool(e.control.value)))
        share_anon_switch.on_change = lambda e: asyncio.create_task(_cs_set(page, "settings.share_anon", bool(e.control.value)))
        image_source_dd.on_change = lambda e: asyncio.create_task(_cs_set(page, "settings.image_source", e.control.value))

        quality_slider.on_change = lambda e: (
            asyncio.create_task(_cs_set(page, "settings.quality", int(e.control.value or 2))),
            _quality_changed(e),
        )

        text_slider.on_change = lambda e: asyncio.create_task(_cs_set(page, "settings.text_size", int(e.control.value or 14)))
        lang_dd.on_change = lambda e: asyncio.create_task(_cs_set(page, "settings.lang", e.control.value))
        model_dd.on_change = lambda e: asyncio.create_task(_cs_set(page, "settings.model", e.control.value))

    async def load_state():
        sync_switch.value = await _cs_get(page, "settings.sync", False)
        flash_switch.value = await _cs_get(page, "settings.flash", True)
        precise_switch.value = await _cs_get(page, "settings.precise", False)
        share_anon_switch.value = await _cs_get(page, "settings.share_anon", True)

        image_source_dd.value = await _cs_get(page, "settings.image_source", "native")
        quality_slider.value = await _cs_get(page, "settings.quality", 2)
        text_slider.value = await _cs_get(page, "settings.text_size", 14)

        lang_dd.value = await _cs_get(page, "settings.lang", "es")
        model_dd.value = await _cs_get(page, "settings.model", "hass_v1")

        v = await _cs_get(page, "settings.variety", "hass")
        if v not in variety_labels:
            v = "hass"
        variety_value["key"] = v
        variety_text.value = variety_labels[v]

        darkmode_switch.value = _is_dark()
        quality_text.value = _quality_label()
        page.update()

    # ===== CARDS =====
    def card_account():
        login_btn = ft.Button(
            "Iniciar sesión",
            on_click=lambda _: _nav(page, "/login"),
            style=ft.ButtonStyle(
                bgcolor={ft.ControlState.DEFAULT: BRAND_GREEN},
                color={ft.ControlState.DEFAULT: ft.Colors.WHITE},
                shape={ft.ControlState.DEFAULT: ft.RoundedRectangleBorder(radius=14)},
                padding={ft.ControlState.DEFAULT: ft.Padding(16, 10, 16, 10)},
            ),
        )
        return _card(
            ft.Column(
                spacing=14,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Column(
                                spacing=2,
                                controls=[
                                    ft.Text("Sin cuenta - modo local", size=12, weight=ft.FontWeight.W_900, color=_c_text()),
                                    ft.Text("Tus datos se guardan en el dispositivo", size=10, color=_c_muted(), weight=ft.FontWeight.W_700),
                                ],
                            ),
                            login_btn,
                        ],
                    ),
                    ft.Divider(height=1, color=_c_border()),
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Column(
                                spacing=2,
                                controls=[
                                    ft.Text("Sincronizar historial", size=11, weight=ft.FontWeight.W_900, color=_c_text()),
                                    ft.Text("Sube datos cuando detecte red WiFi en Ica", size=9, color=_c_muted(), weight=ft.FontWeight.W_700),
                                ],
                            ),
                            sync_switch,
                        ],
                    ),
                ],
            )
        )

    def card_camera():
        probe_btn = ft.OutlinedButton(
            "Probar cámara",
            icon=ft.Icons.PHOTO_CAMERA_OUTLINED,
            on_click=lambda _: _nav(page, "/camera"),
            style=ft.ButtonStyle(
                shape={ft.ControlState.DEFAULT: ft.RoundedRectangleBorder(radius=14)},
                side={ft.ControlState.DEFAULT: ft.BorderSide(1, BRAND_GREEN)},
                color={ft.ControlState.DEFAULT: BRAND_GREEN},
                padding={ft.ControlState.DEFAULT: ft.Padding(18, 12, 18, 12)},
            ),
        )
        return _card(
            ft.Column(
                spacing=14,
                controls=[
                    ft.ResponsiveRow(
                        spacing=14,
                        run_spacing=14,
                        controls=[
                            ft.Container(
                                col={"xs": 12, "lg": 7},
                                content=ft.Column(
                                    spacing=6,
                                    controls=[
                                        ft.Text("Origen de imagen", size=9, color=_c_muted(), weight=ft.FontWeight.W_900),
                                        image_source_dd,
                                    ],
                                ),
                            ),
                            ft.Container(
                                col={"xs": 12, "lg": 5},
                                content=ft.Row(
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                    controls=[
                                        ft.Column(
                                            spacing=2,
                                            controls=[
                                                ft.Text("Flash automático", size=11, weight=ft.FontWeight.W_900, color=_c_text()),
                                                ft.Text("Actívalo en ambientes oscuros", size=9, color=_c_muted(), weight=ft.FontWeight.W_700),
                                            ],
                                        ),
                                        flash_switch,
                                    ],
                                ),
                            ),
                        ],
                    ),
                    ft.Column(
                        spacing=6,
                        controls=[
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[ft.Text("Calidad de captura", size=11, weight=ft.FontWeight.W_900, color=_c_text()), quality_text],
                            ),
                            quality_slider,
                        ],
                    ),
                    probe_btn,
                ],
            )
        )

    def card_model():
        return _card(
            ft.Column(
                spacing=12,
                controls=[
                    ft.Text("Versión del modelo", size=9, color=_c_muted(), weight=ft.FontWeight.W_900),
                    model_dd,
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Column(
                                spacing=2,
                                controls=[
                                    ft.Text("Modo preciso", size=11, weight=ft.FontWeight.W_900, color=_c_text()),
                                    ft.Text("Más riguroso (mock)", size=9, color=_c_muted(), weight=ft.FontWeight.W_700),
                                ],
                            ),
                            precise_switch,
                        ],
                    ),
                ],
            )
        )

    def card_farm():
        manage_btn = ft.Button(
            "Gestionar parcelas",
            icon=ft.Icons.MAP_OUTLINED,
            on_click=lambda _: _snack("Gestión de parcelas: mock"),
            style=ft.ButtonStyle(
                bgcolor={ft.ControlState.DEFAULT: ft.Colors.with_opacity(0.14, ft.Colors.GREEN_400)},
                color={ft.ControlState.DEFAULT: BRAND_GREEN},
                shape={ft.ControlState.DEFAULT: ft.RoundedRectangleBorder(radius=14)},
                padding={ft.ControlState.DEFAULT: ft.Padding(16, 12, 16, 12)},
            ),
        )

        return _card(
            ft.Column(
                spacing=12,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Column(
                                spacing=0,
                                controls=[
                                    ft.Text("CHACRA ACTUAL", size=8, color=_c_muted(), weight=ft.FontWeight.W_900),
                                    ft.Text("San José de los Molinos", size=12, weight=ft.FontWeight.W_900, color=_c_text()),
                                ],
                            ),
                            ft.Icon(ft.Icons.SYNC_ALT, size=18, color=_c_muted()),
                        ],
                    ),
                    ft.Text("Variedad por defecto", size=9, color=_c_muted(), weight=ft.FontWeight.W_900),
                    variety_box,
                    ft.Container(height=2),
                    manage_btn,
                ],
            )
        )

    # ✅ Almacenamiento compacto (como tu imagen)
    def card_storage():
        used_text = ft.Text("256MB de 2GB utilizados", size=9, color=_c_muted(), weight=ft.FontWeight.W_700)
        free_text = ft.Text("1.74GB disponible", size=9, color=BRAND_GREEN, weight=ft.FontWeight.W_900)
        bar = ft.ProgressBar(value=0.13, height=8, border_radius=999)

        async def clear_history():
            if db is None:
                _snack("No hay DB activa (demo).")
                return
            try:
                with db._conn() as conn:
                    conn.execute("DELETE FROM scans")
                    conn.commit()
                _snack("Historial local borrado.")
            except Exception:
                _snack("No se pudo borrar (tabla scans no disponible).")

        delete_btn = ft.Button(
            "BORRAR HISTORIAL LOCAL",
            on_click=lambda _: asyncio.create_task(clear_history()),
            style=ft.ButtonStyle(
                bgcolor={ft.ControlState.DEFAULT: BRAND_GREEN},
                color={ft.ControlState.DEFAULT: ft.Colors.WHITE},
                shape={ft.ControlState.DEFAULT: ft.RoundedRectangleBorder(radius=14)},
                padding={ft.ControlState.DEFAULT: ft.Padding(18, 12, 18, 12)},
            ),
        )

        return _card(
            ft.Column(
                spacing=10,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text("ALMACENAMIENTO", size=10, weight=ft.FontWeight.W_900, color=_c_text()),
                            ft.Text("Gestión de datos locales", size=9, color=_c_muted(), weight=ft.FontWeight.W_700),
                        ],
                    ),
                    ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[used_text, free_text]),
                    bar,
                    delete_btn,
                    ft.Text(
                        "Esta acción no afectará los datos ya sincronizados con la nube.",
                        size=9,
                        color=_c_muted(),
                        weight=ft.FontWeight.W_700,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
            ),
            padding=18,
        )

    def card_ui():
        size_badge = ft.Container(
            padding=ft.Padding(10, 4, 10, 4),
            border_radius=999,
            border=ft.Border.all(1, _c_border()),
            bgcolor=_c_surface(),
            content=ft.Text("Mediano (14px)", size=10, color=_c_text(), weight=ft.FontWeight.W_900),
        )

        def on_text_size_change(_):
            v = int(text_slider.value or 14)
            size_badge.content.value = f"Mediano ({v}px)"
            page.update()

        text_slider.on_change = on_text_size_change

        return _card(
            ft.Column(
                spacing=14,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Column(
                                spacing=2,
                                controls=[
                                    ft.Text("Modo Oscuro", size=11, weight=ft.FontWeight.W_900, color=_c_text()),
                                    ft.Text("Cambiar tema visual", size=9, color=_c_muted(), weight=ft.FontWeight.W_700),
                                ],
                            ),
                            darkmode_switch,
                        ],
                    ),
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Column(
                                spacing=2,
                                controls=[
                                    ft.Text("Tamaño de texto", size=11, weight=ft.FontWeight.W_900, color=_c_text()),
                                    ft.Text("Ajusta lectura", size=9, color=_c_muted(), weight=ft.FontWeight.W_700),
                                ],
                            ),
                            size_badge,
                        ],
                    ),
                    text_slider,
                    ft.Text("Idioma y Localización", size=11, weight=ft.FontWeight.W_900, color=_c_text()),
                    lang_dd,
                ],
            )
        )

    # Privacidad y permisos (como la imagen de referencia)
    def card_privacy():
        def perm_chip(icon, label: str, ok=True):
            return ft.Container(
                col={"xs": 12, "sm": 4, "md": 4, "lg": 4},
                padding=ft.Padding(14, 12, 14, 12),
                border_radius=16,
                border=ft.Border.all(1, _c_border()),
                bgcolor=_c_surface(),
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Row(
                            spacing=10,
                            controls=[
                                ft.Icon(icon, size=18, color=_c_text()),
                                ft.Text(label, size=11, weight=ft.FontWeight.W_900, color=_c_text()),
                            ],
                        ),
                        ft.Container(
                            padding=ft.Padding(10, 4, 10, 4),
                            border_radius=999,
                            bgcolor=ft.Colors.with_opacity(0.14, ft.Colors.GREEN_400) if ok else ft.Colors.with_opacity(0.12, ft.Colors.AMBER_400),
                            content=ft.Text(
                                "OK" if ok else "OFF",
                                size=9,
                                weight=ft.FontWeight.W_900,
                                color=BRAND_GREEN if ok else ft.Colors.AMBER_700,
                            ),
                        ),
                    ],
                ),
            )

        quick_help = ft.Container(
            col={"xs": 12, "md": 6},
            padding=ft.Padding(14, 12, 14, 12),
            border_radius=16,
            border=ft.Border.all(1, _c_border()),
            bgcolor=_c_surface(),
            ink=True,
            on_click=lambda _: _snack("Guía rápida: mock"),
            content=ft.Row(
                spacing=10,
                controls=[
                    ft.Icon(ft.Icons.MENU_BOOK_OUTLINED, size=18, color=BRAND_GREEN),
                    ft.Column(
                        spacing=2,
                        controls=[
                            ft.Text("Guía rápida", size=11, weight=ft.FontWeight.W_900, color=_c_text()),
                            ft.Text("Aprende a usar Avoruna", size=9, color=_c_muted(), weight=ft.FontWeight.W_700),
                        ],
                    ),
                ],
            ),
        )

        report = ft.Container(
            col={"xs": 12, "md": 6},
            padding=ft.Padding(14, 12, 14, 12),
            border_radius=16,
            border=ft.Border.all(1, _c_border()),
            bgcolor=_c_surface(),
            ink=True,
            on_click=lambda _: _snack("Reportar problema: mock"),
            content=ft.Row(
                spacing=10,
                controls=[
                    ft.Icon(ft.Icons.REPORT_GMAILERRORRED_OUTLINED, size=18, color=ft.Colors.RED_400),
                    ft.Column(
                        spacing=2,
                        controls=[
                            ft.Text("Reportar problema", size=11, weight=ft.FontWeight.W_900, color=_c_text()),
                            ft.Text("Soporte técnico 24/7", size=9, color=_c_muted(), weight=ft.FontWeight.W_700),
                        ],
                    ),
                ],
            ),
        )

        footer = ft.Column(
            spacing=6,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Text("v1.4.2 · Avoruna · Chacra Piñeiros, Ica", size=9, color=_c_muted(), weight=ft.FontWeight.W_700),
                ft.Row(
                    spacing=16,
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=[
                        ft.TextButton(
                            content=ft.Text("TÉRMINOS", size=10, color=_c_muted(), weight=ft.FontWeight.W_800),
                            on_click=lambda _: _snack("Términos: mock"),
                            style=ft.ButtonStyle(padding=ft.Padding(0, 0, 0, 0)),
                        ),
                        ft.TextButton(
                            content=ft.Text("PRIVACIDAD", size=10, color=_c_muted(), weight=ft.FontWeight.W_800),
                            on_click=lambda _: _snack("Privacidad: mock"),
                            style=ft.ButtonStyle(padding=ft.Padding(0, 0, 0, 0)),
                        ),
                    ],
                ),
            ],
        )

        return _card(
            ft.Column(
                spacing=14,
                controls=[
                    ft.Row(
                        spacing=8,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Icon(ft.Icons.SHIELD_OUTLINED, size=18, color=BRAND_GREEN),
                            ft.Text("PRIVACIDAD Y PERMISOS", size=10, weight=ft.FontWeight.W_900, color=_c_text()),
                        ],
                    ),
                    ft.ResponsiveRow(
                        spacing=10,
                        run_spacing=10,
                        controls=[
                            perm_chip(ft.Icons.PHOTO_CAMERA_OUTLINED, "Cámara", True),
                            perm_chip(ft.Icons.FOLDER_OPEN_OUTLINED, "Archivos", True),
                            perm_chip(ft.Icons.PUBLIC_OUTLINED, "Internet", True),
                        ],
                    ),
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Column(
                                spacing=2,
                                controls=[
                                    ft.Text("Compartir datos anónimos", size=11, weight=ft.FontWeight.W_900, color=_c_text()),
                                    ft.Text("Ayúdanos a mejorar el rendimiento en campo", size=9, color=_c_muted(), weight=ft.FontWeight.W_700),
                                ],
                            ),
                            share_anon_switch,
                        ],
                    ),
                    ft.ResponsiveRow(spacing=10, run_spacing=10, controls=[quick_help, report]),
                    footer,
                ],
            ),
            padding=18,
        )

    # ===== CONTENT GRID =====
    content = ft.Column(
        spacing=14,
        controls=[
            ft.Text("Ajustes", size=22, weight=ft.FontWeight.W_900, color=_c_text()),
            ft.Text("Configura la aplicación para tu chacra", size=11, color=_c_muted(), weight=ft.FontWeight.W_700),
            ft.ResponsiveRow(
                spacing=14,
                run_spacing=14,
                controls=[
                    ft.Container(col={"xs": 12, "lg": 7}, content=ft.Column(spacing=10, controls=[section_title("CUENTA Y SINCRONIZACIÓN"), card_account()])),
                    ft.Container(col={"xs": 12, "lg": 5}, content=ft.Column(spacing=10, controls=[section_title("CHACRA / PARCELAS"), card_farm()])),
                    ft.Container(col={"xs": 12, "lg": 7}, content=ft.Column(spacing=10, controls=[section_title("CÁMARA Y CAPTURA"), card_camera()])),
                    ft.Container(col={"xs": 12, "lg": 5}, content=ft.Column(spacing=10, controls=[section_title("ALMACENAMIENTO"), card_storage()])),
                    ft.Container(col={"xs": 12, "lg": 7}, content=ft.Column(spacing=10, controls=[section_title("MODELO DE IA"), card_model()])),
                    ft.Container(col={"xs": 12, "lg": 5}, content=ft.Column(spacing=10, controls=[section_title("INTERFAZ Y REGIONAL"), card_ui()])),
                    ft.Container(col={"xs": 12}, content=ft.Column(spacing=10, controls=[section_title("PRIVACIDAD Y PERMISOS"), card_privacy()])),
                    ft.Container(col={"xs": 12}, content=ft.Container(height=80)),
                ],
            ),
        ],
    )

    # ===== shell =====
    root = build_app_shell(page, content)

    bind_persistence()
    asyncio.create_task(load_state())

    # ✅ View scroll para que el mouse wheel funcione en web/desktop
    return ft.View(route="/settings", scroll=ft.ScrollMode.ALWAYS, controls=[ft.SafeArea(expand=True, content=root)])
