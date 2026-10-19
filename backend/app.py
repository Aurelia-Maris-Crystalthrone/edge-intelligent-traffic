"""
城市功能区智能分析平台 —— 后端 Flask 服务（参考重建实现）

说明
----
本文件是根据前端调用与边缘端推理脚本反推出的接口契约重新编写的
**最小可用实现**，并非原始参赛代码。详见 backend/README.md。

接口
----
POST /predict
    multipart/form-data，字段名 image
    成功: {"class": "商业区", "confidence": 0.9342}
    失败: {"error": "..."}

运行
----
    python app.py
"""

from __future__ import annotations

import os
import random
import time
from pathlib import Path

import torch
import torch.nn.functional as F
import torchvision.transforms as transforms
from flask import Flask, jsonify, request
from PIL import Image

try:
    from flask_cors import CORS
except ImportError:  # flask-cors 未安装时用手工响应头兜底，避免服务起不来
    CORS = None

# ---------------------------------------------------------------- 配置区

# 类别顺序必须与训练时 ImageFolder 的索引一致。
# 见 backend/README.md「陷阱 1」，此处按 edge_infer.py:13 的口径。
CLASS_NAMES = ["商业区", "居民区", "工业区", "绿地/公园"]

BASE_DIR = Path(__file__).resolve().parent

# 按优先级尝试加载模型；全部缺失则进入 Demo 模式
MODEL_CANDIDATES = [
    BASE_DIR / "model" / "eurosat_resnet50.pth",
    BASE_DIR.parent / "edge" / "model_quantized.pt",
]

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp"}

# 与 edge/edge_infer.py:26-32 保持完全一致，否则训练/推理不一致会导致结果错误
PREPROCESS = transforms.Compose(
    [
        transforms.Resize((64, 64)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225],
        ),
    ]
)

HOST = os.environ.get("FLASK_HOST", "127.0.0.1")
PORT = int(os.environ.get("FLASK_PORT", "5000"))

# ---------------------------------------------------------------- 模型

app = Flask(__name__)

if CORS is not None:
    # 前端静态服务端口与后端不同，需要允许跨域
    CORS(app)
else:

    @app.after_request
    def _manual_cors(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        return response

_model: torch.nn.Module | None = None
_demo_mode = False


def load_model() -> None:
    """启动时加载模型；找不到任何模型文件时进入 Demo 模式。"""
    global _model, _demo_mode

    for path in MODEL_CANDIDATES:
        if path.exists() and path.stat().st_size > 0:
            try:
                loaded = torch.jit.load(str(path), map_location="cpu")
                loaded.eval()
                _model = loaded
                app.logger.info("已加载 TorchScript 模型: %s", path)
                return
            except Exception as exc:  # noqa: BLE001 - 加载失败需降级而非崩溃
                app.logger.warning("加载 %s 失败: %s", path, exc)

    _demo_mode = True
    app.logger.warning(
        "未找到可用模型文件（已尝试: %s），已进入 Demo 演示模式，"
        "预测结果为随机值，仅供验证前后端连通性使用。",
        ", ".join(str(p) for p in MODEL_CANDIDATES),
    )


def predict_tensor(tensor: torch.Tensor) -> tuple[str, float]:
    """对已预处理的张量做一次前向推理，返回 (类别名, 置信度)。"""
    if _demo_mode or _model is None:
        idx = random.randrange(len(CLASS_NAMES))
        return CLASS_NAMES[idx], round(random.uniform(0.5, 0.99), 4)

    with torch.no_grad():
        output = _model(tensor)
        probs = F.softmax(output, dim=1)
        conf, pred = torch.max(probs, dim=1)
    return CLASS_NAMES[int(pred.item())], float(conf.item())


# ---------------------------------------------------------------- 路由


@app.get("/health")
def health():
    """健康检查，便于部署探活。"""
    return jsonify(
        {
            "status": "ok",
            "demo_mode": _demo_mode,
            "classes": CLASS_NAMES,
        }
    )


@app.post("/predict")
def predict():
    if "image" not in request.files:
        return jsonify({"error": "请求中缺少 image 字段"}), 400

    file = request.files["image"]
    if not file or file.filename == "":
        return jsonify({"error": "未选择文件"}), 400

    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        return (
            jsonify({"error": f"不支持的文件格式: {suffix or '(无扩展名)'}"}),
            400,
        )

    try:
        image = Image.open(file.stream).convert("RGB")
        tensor = PREPROCESS(image).unsqueeze(0)
    except Exception as exc:  # noqa: BLE001 - 图片损坏属用户输入错误
        return jsonify({"error": f"图片解析失败: {exc}"}), 400

    started = time.perf_counter()
    class_name, confidence = predict_tensor(tensor)
    elapsed_ms = (time.perf_counter() - started) * 1000.0

    return jsonify(
        {
            "class": class_name,
            "confidence": round(confidence, 4),
            "inference_ms": round(elapsed_ms, 2),
            "demo_mode": _demo_mode,
        }
    )


# ---------------------------------------------------------------- 入口

load_model()

if __name__ == "__main__":
    app.run(host=HOST, port=PORT, debug=os.environ.get("FLASK_DEBUG") == "1")
