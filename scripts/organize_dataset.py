#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
路径：scripts/organize_dataset.py
功能：将 EuroSAT 原始 10 类数据整理到项目的 4 个目标类别中
使用方法：直接运行 python organize_dataset.py
"""

import os
import shutil
from pathlib import Path

# ==================== 配置区（请根据实际情况修改）====================
SOURCE_DATASET = "EuroSAT"                      # 目前仅支持 EuroSAT
SOURCE_DIR = "/home/lienne/data/eurosat"        # EuroSAT 原始数据路径
TARGET_DIR = "../backend/dataset"               # 目标存储路径（相对于脚本位置）
# ====================================================================

# EuroSAT 原始 10 类 → 目标 4 类的映射
EUROSAT_MAPPING = {
    "AnnualCrop": "green",
    "Forest": "green",
    "HerbaceousVegetation": "green",
    "Pasture": "green",
    "PermanentCrop": "green",
    "Highway": "commercial",
    "Industrial": "industrial",
    "Residential": "residential",
    "River": "green",           # 河流也算作绿色空间
    "SeaLake": "green",         # 湖泊算作绿色空间
}

# 如果你将来需要使用 UC Merced 或 AID，可以在此添加对应映射
UC_MERCED_MAPPING = { ... }    # 省略，按需补充
AID_MAPPING = { ... }          # 省略，按需补充

MAPPING_DICT = {
    "EuroSAT": EUROSAT_MAPPING,
    # "UC_Merced": UC_MERCED_MAPPING,
    # "AID": AID_MAPPING,
}

def organize_dataset(source_dir, target_dir, mapping):
    source_path = Path(source_dir)
    target_path = Path(target_dir)

    # 检查源目录是否存在
    if not source_path.exists():
        raise FileNotFoundError(f"源目录不存在：{source_path}")

    # 创建目标类别文件夹
    for folder in set(mapping.values()):
        (target_path / folder).mkdir(parents=True, exist_ok=True)

    copied_count = 0
    missing_classes = []

    for src_class, dst_class in mapping.items():
        src_class_path = source_path / src_class
        dst_class_path = target_path / dst_class

        if not src_class_path.exists():
            missing_classes.append(src_class)
            continue

        # 复制所有图片文件
        for img_file in src_class_path.glob("*"):
            if img_file.suffix.lower() in [".jpg", ".jpeg", ".png", ".tif", ".tiff"]:
                shutil.copy2(img_file, dst_class_path / img_file.name)
                copied_count += 1

        print(f"✓ 已复制 {src_class} → {dst_class}")

    if missing_classes:
        print(f"\n⚠️ 警告：以下类别文件夹未找到：{missing_classes}")

    print(f"\n✅ 整理完成！共复制 {copied_count} 张图片到 {target_path.resolve()}")

if __name__ == "__main__":
    # 获取脚本所在目录，以便处理相对路径
    script_dir = Path(__file__).parent.resolve()
    target_abs = (script_dir / TARGET_DIR).resolve()

    mapping = MAPPING_DICT.get(SOURCE_DATASET)
    if mapping is None:
        raise ValueError(f"未知的数据集类型: {SOURCE_DATASET}")

    print(f"源数据目录：{SOURCE_DIR}")
    print(f"目标存储目录：{target_abs}")
    print("开始整理...\n")

    organize_dataset(SOURCE_DIR, target_abs, mapping)