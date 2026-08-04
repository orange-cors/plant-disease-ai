from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
)
from torch.utils.data import DataLoader
from tqdm import tqdm

from .utils import DISPLAY_NAMES, save_json


@torch.no_grad()
def collect_predictions(
    model: nn.Module,
    loader: DataLoader,
    device: torch.device,
):
    model.eval()

    all_labels = []
    all_predictions = []

    for images, labels in tqdm(loader, desc="predict"):
        images = images.to(device)

        outputs = model(images)
        predictions = outputs.argmax(dim=1).cpu().numpy()

        all_predictions.extend(predictions)
        all_labels.extend(labels.numpy())

    return np.array(all_labels), np.array(all_predictions)


def compute_classification_metrics(
    y_true,
    y_pred,
    class_names,
):
    report = classification_report(
        y_true,
        y_pred,
        labels=list(range(len(class_names))),
        target_names=class_names,
        output_dict=True,
        zero_division=0,
    )

    report["overall_accuracy"] = accuracy_score(y_true, y_pred)

    return report


def save_classification_report(
    report,
    json_path,
    csv_path,
):
    save_json(report, json_path)

    report_df = pd.DataFrame(report).transpose()
    Path(csv_path).parent.mkdir(parents=True, exist_ok=True)
    report_df.to_csv(csv_path)


def plot_confusion_matrix(
    y_true,
    y_pred,
    class_names,
    save_path,
    normalize=True,
):
    cm = confusion_matrix(
        y_true,
        y_pred,
        labels=list(range(len(class_names))),
    )

    if normalize:
        row_sums = cm.sum(axis=1, keepdims=True)
        cm = np.divide(
            cm.astype(float),
            row_sums,
            out=np.zeros_like(cm, dtype=float),
            where=row_sums != 0,
        )

    labels = DISPLAY_NAMES if len(DISPLAY_NAMES) == len(class_names) else class_names

    fig, ax = plt.subplots(figsize=(14, 12))
    image = ax.imshow(cm, cmap="Blues")

    fig.colorbar(image, ax=ax)

    ax.set_xticks(np.arange(len(labels)))
    ax.set_yticks(np.arange(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=8)
    ax.set_yticklabels(labels, fontsize=8)

    value_format = ".2f" if normalize else "d"

    for i in range(len(labels)):
        for j in range(len(labels)):
            ax.text(
                j,
                i,
                format(cm[i, j], value_format),
                ha="center",
                va="center",
                fontsize=6,
                color="white" if cm[i, j] > 0.5 else "black",
            )

    ax.set_xlabel("Predicted Label")
    ax.set_ylabel("True Label")

    title = "Normalized Confusion Matrix" if normalize else "Confusion Matrix"
    ax.set_title(title)

    plt.tight_layout()
    Path(save_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.close()


def plot_per_class_f1(
    report,
    class_names,
    save_path,
):
    labels = DISPLAY_NAMES if len(DISPLAY_NAMES) == len(class_names) else class_names
    f1_scores = [report[class_name]["f1-score"] for class_name in class_names]

    fig, ax = plt.subplots(figsize=(10, 7))

    ax.barh(labels, f1_scores)
    ax.set_xlim(0, 1.0)
    ax.set_xlabel("F1-score")
    ax.set_title("Per-Class F1-score")

    for index, value in enumerate(f1_scores):
        ax.text(value + 0.01, index, f"{value:.3f}", va="center", fontsize=8)

    plt.tight_layout()
    Path(save_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.close()


def plot_training_curves(
    history,
    save_path,
):
    epochs = range(1, len(history["train_loss"]) + 1)

    fig, axes = plt.subplots(1, 2, figsize=(12, 4))

    axes[0].plot(epochs, history["train_loss"], marker="o", label="Train")
    axes[0].plot(epochs, history["val_loss"], marker="o", label="Validation")
    axes[0].set_title("Training and Validation Loss")
    axes[0].set_xlabel("Epoch")
    axes[0].set_ylabel("Loss")
    axes[0].legend()
    axes[0].grid(True)

    axes[1].plot(epochs, history["train_accuracy"], marker="o", label="Train")
    axes[1].plot(epochs, history["val_accuracy"], marker="o", label="Validation")
    axes[1].set_title("Training and Validation Accuracy")
    axes[1].set_xlabel("Epoch")
    axes[1].set_ylabel("Accuracy")
    axes[1].set_ylim(0, 1)
    axes[1].legend()
    axes[1].grid(True)

    plt.tight_layout()
    Path(save_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.close()


def run_full_evaluation(
    model,
    test_loader,
    class_names,
    device,
    results_dir,
    figures_dir,
    label,
):
    y_true, y_pred = collect_predictions(model, test_loader, device)

    report = compute_classification_metrics(
        y_true,
        y_pred,
        class_names,
    )

    results_dir = Path(results_dir)
    figures_dir = Path(figures_dir)

    save_classification_report(
        report,
        json_path=results_dir / f"classification_report_{label}.json",
        csv_path=results_dir / f"classification_report_{label}.csv",
    )

    plot_confusion_matrix(
        y_true,
        y_pred,
        class_names,
        save_path=figures_dir / f"confusion_matrix_{label}.png",
        normalize=True,
    )

    plot_per_class_f1(
        report,
        class_names,
        save_path=figures_dir / f"per_class_f1_{label}.png",
    )

    print(f"Accuracy: {report['overall_accuracy']:.4f}")
    print(f"Macro F1: {report['macro avg']['f1-score']:.4f}")
    print(f"Weighted F1: {report['weighted avg']['f1-score']:.4f}")

    return report