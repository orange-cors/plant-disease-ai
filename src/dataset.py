from pathlib import Path
from typing import Tuple

import numpy as np
import torch
from PIL import Image
from sklearn.model_selection import train_test_split
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms


IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]
IMAGE_SIZE = 224


def get_transforms(split: str) -> transforms.Compose:
    if split == "train":
        return transforms.Compose([
            transforms.RandomResizedCrop(IMAGE_SIZE, scale=(0.5, 1.0)), 
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.RandomRotation(degrees=15),
            transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.1),
            transforms.ToTensor(),
            transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
        ])

    return transforms.Compose([
        transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
        transforms.ToTensor(),
        transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
    ])


class PlantVillageDataset(Dataset):
    def __init__(self, samples: list[Tuple[Path, int]], transform=None):
        self.samples = samples
        self.transform = transform

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int):
        path, label = self.samples[idx]
        image = Image.open(path).convert("RGB")

        if self.transform:
            image = self.transform(image)

        return image, label


def load_plantvillage(
    root: str | Path,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    seed: int = 42,
):
    root = Path(root)
    image_extensions = {".jpg", ".jpeg", ".png"}

    class_dirs = sorted([d.name for d in root.iterdir() if d.is_dir()])

    if not class_dirs:
        raise ValueError(f"Không tìm thấy thư mục class nào bên trong: {root}")

    class_to_idx = {class_name: idx for idx, class_name in enumerate(class_dirs)}

    paths = []
    labels = []
    class_counts = {}

    for class_name in class_dirs:
        class_dir = root / class_name
        files = sorted([
            p for p in class_dir.iterdir()
            if p.is_file() and p.suffix.lower() in image_extensions
        ])

        class_counts[class_name] = len(files)

        for file_path in files:
            paths.append(file_path)
            labels.append(class_to_idx[class_name])

    paths = np.array(paths)
    labels = np.array(labels)

    val_test_ratio = val_ratio + test_ratio

    paths_train, paths_temp, labels_train, labels_temp = train_test_split(
        paths,
        labels,
        test_size=val_test_ratio,
        stratify=labels,
        random_state=seed,
    )

    test_fraction = test_ratio / val_test_ratio

    paths_val, paths_test, labels_val, labels_test = train_test_split(
        paths_temp,
        labels_temp,
        test_size=test_fraction,
        stratify=labels_temp,
        random_state=seed,
    )

    counts = np.array([class_counts[class_name] for class_name in class_dirs], dtype=float)
    class_weights = counts.sum() / (len(counts) * counts)
    class_weights_tensor = torch.tensor(class_weights, dtype=torch.float32)

    def make_samples(split_paths, split_labels):
        return list(zip(split_paths.tolist(), split_labels.tolist()))

    train_dataset = PlantVillageDataset(
        make_samples(paths_train, labels_train),
        transform=get_transforms("train"),
    )

    val_dataset = PlantVillageDataset(
        make_samples(paths_val, labels_val),
        transform=get_transforms("val"),
    )

    test_dataset = PlantVillageDataset(
        make_samples(paths_test, labels_test),
        transform=get_transforms("test"),
    )

    info = {
        "class_names": class_dirs,
        "class_to_idx": class_to_idx,
        "class_counts": class_counts,
        "class_weights": class_weights_tensor,
        "n_classes": len(class_dirs),
        "split_sizes": {
            "train": len(train_dataset),
            "val": len(val_dataset),
            "test": len(test_dataset),
            "total": len(paths),
        },
    }

    return train_dataset, val_dataset, test_dataset, info


def make_loaders(
    train_dataset,
    val_dataset,
    test_dataset,
    batch_size=32,
    num_workers=0,
    pin_memory=False,
    persistent_workers=False,
):
    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=pin_memory,
        persistent_workers=persistent_workers if num_workers > 0 else False,
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=pin_memory,
        persistent_workers=persistent_workers if num_workers > 0 else False,
    )

    test_loader = DataLoader(
        test_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=pin_memory,
        persistent_workers=persistent_workers if num_workers > 0 else False,
    )

    return train_loader, val_loader, test_loader