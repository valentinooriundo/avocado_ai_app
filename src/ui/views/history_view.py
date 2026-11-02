from __future__ import annotations

import asyncio
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

import flet as ft

from services.scan_flow_service import APP_DB_PATH, get_scan_history
from services.settings_service import load_theme
from ui.components.app_shell import build_app_shell
from ui.theme_tokens import BRAND_PRIMARY

# =========================================================
# SINCRONIZACIÓN EN LA NUBE
# =========================================================
# Desactivada temporalmente. Cuando se implemente cloud_sync_service.py,
# descomenta la importación y cambia ENABLE_CLOUD_SYNC a True.
# from services.cloud_sync_service import sync_pending_history

ENABLE_CLOUD_SYNC = False
sync_pending_history = None


BRAND_GREEN = BRAND_PRIMARY
BRAND_DARK = "#2F5D46"
BRAND_LIGHT = "#EAF8E5"
DANGER = "#D92D20"
WARNING = "#F79009"
SUCCESS = "#2E9D45"


# =========================================================
# COLORES Y UTILIDADES GENERALES
# =========================================================


def _is_dark(page: ft.Page) -> bool:
    return page.theme_mode == ft.ThemeMode.DARK


def _c_surface(page: ft.Page) -> str:
    return "#11161C" if _is_dark(page) else "#FFFFFF"


def _c_soft(page: ft.Page) -> str:
    return "#18211B" if _is_dark(page) else "#F5FAF2"


def _c_text(page: ft.Page) -> str:
    return "#F5F7FA" if _is_dark(page) else "#172018"


def _c_muted(page: ft.Page) -> str:
    return "#97A3B6" if _is_dark(page) else "#667085"


def _c_border(page: ft.Page) -> str:
    return "#253041" if _is_dark(page) else "#DCE5D6"


def _nav(page: ft.Page, route: str) -> None:
    page.run_task(page.push_route, route)


def _close_dialog(page: ft.Page, dialog: ft.AlertDialog) -> None:
    try:
        page.pop_dialog()
    except Exception:
        dialog.open = False
        page.update()


def _show_message(
    page: ft.Page,
    message: str,
    *,
    success: bool = True,
) -> None:
    page.show_dialog(
        ft.SnackBar(
            content=ft.Text(
                message,
                color=ft.Colors.WHITE,
                weight=ft.FontWeight.W_700,
            ),
            bgcolor=BRAND_DARK if success else DANGER,
            show_close_icon=True,
            duration=ft.Duration(seconds=5),
        )
    )


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None

    clean_value = str(value).strip()

    for parser in (
        datetime.fromisoformat,
        lambda text: datetime.strptime(text, "%d/%m/%Y"),
        lambda text: datetime.strptime(text, "%d/%m/%Y %H:%M"),
        lambda text: datetime.strptime(text, "%Y-%m-%d"),
    ):
        try:
            return parser(clean_value)
        except (TypeError, ValueError):
            continue

    return None


def _parse_filter_date(value: str | None, *, end_of_day: bool = False) -> datetime | None:
    if not value:
        return None

    parsed = _parse_datetime(value)

    if parsed is None:
        raise ValueError("Usa el formato de fecha DD/MM/AAAA.")

    if end_of_day:
        return parsed.replace(hour=23, minute=59, second=59, microsecond=999999)

    return parsed.replace(hour=0, minute=0, second=0, microsecond=0)


def _format_datetime(value: str | None) -> str:
    parsed = _parse_datetime(value)

    if parsed is None:
        return value or "Fecha no disponible"

    return parsed.strftime("%d/%m/%Y · %H:%M")


def _format_date_for_export(value: str | None) -> str:
    parsed = _parse_datetime(value)

    if parsed is None:
        return value or ""

    return parsed.strftime("%d/%m/%Y %H:%M")


def _read_thumbnail(path_value: str | None) -> bytes | None:
    if not path_value:
        return None

    path = Path(path_value)

    if not path.exists() or not path.is_file():
        return None

    try:
        return path.read_bytes()
    except OSError:
        return None


def _display_label(item: dict) -> str:
    if not item.get("is_reliable", False):
        return "Resultado no concluyente"

    return str(item.get("label_text") or "Resultado")


def _filter_key(item: dict) -> str:
    if not item.get("is_reliable", False):
        return "inconclusive"

    return str(item.get("label_key") or "").strip().lower()


def _color_for_item(item: dict):
    if not item.get("is_reliable", False):
        return ft.Colors.AMBER_700

    color_name = str(item.get("result_color", "")).lower()

    if color_name == "green":
        return ft.Colors.GREEN_600

    if color_name == "red":
        return ft.Colors.RED_600

    if color_name == "amber":
        return ft.Colors.AMBER_700

    return BRAND_GREEN


def _sync_label(item: dict) -> tuple[str, str, str]:
    status = str(item.get("sync_status") or "pending").lower()

    if status == "synced":
        return "Sincronizado", ft.Icons.CLOUD_DONE_OUTLINED, SUCCESS

    if status == "syncing":
        return "Sincronizando", ft.Icons.SYNC, WARNING

    if status == "error":
        return "Error de sincronización", ft.Icons.CLOUD_OFF_OUTLINED, DANGER

    return "Pendiente", ft.Icons.CLOUD_UPLOAD_OUTLINED, WARNING


def _model_label(item: dict) -> str:
    if item.get("inference_mode") == "model":
        return "Analizado con IA"

    return "Modo de desarrollo"


# =========================================================
# ELIMINACIÓN LOCAL
# =========================================================


def _delete_scan_local(item: dict) -> None:
    scan_id = str(item.get("scan_id") or "").strip()

    if not scan_id:
        raise ValueError("El análisis no tiene un identificador válido.")

    with sqlite3.connect(APP_DB_PATH) as connection:
        connection.execute(
            "DELETE FROM scan_history WHERE scan_id = ?",
            (scan_id,),
        )
        connection.commit()

    image_value = str(item.get("saved_image_path") or "").strip()

    if not image_value:
        return

    image_path = Path(image_value)

    # Solo elimina imágenes administradas por el flujo local de Avoruna.
    safe_parts = {part.lower() for part in image_path.parts}
    is_managed_image = (
        "captures" in safe_parts
        or "scan_temp" in safe_parts
        or "uploads_web" in safe_parts
    )

    if is_managed_image and image_path.exists() and image_path.is_file():
        try:
            image_path.unlink()
        except OSError:
            pass


# =========================================================
# EXPORTACIÓN EXCEL Y PDF
# =========================================================


def _project_root() -> Path:
    return Path(APP_DB_PATH).resolve().parent


def _assets_dir() -> Path:
    candidates = [
        _project_root() / "src" / "assets",
        _project_root() / "assets",
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate

    candidates[0].mkdir(parents=True, exist_ok=True)
    return candidates[0]


def _export_dir() -> Path:
    path = _assets_dir() / "exports"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _logo_path() -> Path | None:
    for name in ("icon.png", "logo.png", "avoruna.png"):
        candidate = _assets_dir() / name
        if candidate.exists():
            return candidate

    return None


def _filter_description(filters: dict) -> str:
    parts: list[str] = []

    quick_filter = filters.get("quick_filter", "all")
    quick_names = {
        "all": "Todos",
        "lista_para_cosecha": "Lista para cosecha",
        "en_proceso": "En proceso",
        "aun_no_lista": "Aún no lista",
        "inconclusive": "No concluyente",
    }

    if quick_filter != "all":
        parts.append(quick_names.get(quick_filter, quick_filter))

    search_text = str(filters.get("search") or "").strip()
    if search_text:
        parts.append(f'Búsqueda: "{search_text}"')

    date_from = str(filters.get("date_from") or "").strip()
    date_to = str(filters.get("date_to") or "").strip()

    if date_from or date_to:
        parts.append(f"Periodo: {date_from or 'inicio'} - {date_to or 'hoy'}")

    minimum = str(filters.get("confidence_min") or "").strip()
    maximum = str(filters.get("confidence_max") or "").strip()

    if minimum or maximum:
        parts.append(f"Confianza: {minimum or '0'}% - {maximum or '100'}%")

    sync_status = str(filters.get("sync_status") or "all")
    if sync_status != "all":
        parts.append(f"Sincronización: {sync_status}")

    return " | ".join(parts) if parts else "Todos los análisis"


def _summary_counts(items: list[dict]) -> dict[str, int]:
    result = {
        "total": len(items),
        "lista_para_cosecha": 0,
        "en_proceso": 0,
        "aun_no_lista": 0,
        "inconclusive": 0,
    }

    for item in items:
        key = _filter_key(item)
        if key in result:
            result[key] += 1

    return result


def _build_excel_report(
    items: list[dict],
    filters: dict,
    user_name: str,
) -> Path:
    try:
        from openpyxl import Workbook
        from openpyxl.drawing.image import Image as XLImage
        from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
        from openpyxl.utils import get_column_letter
    except ImportError as exception:
        raise RuntimeError(
            "Falta openpyxl. Ejecuta: uv add openpyxl"
        ) from exception

    generated_at = datetime.now()
    file_path = _export_dir() / (
        f"Avoruna_Historial_{generated_at.strftime('%Y-%m-%d_%H-%M-%S')}.xlsx"
    )

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Historial de análisis"
    worksheet.sheet_view.showGridLines = False

    green_fill = PatternFill("solid", fgColor="2F5D46")
    light_green_fill = PatternFill("solid", fgColor="EAF8E5")
    soft_fill = PatternFill("solid", fgColor="F5FAF2")
    white_font = Font(color="FFFFFF", bold=True)
    title_font = Font(color="172018", bold=True, size=20)
    subtitle_font = Font(color="667085", size=11)
    section_font = Font(color="2F5D46", bold=True, size=11)
    thin_border = Border(
        left=Side(style="thin", color="DCE5D6"),
        right=Side(style="thin", color="DCE5D6"),
        top=Side(style="thin", color="DCE5D6"),
        bottom=Side(style="thin", color="DCE5D6"),
    )

    worksheet.merge_cells("A1:I1")
    worksheet["A1"] = "AVORUNA"
    worksheet["A1"].font = title_font
    worksheet["A1"].alignment = Alignment(horizontal="center")
    worksheet.row_dimensions[1].height = 28

    worksheet.merge_cells("A2:I2")
    worksheet["A2"] = (
        "Sistema móvil inteligente para la detección del nivel de madurez de la palta Hass"
    )
    worksheet["A2"].font = subtitle_font
    worksheet["A2"].alignment = Alignment(horizontal="center")

    logo = _logo_path()
    if logo is not None:
        try:
            image = XLImage(str(logo))
            image.width = 54
            image.height = 54
            worksheet.add_image(image, "A1")
        except Exception:
            pass

    worksheet["A4"] = "Reporte"
    worksheet["B4"] = "Historial de análisis de madurez"
    worksheet["A5"] = "Generado"
    worksheet["B5"] = generated_at.strftime("%d/%m/%Y %H:%M")
    worksheet["D4"] = "Usuario"
    worksheet["E4"] = user_name or "Usuario Avoruna"
    worksheet["D5"] = "Filtros"
    worksheet["E5"] = _filter_description(filters)
    worksheet.merge_cells("E5:I5")

    for cell in ("A4", "A5", "D4", "D5"):
        worksheet[cell].font = section_font

    summary = _summary_counts(items)
    summary_values = [
        ("Total", summary["total"]),
        ("Listas", summary["lista_para_cosecha"]),
        ("En proceso", summary["en_proceso"]),
        ("Aún no listas", summary["aun_no_lista"]),
        ("No concluyentes", summary["inconclusive"]),
    ]

    columns_for_summary = ["A", "C", "E", "G", "I"]
    for column, (label, value) in zip(columns_for_summary, summary_values):
        worksheet[f"{column}7"] = label
        worksheet[f"{column}7"].font = Font(color="2F5D46", bold=True)
        worksheet[f"{column}7"].fill = light_green_fill
        worksheet[f"{column}7"].alignment = Alignment(horizontal="center")
        worksheet[f"{column}8"] = value
        worksheet[f"{column}8"].font = Font(color="172018", bold=True, size=16)
        worksheet[f"{column}8"].fill = soft_fill
        worksheet[f"{column}8"].alignment = Alignment(horizontal="center")

    headers = [
        "N.°",
        "Fecha y hora",
        "Resultado",
        "Confianza",
        "Confiable",
        "Recomendación",
        "Modelo",
        "Sincronización",
        "ID del análisis",
    ]

    header_row = 10
    for index, header in enumerate(headers, start=1):
        cell = worksheet.cell(row=header_row, column=index, value=header)
        cell.fill = green_fill
        cell.font = white_font
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = thin_border

    result_fills = {
        "lista_para_cosecha": PatternFill("solid", fgColor="E8F5E9"),
        "en_proceso": PatternFill("solid", fgColor="FFF4E5"),
        "aun_no_lista": PatternFill("solid", fgColor="FDECEC"),
        "inconclusive": PatternFill("solid", fgColor="FFF4E5"),
    }

    for row_index, item in enumerate(items, start=header_row + 1):
        confidence = _safe_float(item.get("confidence"))
        values = [
            row_index - header_row,
            _format_date_for_export(item.get("created_at")),
            _display_label(item),
            confidence,
            "Sí" if item.get("is_reliable", False) else "No",
            item.get("recommended_action") or "",
            _model_label(item),
            _sync_label(item)[0],
            item.get("scan_id") or "",
        ]

        for column_index, value in enumerate(values, start=1):
            cell = worksheet.cell(row=row_index, column=column_index, value=value)
            cell.border = thin_border
            cell.alignment = Alignment(
                vertical="top",
                wrap_text=True,
            )

        worksheet.cell(row=row_index, column=4).number_format = "0.00%"
        worksheet.cell(row=row_index, column=3).fill = result_fills.get(
            _filter_key(item),
            soft_fill,
        )

    worksheet.freeze_panes = "A11"
    worksheet.auto_filter.ref = f"A10:I{max(header_row + 1, header_row + len(items))}"

    widths = {
        "A": 8,
        "B": 19,
        "C": 25,
        "D": 13,
        "E": 12,
        "F": 48,
        "G": 20,
        "H": 20,
        "I": 36,
    }

    for column, width in widths.items():
        worksheet.column_dimensions[column].width = width

    for row in range(header_row + 1, header_row + len(items) + 1):
        worksheet.row_dimensions[row].height = 36

    worksheet.print_title_rows = f"1:{header_row}"
    worksheet.page_setup.orientation = "landscape"
    worksheet.page_setup.fitToWidth = 1
    worksheet.page_margins.left = 0.25
    worksheet.page_margins.right = 0.25

    workbook.save(file_path)
    return file_path


def _build_pdf_report(
    items: list[dict],
    filters: dict,
    user_name: str,
) -> Path:
    try:
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import cm
        from reportlab.platypus import (
            Image,
            PageBreak,
            Paragraph,
            SimpleDocTemplate,
            Spacer,
            Table,
            TableStyle,
        )
    except ImportError as exception:
        raise RuntimeError(
            "Falta ReportLab. Ejecuta: uv add reportlab"
        ) from exception

    generated_at = datetime.now()
    file_path = _export_dir() / (
        f"Avoruna_Reporte_Historial_{generated_at.strftime('%Y-%m-%d_%H-%M-%S')}.pdf"
    )

    document = SimpleDocTemplate(
        str(file_path),
        pagesize=landscape(A4),
        rightMargin=1.1 * cm,
        leftMargin=1.1 * cm,
        topMargin=1.0 * cm,
        bottomMargin=1.0 * cm,
        title="Avoruna - Historial de análisis",
        author=user_name or "Avoruna",
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "AvorunaTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=23,
        textColor=colors.HexColor("#2F5D46"),
        alignment=TA_CENTER,
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        "AvorunaSubtitle",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#667085"),
        alignment=TA_CENTER,
    )
    body_style = ParagraphStyle(
        "AvorunaBody",
        parent=styles["Normal"],
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor("#172018"),
    )
    small_style = ParagraphStyle(
        "AvorunaSmall",
        parent=body_style,
        fontSize=6.5,
        leading=8,
    )

    story: list[Any] = []

    logo = _logo_path()
    if logo is not None:
        try:
            logo_table = Table(
                [[Image(str(logo), width=1.25 * cm, height=1.25 * cm)]],
                colWidths=[1.4 * cm],
            )
            logo_table.setStyle(
                TableStyle([
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ])
            )
            story.append(logo_table)
        except Exception:
            pass

    story.append(Paragraph("AVORUNA", title_style))
    story.append(
        Paragraph(
            "Sistema móvil inteligente para la detección del nivel de madurez de la palta Hass",
            subtitle_style,
        )
    )
    story.append(Spacer(1, 0.25 * cm))

    metadata = [
        [
            Paragraph("<b>Reporte:</b> Historial de análisis de madurez", body_style),
            Paragraph(
                f"<b>Generado:</b> {generated_at.strftime('%d/%m/%Y %H:%M')}",
                body_style,
            ),
        ],
        [
            Paragraph(f"<b>Usuario:</b> {user_name or 'Usuario Avoruna'}", body_style),
            Paragraph(f"<b>Filtros:</b> {_filter_description(filters)}", body_style),
        ],
    ]

    metadata_table = Table(metadata, colWidths=[12.5 * cm, 14.5 * cm])
    metadata_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F5FAF2")),
                ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#DCE5D6")),
                ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#DCE5D6")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(metadata_table)
    story.append(Spacer(1, 0.25 * cm))

    summary = _summary_counts(items)
    summary_data = [
        ["Total", "Listas", "En proceso", "Aún no listas", "No concluyentes"],
        [
            summary["total"],
            summary["lista_para_cosecha"],
            summary["en_proceso"],
            summary["aun_no_lista"],
            summary["inconclusive"],
        ],
    ]
    summary_table = Table(summary_data, colWidths=[5.4 * cm] * 5)
    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2F5D46")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#EAF8E5")),
                ("TEXTCOLOR", (0, 1), (-1, 1), colors.HexColor("#172018")),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#DCE5D6")),
                ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#DCE5D6")),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(summary_table)
    story.append(Spacer(1, 0.3 * cm))

    table_data: list[list[Any]] = [
        [
            Paragraph("<b>N.°</b>", small_style),
            Paragraph("<b>Fecha</b>", small_style),
            Paragraph("<b>Resultado</b>", small_style),
            Paragraph("<b>Confianza</b>", small_style),
            Paragraph("<b>Confiable</b>", small_style),
            Paragraph("<b>Recomendación</b>", small_style),
            Paragraph("<b>Modelo</b>", small_style),
            Paragraph("<b>Sincronización</b>", small_style),
        ]
    ]

    for index, item in enumerate(items, start=1):
        table_data.append(
            [
                str(index),
                Paragraph(_format_date_for_export(item.get("created_at")), small_style),
                Paragraph(_display_label(item), small_style),
                f"{_safe_float(item.get('confidence')) * 100:.2f}%",
                "Sí" if item.get("is_reliable", False) else "No",
                Paragraph(str(item.get("recommended_action") or ""), small_style),
                Paragraph(_model_label(item), small_style),
                Paragraph(_sync_label(item)[0], small_style),
            ]
        )

    if len(table_data) == 1:
        table_data.append(
            [
                "-",
                "-",
                Paragraph("No existen análisis para los filtros seleccionados.", small_style),
                "-",
                "-",
                "-",
                "-",
                "-",
            ]
        )

    report_table = Table(
        table_data,
        repeatRows=1,
        colWidths=[
            0.8 * cm,
            2.6 * cm,
            4.0 * cm,
            2.0 * cm,
            1.6 * cm,
            8.5 * cm,
            3.2 * cm,
            3.2 * cm,
        ],
    )
    report_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2F5D46")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("FONTSIZE", (0, 1), (-1, -1), 6.5),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#DCE5D6")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FBF6")]),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(report_table)

    def add_page_number(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.HexColor("#667085"))
        canvas.drawString(
            1.1 * cm,
            0.45 * cm,
            "Avoruna - Sistema móvil inteligente",
        )
        canvas.drawRightString(
            landscape(A4)[0] - 1.1 * cm,
            0.45 * cm,
            f"Página {doc.page}",
        )
        canvas.restoreState()

    document.build(
        story,
        onFirstPage=add_page_number,
        onLaterPages=add_page_number,
    )

    return file_path


# =========================================================
# VISTA PRINCIPAL
# =========================================================


def create_history_view(page: ft.Page) -> ft.View:
    if page.data is None:
        page.data = {}

    db = page.data.get("db") if isinstance(page.data, dict) else None

    if db is not None:
        saved = load_theme(db)
        page.theme_mode = (
            ft.ThemeMode.DARK
            if saved == "dark"
            else ft.ThemeMode.LIGHT
        )

    all_history: list[dict] = get_scan_history(limit=500)
    filtered_history: list[dict] = list(all_history)

    state = {
        "quick_filter": "all",
        "advanced_visible": False,
    }

    is_mobile = (page.width or 1200) < 700

    # -----------------------------------------------------
    # Controles de filtro
    # -----------------------------------------------------

    search_field = ft.TextField(
        hint_text="Buscar por resultado, fecha, confianza o ID...",
        prefix_icon=ft.Icons.SEARCH,
        border_radius=14,
        border_color=_c_border(page),
        focused_border_color=BRAND_GREEN,
        bgcolor=_c_surface(page),
        text_size=12,
        height=46,
        expand=True,
    )

    date_from_field = ft.TextField(
        label="Fecha desde",
        hint_text="DD/MM/AAAA",
        prefix_icon=ft.Icons.CALENDAR_MONTH_OUTLINED,
        width=175,
        height=48,
        text_size=11,
        border_radius=12,
        border_color=_c_border(page),
        focused_border_color=BRAND_GREEN,
    )

    date_to_field = ft.TextField(
        label="Fecha hasta",
        hint_text="DD/MM/AAAA",
        prefix_icon=ft.Icons.EVENT_AVAILABLE_OUTLINED,
        width=175,
        height=48,
        text_size=11,
        border_radius=12,
        border_color=_c_border(page),
        focused_border_color=BRAND_GREEN,
    )

    confidence_min_field = ft.TextField(
        label="Confianza mínima",
        hint_text="0",
        suffix=ft.Text("%", size=11, color=_c_muted(page)),
        keyboard_type=ft.KeyboardType.NUMBER,
        width=165,
        height=48,
        text_size=11,
        border_radius=12,
        border_color=_c_border(page),
        focused_border_color=BRAND_GREEN,
    )

    confidence_max_field = ft.TextField(
        label="Confianza máxima",
        hint_text="100",
        suffix=ft.Text("%", size=11, color=_c_muted(page)),
        keyboard_type=ft.KeyboardType.NUMBER,
        width=165,
        height=48,
        text_size=11,
        border_radius=12,
        border_color=_c_border(page),
        focused_border_color=BRAND_GREEN,
    )

    sync_dropdown = ft.Dropdown(
        visible=ENABLE_CLOUD_SYNC,
        label="Sincronización",
        value="all",
        width=185,
        height=48,
        text_size=11,
        border_radius=12,
        border_color=_c_border(page),
        focused_border_color=BRAND_GREEN,
        options=[
            ft.dropdown.Option(key="all", text="Todos"),
            ft.dropdown.Option(key="synced", text="Sincronizados"),
            ft.dropdown.Option(key="pending", text="Pendientes"),
            ft.dropdown.Option(key="error", text="Con error"),
        ],
    )

    order_dropdown = ft.Dropdown(
        label="Ordenar por",
        value="newest",
        width=185,
        height=48,
        text_size=11,
        border_radius=12,
        border_color=_c_border(page),
        focused_border_color=BRAND_GREEN,
        options=[
            ft.dropdown.Option(key="newest", text="Más recientes"),
            ft.dropdown.Option(key="oldest", text="Más antiguos"),
            ft.dropdown.Option(key="confidence_desc", text="Mayor confianza"),
            ft.dropdown.Option(key="confidence_asc", text="Menor confianza"),
            ft.dropdown.Option(key="result", text="Resultado"),
        ],
    )

    filter_error_text = ft.Text(
        "",
        visible=False,
        size=10,
        color=ft.Colors.RED_600,
    )

    advanced_panel = ft.Container(
        visible=False,
        padding=ft.Padding(14, 14, 14, 14),
        border_radius=16,
        bgcolor=_c_soft(page),
        border=ft.Border.all(1, _c_border(page)),
        content=ft.Column(
            spacing=10,
            controls=[
                ft.Text(
                    "Búsqueda avanzada",
                    size=13,
                    color=_c_text(page),
                    weight=ft.FontWeight.W_900,
                ),
                ft.Row(
                    wrap=True,
                    spacing=10,
                    run_spacing=10,
                    controls=[
                        date_from_field,
                        date_to_field,
                        confidence_min_field,
                        confidence_max_field,
                        sync_dropdown,
                        order_dropdown,
                    ],
                ),
                filter_error_text,
            ],
        ),
    )

    # -----------------------------------------------------
    # Controles dinámicos
    # -----------------------------------------------------

    results_count_text = ft.Text(
        "",
        size=11,
        color=_c_muted(page),
    )

    active_filter_text = ft.Text(
        "",
        size=10,
        color=_c_muted(page),
        italic=True,
    )

    list_view = ft.ListView(
        expand=True,
        spacing=8,
        padding=ft.Padding(0, 0, 2, 14),
    )

    summary_row = ft.Row(
        wrap=True,
        spacing=10,
        run_spacing=10,
    )

    quick_buttons_row = ft.Row(
        wrap=True,
        spacing=8,
        run_spacing=8,
    )

    export_status_icon = ft.Icon(
        ft.Icons.DOWNLOAD_DONE_OUTLINED,
        size=18,
        color=SUCCESS,
    )

    export_status_text = ft.Text(
        "",
        size=10,
        color=_c_text(page),
        weight=ft.FontWeight.W_700,
    )

    export_status_box = ft.Container(
        visible=False,
        padding=ft.Padding(12, 9, 12, 9),
        border_radius=12,
        bgcolor=ft.Colors.with_opacity(0.10, SUCCESS),
        border=ft.Border.all(
            1,
            ft.Colors.with_opacity(0.28, SUCCESS),
        ),
        content=ft.Row(
            spacing=8,
            controls=[
                export_status_icon,
                ft.Container(
                    expand=True,
                    content=export_status_text,
                ),
            ],
        ),
    )

    # -----------------------------------------------------
    # Navegación y detalle
    # -----------------------------------------------------

    def open_result(item: dict):
        def handler(_=None):
            page.data["scan_result"] = item
            page.data["last_scan_id"] = item.get("scan_id")

            thumbnail = _read_thumbnail(item.get("saved_image_path"))

            if thumbnail:
                page.data["scan_image_bytes"] = thumbnail
            else:
                page.data.pop("scan_image_bytes", None)

            _nav(page, "/result")

        return handler

    def show_detail(item: dict) -> None:
        image_bytes = _read_thumbnail(item.get("saved_image_path"))
        sync_text, sync_icon, sync_color = _sync_label(item)
        item_color = _color_for_item(item)

        if image_bytes:
            image_control: ft.Control = ft.Image(
                src=image_bytes,
                width=330 if not is_mobile else 280,
                height=300 if not is_mobile else 240,
                fit=ft.BoxFit.CONTAIN,
                border_radius=18,
                gapless_playback=True,
            )
        else:
            image_control = ft.Container(
                width=330 if not is_mobile else 280,
                height=300 if not is_mobile else 240,
                border_radius=18,
                bgcolor=ft.Colors.with_opacity(0.10, BRAND_GREEN),
                alignment=ft.Alignment(0, 0),
                content=ft.Icon(
                    ft.Icons.IMAGE_NOT_SUPPORTED_OUTLINED,
                    color=BRAND_GREEN,
                    size=60,
                ),
            )

        details = ft.Column(
            spacing=9,
            controls=[
                ft.Text(
                    _display_label(item),
                    size=20,
                    color=item_color,
                    weight=ft.FontWeight.W_900,
                ),
                ft.Text(
                    _format_datetime(item.get("created_at")),
                    size=11,
                    color=_c_muted(page),
                ),
                ft.Divider(color=_c_border(page)),
                ft.Text(
                    f"Confianza: {_safe_float(item.get('confidence')) * 100:.2f}%",
                    size=12,
                    color=_c_text(page),
                    weight=ft.FontWeight.W_800,
                ),
                ft.Text(
                    f"Margen: {_safe_float(item.get('margin')) * 100:.2f}%",
                    size=11,
                    color=_c_text(page),
                ),
                ft.Text(
                    "Evaluación confiable"
                    if item.get("is_reliable", False)
                    else "Resultado no concluyente",
                    size=11,
                    color=item_color,
                    weight=ft.FontWeight.W_700,
                ),
                ft.Row(
                    visible=ENABLE_CLOUD_SYNC,
                    spacing=6,
                    controls=[
                        ft.Icon(sync_icon, size=16, color=sync_color),
                        ft.Text(sync_text, size=10, color=sync_color),
                    ],
                ),
                ft.Text(
                    _model_label(item),
                    size=10,
                    color=_c_muted(page),
                ),
                ft.Text(
                    "Recomendación",
                    size=11,
                    color=_c_text(page),
                    weight=ft.FontWeight.W_900,
                ),
                ft.Text(
                    str(item.get("recommended_action") or "Sin recomendación registrada."),
                    size=11,
                    color=_c_muted(page),
                ),
            ],
        )

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Text(
                        "Detalle del análisis",
                        weight=ft.FontWeight.W_900,
                        color=_c_text(page),
                    ),
                    ft.IconButton(
                        icon=ft.Icons.CLOSE,
                        on_click=lambda _: _close_dialog(page, dialog),
                    ),
                ],
            ),
            content=ft.Container(
                width=780,
                content=(
                    ft.Column(
                        scroll=ft.ScrollMode.AUTO,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[image_control, details],
                    )
                    if is_mobile
                    else ft.Row(
                        spacing=20,
                        vertical_alignment=ft.CrossAxisAlignment.START,
                        controls=[image_control, ft.Container(expand=True, content=details)],
                    )
                ),
            ),
            actions=[
                ft.TextButton(
                    adaptive=False,
                    content="ABRIR RESULTADO COMPLETO",
                    icon=ft.Icons.OPEN_IN_FULL,
                    on_click=open_result(item),
                ),
                ft.FilledButton(
                    adaptive=False,
                    content="CERRAR",
                    on_click=lambda _: _close_dialog(page, dialog),
                    style=ft.ButtonStyle(
                        bgcolor=BRAND_DARK,
                        color=ft.Colors.WHITE,
                    ),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        page.show_dialog(dialog)

    # -----------------------------------------------------
    # Eliminación
    # -----------------------------------------------------

    def confirm_delete(item: dict) -> None:
        sync_text, _, _ = _sync_label(item)

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(
                "Eliminar análisis",
                weight=ft.FontWeight.W_900,
                color=_c_text(page),
            ),
            content=ft.Column(
                tight=True,
                spacing=10,
                controls=[
                    ft.Text(
                        "¿Deseas eliminar este análisis del dispositivo?",
                        color=_c_text(page),
                    ),
                    ft.Text(
                        "Se eliminará el registro de SQLite y la fotografía local administrada por Avoruna.",
                        size=11,
                        color=_c_muted(page),
                    ),
                    ft.Container(
                        visible=ENABLE_CLOUD_SYNC,
                        padding=10,
                        border_radius=12,
                        bgcolor=ft.Colors.with_opacity(0.08, WARNING),
                        content=ft.Text(
                            f"Estado en la nube: {sync_text}. Esta acción no elimina la copia de Firebase.",
                            size=10,
                            color=_c_text(page),
                        ),
                    ),
                ],
            ),
            actions=[
                ft.TextButton(
                    adaptive=False,
                    content="CANCELAR",
                    on_click=lambda _: _close_dialog(page, dialog),
                ),
                ft.FilledButton(
                    adaptive=False,
                    content="ELIMINAR",
                    icon=ft.Icons.DELETE_OUTLINE,
                    style=ft.ButtonStyle(
                        bgcolor=DANGER,
                        color=ft.Colors.WHITE,
                    ),
                    on_click=lambda _: execute_delete(item, dialog),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        page.show_dialog(dialog)

    def execute_delete(item: dict, dialog: ft.AlertDialog) -> None:
        try:
            _delete_scan_local(item)
            _close_dialog(page, dialog)
            refresh_history()
            _show_message(page, "El análisis se eliminó del dispositivo.")
        except Exception as exception:
            _show_message(
                page,
                f"No se pudo eliminar el análisis: {exception}",
                success=False,
            )

    # -----------------------------------------------------
    # Construcción de tarjetas
    # -----------------------------------------------------

    def build_card(item: dict) -> ft.Control:
        item_color = _color_for_item(item)
        thumbnail_bytes = _read_thumbnail(item.get("saved_image_path"))
        sync_text, sync_icon, sync_color = _sync_label(item)

        thumbnail_size = 62 if is_mobile else 68

        if thumbnail_bytes:
            thumbnail: ft.Control = ft.Image(
                src=thumbnail_bytes,
                width=thumbnail_size,
                height=thumbnail_size,
                fit=ft.BoxFit.COVER,
                border_radius=12,
                gapless_playback=True,
            )
        else:
            thumbnail = ft.Container(
                width=thumbnail_size,
                height=thumbnail_size,
                border_radius=12,
                bgcolor=ft.Colors.with_opacity(0.10, BRAND_GREEN),
                alignment=ft.Alignment(0, 0),
                content=ft.Icon(
                    ft.Icons.IMAGE_OUTLINED,
                    color=BRAND_GREEN,
                    size=25,
                ),
            )

        menu = ft.PopupMenuButton(
            icon=ft.Icons.MORE_VERT,
            tooltip="Opciones del análisis",
            items=[
                ft.PopupMenuItem(
                    content=ft.Text("Ver detalle"),
                    icon=ft.Icons.VISIBILITY_OUTLINED,
                    on_click=lambda _: show_detail(item),
                ),
                ft.PopupMenuItem(
                    content=ft.Text("Abrir resultado completo"),
                    icon=ft.Icons.OPEN_IN_FULL,
                    on_click=open_result(item),
                ),
                ft.PopupMenuItem(
                    content=ft.Text("Eliminar del dispositivo"),
                    icon=ft.Icons.DELETE_OUTLINE,
                    on_click=lambda _: confirm_delete(item),
                ),
            ],
        )

        secondary_metadata: list[ft.Control] = [
            ft.Row(
                spacing=4,
                controls=[
                    ft.Icon(
                        ft.Icons.PSYCHOLOGY_OUTLINED,
                        size=13,
                        color=_c_muted(page),
                    ),
                    ft.Text(
                        _model_label(item),
                        size=9,
                        color=_c_muted(page),
                    ),
                ],
            )
        ]

        if ENABLE_CLOUD_SYNC:
            secondary_metadata.append(
                ft.Row(
                    spacing=4,
                    controls=[
                        ft.Icon(sync_icon, size=13, color=sync_color),
                        ft.Text(sync_text, size=9, color=sync_color),
                    ],
                )
            )

        metadata = ft.Column(
            expand=True,
            spacing=2,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Container(
                            expand=True,
                            content=ft.Text(
                                _display_label(item),
                                size=14,
                                color=item_color,
                                weight=ft.FontWeight.W_900,
                                max_lines=1,
                                overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                        ),
                        ft.Container(
                            padding=ft.Padding(7, 3, 7, 3),
                            border_radius=9,
                            bgcolor=ft.Colors.with_opacity(0.10, item_color),
                            content=ft.Text(
                                f"{_safe_float(item.get('confidence')) * 100:.2f}%",
                                size=9,
                                color=item_color,
                                weight=ft.FontWeight.W_900,
                            ),
                        ),
                    ],
                ),
                ft.Text(
                    _format_datetime(item.get("created_at")),
                    size=9,
                    color=_c_muted(page),
                ),
                ft.Row(
                    wrap=True,
                    spacing=10,
                    run_spacing=2,
                    controls=secondary_metadata,
                ),
            ],
        )

        return ft.Container(
            padding=ft.Padding(9, 8, 5, 8),
            border_radius=15,
            bgcolor=_c_surface(page),
            border=ft.Border.all(1, _c_border(page)),
            ink=True,
            on_click=open_result(item),
            content=ft.Row(
                spacing=11,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    thumbnail,
                    metadata,
                    ft.IconButton(
                        icon=ft.Icons.VISIBILITY_OUTLINED,
                        tooltip="Ver detalle ampliado",
                        icon_size=19,
                        on_click=lambda _: show_detail(item),
                    ),
                    menu,
                ],
            ),
        )

    def build_empty_state() -> ft.Control:
        return ft.Container(
            padding=ft.Padding(28, 34, 28, 34),
            border_radius=22,
            bgcolor=_c_surface(page),
            border=ft.Border.all(1, _c_border(page)),
            alignment=ft.Alignment(0, 0),
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
                controls=[
                    ft.Icon(
                        ft.Icons.SEARCH_OFF
                        if all_history
                        else ft.Icons.HISTORY_TOGGLE_OFF,
                        size=52,
                        color=BRAND_GREEN,
                    ),
                    ft.Text(
                        "No se encontraron análisis"
                        if all_history
                        else "Aún no hay análisis guardados",
                        size=17,
                        color=_c_text(page),
                        weight=ft.FontWeight.W_900,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        "Modifica o limpia los filtros para mostrar otros resultados."
                        if all_history
                        else "Los resultados aparecerán aquí después de analizar una fotografía.",
                        size=11,
                        color=_c_muted(page),
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.FilledButton(
                        adaptive=False,
                        content="REALIZAR ANÁLISIS",
                        icon=ft.Icons.PHOTO_CAMERA,
                        on_click=lambda _: _nav(page, "/scan/camera"),
                        style=ft.ButtonStyle(
                            bgcolor=BRAND_GREEN,
                            color=ft.Colors.WHITE,
                        ),
                    ),
                ],
            ),
        )

    # -----------------------------------------------------
    # Resumen, botones rápidos y filtros
    # -----------------------------------------------------

    def summary_card(
        label: str,
        value: int,
        icon: str,
        color: str,
    ) -> ft.Control:
        return ft.Container(
            width=150 if not is_mobile else 135,
            padding=ft.Padding(9, 7, 9, 7),
            border_radius=15,
            bgcolor=_c_surface(page),
            border=ft.Border.all(1, _c_border(page)),
            content=ft.Row(
                spacing=9,
                controls=[
                    ft.Container(
                        width=30,
                        height=30,
                        border_radius=10,
                        bgcolor=ft.Colors.with_opacity(0.12, color),
                        alignment=ft.Alignment(0, 0),
                        content=ft.Icon(icon, size=16, color=color),
                    ),
                    ft.Column(
                        spacing=1,
                        controls=[
                            ft.Text(
                                str(value),
                                size=15,
                                color=_c_text(page),
                                weight=ft.FontWeight.W_900,
                            ),
                            ft.Text(label, size=8, color=_c_muted(page)),
                        ],
                    ),
                ],
            ),
        )

    def set_quick_filter(value: str) -> None:
        state["quick_filter"] = value
        apply_filters()

    def rebuild_quick_buttons() -> None:
        counts = _summary_counts(all_history)

        button_data = [
            ("all", f"Todos ({counts['total']})"),
            (
                "lista_para_cosecha",
                f"Lista para cosecha ({counts['lista_para_cosecha']})",
            ),
            ("en_proceso", f"En proceso ({counts['en_proceso']})"),
            ("aun_no_lista", f"Aún no lista ({counts['aun_no_lista']})"),
            ("inconclusive", f"No concluyente ({counts['inconclusive']})"),
        ]

        controls: list[ft.Control] = []

        for key, label in button_data:
            selected = state["quick_filter"] == key
            controls.append(
                ft.OutlinedButton(
                    adaptive=False,
                    content=label,
                    height=36,
                    on_click=lambda _, selected_key=key: set_quick_filter(selected_key),
                    style=ft.ButtonStyle(
                        bgcolor=(BRAND_LIGHT if selected else _c_surface(page)),
                        color=(BRAND_DARK if selected else _c_muted(page)),
                        side=ft.BorderSide(
                            1.2,
                            BRAND_GREEN if selected else _c_border(page),
                        ),
                        shape=ft.RoundedRectangleBorder(radius=12),
                        padding=ft.Padding(12, 0, 12, 0),
                        text_style=ft.TextStyle(
                            size=10,
                            weight=(
                                ft.FontWeight.W_800
                                if selected
                                else ft.FontWeight.W_600
                            ),
                        ),
                    ),
                )
            )

        quick_buttons_row.controls = controls

    def current_filter_state() -> dict:
        return {
            "quick_filter": state["quick_filter"],
            "search": search_field.value or "",
            "date_from": date_from_field.value or "",
            "date_to": date_to_field.value or "",
            "confidence_min": confidence_min_field.value or "",
            "confidence_max": confidence_max_field.value or "",
            "sync_status": (sync_dropdown.value or "all") if ENABLE_CLOUD_SYNC else "all",
            "order": order_dropdown.value or "newest",
        }

    def apply_filters(_=None) -> None:
        nonlocal filtered_history

        filter_error_text.visible = False
        filter_error_text.value = ""

        try:
            date_from = _parse_filter_date(date_from_field.value)
            date_to = _parse_filter_date(date_to_field.value, end_of_day=True)

            confidence_min = (
                _safe_float(confidence_min_field.value) / 100
                if str(confidence_min_field.value or "").strip()
                else None
            )
            confidence_max = (
                _safe_float(confidence_max_field.value) / 100
                if str(confidence_max_field.value or "").strip()
                else None
            )

            if confidence_min is not None and not 0 <= confidence_min <= 1:
                raise ValueError("La confianza mínima debe estar entre 0 y 100.")

            if confidence_max is not None and not 0 <= confidence_max <= 1:
                raise ValueError("La confianza máxima debe estar entre 0 y 100.")

            if (
                confidence_min is not None
                and confidence_max is not None
                and confidence_min > confidence_max
            ):
                raise ValueError(
                    "La confianza mínima no puede ser mayor que la máxima."
                )

            if date_from and date_to and date_from > date_to:
                raise ValueError("La fecha inicial no puede ser mayor que la final.")

        except ValueError as exception:
            filter_error_text.value = str(exception)
            filter_error_text.visible = True
            page.update()
            return

        query = str(search_field.value or "").strip().lower()
        quick_filter = state["quick_filter"]
        sync_filter = (
            str(sync_dropdown.value or "all")
            if ENABLE_CLOUD_SYNC
            else "all"
        )

        result: list[dict] = []

        for item in all_history:
            item_key = _filter_key(item)

            if quick_filter != "all" and item_key != quick_filter:
                continue

            item_datetime = _parse_datetime(item.get("created_at"))

            if date_from and (item_datetime is None or item_datetime < date_from):
                continue

            if date_to and (item_datetime is None or item_datetime > date_to):
                continue

            confidence = _safe_float(item.get("confidence"))

            if confidence_min is not None and confidence < confidence_min:
                continue

            if confidence_max is not None and confidence > confidence_max:
                continue

            item_sync_status = str(item.get("sync_status") or "pending").lower()

            if sync_filter != "all" and item_sync_status != sync_filter:
                continue

            if query:
                searchable_text = " ".join(
                    [
                        _display_label(item),
                        str(item.get("label_key") or ""),
                        _format_datetime(item.get("created_at")),
                        str(item.get("created_at") or ""),
                        f"{confidence * 100:.2f}",
                        str(item.get("recommended_action") or ""),
                        str(item.get("scan_id") or ""),
                        _model_label(item),
                        _sync_label(item)[0],
                    ]
                ).lower()

                if query not in searchable_text:
                    continue

            result.append(item)

        order = str(order_dropdown.value or "newest")

        if order == "oldest":
            result.sort(
                key=lambda item: _parse_datetime(item.get("created_at"))
                or datetime.min
            )
        elif order == "confidence_desc":
            result.sort(
                key=lambda item: _safe_float(item.get("confidence")),
                reverse=True,
            )
        elif order == "confidence_asc":
            result.sort(key=lambda item: _safe_float(item.get("confidence")))
        elif order == "result":
            result.sort(key=lambda item: _display_label(item).lower())
        else:
            result.sort(
                key=lambda item: _parse_datetime(item.get("created_at"))
                or datetime.min,
                reverse=True,
            )

        filtered_history = result
        rebuild_history_controls()
        page.update()

    def rebuild_history_controls() -> None:
        counts = _summary_counts(filtered_history)

        summary_row.controls = [
            summary_card(
                "Resultados visibles",
                counts["total"],
                ft.Icons.ANALYTICS_OUTLINED,
                BRAND_GREEN,
            ),
            summary_card(
                "Listas para cosecha",
                counts["lista_para_cosecha"],
                ft.Icons.CHECK_CIRCLE_OUTLINE,
                SUCCESS,
            ),
            summary_card(
                "En proceso",
                counts["en_proceso"],
                ft.Icons.TIMELAPSE,
                WARNING,
            ),
            summary_card(
                "Aún no listas",
                counts["aun_no_lista"],
                ft.Icons.CANCEL_OUTLINED,
                DANGER,
            ),
        ]

        results_count_text.value = (
            f"Mostrando {len(filtered_history)} de {len(all_history)} análisis"
            if all_history
            else "Sin registros almacenados"
        )

        active_filter_text.value = _filter_description(current_filter_state())

        if filtered_history:
            list_view.controls = [build_card(item) for item in filtered_history]
        else:
            list_view.controls = [build_empty_state()]

        rebuild_quick_buttons()

    def clear_filters(_=None) -> None:
        state["quick_filter"] = "all"
        search_field.value = ""
        date_from_field.value = ""
        date_to_field.value = ""
        confidence_min_field.value = ""
        confidence_max_field.value = ""
        sync_dropdown.value = "all"
        order_dropdown.value = "newest"
        filter_error_text.visible = False
        apply_filters()

    def toggle_advanced_filters(_=None) -> None:
        state["advanced_visible"] = not state["advanced_visible"]
        advanced_panel.visible = state["advanced_visible"]
        advanced_button.icon = (
            ft.Icons.EXPAND_LESS
            if state["advanced_visible"]
            else ft.Icons.TUNE
        )
        advanced_button.content = (
            "OCULTAR FILTROS"
            if state["advanced_visible"]
            else "FILTROS AVANZADOS"
        )
        page.update()

    # -----------------------------------------------------
    # Exportación
    # -----------------------------------------------------

    def set_export_status(
        message: str,
        *,
        success: bool = True,
        loading: bool = False,
    ) -> None:
        export_status_box.visible = True
        export_status_text.value = message

        if loading:
            export_status_icon.name = ft.Icons.HOURGLASS_TOP
            export_status_icon.color = WARNING
            export_status_box.bgcolor = ft.Colors.with_opacity(0.10, WARNING)
            export_status_box.border = ft.Border.all(
                1,
                ft.Colors.with_opacity(0.28, WARNING),
            )
        elif success:
            export_status_icon.name = ft.Icons.DOWNLOAD_DONE_OUTLINED
            export_status_icon.color = SUCCESS
            export_status_box.bgcolor = ft.Colors.with_opacity(0.10, SUCCESS)
            export_status_box.border = ft.Border.all(
                1,
                ft.Colors.with_opacity(0.28, SUCCESS),
            )
        else:
            export_status_icon.name = ft.Icons.ERROR_OUTLINE
            export_status_icon.color = DANGER
            export_status_box.bgcolor = ft.Colors.with_opacity(0.10, DANGER)
            export_status_box.border = ft.Border.all(
                1,
                ft.Colors.with_opacity(0.28, DANGER),
            )

        page.update()

    async def download_generated_file(file_path: Path) -> None:
        extension = file_path.suffix.lower().lstrip(".")

        try:
            saved_path = await ft.FilePicker().save_file(
                dialog_title="Guardar reporte Avoruna",
                file_name=file_path.name,
                file_type=ft.FilePickerFileType.CUSTOM,
                allowed_extensions=[extension],
                src_bytes=file_path.read_bytes(),
            )
        except Exception as exception:
            set_export_status(
                f"El reporte se generó, pero no pudo descargarse: {exception}",
                success=False,
            )
            _show_message(
                page,
                f"No se pudo descargar el archivo: {exception}",
                success=False,
            )
            return

        if page.web:
            message = (
                f"Descarga completada: {file_path.name}. "
                "Revisa la carpeta Descargas de tu navegador."
            )
        elif saved_path:
            message = f"Archivo guardado en: {saved_path}"
        else:
            message = "La descarga fue cancelada."

        set_export_status(message, success=bool(page.web or saved_path))
        _show_message(
            page,
            message,
            success=bool(page.web or saved_path),
        )

    async def export_excel_async() -> None:
        if not filtered_history:
            _show_message(
                page,
                "No hay análisis visibles para exportar.",
                success=False,
            )
            return

        set_export_status("Generando reporte Excel...", loading=True)

        try:
            file_path = await asyncio.to_thread(
                _build_excel_report,
                list(filtered_history),
                current_filter_state(),
                str(
                    page.data.get("firebase_name")
                    or page.data.get("reg_name")
                    or ""
                ),
            )
            await download_generated_file(file_path)
        except Exception as exception:
            set_export_status(
                f"No se pudo generar el Excel: {exception}",
                success=False,
            )
            _show_message(
                page,
                f"No se pudo generar el Excel: {exception}",
                success=False,
            )

    async def export_pdf_async() -> None:
        if not filtered_history:
            _show_message(
                page,
                "No hay análisis visibles para exportar.",
                success=False,
            )
            return

        set_export_status("Generando reporte PDF...", loading=True)

        try:
            file_path = await asyncio.to_thread(
                _build_pdf_report,
                list(filtered_history),
                current_filter_state(),
                str(
                    page.data.get("firebase_name")
                    or page.data.get("reg_name")
                    or ""
                ),
            )
            await download_generated_file(file_path)
        except Exception as exception:
            set_export_status(
                f"No se pudo generar el PDF: {exception}",
                success=False,
            )
            _show_message(
                page,
                f"No se pudo generar el PDF: {exception}",
                success=False,
            )

    def export_excel(_=None) -> None:
        page.run_task(export_excel_async)

    def export_pdf(_=None) -> None:
        page.run_task(export_pdf_async)

    # -----------------------------------------------------
    # Sincronización opcional
    # -----------------------------------------------------

    sync_button_text = ft.Text(
        "SINCRONIZAR",
        weight=ft.FontWeight.W_800,
    )

    sync_button = ft.OutlinedButton(
        visible=ENABLE_CLOUD_SYNC,
        adaptive=False,
        content=sync_button_text,
        icon=ft.Icons.CLOUD_UPLOAD_OUTLINED,
        height=40,
        style=ft.ButtonStyle(
            color=BRAND_DARK,
            side=ft.BorderSide(1.2, BRAND_GREEN),
            shape=ft.RoundedRectangleBorder(radius=12),
        ),
    )

    async def run_sync() -> None:
        if sync_pending_history is None:
            _show_message(
                page,
                "Todavía no existe services/cloud_sync_service.py. Implementa ese servicio para activar la sincronización.",
                success=False,
            )
            return

        sync_button.disabled = True
        sync_button.icon = ft.Icons.SYNC
        sync_button_text.value = "SINCRONIZANDO..."
        page.update()

        try:
            result = await asyncio.to_thread(sync_pending_history, page)
            synced = int(result.get("synced", 0))
            failed = int(result.get("failed", 0))

            refresh_history()

            if failed:
                _show_message(
                    page,
                    f"{synced} análisis sincronizados y {failed} con error.",
                    success=False,
                )
            else:
                _show_message(
                    page,
                    f"{synced} análisis sincronizados correctamente.",
                )
        except Exception as exception:
            _show_message(
                page,
                f"No se pudo sincronizar: {exception}",
                success=False,
            )
        finally:
            sync_button.disabled = False
            sync_button.icon = ft.Icons.CLOUD_UPLOAD_OUTLINED
            sync_button_text.value = "SINCRONIZAR"
            page.update()

    sync_button.on_click = lambda _: page.run_task(run_sync)

    # -----------------------------------------------------
    # Recarga del historial
    # -----------------------------------------------------

    def refresh_history(_=None) -> None:
        nonlocal all_history
        all_history = get_scan_history(limit=500)
        apply_filters()

    # -----------------------------------------------------
    # Asignar eventos de filtro
    # -----------------------------------------------------

    search_field.on_change = apply_filters
    date_from_field.on_change = apply_filters
    date_to_field.on_change = apply_filters
    confidence_min_field.on_change = apply_filters
    confidence_max_field.on_change = apply_filters
    if ENABLE_CLOUD_SYNC:
        sync_dropdown.on_change = apply_filters
    order_dropdown.on_change = apply_filters

    advanced_button = ft.OutlinedButton(
        adaptive=False,
        content="FILTROS AVANZADOS",
        icon=ft.Icons.TUNE,
        height=40,
        on_click=toggle_advanced_filters,
        style=ft.ButtonStyle(
            color=_c_text(page),
            side=ft.BorderSide(1, _c_border(page)),
            shape=ft.RoundedRectangleBorder(radius=12),
        ),
    )

    export_menu = ft.PopupMenuButton(
        icon=ft.Icons.DOWNLOAD_OUTLINED,
        tooltip="Exportar historial filtrado",
        items=[
            ft.PopupMenuItem(
                content=ft.Text("Descargar Excel"),
                icon=ft.Icons.TABLE_VIEW_OUTLINED,
                on_click=export_excel,
            ),
            ft.PopupMenuItem(
                content=ft.Text("Descargar PDF"),
                icon=ft.Icons.PICTURE_AS_PDF_OUTLINED,
                on_click=export_pdf,
            ),
        ],
    )

    # -----------------------------------------------------
    # Estructura visual
    # -----------------------------------------------------

    header = ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.IconButton(
                icon=ft.Icons.ARROW_BACK,
                tooltip="Volver",
                on_click=lambda _: _nav(page, "/home"),
            ),
            ft.Text(
                "Historial de análisis",
                size=18 if is_mobile else 20,
                color=_c_text(page),
                weight=ft.FontWeight.W_900,
            ),
            ft.IconButton(
                icon=ft.Icons.ADD_A_PHOTO_OUTLINED,
                tooltip="Nuevo análisis",
                on_click=lambda _: _nav(page, "/scan/camera"),
            ),
        ],
    )

    action_row = ft.Row(
        wrap=True,
        spacing=7,
        run_spacing=7,
        controls=[
            advanced_button,
            ft.OutlinedButton(
                adaptive=False,
                content="LIMPIAR",
                icon=ft.Icons.FILTER_ALT_OFF_OUTLINED,
                height=40,
                on_click=clear_filters,
                style=ft.ButtonStyle(
                    color=_c_muted(page),
                    side=ft.BorderSide(1, _c_border(page)),
                    shape=ft.RoundedRectangleBorder(radius=12),
                ),
            ),
            sync_button,
            ft.FilledButton(
                adaptive=False,
                content="EXCEL",
                icon=ft.Icons.TABLE_VIEW_OUTLINED,
                height=40,
                on_click=export_excel,
                style=ft.ButtonStyle(
                    bgcolor=BRAND_DARK,
                    color=ft.Colors.WHITE,
                    shape=ft.RoundedRectangleBorder(radius=12),
                ),
            ),
            ft.OutlinedButton(
                adaptive=False,
                content="PDF",
                icon=ft.Icons.PICTURE_AS_PDF_OUTLINED,
                height=40,
                on_click=export_pdf,
                style=ft.ButtonStyle(
                    color=BRAND_DARK,
                    side=ft.BorderSide(1.2, BRAND_GREEN),
                    shape=ft.RoundedRectangleBorder(radius=12),
                ),
            ),
            ft.IconButton(
                icon=ft.Icons.REFRESH,
                tooltip="Actualizar historial",
                on_click=refresh_history,
            ),
        ],
    )

    search_toolbar: ft.Control

    if is_mobile:
        search_toolbar = ft.Column(
            spacing=8,
            controls=[
                search_field,
                action_row,
            ],
        )
    else:
        search_toolbar = ft.Row(
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                search_field,
                action_row,
            ],
        )

    content = ft.Container(
        expand=True,
        padding=ft.Padding(
            14 if is_mobile else 18,
            10,
            14 if is_mobile else 18,
            24,
        ),
        content=ft.Column(
            expand=True,
            spacing=9,
            controls=[
                header,
                summary_row,
                search_toolbar,
                quick_buttons_row,
                advanced_panel,
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    wrap=True,
                    controls=[
                        results_count_text,
                        active_filter_text,
                    ],
                ),
                export_status_box,
                ft.Divider(height=1, color=_c_border(page)),
                ft.Container(
                    expand=True,
                    border_radius=14,
                    content=list_view,
                ),
            ],
        ),
    )

    rebuild_history_controls()

    root = build_app_shell(page, content)

    return ft.View(
        route="/history",
        controls=[
            ft.SafeArea(
                expand=True,
                content=root,
            ),
        ],
    )
