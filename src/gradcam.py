import sys
import os
import torch
import torch.nn.functional as F
import numpy as np
import matplotlib.pyplot as plt
import torchvision.transforms as T
from PIL import Image
from pytorch_grad_cam import GradCAM
from pytorch_grad_cam.utils.image import show_cam_on_image
from src.utils import DISPLAY_NAMES

def visualize_gradcam(model, image_path, true_label=None):
    print(f"Analyzing image: {image_path}")

    transform = T.Compose([
        T.Resize(299),              
        T.CenterCrop(224),           
        T.ToTensor(),               
        T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    try:
        img_pil = Image.open(image_path).convert('RGB')
    except FileNotFoundError:
        print(f"ERROR: Cannot find image at {image_path}")
        return

    image_tensor = transform(img_pil)
    input_tensor = image_tensor.unsqueeze(0)

    device = next(model.parameters()).device
    input_tensor = input_tensor.to(device)

    model.eval()
    with torch.no_grad():
        outputs = model(input_tensor)
        
        probabilities = F.softmax(outputs, dim=1)[0]
        
        top5_prob, top5_catid = torch.topk(probabilities, 5)
        top5_prob = top5_prob.cpu().numpy() * 100
        top5_catid = top5_catid.cpu().numpy()
        
        predicted_idx = top5_catid[0]

    print(f"AI Prediction: {DISPLAY_NAMES[predicted_idx]} ({top5_prob[0]:.2f}%)")

    target_layers = [model.layer4[-1]]
    cam = GradCAM(model=model, target_layers=target_layers)
    grayscale_cam = cam(input_tensor=input_tensor, targets=None)[0, :]

    mean = np.array([0.485, 0.456, 0.406])
    std = np.array([0.229, 0.224, 0.225])
    rgb_img = image_tensor.cpu().permute(1, 2, 0).numpy()
    rgb_img = np.clip(std * rgb_img + mean, 0, 1) 

    visualization = show_cam_on_image(rgb_img, grayscale_cam, use_rgb=True)

    plt.figure(figsize=(16, 5))
    
    plt.subplot(1, 3, 1)
    plt.imshow(rgb_img)
    title_1 = f"Original Image"
    if true_label:
        title_1 += f"\nTrue Label: {true_label}"
    plt.title(title_1, fontsize=11, fontweight='bold', color='darkgreen')
    plt.axis('off')

    plt.subplot(1, 3, 2)
    plt.imshow(visualization)
    is_correct = (DISPLAY_NAMES[predicted_idx] == true_label) if true_label else False
    color = 'blue' if is_correct else 'red'
    plt.title(f"Grad-CAM Heatmap\nAI Predict: {DISPLAY_NAMES[predicted_idx]}", fontsize=11, fontweight='bold', color=color)
    plt.axis('off')
    
    plt.subplot(1, 3, 3)
    y_pos = np.arange(5)
    top5_names = [DISPLAY_NAMES[i] for i in top5_catid]
    
    bars = plt.barh(y_pos, top5_prob, align='center', color='skyblue', edgecolor='black')
    plt.yticks(y_pos, top5_names, fontsize=9)
    plt.gca().invert_yaxis()
    plt.xlabel('Probability (%)')
    plt.title('Top 5 Predictions', fontsize=12, fontweight='bold')
    plt.xlim(0, 100)
    
    for bar, prob in zip(bars, top5_prob):
        plt.text(bar.get_width() + 2, bar.get_y() + bar.get_height()/2, 
                 f'{prob:.2f}%', va='center', ha='left', fontsize=10, fontweight='bold')

    plt.tight_layout()
    plt.show()