#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
路径：scripts/preprocess_landsat.py
功能：Landsat 8 Level-1 数据预处理（辐射定标 → 大气顶层反射率 → 波段合成）

用法示例
--------
    # 使用内置示例系数（仅演示用）
    python preprocess_landsat.py --scene-dir ./LC08_L1TP_122044_20230415 --output processed.tif

    # 推荐：从场景自带的 MTL 元数据文件中读取真实定标参数
    python preprocess_landsat.py --scene-dir ./LC08_L1TP_122044_20230415 \
        --mtl ./LC08_L1TP_122044_20230415/LC08..._MTL.txt --output processed.tif

⚠️ 关于精度
------------
RADIANCE_MULT / RADIANCE_ADD / SUN_ELEVATION 的默认值为**示例值**，
仅代表某一景的量级，直接用于其他场景会得到错误的反射率。
正式使用请务必通过 --mtl 传入该场景的 MTL 元数据文件。

本脚本计算的是**大气顶层反射率（TOA）**，未做大气校正，
不适用于需要地表反射率的定量分析场景。
"""

import argparse
import glob
import os
import re
import sys

import numpy as np
import rasterio

BANDS = ['B2', 'B3', 'B4', 'B5', 'B6', 'B7']

# ----------------- 默认定标参数（示例值，务必用 --mtl 覆盖） -----------------
DEFAULT_RADIANCE_MULT = {
    'B2': 0.012876, 'B3': 0.011917, 'B4': 0.010033,
    'B5': 0.006132, 'B6': 0.001525, 'B7': 0.000514,
}
DEFAULT_RADIANCE_ADD = {
    'B2': -64.37982, 'B3': -59.58716, 'B4': -50.16554,
    'B5': -30.65926, 'B6': -7.62577, 'B7': -2.56957,
}
DEFAULT_SUN_ELEVATION = 54.5


def parse_mtl(mtl_path):
    """从 Landsat 8 MTL 文件中提取定标参数。

    Returns:
        (radiance_mult, radiance_add, sun_elevation)
    """
    text = open(mtl_path, encoding='utf-8', errors='ignore').read()

    def find(pattern, cast=float):
        m = re.search(pattern, text)
        return cast(m.group(1)) if m else None

    mult = {}
    add = {}
    for band in BANDS:
        m = find(rf'RADIANCE_MULT_BAND_{band[1:]}\s*=\s*([-\d.eE+]+)')
        a = find(rf'RADIANCE_ADD_BAND_{band[1:]}\s*=\s*([-\d.eE+]+)')
        if m is not None and a is not None:
            mult[band] = m
            add[band] = a

    sun_elev = find(r'SUN_ELEVATION\s*=\s*([-\d.eE+]+)')

    missing = [b for b in BANDS if b not in mult or b not in add]
    if missing:
        raise ValueError(
            f"MTL 文件中缺少以下波段的定标参数：{missing}（路径：{mtl_path}）"
        )
    if sun_elev is None:
        raise ValueError(f"MTL 文件中未找到 SUN_ELEVATION（路径：{mtl_path}）")

    return mult, add, sun_elev


def dn_to_reflectance(dn, mult, add, sun_elev):
    """DN 值 → 大气顶层（TOA）反射率。"""
    radiance = dn * mult + add
    # cos(90° - 太阳高度角) 即 sin(太阳高度角)
    reflectance = (np.pi * radiance) / np.sin(np.radians(sun_elev))
    return np.clip(reflectance, 0, 1)


def process_band(band_path, mult, add, sun_elev):
    """读取单个波段并转换为反射率，同时返回原始 GeoTIFF profile。"""
    with rasterio.open(band_path) as src:
        dn = src.read(1).astype(np.float32)
        # 0 是 Landsat L1 的填充值（nodata），置 NaN 避免污染后续统计
        dn[dn == 0] = np.nan
        refl = dn_to_reflectance(dn, mult, add, sun_elev)
        profile = src.profile
    return refl, profile


def find_band_files(scene_dir):
    """在场景目录中定位各波段文件，兼容 .TIF/.tif 扩展名。"""
    band_files = {}
    missing = []
    for band in BANDS:
        matched = []
        for ext in ('TIF', 'tif'):
            matched.extend(glob.glob(os.path.join(scene_dir, f"*_{band}.{ext}")))
        if matched:
            band_files[band] = matched[0]
        else:
            missing.append(band)

    if missing:
        print(f"⚠️ 警告：以下波段文件未找到，将被跳过：{missing}")
    return band_files, missing


def main(argv=None):
    parser = argparse.ArgumentParser(description='Landsat 8 数据预处理')
    parser.add_argument('--scene-dir', required=True, help='场景文件夹路径')
    parser.add_argument(
        '--output',
        default='processed.tif',
        help='输出 GeoTIFF 文件名，默认 processed.tif',
    )
    parser.add_argument(
        '--mtl',
        help='场景的 MTL 元数据文件路径；提供时优先使用其中的真实定标参数',
    )
    args = parser.parse_args(argv)

    scene_dir = args.scene_dir
    if not os.path.isdir(scene_dir):
        print(f"❌ 场景目录不存在：{scene_dir}", file=sys.stderr)
        return 1

    if args.mtl:
        try:
            mult, add, sun_elev = parse_mtl(args.mtl)
        except (OSError, ValueError) as exc:
            print(f"❌ 读取 MTL 失败：{exc}", file=sys.stderr)
            return 1
        print(f"✓ 已从 MTL 读取定标参数（太阳高度角 {sun_elev}°）")
    else:
        mult, add, sun_elev = (
            DEFAULT_RADIANCE_MULT,
            DEFAULT_RADIANCE_ADD,
            DEFAULT_SUN_ELEVATION,
        )
        print("⚠️ 未提供 --mtl，正在使用内置示例系数，结果仅供演示，不可用于定量分析")

    print("开始处理 Landsat 8 数据...")

    band_files, missing = find_band_files(scene_dir)
    if not band_files:
        print(
            f"❌ 在 {scene_dir} 中未找到任何 {'-'.join(BANDS)} 波段文件，无法合成",
            file=sys.stderr,
        )
        return 1

    processed_bands = []
    profile = None
    shape_ref = None

    for band in BANDS:
        if band not in band_files:
            continue
        refl, prof = process_band(
            band_files[band], mult[band], add[band], sun_elev
        )

        # 波段间尺寸必须一致才能 stack
        if shape_ref is None:
            shape_ref = refl.shape
        elif refl.shape != shape_ref:
            print(
                f"❌ 波段 {band} 尺寸 {refl.shape} 与首个波段 {shape_ref} 不一致，跳过",
                file=sys.stderr,
            )
            continue

        processed_bands.append(refl)
        if profile is None:
            profile = prof
        print(f"✓ 已处理波段 {band}")

    if not processed_bands:
        print("❌ 没有成功处理任何波段，终止输出", file=sys.stderr)
        return 1

    stacked = np.stack(processed_bands, axis=0).astype(np.float32)
    profile.update({'count': stacked.shape[0], 'dtype': 'float32', 'driver': 'GTiff'})

    # nodata 保持 NaN，便于下游用 np.nan 统计或按需填充
    if 'nodata' in profile:
        profile['nodata'] = np.nan

    with rasterio.open(args.output, 'w', **profile) as dst:
        dst.write(stacked)

    print(f"\n✅ 预处理完成，输出文件：{args.output}")
    print(f"   波段数：{stacked.shape[0]}   尺寸：{stacked.shape[1]}×{stacked.shape[2]}")
    if missing:
        print(f"   注意：波段 {missing} 缺失，输出不全")
    return 0


if __name__ == "__main__":
    sys.exit(main())
