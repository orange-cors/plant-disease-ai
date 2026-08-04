import random
import json
from pathlib import Path

import numpy as np
import torch


def set_seed(seed: int = 42) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False


def save_json(obj: dict, path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f, indent=2)


def load_json(path: str | Path) -> dict:
    with open(path) as f:
        return json.load(f)

DISPLAY_NAMES = [
    "Apple: Apple Scab",
    "Apple: Black Rot",
    "Apple: Cedar Apple Rust",
    "Apple: Healthy",
    "Blueberry: Healthy",
    "Cherry: Powdery Mildew",
    "Cherry: Healthy",
    "Corn: Cercospora Leaf Spot",
    "Corn: Common Rust",
    "Corn: Northern Leaf Blight",
    "Corn: Healthy",
    "Grape: Black Rot",
    "Grape: Esca (Black Measles)",
    "Grape: Leaf Blight",
    "Grape: Healthy",
    "Orange: Citrus Greening",
    "Peach: Bacterial Spot",
    "Peach: Healthy",
    "Pepper: Bacterial Spot",
    "Pepper: Healthy",
    "Potato: Early Blight",
    "Potato: Late Blight",
    "Potato: Healthy",
    "Raspberry: Healthy",
    "Soybean: Healthy",
    "Squash: Powdery Mildew",
    "Strawberry: Leaf Scorch",
    "Strawberry: Healthy",
    "Tomato: Bacterial Spot",
    "Tomato: Early Blight",
    "Tomato: Late Blight",
    "Tomato: Leaf Mold",
    "Tomato: Septoria Leaf Spot",
    "Tomato: Spider Mites",
    "Tomato: Target Spot",
    "Tomato: Yellow Leaf Curl Virus",
    "Tomato: Mosaic Virus",
    "Tomato: Healthy",
]