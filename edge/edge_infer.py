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

CLASS_NAMES = ["商业区", "居民区", "工业区", "绿地/公园"]

def load_quantized_model(model_path="model_quantized.pt"):
    if not os.path.exists(model_path):
        model_path = "city_function_model_scripted.pt"
    if not os.path.exists(model_path):
        raise FileNotFoundError("未找到量化模型文件，请先运行 quantize.py")
    
    model = torch.jit.load(model_path)
    model.eval()
    return model

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

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python edge_infer.py <image_path>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    print("Loading quantized model...")
    model = load_quantized_model()
    
    print("Preprocessing image...")
    img_tensor = preprocess_image(image_path)
    
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