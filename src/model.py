import torch
import torch.nn as nn
from torchvision import models
from torchvision.models import ResNet18_Weights


def build_model(n_classes: int, freeze_backbone: bool = True) -> nn.Module:
    model = models.resnet18(weights=ResNet18_Weights.IMAGENET1K_V1)

    if freeze_backbone:
        for param in model.parameters():
            param.requires_grad = False

    in_features = model.fc.in_features
    model.fc = nn.Sequential(
        nn.Dropout(p=0.3),
        nn.Linear(in_features, n_classes),
    )

    return model


def unfreeze_backbone(model: nn.Module) -> None:
    for param in model.parameters():
        param.requires_grad = True


def count_parameters(model: nn.Module) -> dict:
    total = sum(p.numel() for p in model.parameters())
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)

    return {
        "total": total,
        "trainable": trainable,
        "frozen": total - trainable,
    }


def save_checkpoint(model: nn.Module, path: str, meta: dict | None = None) -> None:
    torch.save(
        {
            "state_dict": model.state_dict(),
            "meta": meta or {},
        },
        path,
    )


def load_checkpoint(model: nn.Module, path: str) -> dict:
    checkpoint = torch.load(path, map_location="cpu")
    model.load_state_dict(checkpoint["state_dict"])
    return checkpoint.get("meta", {})