import torch
from pathlib import Path
import os
from src.model import build_model, load_checkpoint

def load_best_model(device):
    project_root = Path(os.path.abspath(__file__)).parent.parent
    checkpoint_path = str(project_root / "models" / "resnet18_phase2_best.pth")

    print(f"Loading weights from: {checkpoint_path}")

    model = build_model(n_classes=38, freeze_backbone=False).to(device)

    load_checkpoint(model, checkpoint_path)
    
    model.eval()
    return model