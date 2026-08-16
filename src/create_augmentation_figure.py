import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch


fig, ax = plt.subplots(figsize=(16, 9))

ax.set_xlim(0, 16)
ax.set_ylim(0, 9)
ax.axis("off")


# Các bước trong pipeline
steps = [
    ("Ảnh gốc", "Input Image"),
    ("Random Resized Crop", "224 × 224\nscale = 0.5 – 1.0"),
    ("Random Horizontal Flip", "p = 0.5"),
    ("Random Rotation", "±15°"),
    ("Color Jitter", "Brightness = 0.2\nContrast = 0.2\nSaturation = 0.1"),
    ("ToTensor", "Chuyển ảnh → Tensor"),
    ("Normalize", "ImageNet Mean / Std"),
    ("Ảnh đầu vào CNN", "224 × 224 × 3")
]


# Vị trí các khối
x_positions = [0.5, 2.55, 4.6, 6.65, 8.7, 10.75, 12.8, 14.85]
y = 4.0

box_width = 1.55
box_height = 1.5


# Vẽ các khối
for i, (title, subtitle) in enumerate(steps):

    x = x_positions[i]

    box = FancyBboxPatch(
        (x, y),
        box_width,
        box_height,
        boxstyle="round,pad=0.05,rounding_size=0.12",
        linewidth=1.5,
        edgecolor="black",
        facecolor="white"
    )

    ax.add_patch(box)

    ax.text(
        x + box_width / 2,
        y + 0.95,
        title,
        ha="center",
        va="center",
        fontsize=11,
        fontweight="bold"
    )

    ax.text(
        x + box_width / 2,
        y + 0.45,
        subtitle,
        ha="center",
        va="center",
        fontsize=9
    )


# Vẽ mũi tên giữa các bước
for i in range(len(steps) - 1):

    x_start = x_positions[i] + box_width
    x_end = x_positions[i + 1]

    ax.annotate(
        "",
        xy=(x_end, y + box_height / 2),
        xytext=(x_start, y + box_height / 2),
        arrowprops=dict(
            arrowstyle="->",
            linewidth=1.5
        )
    )


# Tiêu đề
ax.text(
    8,
    7.3,
    "Quy trình tăng cường và tiền xử lý ảnh trong tập huấn luyện",
    ha="center",
    va="center",
    fontsize=18,
    fontweight="bold"
)


# Chú thích
ax.text(
    8,
    2.0,
    "Các phép biến đổi ngẫu nhiên chỉ được áp dụng trên tập Train",
    ha="center",
    va="center",
    fontsize=11
)


# Lưu ảnh
output_path = "figures/data_augmentation_pipeline.png"

plt.savefig(
    output_path,
    dpi=300,
    bbox_inches="tight"
)

plt.show()

print(f"Đã tạo: {output_path}")