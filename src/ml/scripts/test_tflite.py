from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import tensorflow as tf
from PIL import Image, ImageOps


BASE_DIR = Path(__file__).resolve().parents[3]
MODELS_DIR = BASE_DIR / "src" / "ml" / "models"

MODEL_PATH = MODELS_DIR / "avocado_mobilenetv2.tflite"
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

    No aplica preprocess_input porque el modelo exportado ya
    contiene internamente el preprocesamiento de MobileNetV2.
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


def adapt_input_dtype(
    image_array: np.ndarray,
    input_details: dict,
) -> np.ndarray:
    """
    Adapta la imagen al tipo de entrada del modelo.

    Tu exportación actual debería usar float32, pero también
    admite modelos cuantizados en una conversión posterior.
    """

    input_dtype = input_details["dtype"]

    if input_dtype == np.float32:
        return image_array.astype(
            np.float32
        )

    scale, zero_point = input_details[
        "quantization"
    ]

    if scale == 0:
        raise ValueError(
            "El modelo cuantizado no tiene parámetros "
            "de entrada válidos."
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


def dequantize_output(
    predictions: np.ndarray,
    output_details: dict,
) -> np.ndarray:
    output_dtype = output_details["dtype"]

    if output_dtype == np.float32:
        return predictions.astype(
            np.float32
        )

    scale, zero_point = output_details[
        "quantization"
    ]

    if scale == 0:
        return predictions.astype(
            np.float32
        )

    return (
        predictions.astype(np.float32)
        - zero_point
    ) * scale


def predict_tflite(
    image_path: str | Path,
) -> dict:
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            "No existe el modelo TensorFlow Lite:\n"
            f"{MODEL_PATH}\n\n"
            "Ejecuta primero export_tflite.py."
        )

    labels = load_labels()

    interpreter = tf.lite.Interpreter(
        model_path=str(MODEL_PATH)
    )
    interpreter.allocate_tensors()

    input_details = (
        interpreter.get_input_details()[0]
    )
    output_details = (
        interpreter.get_output_details()[0]
    )

    image_array = prepare_image(
        image_path
    )

    image_array = adapt_input_dtype(
        image_array,
        input_details,
    )

    expected_shape = tuple(
        int(value)
        for value in input_details["shape"]
    )

    if tuple(image_array.shape) != expected_shape:
        raise ValueError(
            "La forma de la imagen no coincide con la entrada "
            f"del modelo. Esperado: {expected_shape}; "
            f"recibido: {image_array.shape}."
        )

    interpreter.set_tensor(
        input_details["index"],
        image_array,
    )

    interpreter.invoke()

    predictions = interpreter.get_tensor(
        output_details["index"]
    )[0]

    predictions = dequantize_output(
        predictions,
        output_details,
    )

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

    label_key = labels[
        best_index
    ]
    label_text = LABEL_MAP.get(
        label_key,
        label_key,
    )

    is_reliable = (
        confidence >= MIN_CONFIDENCE
        and margin >= MIN_MARGIN
    )

    return {
        "label_key": label_key,
        "label_text": label_text,
        "confidence": confidence,
        "margin": margin,
        "is_reliable": is_reliable,
        "scores": {
            labels[index]: float(
                predictions[index]
            )
            for index in range(
                len(labels)
            )
        },
        "input_dtype": str(
            input_details["dtype"]
        ),
        "output_dtype": str(
            output_details["dtype"]
        ),
    }


def main() -> None:
    if len(sys.argv) < 2:
        raise ValueError(
            "Debes pasar la ruta de una imagen.\n\n"
            "Ejemplo:\n"
            'uv run python src/ml/scripts/test_tflite.py '
            '"C:\\Users\\VALENTINO\\Downloads\\imagen\\palta_prueba.png"'
        )

    result = predict_tflite(
        sys.argv[1]
    )

    print("=" * 64)
    print("PREDICCIÓN TENSORFLOW LITE - AVORUNA")
    print("=" * 64)

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

    print(
        f"Entrada:       {result['input_dtype']}"
    )
    print(
        f"Salida:        {result['output_dtype']}"
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
