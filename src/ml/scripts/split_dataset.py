from __future__ import annotations

import random
import shutil
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[3]

DATASET_DIR = (
    BASE_DIR
    / "src"
    / "ml"
    / "dataset"
)

RAW_DIR = DATASET_DIR / "raw"

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

TRAIN_RATIO = 0.70
VAL_RATIO = 0.15
TEST_RATIO = 0.15

SEED = 123


def get_images(
    class_directory: Path,
) -> list[Path]:
    return [
        path
        for path in class_directory.rglob("*")
        if path.is_file()
        and path.suffix.lower()
        in VALID_EXTENSIONS
    ]


def clear_output_directories() -> None:
    """
    Elimina las divisiones anteriores para evitar
    duplicados al ejecutar el script nuevamente.
    """

    for split_name in [
        "train",
        "val",
        "test",
    ]:
        split_directory = (
            DATASET_DIR
            / split_name
        )

        if split_directory.exists():
            shutil.rmtree(
                split_directory
            )


def copy_images(
    images: list[Path],
    destination: Path,
) -> None:
    destination.mkdir(
        parents=True,
        exist_ok=True,
    )

    for image_path in images:
        shutil.copy2(
            image_path,
            destination / image_path.name,
        )


def split_class(
    class_name: str,
    random_generator: random.Random,
) -> dict[str, int]:
    source_directory = (
        RAW_DIR
        / class_name
    )

    if not source_directory.exists():
        raise FileNotFoundError(
            f"No existe la carpeta: "
            f"{source_directory}"
        )

    images = get_images(
        source_directory
    )

    if not images:
        raise ValueError(
            f"No hay imágenes en: "
            f"{source_directory}"
        )

    random_generator.shuffle(
        images
    )

    total = len(images)

    train_count = int(
        total * TRAIN_RATIO
    )

    val_count = int(
        total * VAL_RATIO
    )

    test_count = (
        total
        - train_count
        - val_count
    )

    train_images = images[
        :train_count
    ]

    val_images = images[
        train_count:
        train_count + val_count
    ]

    test_images = images[
        train_count + val_count:
    ]

    copy_images(
        train_images,
        DATASET_DIR
        / "train"
        / class_name,
    )

    copy_images(
        val_images,
        DATASET_DIR
        / "val"
        / class_name,
    )

    copy_images(
        test_images,
        DATASET_DIR
        / "test"
        / class_name,
    )

    return {
        "total": total,
        "train": len(train_images),
        "val": len(val_images),
        "test": len(test_images),
    }


def main() -> None:
    if not RAW_DIR.exists():
        raise FileNotFoundError(
            "No existe la carpeta raw:\n"
            f"{RAW_DIR}"
        )

    print("=" * 60)
    print("DIVISIÓN DEL DATASET DE AVORUNA")
    print("=" * 60)

    clear_output_directories()

    random_generator = random.Random(
        SEED
    )

    total_general = {
        "raw": 0,
        "train": 0,
        "val": 0,
        "test": 0,
    }

    for class_name in CLASS_NAMES:
        result = split_class(
            class_name,
            random_generator,
        )

        total_general["raw"] += (
            result["total"]
        )

        total_general["train"] += (
            result["train"]
        )

        total_general["val"] += (
            result["val"]
        )

        total_general["test"] += (
            result["test"]
        )

        print()
        print(f"Clase: {class_name}")
        print(
            f"  Originales: {result['total']}"
        )
        print(
            f"  Train:      {result['train']}"
        )
        print(
            f"  Val:        {result['val']}"
        )
        print(
            f"  Test:       {result['test']}"
        )

    print()
    print("-" * 60)
    print(
        f"Total originales: "
        f"{total_general['raw']}"
    )
    print(
        f"Total train:      "
        f"{total_general['train']}"
    )
    print(
        f"Total val:        "
        f"{total_general['val']}"
    )
    print(
        f"Total test:       "
        f"{total_general['test']}"
    )
    print("-" * 60)

    print()
    print(
        "División completada correctamente."
    )

    print(
        "Las imágenes originales continúan "
        "intactas dentro de raw."
    )


if __name__ == "__main__":
    main()
