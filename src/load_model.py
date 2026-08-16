import os
from pathlib import Path

import torch

from src.model import build_model, load_checkpoint


def load_best_model(device=None):
    """
    Load model ResNet18 đã train từ:
    models/resnet18_phase2_best.pth
    """

    if device is None:
        device = torch.device(
            "cuda" if torch.cuda.is_available() else "cpu"
        )

    project_root = Path(__file__).resolve().parent.parent

    checkpoint_path = (
        project_root
        / "models"
        / "resnet18_phase2_best.pth"
    )

    if not checkpoint_path.exists():
        raise FileNotFoundError(
            f"Không tìm thấy model:\n{checkpoint_path}"
        )

    print("=" * 60)
    print("LOADING AI MODEL")
    print("=" * 60)

    print(f"Model path : {checkpoint_path}")
    print(f"Device     : {device}")

    # 38 class đúng với PlantVillage
    model = build_model(
        n_classes=38,
        freeze_backbone=False
    )

    model = model.to(device)

    # Load checkpoint
    load_checkpoint(
        model,
        str(checkpoint_path)
    )

    model.eval()

    print("Model loaded successfully.")
    print("=" * 60)

    return model