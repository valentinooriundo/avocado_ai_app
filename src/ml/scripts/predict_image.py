from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import tensorflow as tf
from PIL import Image, ImageOps


BASE_DIR = Path(__file__).resolve().parents[3]
MODELS_DIR = BASE_DIR / "src" / "ml" / "models"

MODEL_PATH = MODELS_DIR / "avocado_mobilenetv2.keras"
LABELS_PATH = MODELS_DIR / "labels.txt"

IMG_SIZE = (224, 224)
MIN_CONFIDENCE = 0.60
MIN_MARGIN = 0.10

LABEL_MAP = {
    "aun_no_lista": "Aún no lista",
    "en_proceso": "En proceso",
    "lista_para_cosecha": "Lista para cosecha",
}


def load_labels() -> list[str]:
    if not LABELS_PATH.exists():
        raise FileNotFoundError(
            f"No existe labels.txt: {LABELS_PATH}"
        )

    labels = [
        line.strip()
        for line in LABELS_PATH.read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]

    if not labels:
        raise ValueError(
            "El archivo labels.txt está vacío."
        )

    return labels


def prepare_image(
    image_path: str | Path,
) -> np.ndarray:
    """
    Carga la imagen en RGB y la redimensiona a 224 x 224.

    No aplica preprocess_input porque el modelo entrenado
    ya contiene internamente el preprocesamiento de MobileNetV2.
    """

    image_path = Path(image_path)

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
            image = ImageOps.exif_transpose(image)
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
            f"No se pudo leer la imagen: {image_path}"
        ) from exception

    return np.expand_dims(
        image_array,
        axis=0,
    )


def predict(
    image_path: str | Path,
) -> dict:
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"No existe el modelo: {MODEL_PATH}"
        )

    labels = load_labels()
    model = tf.keras.models.load_model(
        MODEL_PATH
    )

    image_array = prepare_image(
        image_path
    )

    predictions = model.predict(
        image_array,
        verbose=0,
    )[0]

    if len(predictions) != len(labels):
        raise ValueError(
            "La cantidad de salidas del modelo no coincide "
            "con la cantidad de etiquetas."
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

    best_confidence = float(
        predictions[best_index]
    )
    second_confidence = float(
        predictions[second_index]
    )

    confidence_margin = (
        best_confidence
        - second_confidence
    )

    best_label_key = labels[
        best_index
    ]
    best_label_text = LABEL_MAP.get(
        best_label_key,
        best_label_key,
    )

    is_reliable = (
        best_confidence >= MIN_CONFIDENCE
        and confidence_margin >= MIN_MARGIN
    )

    return {
        "label_key": best_label_key,
        "label_text": best_label_text,
        "confidence": best_confidence,
        "margin": confidence_margin,
        "is_reliable": is_reliable,
        "scores": {
            labels[index]: float(
                predictions[index]
            )
            for index in range(
                len(labels)
            )
        },
    }


def main() -> None:
    if len(sys.argv) < 2:
        raise ValueError(
            "Debes pasar la ruta de una imagen.\n\n"
            "Ejemplo:\n"
            'uv run python src/ml/scripts/predict_image.py '
            '"C:\\Users\\VALENTINO\\Pictures\\palta_prueba.jpg"'
        )

    result = predict(
        sys.argv[1]
    )

    print("=" * 60)
    print("PREDICCIÓN DE MADUREZ - AVORUNA")
    print("=" * 60)

    print(
        f"Clase interna: {result['label_key']}"
    )
    print(
        f"Resultado:     {result['label_text']}"
    )
    print(
        "Confianza:     "
        f"{result['confidence'] * 100:.2f}%"
    )
    print(
        "Margen:        "
        f"{result['margin'] * 100:.2f}%"
    )

    if result["is_reliable"]:
        print(
            "Estado:        Predicción confiable"
        )
    else:
        print(
            "Estado:        Resultado no concluyente; "
            "toma otra fotografía."
        )

    print("\nPuntajes por clase:")

    for key, value in sorted(
        result["scores"].items(),
        key=lambda item: item[1],
        reverse=True,
    ):
        print(
            f"  {LABEL_MAP.get(key, key)}: "
            f"{value * 100:.2f}%"
        )


if __name__ == "__main__":
    main()
