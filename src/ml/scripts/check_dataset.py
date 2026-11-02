from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[3]
RAW_DIR = BASE_DIR / "src" / "ml" / "dataset" / "raw"

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


def main() -> None:
    total = 0

    for class_name in CLASS_NAMES:
        class_dir = RAW_DIR / class_name

        if not class_dir.exists():
            print(f"[FALTA] {class_dir}")
            continue

        images = [
            path
            for path in class_dir.rglob("*")
            if path.is_file()
            and path.suffix.lower() in VALID_EXTENSIONS
        ]

        count = len(images)
        total += count

        print(
            f"{class_name}: {count} imágenes"
        )

    print("-" * 40)
    print(f"Total: {total} imágenes")


if __name__ == "__main__":
    main()
