from __future__ import annotations

import json
import shutil
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import requests
from PIL import Image, UnidentifiedImageError


# =========================================================
# RUTAS Y CONFIGURACIÓN
# =========================================================

BASE_DIR = Path(__file__).resolve().parents[2]

APP_DB_PATH = BASE_DIR / "avocado_app.db"
TEMP_SCAN_DIR = BASE_DIR / "captures" / "scan_temp"
WEB_UPLOAD_DIR = BASE_DIR / "src" / "uploads_web"

ALLOWED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
}

MAX_DOWNLOAD_BYTES = 10 * 1024 * 1024

LABEL_META = {
    "aun_no_lista": {
        "label_text": "Aún no lista",
        "color": "red",
        "recommendation": (
            "La palta aún no presenta condiciones "
            "adecuadas para la cosecha. Continúa "
            "con el seguimiento."
        ),
    },
    "en_proceso": {
        "label_text": "En proceso",
        "color": "amber",
        "recommendation": (
            "La palta presenta un estado intermedio "
            "de madurez. Realiza una nueva evaluación "
            "antes de cosechar."
        ),
    },
    "lista_para_cosecha": {
        "label_text": "Lista para cosecha",
        "color": "green",
        "recommendation": (
            "La palta presenta condiciones favorables "
            "para programar la cosecha."
        ),
    },
}


# =========================================================
# DIRECTORIOS Y BASE DE DATOS
# =========================================================

def ensure_scan_directories() -> None:
    TEMP_SCAN_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )
    WEB_UPLOAD_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


def _ensure_scan_history_columns(
    connection: sqlite3.Connection,
) -> None:
    """
    Agrega columnas nuevas cuando la tabla ya existía
    en una versión anterior de la aplicación.
    """

    existing_columns = {
        row[1]
        for row in connection.execute(
            "PRAGMA table_info(scan_history)"
        ).fetchall()
    }

    required_columns = {
        "margin": (
            "ALTER TABLE scan_history "
            "ADD COLUMN margin REAL NOT NULL DEFAULT 0"
        ),
        "is_reliable": (
            "ALTER TABLE scan_history "
            "ADD COLUMN is_reliable INTEGER NOT NULL DEFAULT 0"
        ),
        "status": (
            "ALTER TABLE scan_history "
            "ADD COLUMN status TEXT NOT NULL DEFAULT 'completed'"
        ),
    }

    for column_name, sql in required_columns.items():
        if column_name not in existing_columns:
            connection.execute(sql)


def ensure_scan_table() -> None:
    ensure_scan_directories()

    with sqlite3.connect(APP_DB_PATH) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS scan_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scan_id TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL,
                source_type TEXT NOT NULL,
                source_value TEXT,
                saved_image_path TEXT NOT NULL,
                label_key TEXT NOT NULL,
                label_text TEXT NOT NULL,
                confidence REAL NOT NULL,
                margin REAL NOT NULL DEFAULT 0,
                is_reliable INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'completed',
                scores_json TEXT,
                recommended_action TEXT,
                result_color TEXT,
                inference_mode TEXT NOT NULL
            )
            """
        )

        _ensure_scan_history_columns(
            connection
        )

        connection.commit()


# =========================================================
# VALIDACIÓN Y PREPARACIÓN DE IMÁGENES
# =========================================================

def _safe_extension_from_name(
    name: str,
) -> str:
    suffix = Path(name).suffix.lower()

    if suffix in ALLOWED_EXTENSIONS:
        return suffix

    return ".jpg"


def _validate_image_file(
    image_path: Path,
) -> None:
    if not image_path.exists():
        raise FileNotFoundError(
            f"No existe la imagen: {image_path}"
        )

    if not image_path.is_file():
        raise ValueError(
            f"La ruta no corresponde a un archivo: {image_path}"
        )

    try:
        with Image.open(image_path) as image:
            image.verify()

    except (
        UnidentifiedImageError,
        OSError,
        ValueError,
    ) as exception:
        raise ValueError(
            f"El archivo no es una imagen válida: {image_path}"
        ) from exception


def _copy_image_to_temp(
    source_path: str | Path,
    *,
    prefix: str,
) -> Path:
    ensure_scan_directories()

    source = Path(source_path)
    _validate_image_file(source)

    extension = _safe_extension_from_name(
        source.name
    )

    destination = TEMP_SCAN_DIR / (
        f"{prefix}_"
        f"{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}_"
        f"{uuid.uuid4().hex[:8]}"
        f"{extension}"
    )

    shutil.copy2(
        source,
        destination,
    )

    _validate_image_file(destination)

    return destination


def save_local_image_to_temp(
    source_path: str,
) -> Path:
    return _copy_image_to_temp(
        source_path,
        prefix="scan",
    )


def copy_uploaded_web_image_to_temp(
    source_path: str,
) -> Path:
    return _copy_image_to_temp(
        source_path,
        prefix="web_scan",
    )


def download_image_from_url(
    image_url: str,
    timeout: int = 20,
) -> Path:
    ensure_scan_directories()

    clean_url = (
        image_url or ""
    ).strip()

    parsed = urlparse(clean_url)

    if parsed.scheme not in {
        "http",
        "https",
    }:
        raise ValueError(
            "La URL debe iniciar con http:// o https://"
        )

    extension = _safe_extension_from_name(
        parsed.path or "image.jpg"
    )

    destination = TEMP_SCAN_DIR / (
        "url_scan_"
        f"{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}_"
        f"{uuid.uuid4().hex[:8]}"
        f"{extension}"
    )

    try:
        with requests.get(
            clean_url,
            timeout=timeout,
            stream=True,
        ) as response:
            response.raise_for_status()

            content_type = (
                response.headers.get(
                    "Content-Type",
                    "",
                )
                .split(";")[0]
                .strip()
                .lower()
            )

            if not content_type.startswith(
                "image/"
            ):
                raise ValueError(
                    "La URL no devuelve una imagen válida."
                )

            declared_size = int(
                response.headers.get(
                    "Content-Length",
                    "0",
                )
                or 0
            )

            if declared_size > MAX_DOWNLOAD_BYTES:
                raise ValueError(
                    "La imagen supera el tamaño máximo permitido "
                    "de 10 MB."
                )

            downloaded_bytes = 0

            with destination.open("wb") as file:
                for chunk in response.iter_content(
                    chunk_size=8192
                ):
                    if not chunk:
                        continue

                    downloaded_bytes += len(
                        chunk
                    )

                    if downloaded_bytes > MAX_DOWNLOAD_BYTES:
                        raise ValueError(
                            "La imagen supera el tamaño máximo "
                            "permitido de 10 MB."
                        )

                    file.write(chunk)

        _validate_image_file(
            destination
        )

        return destination

    except Exception:
        destination.unlink(
            missing_ok=True
        )
        raise


# =========================================================
# INFERENCIA REAL
# =========================================================

def run_inference(
    image_path: str,
) -> dict:
    """
    Ejecuta exclusivamente el modelo TensorFlow Lite entrenado.

    No existe modo simulado ni resultado alternativo. Si el
    modelo, las etiquetas o LiteRT presentan un error, el flujo
    se detiene y comunica el problema.
    """

    try:
        from services.ripeness_inference_service import (
            predict_ripeness,
        )

        result = predict_ripeness(
            image_path
        )

    except Exception as exception:
        raise RuntimeError(
            "No se pudo ejecutar el modelo real de madurez. "
            "Verifica avocado_mobilenetv2.tflite, labels.txt, "
            "el preprocesamiento y la instalación de LiteRT. "
            f"Detalle técnico: {exception}"
        ) from exception

    if not isinstance(result, dict):
        raise RuntimeError(
            "El modelo real devolvió un resultado inválido: "
            "se esperaba un diccionario."
        )

    label_key = str(
        result.get(
            "label_key",
            "",
        )
    ).strip()

    if label_key not in LABEL_META:
        raise RuntimeError(
            "El modelo devolvió una etiqueta no reconocida: "
            f"{label_key!r}. Revisa el orden y contenido de "
            "labels.txt."
        )

    scores = result.get(
        "scores",
        {},
    )

    if not isinstance(scores, dict):
        raise RuntimeError(
            "El modelo devolvió probabilidades inválidas."
        )

    missing_score_labels = [
        label
        for label in LABEL_META
        if label not in scores
    ]

    if missing_score_labels:
        raise RuntimeError(
            "Faltan clases en las probabilidades del modelo: "
            + ", ".join(missing_score_labels)
            + ". Revisa labels.txt y la salida del modelo."
        )

    # Marca inequívocamente que la inferencia proviene del
    # archivo TensorFlow Lite real.
    result["source_mode"] = "model"

    return result


# =========================================================
# HISTORIAL
# =========================================================

def insert_scan_history(
    entry: dict,
) -> None:
    ensure_scan_table()

    with sqlite3.connect(APP_DB_PATH) as connection:
        connection.execute(
            """
            INSERT INTO scan_history (
                scan_id,
                created_at,
                source_type,
                source_value,
                saved_image_path,
                label_key,
                label_text,
                confidence,
                margin,
                is_reliable,
                status,
                scores_json,
                recommended_action,
                result_color,
                inference_mode
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                entry["scan_id"],
                entry["created_at"],
                entry["source_type"],
                entry.get("source_value"),
                entry["saved_image_path"],
                entry["label_key"],
                entry["label_text"],
                entry["confidence"],
                entry["margin"],
                1 if entry["is_reliable"] else 0,
                entry["status"],
                json.dumps(
                    entry.get(
                        "scores",
                        {},
                    ),
                    ensure_ascii=False,
                ),
                entry.get(
                    "recommended_action"
                ),
                entry.get(
                    "result_color"
                ),
                entry["inference_mode"],
            ),
        )

        connection.commit()


def _row_to_scan(
    row: sqlite3.Row,
) -> dict:
    data = dict(row)

    try:
        data["scores"] = json.loads(
            data.get(
                "scores_json",
                "{}",
            )
            or "{}"
        )

    except (
        TypeError,
        json.JSONDecodeError,
    ):
        data["scores"] = {}

    data["is_reliable"] = bool(
        data.get(
            "is_reliable",
            0,
        )
    )

    return data


def get_latest_scan() -> dict | None:
    ensure_scan_table()

    with sqlite3.connect(APP_DB_PATH) as connection:
        connection.row_factory = (
            sqlite3.Row
        )

        row = connection.execute(
            """
            SELECT
                scan_id,
                created_at,
                source_type,
                source_value,
                saved_image_path,
                label_key,
                label_text,
                confidence,
                margin,
                is_reliable,
                status,
                scores_json,
                recommended_action,
                result_color,
                inference_mode
            FROM scan_history
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()

    if not row:
        return None

    return _row_to_scan(row)

def get_scan_history(
    limit: int = 100,
) -> list[dict]:
    """
    Devuelve los análisis más recientes almacenados
    en la tabla scan_history.
    """

    ensure_scan_table()

    try:
        safe_limit = int(limit)
    except (TypeError, ValueError):
        safe_limit = 100

    safe_limit = max(
        1,
        min(
            safe_limit,
            500,
        ),
    )

    with sqlite3.connect(
        APP_DB_PATH
    ) as connection:
        connection.row_factory = sqlite3.Row

        rows = connection.execute(
            """
            SELECT
                scan_id,
                created_at,
                source_type,
                source_value,
                saved_image_path,
                label_key,
                label_text,
                confidence,
                margin,
                is_reliable,
                status,
                scores_json,
                recommended_action,
                result_color,
                inference_mode
            FROM scan_history
            ORDER BY id DESC
            LIMIT ?
            """,
            (
                safe_limit,
            ),
        ).fetchall()

    return [
        _row_to_scan(row)
        for row in rows
    ]
# =========================================================
# FLUJO PRINCIPAL
# =========================================================

def process_scan_input(
    local_path: str | None = None,
    image_url: str | None = None,
) -> dict:
    if bool(local_path) == bool(image_url):
        raise ValueError(
            "Debe proporcionarse únicamente un archivo local "
            "o una URL de imagen."
        )

    if local_path:
        source_path = Path(
            local_path
        )

        normalized_path = str(
            source_path
        ).replace(
            "\\",
            "/",
        )

        if "/uploads_web/" in (
            f"/{normalized_path}/"
        ):
            temp_image = (
                copy_uploaded_web_image_to_temp(
                    local_path
                )
            )
            source_type = "web_upload"
        else:
            temp_image = (
                save_local_image_to_temp(
                    local_path
                )
            )
            source_type = "local_file"

        source_value = local_path

    else:
        clean_url = (
            image_url or ""
        ).strip()

        temp_image = download_image_from_url(
            clean_url
        )
        source_type = "image_url"
        source_value = clean_url

    inference = run_inference(
        str(temp_image)
    )

    label_key = inference.get(
        "label_key",
        "aun_no_lista",
    )

    if label_key not in LABEL_META:
        raise RuntimeError(
            "La etiqueta producida por el modelo no está "
            f"registrada en LABEL_META: {label_key!r}."
        )

    meta = LABEL_META[label_key]

    confidence = float(
        inference.get(
            "confidence",
            0.0,
        )
    )

    margin = float(
        inference.get(
            "margin",
            0.0,
        )
    )

    is_reliable = bool(
        inference.get(
            "is_reliable",
            False,
        )
    )

    status = inference.get(
        "status",
        (
            "completed"
            if is_reliable
            else "inconclusive"
        ),
    )

    result = {
        "scan_id": uuid.uuid4().hex,
        "created_at": datetime.now().isoformat(
            timespec="seconds"
        ),
        "source_type": source_type,
        "source_value": source_value,
        "saved_image_path": str(
            temp_image.resolve()
        ),
        "label_key": label_key,
        "label_text": inference.get(
            "label_text",
            meta["label_text"],
        ),
        "confidence": confidence,
        "margin": margin,
        "is_reliable": is_reliable,
        "status": status,
        "scores": inference.get(
            "scores",
            {},
        ),
        "recommended_action": inference.get(
            "recommended_action",
            meta["recommendation"],
        ),
        "result_color": (
            meta["color"]
            if is_reliable
            else "amber"
        ),
        "inference_mode": "model",
    }

    insert_scan_history(
        result
    )

    return result


def run_camera_scan() -> dict:
    """
    Abre la cámara local, guarda la fotografía,
    ejecuta la inferencia y registra el resultado.
    """

    from services.camera_capture_service import (
        capture_image_with_assistance,
    )

    image_path = (
        capture_image_with_assistance()
    )

    if not image_path:
        return {
            "success": False,
            "status": "cancelled",
            "message": (
                "La captura fue cancelada o no se pudo "
                "obtener una fotografía."
            ),
        }

    try:
        result = process_scan_input(
            local_path=image_path
        )

        return {
            "success": True,
            **result,
        }

    except Exception as exception:
        return {
            "success": False,
            "status": "error",
            "image_path": image_path,
            "message": str(exception),
        }
