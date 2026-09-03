import io

import numpy as np
import torch
import torch.nn.functional as F
import torchvision.transforms as T

from PIL import Image

from pytorch_grad_cam import GradCAM
from pytorch_grad_cam.utils.image import show_cam_on_image

from src.utils import DISPLAY_NAMES


# IMAGE TRANSFORM
TRANSFORM = T.Compose([
    T.Resize(256),
    T.CenterCrop(224),
    T.ToTensor(),
    T.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])


# IMAGE -> TENSOR
def prepare_image(image):

    image = image.convert("RGB")

    tensor = TRANSFORM(image)

    return tensor.unsqueeze(0)


# ORIGINAL IMAGE FOR GRAD-CAM
def get_display_image(image):

    image = image.convert("RGB")

    tensor = TRANSFORM(image)

    mean = np.array(
        [0.485, 0.456, 0.406]
    )

    std = np.array(
        [0.229, 0.224, 0.225]
    )

    rgb = tensor.squeeze(0).permute(
        1, 2, 0
    ).numpy()

    rgb = rgb * std + mean

    rgb = np.clip(
        rgb,
        0,
        1
    )

    return rgb


# NUMPY -> PNG BYTES
def numpy_to_png_bytes(image):

    image = np.clip(
        image * 255,
        0,
        255
    ).astype(np.uint8)

    pil_image = Image.fromarray(
        image
    )

    buffer = io.BytesIO()

    pil_image.save(
        buffer,
        format="PNG"
    )

    return buffer.getvalue()


# MAIN PREDICTION
def predict_with_gradcam(
    model,
    image,
    device
):
    input_tensor = prepare_image(
        image
    ).to(device)

    model.eval()

    with torch.no_grad():

        outputs = model(
            input_tensor
        )

        probabilities = F.softmax(
            outputs,
            dim=1
        )[0]

        top5_prob, top5_indices = torch.topk(
            probabilities,
            k=5
        )

    top5_prob = (
        top5_prob
        .detach()
        .cpu()
        .numpy()
    )

    top5_indices = (
        top5_indices
        .detach()
        .cpu()
        .numpy()
    )

    predicted_idx = int(
        top5_indices[0]
    )

    predicted_class = DISPLAY_NAMES[
        predicted_idx
    ]

    confidence = float(
        top5_prob[0]
    )

    top5 = []

    for idx, prob in zip(
        top5_indices,
        top5_prob
    ):

        idx = int(idx)

        top5.append({
            "index": idx,
            "class_name": DISPLAY_NAMES[idx],
            "probability": float(prob),
            "percentage": float(prob * 100)
        })

    target_layers = [
        model.layer4[-1]
    ]

    cam = GradCAM(
        model=model,
        target_layers=target_layers
    )

    grayscale_cam = cam(
        input_tensor=input_tensor,
        targets=None
    )[0]

    rgb_img = get_display_image(
        image
    )

    visualization = show_cam_on_image(
        rgb_img,
        grayscale_cam,
        use_rgb=True
    )

    original_png = numpy_to_png_bytes(
        rgb_img
    )

    heatmap_png = numpy_to_png_bytes(
        visualization / 255.0
    )

    return {
        "predicted_index": predicted_idx,

        "predicted_class": predicted_class,

        "confidence": confidence,

        "confidence_percentage": confidence * 100,

        "top5": top5,

        "original_image": original_png,

        "gradcam_image": heatmap_png
    }