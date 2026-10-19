#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
路径：scripts/organize_dataset.py
功能：将 EuroSAT 原始 10 类数据整理到本项目的 4 个目标类别中

用法示例
--------
    python organize_dataset.py --source-dir /data/EuroSAT --target-dir ../backend/dataset
    python organize_dataset.py --source-dir /data/EuroSAT --dry-run      # 只统计不复制

⚠️ 类别顺序约定（重要）
------------------------
本脚本输出的是**英文目录名**，而推理侧使用中文类别名。
`torchvision.datasets.ImageFolder` 会按**字母序**为目录分配索引，得到的顺序是：

    索引 0 -> commercial    -> 商业区
    索引 1 -> green         -> 绿地/公园
    索引 2 -> industrial    -> 工业区
    索引 3 -> residential   -> 居民区

因此 `edge/edge_infer.py` 与 `backend/app.py` 中的 CLASS_NAMES 必须与此完全一致。
三者任一改动都要同步修改另外两处，否则模型会「看起来能跑但预测全错」。
"""

import argparse
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TARGET = REPO_ROOT / "backend" / "dataset"

# EuroSAT 原始 10 类 → 本项目的 4 个目标类别（英文目录名）
EUROSAT_MAPPING = {
    "AnnualCrop": "green",
    "Forest": "green",
    "HerbaceousVegetation": "green",
    "Pasture": "green",
    "PermanentCrop": "green",
    "Highway": "commercial",
    "Industrial": "industrial",
    "Residential": "residential",
    "River": "green",       # 河流归入绿色空间
    "SeaLake": "green",     # 湖泊归入绿色空间
}

# UC Merced Land Use（21 类）到本项目类别的完整映射，供切换数据集时使用
UC_MERCED_MAPPING = {
    "agricultural": "green",
    "airplane": "industrial",
    "baseballdiamond": "green",
    "beach": "green",
    "buildings": "commercial",
    "chaparral": "green",
    "denseresidential": "residential",
    "forest": "green",
    "freeway": "commercial",
    "golfcourse": "green",
    "harbor": "industrial",
    "intersection": "commercial",
    "mediumresidential": "residential",
    "mobilehomepark": "residential",
    "overpass": "commercial",
    "parkinglot": "commercial",
    "river": "green",
    "runway": "industrial",
    "sparseresidential": "residential",
    "storagetanks": "industrial",
    "tenniscourt": "green",
}

DATASET_MAPPINGS = {
    "EuroSAT": EUROSAT_MAPPING,
    "UC_Merced": UC_MERCED_MAPPING,
}

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".tif", ".tiff"}


def organize_dataset(source_dir, target_dir, mapping, dry_run=False):
    """按映射表把源数据集复制到目标目录，返回复制的文件总数。"""
    source_path = Path(source_dir)
    target_path = Path(target_dir)

    if not source_path.exists():
        raise FileNotFoundError(f"源目录不存在：{source_path}")

    if not dry_run:
        for folder in sorted(set(mapping.values())):
            (target_path / folder).mkdir(parents=True, exist_ok=True)

    copied_count = 0
    missing_classes = []

    for src_class, dst_class in mapping.items():
        src_class_path = source_path / src_class
        dst_class_path = target_path / dst_class

        if not src_class_path.exists():
            missing_classes.append(src_class)
            continue

        class_count = 0
        for img_file in src_class_path.glob("*"):
            if img_file.suffix.lower() not in IMAGE_SUFFIXES:
                continue
            class_count += 1
            if not dry_run:
                shutil.copy2(img_file, dst_class_path / img_file.name)

        copied_count += class_count
        print(f"✓ {src_class} → {dst_class}（{class_count} 张）")

    if missing_classes:
        print(f"\n⚠️ 警告：以下类别文件夹未找到：{missing_classes}")

    return copied_count


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="整理遥感数据集到本项目的 4 类别目录结构"
    )
    parser.add_argument(
        "--source-dir",
        required=True,
        help="原始数据集根目录（其下应直接是各类别文件夹）",
    )
    parser.add_argument(
        "--target-dir",
        default=str(DEFAULT_TARGET),
        help=(
            "目标存储路径，默认 <仓库根>/backend/dataset。"
            "显式传入的相对路径按当前工作目录解析"
        ),
    )
    parser.add_argument(
        "--dataset",
        default="EuroSAT",
        choices=sorted(DATASET_MAPPINGS.keys()),
        help="输入数据集类型，默认 EuroSAT",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只统计将要处理的文件数量，不实际复制",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    target_abs = Path(args.target_dir)
    if not target_abs.is_absolute():
        # 相对路径按当前工作目录解析，符合命令行工具的通用习惯
        target_abs = target_abs.resolve()

    mapping = DATASET_MAPPINGS.get(args.dataset)
    if mapping is None:
        raise ValueError(
            f"未知的数据集类型: {args.dataset}，可选：{sorted(DATASET_MAPPINGS)}"
        )

    print(f"数据集类型：{args.dataset}")
    print(f"源数据目录：{args.source_dir}")
    print(f"目标存储目录：{target_abs}")
    if args.dry_run:
        print("（dry-run 模式，不会复制文件）")
    print("开始整理...\n")

    try:
        count = organize_dataset(
            args.source_dir, target_abs, mapping, dry_run=args.dry_run
        )
    except FileNotFoundError as exc:
        print(f"❌ {exc}", file=sys.stderr)
        return 1

    mode = "预计复制" if args.dry_run else "已复制"
    print(f"\n✅ 整理完成！{mode} {count} 张图片到 {target_abs}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
