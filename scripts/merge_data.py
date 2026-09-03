import os
import shutil
from pathlib import Path

PROJECT_ROOT = Path(os.getcwd())
PLANT_DOC_DIR = PROJECT_ROOT / "data" / "PlantDoc"
PLANT_VILLAGE_DIR = PROJECT_ROOT / "data" / "PlantVillage"

# Mapping chuẩn hoá (Key: PlantDoc, Value: Từ khoá nhận diện trong PlantVillage)
CLASS_MAPPING = {
    "Apple leaf": "Apple___healthy",
    "Apple rust leaf": "Apple___Cedar_apple_rust",
    "Apple Scab Leaf": "Apple___Apple_scab",
    "Bell_pepper leaf": "Pepper,_bell___healthy",
    "Bell_pepper leaf spot": "Pepper,_bell___Bacterial_spot",
    "Blueberry leaf": "Blueberry___healthy",
    "Cherry leaf": "Cherry_(including_sour)___healthy",
    "Corn Gray leaf spot": "Cercospora_leaf_spot",
    "Corn leaf blight": "Northern_Leaf_Blight",
    "Corn rust leaf": "Common_rust",
    "grape leaf": "Grape___healthy",
    "grape leaf black rot": "Grape___Black_rot",
    "Peach leaf": "Peach___healthy",
    "Potato leaf early blight": "Potato___Early_blight",
    "Potato leaf late blight": "Potato___Late_blight",
    "Raspberry leaf": "Raspberry___healthy",
    "Soyabean leaf": "Soybean___healthy",
    "Squash Powdery mildew leaf": "Squash___Powdery_mildew",
    "Strawberry leaf": "Strawberry___healthy",
    "Tomato Early blight leaf": "Tomato___Early_blight",
    "Tomato leaf": "Tomato___healthy",
    "Tomato leaf bacterial spot": "Tomato___Bacterial_spot",
    "Tomato leaf late blight": "Tomato___Late_blight",
    "Tomato leaf mosaic virus": "Tomato_mosaic_virus",
    "Tomato leaf yellow virus": "Yellow_Leaf_Curl_Virus",
    "Tomato mold leaf": "Leaf_Mold",
    "Tomato Septoria leaf spot": "Septoria_leaf_spot",
    "Tomato two spotted spider mites leaf": "Spider_mites"
}

def find_target_folder(base_dir, keyword):
    for entry in os.listdir(base_dir):
        full_path = base_dir / entry
        if full_path.is_dir() and keyword.lower() in entry.lower():
            return full_path
    return None

def merge_datasets():
    print("--- CHUẨN ĐOÁN LỖI ĐƯỜNG DẪN ---")
    print(f"Thư mục gốc đang chạy (PROJECT_ROOT): {PROJECT_ROOT}")
    print(f"Đang tìm PlantDoc tại: {PLANT_DOC_DIR} (Tồn tại: {PLANT_DOC_DIR.exists()})")
    print(f"Đang tìm PlantVillage tại: {PLANT_VILLAGE_DIR} (Tồn tại: {PLANT_VILLAGE_DIR.exists()})\n")

    if not PLANT_DOC_DIR.exists() or not PLANT_VILLAGE_DIR.exists():
        print("DỪNG LẠI: Python vẫn không thấy thư mục data. Hãy kiểm tra Terminal đang mở ở đâu!")
        return

    total_copied = 0

    for split_folder in ["train", "test"]:
        split_path = PLANT_DOC_DIR / split_folder
        if not split_path.exists():
            print(f"Skip: Không thấy folder {split_path}")
            continue

        print(f"\n---> Đang xử lý: {split_folder}")

        for doc_class, target_keyword in CLASS_MAPPING.items():
            source_dir = split_path / doc_class
            target_dir = find_target_folder(PLANT_VILLAGE_DIR, target_keyword)

            if not source_dir.exists():
                continue

            if target_dir is None:
                print(f"Không tìm thấy folder tương ứng cho: '{doc_class}' (Keyword: '{target_keyword}')")
                continue

            images = [f for f in os.listdir(source_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            copied_in_class = 0

            for img_name in images:
                src_path = source_dir / img_name
                new_img_name = f"pd_{split_folder}_{img_name}"
                dst_path = target_dir / new_img_name

                try:
                    shutil.copy(src_path, dst_path)
                    copied_in_class += 1
                    total_copied += 1
                except Exception as e:
                    print(f"Lỗi copy {img_name}: {e}")

            print(f"  + [{doc_class}] -> Copy thành công {copied_in_class} ảnh sang [{target_dir.name}]")

    print(f"\n==========================================")
    print(f"HOÀN TẤT: Đã trộn tổng cộng {total_copied} bức ảnh!")
    print(f"==========================================")

if __name__ == "__main__":
    merge_datasets()