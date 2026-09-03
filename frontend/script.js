const API_URL = "http://127.0.0.1:8000/api/predict";

const imageInput = document.getElementById("imageInput");
const uploadZone = document.getElementById("uploadZone");
const fileName = document.getElementById("fileName");
const predictButton = document.getElementById("predictButton");
const loading = document.getElementById("loading");
const errorBox = document.getElementById("errorBox");
const resultSection = document.getElementById("resultSection");

imageInput.addEventListener("change", handleFile);

function handleFile() {
    const file = imageInput.files[0];

    if (!file) {
        return;
    }

    if (!file.type.startsWith("image/")) {
        showError("File được chọn không phải là ảnh.");
        return;
    }

    fileName.innerText = file.name;

    // Hiển thị ảnh gốc ngay lập tức
    const imageURL = URL.createObjectURL(file);
    document.getElementById("originalImage").src = imageURL;

    resultSection.style.display = "none";
    errorBox.style.display = "none";
}


["dragenter", "dragover"].forEach(eventName => {
    uploadZone.addEventListener(eventName, event => {
        event.preventDefault();
        uploadZone.classList.add("dragover");
    });
});

["dragleave", "drop"].forEach(eventName => {
    uploadZone.addEventListener(eventName, event => {
        event.preventDefault();
        uploadZone.classList.remove("dragover");
    });
});

uploadZone.addEventListener("drop", event => {
    const files = event.dataTransfer.files;

    if (!files.length) {
        return;
    }

    imageInput.files = files;
    handleFile();
});


function renderList(elementId, items) {
    const list = document.getElementById(elementId);
    list.innerHTML = "";

    if (!Array.isArray(items) || items.length === 0) {
        const li = document.createElement("li");
        li.innerText = "Chưa có thông tin.";
        list.appendChild(li);
        return;
    }

    items.forEach(item => {
        const li = document.createElement("li");
        li.innerText = item;
        list.appendChild(li);
    });
}


function renderTopPredictions(predictions) {
    const container = document.getElementById("topPredictions");
    container.innerHTML = "";

    if (!Array.isArray(predictions) || predictions.length === 0) {
        container.innerHTML = `<p style="color:#64748b">Backend chưa trả về Top 5 predictions.</p>`;
        return;
    }

    predictions.slice(0, 5).forEach((prediction, index) => {
        const name = prediction.class_name || prediction.label || prediction.name || prediction.class || "Unknown";
        
        let probability = Number(prediction.probability ?? prediction.confidence ?? prediction.score ?? 0);
        if (probability <= 1) {
            probability *= 100;
        }

        const item = document.createElement("div");
        item.className = "prediction-item";
        item.innerHTML = `
            <div class="prediction-top">
                <span class="prediction-name">
                    ${index + 1}. ${escapeHTML(name)}
                </span>
                <span class="prediction-percent">
                    ${probability.toFixed(2)}%
                </span>
            </div>
            <div class="progress">
                <div class="progress-bar" style="width:${Math.min(probability, 100)}%"></div>
            </div>
        `;
        container.appendChild(item);
    });
}

function escapeHTML(text) {
    const div = document.createElement("div");
    div.innerText = text;
    return div.innerHTML;
}


predictButton.addEventListener("click", sendToAI);

async function sendToAI() {
    if (imageInput.files.length === 0) {
        showError("Bạn chưa chọn ảnh lá cây.");
        return;
    }

    const file = imageInput.files[0];

    predictButton.disabled = true;
    loading.style.display = "block";
    errorBox.style.display = "none";
    resultSection.style.display = "none";

    const formData = new FormData();
    formData.append("file", file);

    try {
        const response = await fetch(API_URL, {
            method: "POST",
            body: formData
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();
        console.log("AI RESPONSE:", data);

        if (!data.success) {
            throw new Error(data.message || "AI không thể phân tích ảnh.");
        }

        const info = data.info || {};

        document.getElementById("diseaseName").innerText = info.name || data.ai_prediction || "Không xác định";

        const meta = document.getElementById("diseaseMeta");
        meta.innerHTML = "";

        if (info.english_name) {
            meta.innerHTML += `<span class="tag">${escapeHTML(info.english_name)}</span>`;
        }

        if (info.crop) {
            meta.innerHTML += `<span class="tag">🌱 ${escapeHTML(info.crop)}</span>`;
        }

        if (data.database_key) {
            meta.innerHTML += `<span class="tag">${escapeHTML(data.database_key)}</span>`;
        }

        let confidence = Number(data.confidence || 0);

        if (confidence <= 1) {
            confidence *= 100;
        }

        document.getElementById("confidence").innerText = confidence.toFixed(2) + "%";

        document.getElementById("description").innerText = info.description || "Chưa có thông tin.";

        renderList("symptomsList", info.symptoms);
        renderList("causeList", info.cause);
        renderList("preventionList", info.prevention);
        renderList("treatmentList", info.treatment);

        document.getElementById("originalImage").src = URL.createObjectURL(file);

        const gradcam = data.gradcam_image || data.gradcam || data.gradcam_url;

        if (gradcam) {
            document.getElementById("gradcamImage").src = gradcam;
        } else {
            document.getElementById("gradcamImage").removeAttribute("src");
            document.getElementById("gradcamImage").alt = "Backend chưa trả về Grad-CAM";
        }

        renderTopPredictions(data.top_predictions || data.top5 || data.top_5_predictions || []);

        resultSection.style.display = "block";

        setTimeout(() => {
            resultSection.scrollIntoView({
                behavior: "smooth",
                block: "start"
            });
        }, 100);

    } catch (error) {
        console.error("AI ERROR:", error);
        showError("Không thể kết nối hoặc xử lý dữ liệu từ AI Backend. " + error.message);
    } finally {
        predictButton.disabled = false;
        loading.style.display = "none";
    }
}

function showError(message) {
    errorBox.innerText = message;
    errorBox.style.display = "block";
}