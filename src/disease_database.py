import json
from pathlib import Path


# Lấy thư mục gốc của project
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Đường dẫn tới diseases.json
JSON_PATH = PROJECT_ROOT / "data" / "diseases.json"


def load_diseases():
    
    with open(JSON_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def get_disease(class_name):

    diseases = load_diseases()

    return diseases.get(class_name)