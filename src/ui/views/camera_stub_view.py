# src/ui/views/camera_stub_view.py
import asyncio
import os
import time
import random
import base64
import io
from typing import Optional
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from ui.theme_tokens import BRAND_PRIMARY, BRAND_SOFT, text_color, muted_color, border_color, surface_color

import flet as ft
import flet_camera as fc
import flet_permission_handler as fph

from PIL import Image, ImageStat
import numpy as np

# Theme persistence (no revienta si no existe save_theme)
try:
    from services.settings_service import load_theme, save_theme  # type: ignore
except Exception:
    from services.settings_service import load_theme  # type: ignore

    def save_theme(db, mode: str):  # type: ignore
        return


BRAND_GREEN = BRAND_PRIMARY
TRANSPARENT_1PX = "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw=="


def _nav(page: ft.Page, route: str):
    asyncio.create_task(page.push_route(route))


def _is_web(page: ft.Page) -> bool:
    return getattr(page, "web", False) is True


def _is_native_desktop(page: ft.Page) -> bool:
    return (not _is_web(page)) and page.platform in (
        ft.PagePlatform.WINDOWS,
        ft.PagePlatform.MACOS,
        ft.PagePlatform.LINUX,
    )


def _is_dark(page: ft.Page) -> bool:
    return page.theme_mode == ft.ThemeMode.DARK


def _tokens(page: ft.Page) -> dict:
    if _is_dark(page):
        return {
            "page_bg": "#0B0F0C",
            "page_bg2": "#070A08",
            "card_bg": "#141614",
            "card_border": ft.Colors.with_opacity(0.18, ft.Colors.WHITE),
            "text": "#FFFFFF",
            "muted": ft.Colors.with_opacity(0.75, ft.Colors.WHITE),
            "muted2": ft.Colors.with_opacity(0.55, ft.Colors.WHITE),
            "shadow": ft.Colors.with_opacity(0.25, ft.Colors.BLACK),
            "drop_bg": "#111311",
            "drop_border2": ft.Colors.with_opacity(0.10, ft.Colors.WHITE),
            "chip_bg": ft.Colors.with_opacity(0.10, ft.Colors.WHITE),
            "btn_secondary_bg": ft.Colors.with_opacity(0.14, ft.Colors.WHITE),
            "btn_secondary_fg": ft.Colors.with_opacity(0.90, ft.Colors.WHITE),
            "btn_secondary_dis_bg": ft.Colors.with_opacity(0.10, ft.Colors.WHITE),
            "btn_secondary_dis_fg": ft.Colors.with_opacity(0.40, ft.Colors.WHITE),
            "link": "#A7FF8A",
            "accent_bg": ft.Colors.with_opacity(0.16, ft.Colors.GREEN_400),
        }

    return {
        "page_bg": "#F5FAF3",
        "page_bg2": "#FFFFFF",
        "card_bg": "#FFFFFF",
        "card_border": ft.Colors.with_opacity(0.10, ft.Colors.BLACK),
        "text": "#0F172A",
        "muted": ft.Colors.with_opacity(0.70, ft.Colors.BLACK),
        "muted2": ft.Colors.with_opacity(0.55, ft.Colors.BLACK),
        "shadow": ft.Colors.with_opacity(0.10, ft.Colors.BLACK),
        "drop_bg": "#FFFFFF",
        "drop_border2": ft.Colors.with_opacity(0.18, ft.Colors.BLUE_GREY),
        "chip_bg": ft.Colors.with_opacity(0.06, ft.Colors.BLACK),
        "btn_secondary_bg": ft.Colors.with_opacity(0.10, ft.Colors.BLACK),
        "btn_secondary_fg": ft.Colors.with_opacity(0.85, ft.Colors.BLACK),
        "btn_secondary_dis_bg": ft.Colors.with_opacity(0.08, ft.Colors.BLACK),
        "btn_secondary_dis_fg": ft.Colors.with_opacity(0.45, ft.Colors.BLACK),
        "link": "#1F7A00",
        "accent_bg": ft.Colors.with_opacity(0.18, ft.Colors.GREEN_200),
    }


def _apply_saved_theme(page: ft.Page, db):
    tm = page.data.get("theme_mode")
    if tm in ("dark", "light"):
        page.theme_mode = ft.ThemeMode.DARK if tm == "dark" else ft.ThemeMode.LIGHT
        return

    if db is not None:
        saved = load_theme(db)
        page.theme_mode = ft.ThemeMode.DARK if saved == "dark" else ft.ThemeMode.LIGHT
        page.data["theme_mode"] = "dark" if page.theme_mode == ft.ThemeMode.DARK else "light"
        return

    page.theme_mode = ft.ThemeMode.LIGHT
    page.data["theme_mode"] = "light"


def _persist_theme(page: ft.Page, db):
    mode = "dark" if page.theme_mode == ft.ThemeMode.DARK else "light"
    page.data["theme_mode"] = mode
    if db is not None:
        try:
            save_theme(db, mode)
        except Exception:
            pass


def _validate_image_quality(img_bytes: bytes) -> tuple[bool, str]:
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    mean_brightness = ImageStat.Stat(img.convert("L")).mean[0]

    gray = np.array(img.convert("L"), dtype=np.float32)
    lap = (
        -1 * np.roll(gray, 1, axis=0)
        -1 * np.roll(gray, -1, axis=0)
        -1 * np.roll(gray, 1, axis=1)
        -1 * np.roll(gray, -1, axis=1)
        + 4 * gray
    )
    sharpness = float(lap.var())

    if mean_brightness < 60:
        return False, "Iluminación insuficiente. Sube una foto con más luz."
    if sharpness < 50:
        return False, "Imagen borrosa. Vuelve a tomar la foto con mejor enfoque."
    return True, f"Imagen OK ✅ (brillo={mean_brightness:.0f}, nitidez={sharpness:.0f})"


def _save_bytes_to_captures(img_bytes: bytes) -> str:
    os.makedirs("captures", exist_ok=True)
    fname = f"captures/scan_{int(time.time())}.jpg"
    with open(fname, "wb") as f:
        f.write(img_bytes)
    return fname


def _as_data_url(img_bytes: bytes) -> str:
    b64 = base64.b64encode(img_bytes).decode("utf-8")
    return f"data:image/jpeg;base64,{b64}"


def _pick_file_with_tkinter() -> Optional[str]:
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        path = filedialog.askopenfilename(
            title="Selecciona una imagen",
            filetypes=[("Imágenes", "*.jpg *.jpeg *.png"), ("Todos", "*.*")],
        )
        root.destroy()
        return path if path else None
    except Exception:
        return None


def _download_image_from_url(url: str, timeout_s: int = 12, max_bytes: int = 8 * 1024 * 1024) -> bytes:
    url = url.strip()
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError("La URL debe iniciar con http:// o https://")

    headers = {"User-Agent": "AvorunaWeb/1.0", "Accept": "image/*,*/*;q=0.8"}
    req = Request(url, headers=headers, method="GET")
    with urlopen(req, timeout=timeout_s) as resp:
        ctype = (resp.headers.get("Content-Type") or "").lower()
        if ctype and ("image/" not in ctype):
            raise ValueError(f"El enlace no parece una imagen (Content-Type: {ctype})")

        data = resp.read(max_bytes + 1)
        if len(data) > max_bytes:
            raise ValueError("La imagen excede el tamaño permitido (máx 8MB).")

    try:
        Image.open(io.BytesIO(data)).verify()
    except Exception as ex:
        raise ValueError(f"No se pudo leer como imagen: {ex}")

    return data


def create_camera_stub_view(page: ft.Page) -> ft.View:
    db = page.data.get("db")
    _apply_saved_theme(page, db)

    # ============================================================
    # A1) WEB: diseño como tu imagen (URL -> descargar -> analizar)
    # ============================================================
    if _is_web(page):
        t = _tokens(page)

        picked = {"bytes": None, "name": None, "ready": False}

        hero_title = ft.Text("Análisis de Madurez", size=34, weight=ft.FontWeight.W_900)
        hero_sub = ft.Text(
            "Herramienta agrícola de precisión para determinar el estado óptimo\n"
            "de sus aguacates mediante análisis de imagen.",
            size=12,
            text_align=ft.TextAlign.CENTER,
        )

        url_tf = ft.TextField(
            label="URL DE LA IMAGEN",
            hint_text="Pegue aquí el enlace de la imagen (Google Drive, Dropbox, hosting)",
            expand=True,
            dense=True,
        )

        analyze_btn = ft.Button("ANALIZAR", icon=ft.Icons.CENTER_FOCUS_STRONG)

        theme_btn = ft.IconButton(
            icon=ft.Icons.LIGHT_MODE_OUTLINED if _is_dark(page) else ft.Icons.DARK_MODE_OUTLINED,
            tooltip="Cambiar tema",
        )
        close_btn = ft.IconButton(icon=ft.Icons.CLOSE, tooltip="Cerrar", on_click=lambda _: _nav(page, "/home"))

        helper = ft.Row(
            spacing=6,
            controls=[
                ft.Icon(ft.Icons.INFO_OUTLINE, size=14),
                ft.Text("No se requieren archivos locales. Solo pegue el link directo de la imagen.", size=11),
            ],
        )

        thumb = ft.Image(src=TRANSPARENT_1PX, width=54, height=54, fit=ft.BoxFit.COVER, visible=False)
        file_name_txt = ft.Text("", size=12, weight=ft.FontWeight.W_900)
        file_status_txt = ft.Text("", size=11)
        clear_btn = ft.IconButton(icon=ft.Icons.CLOSE, tooltip="Quitar", visible=False)

        detected_card = ft.Container(
            visible=False,
            border_radius=12,
            padding=ft.Padding(14, 12, 14, 12),
            content=ft.Row(
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Container(width=58, height=58, border_radius=10, alignment=ft.Alignment(0, 0), content=thumb),
                    ft.Column(expand=True, spacing=2, controls=[file_name_txt, file_status_txt]),
                    clear_btn,
                ],
            ),
        )

        def step(icon, title, desc):
            return ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=6,
                controls=[
                    ft.Container(width=44, height=44, border_radius=22, alignment=ft.Alignment(0, 0), content=ft.Icon(icon, size=20)),
                    ft.Text(title, size=12, weight=ft.FontWeight.W_900, text_align=ft.TextAlign.CENTER),
                    ft.Text(desc, size=11, text_align=ft.TextAlign.CENTER),
                ],
            )

        steps_row = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_EVENLY,
            vertical_alignment=ft.CrossAxisAlignment.START,
            controls=[
                step(ft.Icons.LINK, "1. Pegue el link", "Soporte para nubes\n y URLs directas de imagen."),
                step(ft.Icons.AUTO_FIX_HIGH, "2. IA de Visión", "Nuestro algoritmo procesa el color\n y textura de la cáscara."),
                step(ft.Icons.CHECK_CIRCLE_OUTLINE, "3. Resultado", "Obtenga el porcentaje de madurez\n y estado estimado."),
            ],
        )

        footer = ft.Text("© 2026 Avoruna. Todos los derechos reservados.", size=10, text_align=ft.TextAlign.CENTER)

        input_row = ft.Row(
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.END,
            controls=[ft.Container(expand=True, content=url_tf), ft.Container(width=160, content=analyze_btn)],
        )

        top_right = ft.Row(spacing=6, controls=[theme_btn, close_btn])

        main_card = ft.Container(
            width=720,
            border_radius=16,
            padding=ft.Padding(18, 16, 18, 16),
            content=ft.Column(
                spacing=14,
                controls=[ft.Row(alignment=ft.MainAxisAlignment.END, controls=[top_right]), input_row, helper, detected_card],
            ),
        )

        root = ft.Container(
            expand=True,
            padding=ft.Padding(22, 22, 22, 22),
            alignment=ft.Alignment(0, 0),
            content=ft.Column(
                expand=True,
                spacing=18,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[ft.Container(height=10), hero_title, hero_sub, main_card, ft.Container(height=10), steps_row, ft.Container(expand=True), footer],
            ),
        )

        def apply_theme():
            nonlocal t
            t = _tokens(page)

            root.bgcolor = t["page_bg"]
            root.gradient = ft.LinearGradient(begin=ft.Alignment(-1, -1), end=ft.Alignment(1, 1), colors=[t["page_bg"], t["page_bg2"]])

            hero_title.color = t["text"]
            hero_sub.color = t["muted"]

            main_card.bgcolor = t["card_bg"]
            main_card.border = ft.Border.all(1, t["card_border"])
            main_card.shadow = ft.BoxShadow(blur_radius=26, color=t["shadow"], offset=ft.Offset(0, 10))

            helper.controls[0].color = t["muted2"]
            helper.controls[1].color = t["muted"]

            detected_card.bgcolor = t["accent_bg"]
            detected_card.border = ft.Border.all(1, ft.Colors.with_opacity(0.10, ft.Colors.BLACK if not _is_dark(page) else ft.Colors.WHITE))

            file_name_txt.color = t["text"]
            file_status_txt.color = t["muted"]
            clear_btn.icon_color = t["muted"]

            for col in steps_row.controls:
                if isinstance(col, ft.Column) and col.controls:
                    icon_circle = col.controls[0]
                    if isinstance(icon_circle, ft.Container) and isinstance(icon_circle.content, ft.Icon):
                        icon_circle.bgcolor = t["accent_bg"]
                        icon_circle.content.color = BRAND_GREEN
                    for c in col.controls[1:]:
                        if isinstance(c, ft.Text):
                            c.color = t["text"] if c.weight == ft.FontWeight.W_900 else t["muted"]

            footer.color = t["muted2"]

            analyze_btn.style = ft.ButtonStyle(
                bgcolor={ft.ControlState.DEFAULT: BRAND_GREEN},
                color={ft.ControlState.DEFAULT: ft.Colors.WHITE},
                padding={ft.ControlState.DEFAULT: ft.Padding(14, 12, 14, 12)},
                shape={ft.ControlState.DEFAULT: ft.RoundedRectangleBorder(radius=12)},
            )
            analyze_btn.icon_color = ft.Colors.WHITE

            theme_btn.icon = ft.Icons.LIGHT_MODE_OUTLINED if _is_dark(page) else ft.Icons.DARK_MODE_OUTLINED
            theme_btn.icon_color = t["muted"]
            close_btn.icon_color = t["muted"]

        def toggle_theme(_):
            page.theme_mode = ft.ThemeMode.LIGHT if _is_dark(page) else ft.ThemeMode.DARK
            _persist_theme(page, db)
            apply_theme()
            page.update()

        theme_btn.on_click = toggle_theme

        def clear_detected(_=None):
            picked["bytes"] = None
            picked["name"] = None
            picked["ready"] = False
            thumb.visible = False
            thumb.src = TRANSPARENT_1PX
            detected_card.visible = False
            clear_btn.visible = False
            file_name_txt.value = ""
            file_status_txt.value = ""
            page.update()

        clear_btn.on_click = clear_detected

        def show_detected(img_bytes: bytes, name: str, msg: str):
            picked["bytes"] = img_bytes
            picked["name"] = name
            picked["ready"] = True
            thumb.src = _as_data_url(img_bytes)
            thumb.visible = True
            file_name_txt.value = name
            file_status_txt.value = msg
            detected_card.visible = True
            clear_btn.visible = True
            page.update()

        async def download_from_url_async(url: str):
            try:
                analyze_btn.disabled = True
                analyze_btn.text = "CARGANDO..."
                page.update()

                loop = asyncio.get_running_loop()
                data = await loop.run_in_executor(None, _download_image_from_url, url)

                ok, msg = _validate_image_quality(data)
                if not ok:
                    show_detected(data, "imagen.jpg", msg)
                    analyze_btn.disabled = True
                    analyze_btn.text = "ANALIZAR"
                    page.update()
                    return

                path = urlparse(url).path
                name = os.path.basename(path) or "imagen.jpg"
                show_detected(data, name, "Imagen detectada • Lista para procesar")

                analyze_btn.disabled = False
                analyze_btn.text = "ANALIZAR"
                page.update()

            except Exception as ex:
                clear_detected()
                analyze_btn.disabled = False
                analyze_btn.text = "ANALIZAR"
                file_status_txt.value = f"Error: {ex}"
                detected_card.visible = True
                page.update()

        def do_analysis_now():
            img_bytes = picked["bytes"]
            if not img_bytes:
                return
            try:
                asset = _as_data_url(img_bytes)
                pct = random.choice([40, 55, 75, 85, 92, 95])
                status = "Listo" if pct >= 80 else "Espera"

                if db is not None:
                    db.execute(
                        "INSERT INTO scans (source, image_asset, maturity_percent, status) VALUES (?, ?, ?, ?)",
                        ("url", asset, int(pct), status),
                    )
                _nav(page, "/home")
            except Exception as ex:
                file_status_txt.value = f"Error analizando: {ex}"
                page.update()

        def on_analyze_click(_):
            if not picked["ready"]:
                url = (url_tf.value or "").strip()
                if not url:
                    detected_card.visible = True
                    file_name_txt.value = "URL requerida"
                    file_status_txt.value = "Pegue un enlace directo a la imagen."
                    clear_btn.visible = True
                    page.update()
                    return
                asyncio.create_task(download_from_url_async(url))
                return
            do_analysis_now()

        analyze_btn.on_click = on_analyze_click

        apply_theme()
        return ft.View(route="/camera", controls=[ft.SafeArea(expand=True, content=root)])

    # ============================================================
    # A2) DESKTOP: tu diseño actual (NO MOVER)
    # ============================================================
    if _is_native_desktop(page):
        title_txt = ft.Text("Subir foto para analizar madurez", size=18, weight=ft.FontWeight.W_900, text_align=ft.TextAlign.CENTER)
        subtitle_txt = ft.Text("Desktop: sube una foto de alta resolución", size=11, text_align=ft.TextAlign.CENTER)
        status_txt = ft.Text("", size=12)

        upload_btn = ft.Button("Subir foto", icon=ft.Icons.CAMERA_ALT_OUTLINED)
        analyze_btn = ft.Button("Analizar", icon=ft.Icons.ANALYTICS_OUTLINED, disabled=True)

        theme_btn = ft.IconButton(tooltip="Cambiar tema", icon=ft.Icons.DARK_MODE_OUTLINED)
        close_btn = ft.IconButton(tooltip="Cerrar", icon=ft.Icons.CLOSE, on_click=lambda _: _nav(page, "/home"))

        picked = {"bytes": None}

        drop_title = ft.Text("Sube una foto de la palta", size=16, weight=ft.FontWeight.W_900, text_align=ft.TextAlign.CENTER)
        drop_sub = ft.Text("Haz clic para ", size=12)
        drop_link = ft.Text("buscar en tu ordenador", size=12, weight=ft.FontWeight.W_900)

        drop_meta = ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=16,
            controls=[
                ft.Row(spacing=6, controls=[ft.Icon(ft.Icons.IMAGE_OUTLINED, size=14), ft.Text("JPG / PNG", size=11)]),
                ft.Row(spacing=6, controls=[ft.Icon(ft.Icons.CLOUD_UPLOAD_OUTLINED, size=14), ft.Text("MAX 10MB", size=11)]),
            ],
        )

        icon_box = ft.Container(width=56, height=56, border_radius=14, alignment=ft.Alignment(0, 0), content=ft.Icon(ft.Icons.IMAGE_OUTLINED, size=26))

        placeholder = ft.Container(
            expand=True,
            alignment=ft.Alignment(0, 0),
            content=ft.Column(
                expand=True,
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=12,
                controls=[icon_box, drop_title, ft.Row(alignment=ft.MainAxisAlignment.CENTER, spacing=0, controls=[drop_sub, drop_link]), drop_meta],
            ),
        )

        img_preview = ft.Image(src=TRANSPARENT_1PX, visible=False, fit=ft.BoxFit.CONTAIN, expand=True)

        drop_zone = ft.Container(
            height=360,
            border_radius=16,
            padding=ft.Padding(18, 18, 18, 18),
            alignment=ft.Alignment(0, 0),
            content=ft.Stack(expand=True, controls=[placeholder, img_preview]),
        )

        hint_row = ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=8,
            controls=[ft.Icon(ft.Icons.TIPS_AND_UPDATES_OUTLINED, size=16), ft.Text("Consejo: Luz uniforme, sin sombras duras, palta centrada y enfocada para un resultado óptimo.", size=11)],
        )

        header = ft.Row(
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Container(expand=1, alignment=ft.Alignment(-1, 0), content=ft.Row(spacing=10, controls=[upload_btn, analyze_btn])),
                ft.Container(expand=1, alignment=ft.Alignment(0, 0), content=ft.Column(spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER, controls=[title_txt, subtitle_txt])),
                ft.Container(expand=1, alignment=ft.Alignment(1, 0), content=ft.Row(spacing=6, controls=[theme_btn, close_btn])),
            ],
        )

        card = ft.Container(
            width=980,
            border_radius=18,
            padding=ft.Padding(18, 14, 18, 16),
            content=ft.Column(spacing=14, horizontal_alignment=ft.CrossAxisAlignment.CENTER, controls=[header, drop_zone, ft.Container(width=980, padding=ft.Padding(4, 0, 4, 0), content=status_txt), hint_row]),
        )

        root = ft.Container(expand=True, padding=ft.Padding(18, 18, 18, 18), alignment=ft.Alignment(0, 0), content=card)

        def apply_theme():
            t = _tokens(page)

            root.bgcolor = t["page_bg"]
            root.gradient = ft.LinearGradient(begin=ft.Alignment(-1, -1), end=ft.Alignment(1, 1), colors=[t["page_bg"], t["page_bg2"]])

            card.bgcolor = t["card_bg"]
            card.border = ft.Border.all(1, t["card_border"])
            card.shadow = ft.BoxShadow(blur_radius=26, color=t["shadow"], offset=ft.Offset(0, 10))

            title_txt.color = t["text"]
            subtitle_txt.color = t["muted"]
            status_txt.color = t["muted"]

            drop_title.color = t["text"]
            drop_sub.color = t["muted"]
            drop_link.color = t["link"]

            icon_box.bgcolor = t["chip_bg"]
            if isinstance(icon_box.content, ft.Icon):
                icon_box.content.color = t["muted"]

            for row in drop_meta.controls:
                if isinstance(row, ft.Row):
                    for subc in row.controls:
                        if isinstance(subc, ft.Icon):
                            subc.color = t["muted2"]
                        if isinstance(subc, ft.Text):
                            subc.color = t["muted2"]

            drop_zone.bgcolor = t["drop_bg"]
            drop_zone.border = ft.Border.all(2, t["drop_border2"])

            for c in hint_row.controls:
                if isinstance(c, ft.Icon):
                    c.color = t["link"]
                if isinstance(c, ft.Text):
                    c.color = t["muted"]

            upload_btn.style = ft.ButtonStyle(
                bgcolor={ft.ControlState.DEFAULT: BRAND_GREEN},
                color={ft.ControlState.DEFAULT: ft.Colors.WHITE},
                padding={ft.ControlState.DEFAULT: ft.Padding(14, 10, 14, 10)},
                shape={ft.ControlState.DEFAULT: ft.RoundedRectangleBorder(radius=999)},
            )
            upload_btn.icon_color = ft.Colors.WHITE

            analyze_btn.style = ft.ButtonStyle(
                bgcolor={ft.ControlState.DEFAULT: t["btn_secondary_bg"], ft.ControlState.DISABLED: t["btn_secondary_dis_bg"]},
                color={ft.ControlState.DEFAULT: t["btn_secondary_fg"], ft.ControlState.DISABLED: t["btn_secondary_dis_fg"]},
                padding={ft.ControlState.DEFAULT: ft.Padding(14, 10, 14, 10)},
                shape={ft.ControlState.DEFAULT: ft.RoundedRectangleBorder(radius=999)},
            )
            analyze_btn.icon_color = t["btn_secondary_fg"]

            close_btn.icon_color = t["muted"]
            theme_btn.icon_color = t["muted"]
            theme_btn.icon = ft.Icons.LIGHT_MODE_OUTLINED if _is_dark(page) else ft.Icons.DARK_MODE_OUTLINED

        def toggle_theme(_):
            page.theme_mode = ft.ThemeMode.LIGHT if _is_dark(page) else ft.ThemeMode.DARK
            _persist_theme(page, db)
            apply_theme()
            page.update()

        theme_btn.on_click = toggle_theme

        def _apply_image_bytes(img_bytes: bytes):
            picked["bytes"] = img_bytes
            ok, msg = _validate_image_quality(img_bytes)
            status_txt.value = msg
            analyze_btn.disabled = not ok

            img_preview.src = _as_data_url(img_bytes)
            img_preview.visible = True
            placeholder.visible = False
            page.update()

        async def pick_file_desktop_async():
            loop = asyncio.get_running_loop()
            path = await loop.run_in_executor(None, _pick_file_with_tkinter)
            if not path:
                status_txt.value = "No se seleccionó archivo."
                page.update()
                return
            try:
                with open(path, "rb") as fh:
                    _apply_image_bytes(fh.read())
            except Exception as ex:
                status_txt.value = f"Error leyendo archivo: {ex}"
                analyze_btn.disabled = True
                page.update()

        def pick_file(_=None):
            asyncio.create_task(pick_file_desktop_async())

        upload_btn.on_click = pick_file
        drop_zone.on_click = pick_file

        def on_analyze(_):
            if not picked["bytes"]:
                status_txt.value = "Primero sube una foto."
                page.update()
                return
            img_bytes = picked["bytes"]
            try:
                asset = _save_bytes_to_captures(img_bytes)
                pct = random.choice([40, 55, 75, 85, 92, 95])
                status = "Listo" if pct >= 80 else "Espera"

                if db is not None:
                    db.execute(
                        "INSERT INTO scans (source, image_asset, maturity_percent, status) VALUES (?, ?, ?, ?)",
                        ("upload", asset, int(pct), status),
                    )

                status_txt.value = f"Analizado ({pct}%) - {status}"
                page.update()
                _nav(page, "/home")
            except Exception as ex:
                status_txt.value = f"Error analizando: {ex}"
                page.update()

        analyze_btn.on_click = on_analyze

        apply_theme()
        return ft.View(route="/camera", controls=[ft.SafeArea(expand=True, content=root)])

    # ============================================================
    # B) ANDROID/iOS: Cámara en vivo (fix pantalla gris)
    # ============================================================
    def _c_text() -> str:
        return _tokens(page)["text"]

    status_txt = ft.Text("Inicializando...", size=12, color=ft.Colors.WHITE)
    title_txt = ft.Text("Escaneando...", size=22, weight=ft.FontWeight.W_900, color=ft.Colors.WHITE)
    subtitle_txt = ft.Text("Detectando madurez del fruto", size=11, color=ft.Colors.with_opacity(0.75, ft.Colors.WHITE))

    ring_host = ft.Container()

    def build_ring(size: int) -> ft.Container:
        outer = size
        inner = int(size * 0.78)
        return ft.Container(
            width=outer,
            height=outer,
            border_radius=outer // 2,
            alignment=ft.Alignment(0, 0),
            content=ft.Stack(
                alignment=ft.Alignment(0, 0),
                controls=[
                    ft.Container(width=outer, height=outer, border_radius=outer // 2, border=ft.Border.all(4, ft.Colors.with_opacity(0.85, ft.Colors.GREEN_400))),
                    ft.Container(
                        width=int(outer * 0.92),
                        height=int(outer * 0.92),
                        border_radius=int(outer * 0.92) // 2,
                        border=ft.Border.all(3, ft.Colors.with_opacity(0.25, ft.Colors.WHITE)),
                    ),
                    ft.Container(
                        width=inner,
                        height=inner,
                        border_radius=inner // 2,
                        bgcolor=ft.Colors.with_opacity(0.14, ft.Colors.GREEN_400),
                        alignment=ft.Alignment(0, 0),
                        content=ft.Icon(ft.Icons.CENTER_FOCUS_STRONG, size=max(34, int(size * 0.16)), color=ft.Colors.with_opacity(0.92, ft.Colors.WHITE)),
                    ),
                ],
            ),
        )

    def on_resize(_=None):
        w = page.width or 360
        size = 300 if w >= 420 else 270 if w >= 360 else 240
        ring_host.content = build_ring(size)
        page.update()

    page.on_resize = on_resize

    def pill(icon, text):
        return ft.Container(
            border_radius=999,
            bgcolor=ft.Colors.with_opacity(0.22, ft.Colors.BLACK),
            padding=ft.Padding(14, 8, 14, 8),
            content=ft.Row(
                tight=True,
                spacing=8,
                controls=[
                    ft.Icon(icon, size=16, color=ft.Colors.with_opacity(0.92, ft.Colors.WHITE)),
                    ft.Text(text, size=11, color=ft.Colors.with_opacity(0.92, ft.Colors.WHITE), weight=ft.FontWeight.W_700),
                ],
            ),
        )

    hint1 = pill(ft.Icons.CENTER_FOCUS_WEAK, "Alinea la palta en el centro")
    hint2 = pill(ft.Icons.WB_SUNNY_OUTLINED, "Busca una luz natural uniforme")

    ph = fph.PermissionHandler()
    init_lock = asyncio.Lock()
    is_initialized = False

    preview = fc.Camera(expand=True, preview_enabled=True)

    cameras = []
    current_index = 0

    def cam_label(c) -> str:
        return getattr(c, "name", None) or getattr(c, "label", None) or str(c)

    async def ensure_permissions():
        cam_status = await ph.request(fph.Permission.CAMERA)
        if cam_status is None or cam_status.name not in ("GRANTED", "LIMITED"):
            raise RuntimeError("Permiso de cámara no concedido.")

    async def load_cameras():
        nonlocal cameras, current_index
        await ensure_permissions()

        status_txt.value = "Buscando cámaras..."
        page.update()

        cams = await preview.get_available_cameras()
        if not cams:
            raise RuntimeError("No se encontraron cámaras disponibles.")

        cams = sorted(
            cams,
            key=lambda c: ("obs" in cam_label(c).lower() or "virtual" in cam_label(c).lower(), cam_label(c).lower()),
        )
        cameras = cams
        current_index = 0

    async def init_camera():
        nonlocal is_initialized
        async with init_lock:
            try:
                # ✅ espera breve: permite que el view se monte (evita preview gris)
                await asyncio.sleep(0.25)

                if not cameras:
                    await load_cameras()

                status_txt.value = "Iniciando cámara..."
                page.update()

                await preview.set_description(cameras[current_index])

                last_err = None
                for _ in range(3):
                    try:
                        await preview.initialize()
                        is_initialized = True
                        status_txt.value = "Cámara lista ✅"
                        page.update()
                        return
                    except Exception as ex:
                        last_err = ex
                        await asyncio.sleep(0.4)

                is_initialized = False
                raise last_err or RuntimeError("No se pudo inicializar la cámara.")

            except Exception as ex:
                is_initialized = False
                status_txt.value = f"Error cámara: {ex}"
                page.update()

    async def capture_and_save():
        nonlocal is_initialized
        if not is_initialized:
            await init_camera()
            if not is_initialized:
                return

        try:
            status_txt.value = "Capturando..."
            page.update()

            img_bytes = await preview.take_picture()
            fname = _save_bytes_to_captures(img_bytes)

            pct = random.choice([40, 55, 75, 85, 92, 95])
            status = "Listo" if pct >= 80 else "Espera"

            if db is not None:
                db.execute(
                    "INSERT INTO scans (source, image_asset, maturity_percent, status) VALUES (?, ?, ?, ?)",
                    ("camera", fname, int(pct), status),
                )

            status_txt.value = f"Capturado ({pct}%) - {status}"
            page.update()
            _nav(page, "/home")

        except Exception as ex:
            status_txt.value = f"Error capturando: {ex}"
            page.update()

    async def next_camera():
        nonlocal current_index, is_initialized
        if not cameras:
            await load_cameras()
        if not cameras:
            return
        current_index = (current_index + 1) % len(cameras)
        is_initialized = False
        await init_camera()

    def toggle_theme_mobile(_):
        page.theme_mode = ft.ThemeMode.LIGHT if _is_dark(page) else ft.ThemeMode.DARK
        _persist_theme(page, db)
        theme_btn.icon = ft.Icons.LIGHT_MODE_OUTLINED if _is_dark(page) else ft.Icons.DARK_MODE_OUTLINED
        page.update()

    theme_btn = ft.IconButton(
        icon=ft.Icons.LIGHT_MODE_OUTLINED if _is_dark(page) else ft.Icons.DARK_MODE_OUTLINED,
        icon_color=ft.Colors.WHITE,
        tooltip="Tema",
        on_click=toggle_theme_mobile,
    )

    close_btn = ft.IconButton(
        icon=ft.Icons.CLOSE,
        icon_color=ft.Colors.WHITE,
        tooltip="Cerrar",
        on_click=lambda _: _nav(page, "/home"),
    )

    trash_btn = ft.IconButton(icon=ft.Icons.DELETE_OUTLINE, icon_color=ft.Colors.WHITE, tooltip="Limpiar", on_click=lambda _: None)

    topbar = ft.Container(
        padding=ft.Padding(12, 10, 12, 10),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                close_btn,
                ft.Column(
                    spacing=2,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Text("AVORUNA AI", size=11, weight=ft.FontWeight.W_900, color=ft.Colors.WHITE),
                        ft.Container(width=26, height=3, bgcolor=ft.Colors.GREEN_400, border_radius=99),
                    ],
                ),
                ft.Row(spacing=4, controls=[theme_btn, trash_btn]),
            ],
        ),
    )

    gallery_btn = ft.Container(
        width=44,
        height=44,
        border_radius=22,
        bgcolor=ft.Colors.with_opacity(0.22, ft.Colors.BLACK),
        alignment=ft.Alignment(0, 0),
        content=ft.Icon(ft.Icons.PHOTO_LIBRARY_OUTLINED, color=ft.Colors.WHITE),
    )

    switch_btn = ft.Container(
        width=44,
        height=44,
        border_radius=22,
        bgcolor=ft.Colors.with_opacity(0.22, ft.Colors.BLACK),
        alignment=ft.Alignment(0, 0),
        content=ft.Icon(ft.Icons.CACHED, color=ft.Colors.WHITE),
        on_click=lambda _: asyncio.create_task(next_camera()),
    )

    shutter = ft.Container(
        width=78,
        height=78,
        border_radius=39,
        bgcolor=ft.Colors.WHITE,
        alignment=ft.Alignment(0, 0),
        content=ft.Container(
            width=62,
            height=62,
            border_radius=31,
            bgcolor=BRAND_GREEN,
            alignment=ft.Alignment(0, 0),
            content=ft.Icon(ft.Icons.ECO, color=ft.Colors.BLACK, size=24),
        ),
        on_click=lambda _: asyncio.create_task(capture_and_save()),
    )

    bottom_bar = ft.Container(
        padding=ft.Padding(18, 0, 18, 18),
        content=ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[gallery_btn, shutter, switch_btn]),
    )

    center_overlay = ft.Container(
        expand=True,
        alignment=ft.Alignment(0, 0.25),
        content=ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
            controls=[ring_host, ft.Container(height=8), title_txt, subtitle_txt, ft.Container(height=6), hint1, hint2, status_txt],
        ),
    )

    shade = ft.Container(expand=True, bgcolor=ft.Colors.with_opacity(0.25, ft.Colors.BLACK))

    mobile_root = ft.Container(
        expand=True,
        bgcolor=_tokens(page)["page_bg"],
        content=ft.Stack(
            expand=True,
            controls=[
                preview,
                shade,
                ft.SafeArea(
                    expand=True,
                    top=True,
                    bottom=True,
                    content=ft.Stack(
                        expand=True,
                        controls=[
                            ft.Container(alignment=ft.Alignment(0, -1), content=topbar),
                            center_overlay,
                            ft.Container(alignment=ft.Alignment(0, 1), content=bottom_bar),
                        ],
                    ),
                ),
            ],
        ),
    )

    on_resize()
    asyncio.create_task(init_camera())

    return ft.View(route="/camera", controls=[mobile_root])
