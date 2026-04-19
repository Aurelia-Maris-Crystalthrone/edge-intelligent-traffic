#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
路径：scripts/preprocess_landsat.py
功能：Landsat 8 数据预处理（辐射定标、反射率计算、波段合成）
"""

import os
import numpy as np
import rasterio
import glob

# ----------------- 参数配置 -----------------
SCENE_DIR = "./LC08_L1TP_122044_20230415_20230422_02_T1"  # 修改为你的场景文件夹路径
OUTPUT_FILE = "guangzhou_20230415_processed.tif"

# 辐射定标系数（示例值，实际应从MTL.txt中提取）
RADIANCE_MULT = {
    'B2': 0.012876, 'B3': 0.011917, 'B4': 0.010033,
    'B5': 0.006132, 'B6': 0.001525, 'B7': 0.000514
}
RADIANCE_ADD = {
    'B2': -64.37982, 'B3': -59.58716, 'B4': -50.16554,
    'B5': -30.65926, 'B6': -7.62577, 'B7': -2.56957
}
SUN_ELEVATION = 54.5  # 从MTL.txt获取

# ----------------- 函数定义 -----------------
def dn_to_reflectance(dn, mult, add, sun_elev):
    """DN值转换为大气顶层反射率"""
    radiance = dn * mult + add
    reflectance = (np.pi * radiance) / (np.cos(np.radians(90 - sun_elev)) * 1.0)
    return np.clip(reflectance, 0, 1)

def process_band(band_path, mult, add, sun_elev):
    with rasterio.open(band_path) as src:
        dn = src.read(1).astype(np.float32)
        dn[dn == 0] = np.nan
        refl = dn_to_reflectance(dn, mult, add, sun_elev)
        profile = src.profile
    return refl, profile

# ----------------- 主流程 -----------------
if __name__ == "__main__":
    print("开始处理 Landsat 8 数据...")
    
    band_files = {}
    for b in ['B2', 'B3', 'B4', 'B5', 'B6', 'B7']:
        pattern = os.path.join(SCENE_DIR, f"*_{b}.TIF")
        files = glob.glob(pattern)
        if files:
            band_files[b] = files[0]
        else:
            print(f"警告：未找到 {b} 波段文件")
    
    processed_bands = []
    profile = None
    for b in ['B2', 'B3', 'B4', 'B5', 'B6', 'B7']:
        if b in band_files:
            refl, prof = process_band(band_files[b], RADIANCE_MULT[b], RADIANCE_ADD[b], SUN_ELEVATION)
            processed_bands.append(refl)
            if profile is None:
                profile = prof
    
    stacked = np.stack(processed_bands, axis=0)
    profile.update({'count': stacked.shape[0], 'dtype': rasterio.float32, 'driver': 'GTiff'})
    
    with rasterio.open(OUTPUT_FILE, 'w', **profile) as dst:
        dst.write(stacked)
    
    print(f"预处理完成，输出文件：{OUTPUT_FILE}")