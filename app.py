import base64
import json
from pathlib import Path

import torch

from fastapi import (
    FastAPI,
    UploadFile,
    File,
    HTTPException
)

from fastapi.middleware.cors import CORSMiddleware

from PIL import Image

from src.load_model import load_best_model
from src.gradcam import predict_with_gradcam
from src.disease_database import get_disease


# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent

DATABASE_PATH = (
    PROJECT_ROOT
    / "data"
    / "diseases.json"
)


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title="AI Plant Disease API",
    description="API nhận dạng và chẩn đoán bệnh trên lá cây bằng AI",
    version="2.0.0"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,

    allow_origins=["*"],

    allow_credentials=False,

    allow_methods=["*"],

    allow_headers=["*"],
)


# ============================================================
# DEVICE
# ============================================================

device = torch.device(
    "cuda"
    if torch.cuda.is_available()
    else "cpu"
)

print("=" * 60)
print("AI PLANT DISEASE API")
print("=" * 60)

print(
    f"Device: {device}"
)


# ============================================================
# LOAD MODEL
# ============================================================

print("Loading trained model...")

model = load_best_model(
    device
)

print("AI model ready.")


# ============================================================
# LOAD DISEASE DATABASE
# ============================================================

if not DATABASE_PATH.exists():

    raise FileNotFoundError(
        f"Không tìm thấy diseases.json:\n{DATABASE_PATH}"
    )


with open(
    DATABASE_PATH,
    "r",
    encoding="utf-8"
) as f:

    disease_db = json.load(f)


print(
    f"Disease database loaded: "
    f"{len(disease_db)} diseases"
)


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/")
def root():

    return {
        "success": True,

        "message": "AI Plant Disease API is running.",

        "model": "resnet18_phase2_best.pth",

        "device": str(device),

        "diseases": len(disease_db)
    }


# ============================================================
# PREDICT
# ============================================================

@app.post("/api/predict")
def predict_disease(
    file: UploadFile = File(...)
):

    # --------------------------------------------------------
    # Validate file
    # --------------------------------------------------------

    if not file.content_type:

        raise HTTPException(
            status_code=400,
            detail="Không xác định được loại file."
        )


    allowed_types = [
        "image/jpeg",
        "image/jpg",
        "image/png",
        "image/webp"
    ]


    if file.content_type not in allowed_types:

        raise HTTPException(
            status_code=400,
            detail=(
                "File không phải ảnh hợp lệ. "
                "Chỉ hỗ trợ JPG, PNG, WEBP."
            )
        )


    # --------------------------------------------------------
    # Read image
    # --------------------------------------------------------

    try:

        image_bytes = file.file.read()

        image = Image.open(
            __import__("io").BytesIO(
                image_bytes
            )
        ).convert("RGB")

    except Exception as e:

        raise HTTPException(
            status_code=400,
            detail=f"Không thể đọc ảnh: {str(e)}"
        )


    # --------------------------------------------------------
    # AI + GRAD-CAM
    # --------------------------------------------------------

    try:

        result = predict_with_gradcam(
            model=model,
            image=image,
            device=device
        )

    except Exception as e:

        print(
            "Prediction error:",
            repr(e)
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Lỗi khi chạy AI: "
                f"{str(e)}"
            )
        )


    # --------------------------------------------------------
    # Prediction information
    # --------------------------------------------------------

    predicted_class = result[
        "predicted_class"
    ]

    confidence = result[
        "confidence"
    ]


    # --------------------------------------------------------
    # Disease database
    # --------------------------------------------------------

    disease_info = get_disease(
        predicted_class
    )


    # Nếu get_disease không tìm thấy,
    # thử lấy trực tiếp từ JSON.

    if disease_info is None:

        disease_info = disease_db.get(
            predicted_class,
            {}
        )


    # --------------------------------------------------------
    # Convert images -> Base64
    # --------------------------------------------------------

    original_base64 = base64.b64encode(
        result["original_image"]
    ).decode("utf-8")


    gradcam_base64 = base64.b64encode(
        result["gradcam_image"]
    ).decode("utf-8")


    # --------------------------------------------------------
    # RESPONSE
    # --------------------------------------------------------

    return {

        "success": True,

        # -----------------------------------------------
        # AI
        # -----------------------------------------------

        "ai_prediction": predicted_class,

        "confidence": confidence,

        "confidence_percentage":
            result[
                "confidence_percentage"
            ],

        # -----------------------------------------------
        # Disease DB key
        # -----------------------------------------------

        "database_key": predicted_class,

        # -----------------------------------------------
        # Disease information
        # -----------------------------------------------

        "info": disease_info,

        # -----------------------------------------------
        # Top 5
        # -----------------------------------------------

        "top5": result["top5"],

        # -----------------------------------------------
        # Images
        # -----------------------------------------------

        "original_image":
            f"data:image/png;base64,{original_base64}",

        "gradcam_image":
            f"data:image/png;base64,{gradcam_base64}"
    }


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "app:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )