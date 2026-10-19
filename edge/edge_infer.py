"""
边缘端推理脚本
适用于新大陆边缘智能实验平台或其他ARM/Linux设备
使用量化后的模型进行低功耗推理
"""
import torch
import torchvision.transforms as transforms
from PIL import Image
import sys
import time
import os

# 类别顺序必须与 ImageFolder 的索引一致。
#
# scripts/organize_dataset.py 输出的是英文目录名 commercial / green /
# industrial / residential，ImageFolder 按字母序分配索引，因此对应关系为：
#     0 -> commercial  -> 商业区
#     1 -> green       -> 绿地/公园
#     2 -> industrial  -> 工业区
#     3 -> residential -> 居民区
#
# 修改此处必须同步修改 backend/app.py 的 CLASS_NAMES，
# 否则模型输出会被映射成错误的类别。
CLASS_NAMES = ["商业区", "绿地/公园", "工业区", "居民区"]

# 模型文件按优先级尝试（相对本脚本所在目录解析，避免依赖当前工作目录）
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_CANDIDATES = [
    os.path.join(BASE_DIR, "model_quantized.pt"),
    os.path.join(BASE_DIR, "city_function_model_scripted.pt"),
]


def load_quantized_model(model_path=None):
    """加载量化模型。model_path 为空时按 MODEL_CANDIDATES 依次尝试。"""
    candidates = [model_path] if model_path else MODEL_CANDIDATES

    for path in candidates:
        if path and os.path.exists(path) and os.path.getsize(path) > 0:
            model = torch.jit.load(path, map_location="cpu")
            model.eval()
            print(f"已加载模型：{path}")
            return model

    raise FileNotFoundError(
        "未找到量化模型文件（已尝试：{}），请先运行 quantize.py 生成，"
        "或用 --model 参数指定路径。".format(", ".join(str(c) for c in candidates))
    )

def preprocess_image(image_path):
    transform = transforms.Compose([
        transforms.Resize((64, 64)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    image = Image.open(image_path).convert('RGB')
    return transform(image).unsqueeze(0)

def infer(model, image_tensor):
    with torch.no_grad():
        start = time.time()
        output = model(image_tensor)
        inference_time = (time.time() - start) * 1000
        probabilities = torch.nn.functional.softmax(output, dim=1)
        conf, pred = torch.max(probabilities, 1)
    return pred.item(), conf.item(), probabilities[0].tolist(), inference_time

def main(argv=None):
    import argparse

    parser = argparse.ArgumentParser(description="边缘端遥感图像功能区推理")
    parser.add_argument("image", help="待推理的卫星图像切片路径")
    parser.add_argument(
        "--model",
        help="模型文件路径；不指定时按默认候选路径依次查找",
    )
    args = parser.parse_args(argv)

    if not os.path.exists(args.image):
        print(f"❌ 图像文件不存在：{args.image}")
        return 1

    print("Loading quantized model...")
    try:
        model = load_quantized_model(args.model)
    except FileNotFoundError as exc:
        print(f"❌ {exc}")
        return 1

    print("Preprocessing image...")
    img_tensor = preprocess_image(args.image)

    print("Running inference...")
    pred_idx, confidence, all_probs, inf_time = infer(model, img_tensor)

    print("\n===== 推理结果 =====")
    print(f"功能区类别: {CLASS_NAMES[pred_idx]}")
    print(f"置信度: {confidence:.4f}")
    print(f"推理耗时: {inf_time:.2f} ms")
    print("各类别概率:")
    for i, cls in enumerate(CLASS_NAMES):
        print(f"  {cls}: {all_probs[i]:.4f}")
    print("====================")
    return 0


if __name__ == "__main__":
    sys.exit(main())