from __future__ import annotations

from pathlib import Path
from typing import Tuple

import cv2
import numpy as np
from PIL import Image

IMG_SIZE: Tuple[int, int] = (224, 224)


def load_image_with_pillow(image_path: str | Path, target_size: Tuple[int, int] = IMG_SIZE) -> np.ndarray:
    """
    Carga una imagen con Pillow, la convierte a RGB, la redimensiona
    y retorna un numpy array float32.
    """
    image_path = Path(image_path)
    if not image_path.exists():
        raise FileNotFoundError(f"No existe la imagen: {image_path}")

    image = Image.open(image_path).convert("RGB")
    image = image.resize(target_size)
    image_array = np.array(image, dtype=np.float32)
    return image_array


def load_image_with_opencv(image_path: str | Path, target_size: Tuple[int, int] = IMG_SIZE) -> np.ndarray:
    """
    Carga una imagen con OpenCV, la convierte de BGR a RGB, la redimensiona
    y retorna un numpy array float32.
    """
    image_path = Path(image_path)
    if not image_path.exists():
        raise FileNotFoundError(f"No existe la imagen: {image_path}")

    image = cv2.imread(str(image_path))
    if image is None:
        raise ValueError(f"No se pudo leer la imagen: {image_path}")

    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    image = cv2.resize(image, target_size)
    image_array = image.astype(np.float32)
    return image_array


def prepare_image_for_mobilenet(image_path: str | Path, target_size: Tuple[int, int] = IMG_SIZE) -> np.ndarray:
    """
    Carga una imagen, la prepara para MobileNetV2 y retorna un tensor
    con shape (1, alto, ancho, 3).
    """
    image_array = load_image_with_pillow(image_path, target_size=target_size)
    image_array = np.expand_dims(image_array, axis=0)
    image_array = image_array.astype(np.float32)
    return image_array
