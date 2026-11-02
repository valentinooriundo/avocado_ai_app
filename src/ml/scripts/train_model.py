from __future__ import annotations

import json
import random
from pathlib import Path

import tensorflow as tf


# =========================================================
# RUTAS DEL PROYECTO
# =========================================================

BASE_DIR = Path(__file__).resolve().parents[3]

DATASET_DIR = (
    BASE_DIR
    / "src"
    / "ml"
    / "dataset"
)

MODELS_DIR = (
    BASE_DIR
    / "src"
    / "ml"
    / "models"
)

TRAIN_DIR = DATASET_DIR / "train"
VAL_DIR = DATASET_DIR / "val"
TEST_DIR = DATASET_DIR / "test"


# =========================================================
# CONFIGURACIÓN
# =========================================================

CLASS_NAMES = [
    "aun_no_lista",
    "en_proceso",
    "lista_para_cosecha",
]

VALID_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
}

IMG_HEIGHT = 224
IMG_WIDTH = 224
IMG_SIZE = (
    IMG_HEIGHT,
    IMG_WIDTH,
)

BATCH_SIZE = 32
SEED = 123
EPOCHS = 20


# =========================================================
# ARCHIVOS GENERADOS
# =========================================================

BEST_MODEL_PATH = (
    MODELS_DIR
    / "avocado_mobilenetv2_best.keras"
)

MODEL_OUTPUT_PATH = (
    MODELS_DIR
    / "avocado_mobilenetv2.keras"
)

LABELS_OUTPUT_PATH = (
    MODELS_DIR
    / "labels.txt"
)

METRICS_OUTPUT_PATH = (
    MODELS_DIR
    / "training_summary.json"
)

TRAINING_LOG_PATH = (
    MODELS_DIR
    / "training_log.csv"
)


# =========================================================
# VALIDACIÓN DEL DATASET
# =========================================================

def list_images(
    directory: Path,
) -> list[Path]:
    return [
        path
        for path in directory.rglob("*")
        if path.is_file()
        and path.suffix.lower() in VALID_EXTENSIONS
    ]


def validate_dataset() -> dict:
    """
    Verifica que existan las carpetas requeridas y que
    cada una tenga imágenes.
    """

    split_directories = {
        "train": TRAIN_DIR,
        "val": VAL_DIR,
        "test": TEST_DIR,
    }

    counts: dict[str, dict[str, int]] = {}

    missing_directories: list[str] = []
    empty_directories: list[str] = []

    for split_name, split_directory in (
        split_directories.items()
    ):
        counts[split_name] = {}

        for class_name in CLASS_NAMES:
            class_directory = (
                split_directory
                / class_name
            )

            if not class_directory.exists():
                missing_directories.append(
                    str(class_directory)
                )
                continue

            images = list_images(
                class_directory
            )

            image_count = len(images)

            counts[split_name][
                class_name
            ] = image_count

            if image_count == 0:
                empty_directories.append(
                    str(class_directory)
                )

    if missing_directories:
        raise FileNotFoundError(
            "Faltan carpetas del dataset:\n- "
            + "\n- ".join(
                missing_directories
            )
        )

    if empty_directories:
        raise ValueError(
            "Las siguientes carpetas no tienen imágenes:\n- "
            + "\n- ".join(
                empty_directories
            )
        )

    print("\nCantidad de imágenes:")

    for split_name, classes in counts.items():
        print(
            f"\n{split_name.upper()}"
        )

        split_total = 0

        for class_name, count in classes.items():
            print(
                f"  {class_name}: {count}"
            )

            split_total += count

        print(
            f"  Total {split_name}: "
            f"{split_total}"
        )

    return counts


# =========================================================
# CARGA DE DATASETS
# =========================================================

def load_dataset(
    directory: Path,
    *,
    shuffle: bool,
) -> tf.data.Dataset:
    """
    Carga las imágenes conservando un orden explícito
    para las tres clases.
    """

    return (
        tf.keras.utils
        .image_dataset_from_directory(
            directory,
            labels="inferred",
            label_mode="int",
            class_names=CLASS_NAMES,
            image_size=IMG_SIZE,
            batch_size=BATCH_SIZE,
            shuffle=shuffle,
            seed=SEED if shuffle else None,
        )
    )


def build_datasets():
    train_ds = load_dataset(
        TRAIN_DIR,
        shuffle=True,
    )

    val_ds = load_dataset(
        VAL_DIR,
        shuffle=False,
    )

    test_ds = load_dataset(
        TEST_DIR,
        shuffle=False,
    )

    autotune = tf.data.AUTOTUNE

    train_ds = train_ds.prefetch(
        buffer_size=autotune
    )

    val_ds = val_ds.prefetch(
        buffer_size=autotune
    )

    test_ds = test_ds.prefetch(
        buffer_size=autotune
    )

    return (
        train_ds,
        val_ds,
        test_ds,
    )


# =========================================================
# CONSTRUCCIÓN DEL MODELO
# =========================================================

def build_model() -> tf.keras.Model:
    """
    Construye un clasificador basado en MobileNetV2
    mediante transferencia de aprendizaje.
    """

    data_augmentation = (
        tf.keras.Sequential(
            [
                tf.keras.layers.RandomFlip(
                    "horizontal"
                ),
                tf.keras.layers.RandomRotation(
                    0.08
                ),
                tf.keras.layers.RandomZoom(
                    0.10
                ),
                tf.keras.layers.RandomContrast(
                    0.10
                ),
                tf.keras.layers.RandomTranslation(
                    height_factor=0.05,
                    width_factor=0.05,
                ),
            ],
            name="data_augmentation",
        )
    )

    base_model = (
        tf.keras.applications
        .MobileNetV2(
            input_shape=(
                IMG_HEIGHT,
                IMG_WIDTH,
                3,
            ),
            include_top=False,
            weights="imagenet",
        )
    )

    # Primera etapa:
    # MobileNetV2 permanece congelado.
    base_model.trainable = False

    inputs = tf.keras.Input(
        shape=(
            IMG_HEIGHT,
            IMG_WIDTH,
            3,
        ),
        name="input_image",
    )

    x = data_augmentation(
        inputs
    )

    # MobileNetV2 necesita valores entre -1 y 1.
    # La transformación queda dentro del modelo.
    x = tf.keras.layers.Rescaling(
        scale=1.0 / 127.5,
        offset=-1.0,
        name="mobilenet_preprocessing",
    )(x)

    x = base_model(
        x,
        training=False,
    )

    x = (
        tf.keras.layers
        .GlobalAveragePooling2D(
            name="global_average_pooling",
        )(x)
    )

    x = tf.keras.layers.Dropout(
        0.30,
        name="dropout",
    )(x)

    outputs = tf.keras.layers.Dense(
        len(CLASS_NAMES),
        activation="softmax",
        name="maturity_classifier",
    )(x)

    model = tf.keras.Model(
        inputs=inputs,
        outputs=outputs,
        name="avoruna_mobilenetv2",
    )

    model.compile(
        optimizer=tf.keras.optimizers.Adam(
            learning_rate=1e-3,
        ),
        loss=(
            "sparse_categorical_crossentropy"
        ),
        metrics=[
            tf.keras.metrics
            .SparseCategoricalAccuracy(
                name="accuracy",
            )
        ],
    )

    return model


# =========================================================
# GUARDADO DE RESULTADOS
# =========================================================

def save_labels() -> None:
    LABELS_OUTPUT_PATH.write_text(
        "\n".join(
            CLASS_NAMES
        )
        + "\n",
        encoding="utf-8",
    )


def save_summary(
    history,
    dataset_counts: dict,
    test_loss: float,
    test_accuracy: float,
) -> None:
    """
    Guarda las métricas principales del entrenamiento.
    """

    history_data = history.history

    val_losses = history_data.get(
        "val_loss",
        [],
    )

    val_accuracies = history_data.get(
        "val_accuracy",
        [],
    )

    summary = {
        "architecture": "MobileNetV2",
        "image_size": [
            IMG_HEIGHT,
            IMG_WIDTH,
        ],
        "batch_size": BATCH_SIZE,
        "seed": SEED,
        "class_names": CLASS_NAMES,
        "dataset_counts": dataset_counts,
        "epochs_requested": EPOCHS,
        "epochs_completed": len(
            history_data.get(
                "loss",
                [],
            )
        ),
        "best_val_loss": (
            float(min(val_losses))
            if val_losses
            else None
        ),
        "best_val_accuracy": (
            float(max(val_accuracies))
            if val_accuracies
            else None
        ),
        "test_loss": float(
            test_loss
        ),
        "test_accuracy": float(
            test_accuracy
        ),
    }

    METRICS_OUTPUT_PATH.write_text(
        json.dumps(
            summary,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


# =========================================================
# ENTRENAMIENTO
# =========================================================

def main() -> None:
    random.seed(SEED)
    tf.random.set_seed(SEED)

    # Debe existir antes de usar ModelCheckpoint.
    MODELS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("=" * 68)
    print("ENTRENAMIENTO DEL MODELO AVORUNA")
    print("=" * 68)

    print(
        "\n1. Validando el dataset..."
    )

    dataset_counts = (
        validate_dataset()
    )

    print(
        "\n2. Cargando imágenes..."
    )

    (
        train_ds,
        val_ds,
        test_ds,
    ) = build_datasets()

    print(
        "\nOrden de clases:"
    )

    for index, class_name in enumerate(
        CLASS_NAMES
    ):
        print(
            f"  {index}: {class_name}"
        )

    print(
        "\n3. Construyendo MobileNetV2..."
    )

    model = build_model()

    model.summary()

    callbacks = [
        tf.keras.callbacks
        .ModelCheckpoint(
            filepath=str(
                BEST_MODEL_PATH
            ),
            monitor="val_loss",
            mode="min",
            save_best_only=True,
            verbose=1,
        ),

        tf.keras.callbacks
        .EarlyStopping(
            monitor="val_loss",
            mode="min",
            patience=5,
            restore_best_weights=True,
            verbose=1,
        ),

        tf.keras.callbacks
        .ReduceLROnPlateau(
            monitor="val_loss",
            mode="min",
            factor=0.30,
            patience=2,
            min_lr=1e-6,
            verbose=1,
        ),

        tf.keras.callbacks
        .CSVLogger(
            filename=str(
                TRAINING_LOG_PATH
            ),
        ),
    ]

    print(
        "\n4. Entrenando modelo..."
    )

    history = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=EPOCHS,
        callbacks=callbacks,
    )

    print(
        "\n5. Cargando el mejor modelo..."
    )

    best_model = (
        tf.keras.models
        .load_model(
            BEST_MODEL_PATH
        )
    )

    print(
        "\n6. Evaluando con imágenes de test..."
    )

    test_loss, test_accuracy = (
        best_model.evaluate(
            test_ds,
            verbose=1,
        )
    )

    print(
        f"\nTest loss: "
        f"{test_loss:.4f}"
    )

    print(
        "Test accuracy: "
        f"{test_accuracy * 100:.2f}%"
    )

    print(
        "\n7. Guardando modelo final..."
    )

    best_model.save(
        MODEL_OUTPUT_PATH
    )

    save_labels()

    save_summary(
        history=history,
        dataset_counts=dataset_counts,
        test_loss=test_loss,
        test_accuracy=test_accuracy,
    )

    print("\n" + "=" * 68)
    print("ENTRENAMIENTO COMPLETADO")
    print("=" * 68)

    print(
        f"Modelo final:\n"
        f"{MODEL_OUTPUT_PATH}"
    )

    print(
        f"\nMejor checkpoint:\n"
        f"{BEST_MODEL_PATH}"
    )

    print(
        f"\nEtiquetas:\n"
        f"{LABELS_OUTPUT_PATH}"
    )

    print(
        f"\nResumen:\n"
        f"{METRICS_OUTPUT_PATH}"
    )

    print(
        f"\nRegistro de épocas:\n"
        f"{TRAINING_LOG_PATH}"
    )


if __name__ == "__main__":
    main()
