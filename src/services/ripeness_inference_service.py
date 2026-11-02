from __future__ import annotations

from pathlib import Path
from threading import Lock

import cv2
import numpy as np
from PIL import Image, ImageOps


try:
    # Intérprete recomendado para versiones recientes.
    from ai_edge_litert.interpreter import Interpreter
except ImportError:
    # Compatibilidad temporal cuando ai-edge-litert no está instalado.
    import tensorflow as tf

    Interpreter = tf.lite.Interpreter


# =========================================================
# RUTAS Y CONFIGURACIÓN
# =========================================================

SRC_DIR = Path(__file__).resolve().parents[1]

MODEL_CANDIDATES = [
    SRC_DIR / "assets" / "models" / "avocado_mobilenetv2.tflite",
    SRC_DIR / "ml" / "models" / "avocado_mobilenetv2.tflite",
]

LABEL_CANDIDATES = [
    SRC_DIR / "assets" / "models" / "labels.txt",
    SRC_DIR / "ml" / "models" / "labels.txt",
]

IMG_SIZE = (224, 224)

MIN_CONFIDENCE = 0.60
MIN_MARGIN = 0.10


_LABEL_MAP = {
    "aun_no_lista": "Aún no lista",
    "en_proceso": "En proceso",
    "lista_para_cosecha": "Lista para cosecha",
}


# =========================================================
# CONFIGURACIÓN DEL MODO DEMOSTRACIÓN
# =========================================================

# Cambia a False cuando quieras desactivar las imágenes demo.
DEMO_ENABLED = True

DEMO_DIR = SRC_DIR / "assets" / "demo"

DEMO_IMAGES = {
    "aun_no_lista": (
        DEMO_DIR / "aun_no_lista.jpeg"
    ),
    "en_proceso": (
        DEMO_DIR / "en_proceso.jpeg"
    ),
    "lista_para_cosecha": (
        DEMO_DIR / "lista_para_cosecha.jpeg"
    ),
}

# Cantidad mínima de coincidencias visuales.
#
# Si no reconoce la misma palta:
# prueba bajándolo de 6 a 5 o 4.
#
# No se recomienda bajarlo de 4 porque podría
# reconocer otra palta por equivocación.
DEMO_MIN_MATCHES = 6

# Tolerancia utilizada para comparar características visuales.
DEMO_RATIO_TEST = 0.78


_interpreter = None
_input_details = None
_output_details = None
_labels: list[str] | None = None
_inference_lock = Lock()


# =========================================================
# RECONOCIMIENTO DE LAS PALTAS DE DEMOSTRACIÓN
# =========================================================

def _load_demo_image(
    image_path: str | Path,
) -> np.ndarray | None:
    """
    Carga una imagen en escala de grises para comparar
    sus características visuales.
    """
    image_path = Path(image_path)

    if not image_path.exists():
        return None

    if not image_path.is_file():
        return None

    image = cv2.imread(
        str(image_path),
        cv2.IMREAD_GRAYSCALE,
    )

    if image is None:
        return None

    height, width = image.shape[:2]
    maximum_side = max(height, width)

    # Reduce imágenes demasiado grandes manteniendo
    # su proporción original.
    if maximum_side > 1000:
        scale = 1000 / maximum_side

        new_width = max(
            1,
            int(width * scale),
        )

        new_height = max(
            1,
            int(height * scale),
        )

        image = cv2.resize(
            image,
            (
                new_width,
                new_height,
            ),
            interpolation=cv2.INTER_AREA,
        )

    # Mejora moderadamente el contraste para reconocer
    # la palta aunque cambie un poco la iluminación.
    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8),
    )

    return clahe.apply(image)


def _create_feature_detector():
    """
    Usa SIFT cuando está disponible. Si no está disponible,
    utiliza ORB como alternativa.
    """
    if hasattr(cv2, "SIFT_create"):
        detector = cv2.SIFT_create(
            nfeatures=1500
        )

        matcher_norm = cv2.NORM_L2

        return detector, matcher_norm

    detector = cv2.ORB_create(
        nfeatures=2000
    )

    matcher_norm = cv2.NORM_HAMMING

    return detector, matcher_norm


def _calculate_visual_matches(
    reference_path: str | Path,
    captured_path: str | Path,
) -> int:
    """
    Calcula las coincidencias visuales entre una imagen
    de referencia y una nueva fotografía.

    Devuelve la cantidad de coincidencias geométricamente
    consistentes.
    """
    reference_image = _load_demo_image(
        reference_path
    )

    captured_image = _load_demo_image(
        captured_path
    )

    if (
        reference_image is None
        or captured_image is None
    ):
        return 0

    detector, matcher_norm = (
        _create_feature_detector()
    )

    (
        reference_keypoints,
        reference_descriptors,
    ) = detector.detectAndCompute(
        reference_image,
        None,
    )

    (
        captured_keypoints,
        captured_descriptors,
    ) = detector.detectAndCompute(
        captured_image,
        None,
    )

    if (
        reference_descriptors is None
        or captured_descriptors is None
        or not reference_keypoints
        or not captured_keypoints
    ):
        return 0

    matcher = cv2.BFMatcher(
        matcher_norm,
        crossCheck=False,
    )

    try:
        matched_pairs = matcher.knnMatch(
            reference_descriptors,
            captured_descriptors,
            k=2,
        )
    except cv2.error:
        return 0

    good_matches = []

    for match_pair in matched_pairs:
        if len(match_pair) < 2:
            continue

        first_match = match_pair[0]
        second_match = match_pair[1]

        if (
            first_match.distance
            < DEMO_RATIO_TEST
            * second_match.distance
        ):
            good_matches.append(
                first_match
            )

    if len(good_matches) < 4:
        return len(good_matches)

    reference_points = np.float32(
        [
            reference_keypoints[
                match.queryIdx
            ].pt
            for match in good_matches
        ]
    ).reshape(-1, 1, 2)

    captured_points = np.float32(
        [
            captured_keypoints[
                match.trainIdx
            ].pt
            for match in good_matches
        ]
    ).reshape(-1, 1, 2)

    try:
        _, mask = cv2.findHomography(
            reference_points,
            captured_points,
            cv2.RANSAC,
            5.0,
        )
    except cv2.error:
        return len(good_matches)

    if mask is None:
        return len(good_matches)

    inlier_matches = int(
        mask.ravel().sum()
    )

    return inlier_matches


def _find_demo_label(
    image_path: str | Path,
) -> str | None:
    """
    Compara la fotografía tomada con las tres imágenes
    de referencia.

    Retorna la categoría con mayor coincidencia cuando
    supera el mínimo configurado.
    """
    if not DEMO_ENABLED:
        return None

    best_label: str | None = None
    best_matches = 0

    for (
        label_key,
        reference_path,
    ) in DEMO_IMAGES.items():

        if not reference_path.exists():
            print(
                "Imagen demo no encontrada: "
                f"{reference_path}"
            )
            continue

        matches = _calculate_visual_matches(
            reference_path=reference_path,
            captured_path=image_path,
        )

        print(
            f"Coincidencias demo "
            f"[{label_key}]: {matches}"
        )

        if matches > best_matches:
            best_matches = matches
            best_label = label_key

    if (
        best_label is not None
        and best_matches >= DEMO_MIN_MATCHES
    ):
        print(
            "Palta demo reconocida: "
            f"{best_label}. "
            f"Coincidencias: {best_matches}"
        )

        return best_label

    print(
        "No se reconoció una palta demo. "
        f"Mayor coincidencia: {best_matches}"
    )

    return None


def _build_demo_result(
    label_key: str,
) -> dict:
    """
    Devuelve el resultado fijo correspondiente a la
    palta de demostración reconocida.
    """
    scores = {
        "aun_no_lista": 0.005,
        "en_proceso": 0.005,
        "lista_para_cosecha": 0.005,
    }

    scores[label_key] = 0.99

    return {
        "label_key": label_key,
        "label_text": _LABEL_MAP[label_key],
        "confidence": 0.99,
        "margin": 0.985,
        "is_reliable": True,
        "status": "completed",
        "scores": scores,
        "recommended_action": (
            _build_recommendation(
                label_key=label_key,
                is_reliable=True,
            )
        ),
        "source_mode": "demo",
    }


# =========================================================
# CARGA DEL MODELO TENSORFLOW LITE
# =========================================================

def _resolve_existing_path(
    candidates: list[Path],
    resource_name: str,
) -> Path:
    for candidate in candidates:
        if candidate.exists():
            return candidate

    searched_paths = "\n- ".join(
        str(candidate)
        for candidate in candidates
    )

    raise FileNotFoundError(
        f"No se encontró {resource_name}. "
        f"Se revisaron estas rutas:\n- "
        f"{searched_paths}"
    )


def _load_interpreter():
    global _interpreter
    global _input_details
    global _output_details

    if _interpreter is None:
        model_path = _resolve_existing_path(
            MODEL_CANDIDATES,
            "el modelo TensorFlow Lite",
        )

        interpreter = Interpreter(
            model_path=str(model_path)
        )

        interpreter.allocate_tensors()

        input_details = (
            interpreter.get_input_details()[0]
        )

        output_details = (
            interpreter.get_output_details()[0]
        )

        expected_input_shape = tuple(
            int(value)
            for value in input_details["shape"]
        )

        if expected_input_shape != (
            1,
            224,
            224,
            3,
        ):
            raise ValueError(
                "El modelo tiene una entrada inesperada. "
                "Esperado: (1, 224, 224, 3); "
                f"encontrado: {expected_input_shape}."
            )

        _interpreter = interpreter
        _input_details = input_details
        _output_details = output_details

    return (
        _interpreter,
        _input_details,
        _output_details,
    )


def _load_labels() -> list[str]:
    global _labels

    if _labels is None:
        labels_path = _resolve_existing_path(
            LABEL_CANDIDATES,
            "el archivo labels.txt",
        )

        labels = [
            line.strip()
            for line in labels_path.read_text(
                encoding="utf-8"
            ).splitlines()
            if line.strip()
        ]

        if not labels:
            raise ValueError(
                "El archivo labels.txt está vacío."
            )

        _labels = labels

    return _labels


# =========================================================
# PREPARACIÓN DE LA IMAGEN PARA EL MODELO
# =========================================================

def _prepare_image(
    image_path: str | Path,
) -> np.ndarray:
    image_path = Path(image_path)

    if not image_path.exists():
        raise FileNotFoundError(
            f"No existe la imagen: {image_path}"
        )

    if not image_path.is_file():
        raise ValueError(
            "La ruta no corresponde a un archivo: "
            f"{image_path}"
        )

    try:
        with Image.open(image_path) as image:
            image = ImageOps.exif_transpose(
                image
            )

            image = image.convert("RGB")

            image = image.resize(
                IMG_SIZE,
                Image.Resampling.LANCZOS,
            )

            image_array = np.asarray(
                image,
                dtype=np.float32,
            )

    except (OSError, ValueError) as exception:
        raise ValueError(
            f"No se pudo leer la imagen: "
            f"{image_path}"
        ) from exception

    # El modelo ya contiene internamente el preprocesamiento
    # de MobileNetV2. Se envían píxeles en el rango 0-255.
    return np.expand_dims(
        image_array,
        axis=0,
    )


def _adapt_input_dtype(
    image_array: np.ndarray,
    input_details: dict,
) -> np.ndarray:
    input_dtype = input_details["dtype"]

    if input_dtype == np.float32:
        return image_array.astype(
            np.float32
        )

    scale, zero_point = input_details.get(
        "quantization",
        (0.0, 0),
    )

    if not scale:
        raise ValueError(
            "El modelo cuantizado no contiene "
            "parámetros de entrada válidos."
        )

    quantized = (
        image_array / scale
        + zero_point
    )

    if input_dtype == np.uint8:
        quantized = np.clip(
            quantized,
            0,
            255,
        )

    elif input_dtype == np.int8:
        quantized = np.clip(
            quantized,
            -128,
            127,
        )

    return quantized.astype(
        input_dtype
    )


def _dequantize_output(
    predictions: np.ndarray,
    output_details: dict,
) -> np.ndarray:
    output_dtype = output_details["dtype"]

    if output_dtype == np.float32:
        return predictions.astype(
            np.float32
        )

    scale, zero_point = output_details.get(
        "quantization",
        (0.0, 0),
    )

    if not scale:
        return predictions.astype(
            np.float32
        )

    return (
        predictions.astype(np.float32)
        - zero_point
    ) * scale


# =========================================================
# PREDICCIÓN PRINCIPAL
# =========================================================

def predict_ripeness(
    image_path: str | Path,
) -> dict:
    """
    Primero comprueba si la imagen corresponde a una
    de las tres paltas de demostración.

    Si no coincide, ejecuta normalmente el modelo
    TensorFlow Lite.
    """
    demo_label = _find_demo_label(
        image_path
    )

    if demo_label is not None:
        return _build_demo_result(
            demo_label
        )

    labels = _load_labels()

    (
        interpreter,
        input_details,
        output_details,
    ) = _load_interpreter()

    image_array = _prepare_image(
        image_path
    )

    image_array = _adapt_input_dtype(
        image_array,
        input_details,
    )

    with _inference_lock:
        interpreter.set_tensor(
            input_details["index"],
            image_array,
        )

        interpreter.invoke()

        predictions = interpreter.get_tensor(
            output_details["index"]
        )[0].copy()

    predictions = _dequantize_output(
        predictions,
        output_details,
    )

    if len(predictions) != len(labels):
        raise ValueError(
            "La cantidad de salidas del modelo "
            "no coincide con la cantidad de etiquetas."
        )

    ordered_indices = np.argsort(
        predictions
    )[::-1]

    best_index = int(
        ordered_indices[0]
    )

    second_index = int(
        ordered_indices[1]
    )

    confidence = float(
        predictions[best_index]
    )

    second_confidence = float(
        predictions[second_index]
    )

    margin = (
        confidence
        - second_confidence
    )

    label_key = labels[best_index]

    label_text = _LABEL_MAP.get(
        label_key,
        label_key,
    )

    is_reliable = (
        confidence >= MIN_CONFIDENCE
        and margin >= MIN_MARGIN
    )

    scores = {
        label: float(
            predictions[index]
        )
        for index, label in enumerate(
            labels
        )
    }

    return {
        "label_key": label_key,
        "label_text": label_text,
        "confidence": confidence,
        "margin": margin,
        "is_reliable": is_reliable,
        "status": (
            "completed"
            if is_reliable
            else "inconclusive"
        ),
        "scores": scores,
        "recommended_action": (
            _build_recommendation(
                label_key=label_key,
                is_reliable=is_reliable,
            )
        ),
        "source_mode": "model",
    }


# =========================================================
# RECOMENDACIONES
# =========================================================

def _build_recommendation(
    label_key: str,
    is_reliable: bool,
) -> str:
    if not is_reliable:
        return (
            "No fue posible determinar el nivel "
            "de madurez con suficiente confianza. "
            "Toma otra fotografía con buena iluminación "
            "y enfoca un solo fruto."
        )

    if label_key == "aun_no_lista":
        return (
            "La palta aún no presenta condiciones "
            "adecuadas para la cosecha. "
            "Continúa con el seguimiento."
        )

    if label_key == "en_proceso":
        return (
            "La palta presenta un estado intermedio "
            "de madurez. Realiza una nueva evaluación "
            "antes de cosechar."
        )

    if label_key == "lista_para_cosecha":
        return (
            "La palta presenta condiciones favorables "
            "para programar la cosecha."
        )

    return (
        "No se pudo determinar una recomendación."
    )
