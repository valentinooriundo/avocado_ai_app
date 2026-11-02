from __future__ import annotations

from services.camera_capture_service import (
    capture_image_with_assistance,
)
from services.ripeness_inference_service import (
    predict_ripeness,
)


def main() -> None:
    print("Abriendo cámara...")

    image_path = (
        capture_image_with_assistance()
    )

    if not image_path:
        print(
            "La captura fue cancelada "
            "o no se pudo abrir la cámara."
        )
        return

    print(
        f"\nImagen guardada en:\n{image_path}"
    )
    print("\nAnalizando madurez...")

    result = predict_ripeness(
        image_path
    )

    print("\n" + "=" * 62)
    print("RESULTADO DE CÁMARA - AVORUNA")
    print("=" * 62)

    print(
        f"Nivel:      {result['label_text']}"
    )
    print(
        "Confianza:  "
        f"{result['confidence'] * 100:.2f}%"
    )
    print(
        "Margen:     "
        f"{result['margin'] * 100:.2f}%"
    )
    print(
        "Confiable:  "
        f"{'Sí' if result['is_reliable'] else 'No'}"
    )
    print(
        f"Estado:     {result['status']}"
    )
    print(
        "\nRecomendación:\n"
        f"{result['recommended_action']}"
    )

    print("\nPuntajes:")

    for label, score in sorted(
        result["scores"].items(),
        key=lambda item: item[1],
        reverse=True,
    ):
        print(
            f"  {label}: "
            f"{score * 100:.2f}%"
        )


if __name__ == "__main__":
    main()
