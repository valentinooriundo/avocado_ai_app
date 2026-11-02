from __future__ import annotations

from pathlib import Path

import tensorflow as tf


BASE_DIR = Path(__file__).resolve().parents[3]
MODELS_DIR = BASE_DIR / "src" / "ml" / "models"

KERAS_MODEL_PATH = (
    MODELS_DIR
    / "avocado_mobilenetv2.keras"
)

TFLITE_MODEL_PATH = (
    MODELS_DIR
    / "avocado_mobilenetv2.tflite"
)

LABELS_PATH = (
    MODELS_DIR
    / "labels.txt"
)


def validate_files() -> None:
    if not KERAS_MODEL_PATH.exists():
        raise FileNotFoundError(
            "No existe el modelo Keras entrenado:\n"
            f"{KERAS_MODEL_PATH}\n\n"
            "Primero ejecuta train_model.py."
        )

    if not LABELS_PATH.exists():
        raise FileNotFoundError(
            "No existe el archivo de etiquetas:\n"
            f"{LABELS_PATH}"
        )


def validate_tflite_model() -> None:
    """
    Comprueba que el modelo TFLite generado pueda cargarse
    y muestra la información de entrada y salida.
    """

    interpreter = tf.lite.Interpreter(
        model_path=str(TFLITE_MODEL_PATH)
    )

    interpreter.allocate_tensors()

    input_details = (
        interpreter.get_input_details()[0]
    )

    output_details = (
        interpreter.get_output_details()[0]
    )

    print("\nModelo TFLite verificado correctamente.")

    print(
        "Entrada:"
        f"\n  Shape: {input_details['shape']}"
        f"\n  Tipo:  {input_details['dtype']}"
    )

    print(
        "Salida:"
        f"\n  Shape: {output_details['shape']}"
        f"\n  Tipo:  {output_details['dtype']}"
    )


def main() -> None:
    MODELS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("=" * 62)
    print("EXPORTACIÓN A TENSORFLOW LITE - AVORUNA")
    print("=" * 62)

    print("\n1. Validando archivos...")
    validate_files()

    print("\n2. Cargando modelo Keras...")
    model = tf.keras.models.load_model(
        KERAS_MODEL_PATH,
        compile=False,
    )

    print("\n3. Convirtiendo a TensorFlow Lite...")

    converter = (
        tf.lite.TFLiteConverter
        .from_keras_model(model)
    )

    # Por ahora no se aplica cuantización.
    # Esto permite comparar el modelo TFLite con el modelo Keras
    # sin introducir cambios adicionales en la precisión.
    tflite_model = converter.convert()

    print("\n4. Guardando modelo TFLite...")

    TFLITE_MODEL_PATH.write_bytes(
        tflite_model
    )

    validate_tflite_model()

    file_size_mb = (
        TFLITE_MODEL_PATH.stat().st_size
        / (1024 * 1024)
    )

    print("\n" + "=" * 62)
    print("CONVERSIÓN COMPLETADA")
    print("=" * 62)

    print(
        f"Modelo generado:\n"
        f"{TFLITE_MODEL_PATH}"
    )

    print(
        f"\nTamaño del archivo: "
        f"{file_size_mb:.2f} MB"
    )


if __name__ == "__main__":
    main()
