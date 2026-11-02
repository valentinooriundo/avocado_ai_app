from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np


PROJECT_DIR = Path(__file__).resolve().parents[2]

CAMERA_INDEX = int(
    os.getenv("AVORUNA_CAMERA_INDEX", "0")
)


def _focus_status(
    frame,
) -> tuple[str, tuple[int, int, int], bool]:
    gray = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2GRAY,
    )
    lap_var = float(
        cv2.Laplacian(
            gray,
            cv2.CV_64F,
        ).var()
    )

    if lap_var >= 120:
        return (
            "Nítido",
            (57, 216, 12),
            True,
        )

    if lap_var >= 70:
        return (
            "Aceptable",
            (255, 193, 7),
            True,
        )

    return (
        "Imagen borrosa",
        (244, 67, 54),
        False,
    )


def _lighting_status(
    frame,
) -> tuple[str, tuple[int, int, int], bool]:
    gray = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2GRAY,
    )
    mean_val = float(
        np.mean(gray)
    )

    if 95 <= mean_val <= 185:
        return (
            "Iluminación correcta",
            (57, 216, 12),
            True,
        )

    if mean_val < 95:
        return (
            "Baja luz",
            (255, 193, 7),
            False,
        )

    return (
        "Exceso de brillo",
        (244, 67, 54),
        False,
    )


def _assess_quality(
    frame,
) -> dict:
    (
        focus_text,
        focus_color,
        focus_ok,
    ) = _focus_status(frame)

    (
        light_text,
        light_color,
        light_ok,
    ) = _lighting_status(frame)

    return {
        "focus_text": focus_text,
        "focus_color": focus_color,
        "focus_ok": focus_ok,
        "light_text": light_text,
        "light_color": light_color,
        "light_ok": light_ok,
        "acceptable": (
            focus_ok
            and light_ok
        ),
    }


def _draw_overlay(
    original_frame,
):
    # La calidad se calcula sobre la imagen original,
    # antes de agregar textos, marcos o sombreado.
    quality = _assess_quality(
        original_frame
    )

    frame = original_frame.copy()
    height, width = frame.shape[:2]

    box_width = int(
        width * 0.42
    )
    box_height = int(
        height * 0.58
    )

    x1 = (
        width - box_width
    ) // 2
    y1 = (
        height - box_height
    ) // 2
    x2 = x1 + box_width
    y2 = y1 + box_height

    overlay = frame.copy()
    cv2.rectangle(
        overlay,
        (x1, y1),
        (x2, y2),
        (57, 216, 12),
        2,
    )

    shade = frame.copy()
    cv2.rectangle(
        shade,
        (0, 0),
        (width, y1),
        (0, 0, 0),
        -1,
    )
    cv2.rectangle(
        shade,
        (0, y2),
        (width, height),
        (0, 0, 0),
        -1,
    )
    cv2.rectangle(
        shade,
        (0, y1),
        (x1, y2),
        (0, 0, 0),
        -1,
    )
    cv2.rectangle(
        shade,
        (x2, y1),
        (width, y2),
        (0, 0, 0),
        -1,
    )

    frame = cv2.addWeighted(
        shade,
        0.18,
        overlay,
        0.82,
        0,
    )

    cv2.putText(
        frame,
        "Ubique una sola palta dentro del recuadro",
        (24, 36),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.75,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )

    cv2.putText(
        frame,
        f"Enfoque: {quality['focus_text']}",
        (24, height - 78),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.68,
        quality["focus_color"],
        2,
        cv2.LINE_AA,
    )

    cv2.putText(
        frame,
        f"Iluminacion: {quality['light_text']}",
        (24, height - 48),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.68,
        quality["light_color"],
        2,
        cv2.LINE_AA,
    )

    cv2.putText(
        frame,
        "ESPACIO: capturar | R: repetir | ESC: salir",
        (24, height - 16),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.62,
        (230, 230, 230),
        2,
        cv2.LINE_AA,
    )

    return frame, quality


def _draw_frozen_preview(
    frozen_frame,
    quality: dict,
    warning_text: str = "",
):
    display = frozen_frame.copy()
    height, _ = display.shape[:2]

    cv2.putText(
        display,
        f"Enfoque: {quality['focus_text']}",
        (24, 36),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.68,
        quality["focus_color"],
        2,
        cv2.LINE_AA,
    )

    cv2.putText(
        display,
        f"Iluminacion: {quality['light_text']}",
        (24, 66),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.68,
        quality["light_color"],
        2,
        cv2.LINE_AA,
    )

    if warning_text:
        cv2.putText(
            display,
            warning_text,
            (24, height - 48),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.62,
            (244, 67, 54),
            2,
            cv2.LINE_AA,
        )

    cv2.putText(
        display,
        "ESPACIO: usar imagen | R: repetir | ESC: salir",
        (24, height - 16),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.62,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )

    return display


def capture_image_with_assistance() -> str | None:
    captures_dir = (
        PROJECT_DIR
        / "captures"
        / "camera"
    )
    captures_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    camera = cv2.VideoCapture(
        CAMERA_INDEX
    )

    if not camera.isOpened():
        return None

    window_name = (
        "Avoruna - Captura asistida"
    )

    frozen_frame = None
    frozen_quality = None
    accepted_frame = None
    warning_text = ""

    try:
        while True:
            if frozen_frame is None:
                ok, frame = camera.read()

                if not ok:
                    break

                (
                    display,
                    live_quality,
                ) = _draw_overlay(
                    frame
                )
            else:
                display = _draw_frozen_preview(
                    frozen_frame,
                    frozen_quality,
                    warning_text,
                )

            cv2.imshow(
                window_name,
                display,
            )

            key = (
                cv2.waitKey(1)
                & 0xFF
            )

            if key == 27:
                break

            if key in (
                ord("r"),
                ord("R"),
            ):
                frozen_frame = None
                frozen_quality = None
                warning_text = ""
                continue

            if key == 32:
                if frozen_frame is None:
                    frozen_frame = (
                        frame.copy()
                    )
                    frozen_quality = (
                        live_quality
                    )
                    warning_text = ""
                    continue

                if not frozen_quality[
                    "acceptable"
                ]:
                    warning_text = (
                        "Mejore el enfoque o la iluminacion "
                        "y presione R para repetir."
                    )
                    continue

                accepted_frame = (
                    frozen_frame.copy()
                )
                break

    finally:
        camera.release()

        try:
            cv2.destroyAllWindows()
        except Exception:
            pass

    if accepted_frame is None:
        return None

    file_path = captures_dir / (
        "camera_"
        f"{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        ".jpg"
    )

    saved = cv2.imwrite(
        str(file_path),
        accepted_frame,
    )

    if not saved:
        raise RuntimeError(
            "No se pudo guardar la fotografía capturada."
        )

    return str(
        file_path.resolve()
    )
