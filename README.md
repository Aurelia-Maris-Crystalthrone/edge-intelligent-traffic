# 城市功能区智能分析平台

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://python.org)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.1.0-red)](https://pytorch.org)
[![Flask](https://img.shields.io/badge/Flask-2.3.3-lightgrey)](https://flask.palletsprojects.com)
[![高德地图](https://img.shields.io/badge/高德地图-2.0-brightgreen)](https://lbs.amap.com)

**2026年广东省大学生计算机设计大赛 · 边缘智能应用专项挑战赛（本科组）参赛作品**

## 📌 项目简介

本平台是一个**基于边缘智能的城市功能区遥感分析系统**。它结合深度学习与3D地球可视化技术，能够对卫星遥感图像切片进行实时分类（商业区、居民区、工业区、绿地等），并将分析结果直观展示在高德地图构建的交互式3D地球之上。

项目完整覆盖**模型训练 → 量化压缩 → 边缘端部署 → 前后端交互**全流程，完美契合“边缘智能应用”赛题要求。

## 📂 项目结构
```bash
city-function-platform/
├── README.md
├── 答辩PPT框架.md
├── 运行指南.md
├── backend/ # 后端服务
│ ├── app.py
│ ├── requirements.txt
│ ├── model/
│ │ ├── classifier.py
│ │ ├── train.py
│ │ ├── quantize.py
│ │ └── eurosat_resnet50.pth 
│ └── dataset/
├── frontend/ # 前端界面
│ ├── index.html
│ └── static/
│ ├── style.css
│ └── script.js
├── edge/ # 边缘端推理
│ ├── edge_infer.py
│ └── model_quantized.pt 
└── scripts/ # 数据预处理脚本
├── preprocess_landsat.py
└── organize_dataset.py
```

## 🚀 快速开始

### 1. 后端环境配置与启动

```bash
cd backend
pip install -r requirements.txt

# （可选）训练模型
python model/train.py

# （可选）量化模型
python model/quantize.py

# 启动Flask服务
python app.py# edge-intelligent-traffic
