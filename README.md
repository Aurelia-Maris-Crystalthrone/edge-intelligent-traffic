# 城市功能区智能分析平台

**2026年广东省大学生计算机设计大赛 · 边缘智能应用专项挑战赛（本科组）参赛作品**

## 🚀 项目简介

本平台是一个**基于边缘智能的城市功能区遥感分析系统**。它融合了深度学习模型与高德地图3D地球可视化技术，能够对上传的卫星遥感图像切片进行实时分类，并直观展示分析结果。

项目覆盖了 **模型训练 → 量化压缩 → 边缘端部署 → 前后端交互** 的完整流程，完美契合“边缘智能应用”的赛题要求。

## 📁 项目结构

```text
edge-intelligent-traffic/
├── README.md                     # 项目说明文档
├── 答辩PPT框架.md                 # 答辩PPT内容大纲
├── 运行指南.md                    # 详细的环境配置与运行指南
├── backend/                      # 后端服务
│   ├── app.py                    # Flask API服务，提供功能区预测接口
│   ├── requirements.txt          # Python依赖包列表
│   └── model/                    # 模型相关代码
│       ├── classifier.py         # 轻量级CNN模型定义
│       ├── train.py              # 模型训练脚本
│       ├── quantize.py           # 模型量化脚本
│       └── eurosat_resnet50.pth  # 预训练模型文件
├── frontend/                     # 前端可视化界面
│   ├── index.html                # 主页面，含高德3D地球及标注
│   └── static/
│       ├── style.css             # 样式文件
│       └── script.js             # 地图交互逻辑
├── edge/                         # 边缘端推理脚本
│   ├── edge_infer.py             # 量化模型推理脚本
│   └── model_quantized.pt        # 量化后的模型（需运行quantize.py生成）
└── scripts/                      # 数据预处理脚本
    ├── preprocess_landsat.py     # Landsat数据预处理
    └── organize_dataset.py       # 数据集组织工具
```

## ⚙️ 技术栈

| 技术领域 | 技术选型 |
| :--- | :--- |
| **后端框架** | Flask |
| **深度学习框架** | PyTorch & TorchVision |
| **前端地图** | 高德地图 JS API 2.0（3D视图 + 卫星图层） |
| **模型架构** | 轻量级CNN / ResNet50（迁移学习） |
| **边缘部署** | PyTorch动态量化 (INT8)、TorchScript |

## 🧠 核心功能

1.  **高德地图3D地球可视化**：提供沉浸式的交互地图，加载卫星影像图层。
2.  **功能区智能分析**：后端集成了轻量级CNN模型，可对上传的遥感图像切片进行分类，识别商业区、居民区、工业区等。
3.  **模型量化与边缘部署**：支持将训练好的模型量化为INT8精度，并通过`TorchScript`导出，以便在边缘设备上高效运行。
```

### 🛠️ 运行指南.md

```markdown
# 城市功能区智能分析平台 - 运行指南

本文档将指导你完成项目的环境配置与启动。

## 一、环境要求

| 项目 | 要求 |
| :--- | :--- |
| **操作系统** | Windows 10/11， Ubuntu 20.04+， macOS |
| **Python** | 3.8 或以上 |
| **Node.js** | 14+ （可选，用于前端静态服务） |
| **边缘设备** | 新大陆边缘智能应用实验平台v2.0 或其他ARM Linux设备（可选） |

## 二、快速开始

### 1. 后端服务搭建

首先，进入后端目录并安装依赖。

```bash
# 1. 进入后端目录
cd backend

# 2. 创建并激活Python虚拟环境（推荐）
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# 3. 安装Python依赖包
pip install -r requirements.txt
```

### 2. 模型准备（可选）

项目包含一个预训练模型。如需自行训练或量化，请执行以下步骤：

```bash
# 1. 准备数据集（示例：UC Merced Land Use Dataset）
# 将数据集按类别文件夹放入 backend/dataset/ 目录

# 2. 训练模型（可选）
# 运行训练脚本，将生成 city_function_model.pth
python model/train.py

# 3. 模型量化（用于边缘部署，可选）
# 运行量化脚本，将生成量化模型
python model/quantize.py
```

### 3. 启动后端服务

```bash
# 启动Flask API服务（默认监听5000端口）
python app.py
```
服务启动后，将监听 `http://localhost:5000`。若无模型文件，系统将自动进入演示模式。

### 4. 前端界面运行

推荐使用本地HTTP服务器运行前端，以避免跨域问题。

```bash
# 1. 打开新终端，进入前端目录
cd frontend

# 2. 使用 http-server 启动（需Node.js）
# 首次使用需安装：npm install -g http-server
http-server -p 8080
```

在浏览器中访问 `http://localhost:8080` 即可看到前端界面。

## 三、边缘端推理测试

将 `edge/` 文件夹拷贝至边缘设备（如新大陆平台），并确保已安装PyTorch。

```bash
# 1. 确保量化模型文件 city_function_model_scripted.pt 在 edge/ 目录下
# 2. 运行推理脚本
python edge_infer.py /path/to/your_test_image.jpg
```

## 四、注意事项与常见问题

### ⚠️ 注意事项

*   **高德地图Key**：已内置在 `index.html` 中，请勿用于商业用途。
*   **后端API地址**：前端默认请求 `http://localhost:5000`。若部署地址变更，请同步修改 `frontend/static/script.js` 中的 `fetch` URL。
*   **模型文件缺失**：若后端启动时无模型文件，系统会自动进入演示模式，随机返回结果。

### ❓ 常见问题

*   **Q：前端页面无法显示地图？**
    *   A：请检查网络是否能访问高德地图API，或尝试更换Key。
*   **Q：后端启动报错 `ModuleNotFoundError: No module named 'torch'`？**
    *   A：请确保已正确安装依赖。若在边缘设备上，请安装对应架构的PyTorch版本。
*   **Q：如何更换为自己的数据集？**
    *   A：修改 `train.py` 中的 `data_dir` 路径，并确保图片按类别文件夹组织。

## 五、提交材料清单（初赛）

*   **数据集**：可提供示例数据集或说明来源。
*   **模型构建源码**：`backend/model/` 目录。
*   **作品源码**：全部项目文件。
