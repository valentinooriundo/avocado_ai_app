from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import tensorflow as tf
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    classification_report,
    confusion_matrix,
)


BASE_DIR = Path(__file__).resolve().parents[3]

TEST_DIR = (
    BASE_DIR
    / "src"
    / "ml"
    / "dataset"
    / "test"
)

MODELS_DIR = (
    BASE_DIR
    / "src"
    / "ml"
    / "models"
)

MODEL_PATH = (
    MODELS_DIR
    / "avocado_mobilenetv2.keras"
)

REPORT_PATH = (
    MODELS_DIR
    / "classification_report.json"
)

CONFUSION_MATRIX_PATH = (
    MODELS_DIR
    / "confusion_matrix.png"
)

EVALUATION_PATH = (
    MODELS_DIR
    / "evaluation_summary.json"
)

CLASS_NAMES = [
    "aun_no_lista",
    "en_proceso",
    "lista_para_cosecha",
]

IMG_SIZE = (224, 224)
BATCH_SIZE = 32


def load_test_dataset() -> tf.data.Dataset:
    if not TEST_DIR.exists():
        raise FileNotFoundError(
            f"No existe el conjunto test: {TEST_DIR}"
        )

    return (
        tf.keras.utils
        .image_dataset_from_directory(
            TEST_DIR,
            labels="inferred",
            label_mode="int",
            class_names=CLASS_NAMES,
            image_size=IMG_SIZE,
            batch_size=BATCH_SIZE,
            shuffle=False,
        )
    )


def save_confusion_matrix(
    matrix: np.ndarray,
) -> None:
    display = ConfusionMatrixDisplay(
        confusion_matrix=matrix,
        display_labels=[
            "Aún no lista",
            "En proceso",
            "Lista para cosecha",
        ],
    )

    figure, axis = plt.subplots(
        figsize=(9, 7)
    )

    display.plot(
        ax=axis,
        values_format="d",
    )

    axis.set_title(
        "Matriz de confusión del modelo Avoruna"
    )

    axis.set_xlabel(
        "Clase predicha"
    )

    axis.set_ylabel(
        "Clase real"
    )

    figure.tight_layout()

    figure.savefig(
        CONFUSION_MATRIX_PATH,
        dpi=180,
        bbox_inches="tight",
    )

    plt.close(figure)


def main() -> None:
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"No existe el modelo: {MODEL_PATH}"
        )

    print("Cargando conjunto de prueba...")
    test_ds = load_test_dataset()

    print("Cargando modelo...")
    model = tf.keras.models.load_model(
        MODEL_PATH
    )

    print("Evaluando modelo...")
    test_loss, test_accuracy = model.evaluate(
        test_ds,
        verbose=1,
    )

    print("Generando predicciones...")
    probabilities = model.predict(
        test_ds,
        verbose=1,
    )

    predicted_labels = np.argmax(
        probabilities,
        axis=1,
    )

    real_labels = np.concatenate(
        [
            labels.numpy()
            for _, labels in test_ds
        ]
    )

    report = classification_report(
        real_labels,
        predicted_labels,
        labels=[
            0,
            1,
            2,
        ],
        target_names=CLASS_NAMES,
        output_dict=True,
        zero_division=0,
    )

    matrix = confusion_matrix(
        real_labels,
        predicted_labels,
        labels=[
            0,
            1,
            2,
        ],
    )

    REPORT_PATH.write_text(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    save_confusion_matrix(
        matrix
    )

    evaluation = {
        "test_loss": float(
            test_loss
        ),
        "test_accuracy": float(
            test_accuracy
        ),
        "macro_precision": float(
            report["macro avg"]["precision"]
        ),
        "macro_recall": float(
            report["macro avg"]["recall"]
        ),
        "macro_f1_score": float(
            report["macro avg"]["f1-score"]
        ),
        "weighted_f1_score": float(
            report["weighted avg"]["f1-score"]
        ),
        "confusion_matrix": (
            matrix.tolist()
        ),
    }

    EVALUATION_PATH.write_text(
        json.dumps(
            evaluation,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print()
    print("=" * 64)
    print("EVALUACIÓN COMPLETADA")
    print("=" * 64)

    print(
        "Test accuracy: "
        f"{test_accuracy * 100:.2f}%"
    )

    print(
        "Macro precision: "
        f"{evaluation['macro_precision'] * 100:.2f}%"
    )

    print(
        "Macro recall: "
        f"{evaluation['macro_recall'] * 100:.2f}%"
    )

    print(
        "Macro F1-score: "
        f"{evaluation['macro_f1_score'] * 100:.2f}%"
    )

    print()
    print(
        f"Reporte:\n{REPORT_PATH}"
    )

    print()
    print(
        "Matriz de confusión:\n"
        f"{CONFUSION_MATRIX_PATH}"
    )

    print()
    print(
        f"Resumen:\n{EVALUATION_PATH}"
    )


if __name__ == "__main__":
    main()
