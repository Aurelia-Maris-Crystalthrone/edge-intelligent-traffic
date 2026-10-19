# 城市功能区智能分析平台

**2026年广东省大学生计算机设计大赛 · 边缘智能应用专项挑战赛（本科组）参赛作品**

基于边缘智能的城市功能区遥感分析系统：上传卫星遥感图像切片，由轻量级 CNN 模型完成功能区分类，结果在高德地图 3D 卫星视图上可视化标注。链路覆盖 **数据整理 → 模型训练 → 量化导出 → 边缘推理 → 前后端交互**。

完整的环境配置、部署流程与故障排查见 [运行指南.md](运行指南.md)。

---

## ⚠️ 当前状态与已知缺口

在按下方步骤操作前，请务必先了解仓库当前的三个缺口。这些是**已知且尚未修复**的问题，不是文档疏漏。

| # | 缺口 | 影响 | 处理建议 |
| :--- | :--- | :--- | :--- |
| 1 | **后端原始源码已丢失** | `backend/` 原先是一个没有 URL 记录的 gitlink（submode 指针 `8773e09`），对应的 commit 对象不在仓库里，无法从 Git 历史恢复 | 当前 `backend/app.py` 是依据前端调用与边缘脚本**反向推断后重新编写**的最小可用实现，能跑通 `/predict`，但不包含原始训练代码。契约详见 [backend/README.md](backend/README.md) |
| 2 | **模型权重文件不在仓库中** | 无可推理模型。缺失文件：`model/eurosat_resnet50.pth`、`edge/model_quantized.pt` | 需自行训练生成。后端在无模型时会自动进入 **Demo 模式**（随机返回结果），可用于验证前后端连通性 |
| 3 | **训练脚本未包含** | `backend/model/train.py`、`quantize.py` 随后端一同丢失 | 需重建。重建时注意 [backend/README.md](backend/README.md)「三、重建时需要注意的两个陷阱」中记录的**类别顺序错位**与**输入尺寸不匹配**问题 |

> **关于 Windows 下 clone 失败（已修复）**
> 仓库历史中曾存在一个名为 `edge/model_quantized.pt `（**末尾带空格**）的 0 字节占位文件。
> Windows 不允许尾空格文件名，导致 `git clone` 在 checkout 阶段直接中止
> （`fatal: unable to checkout working tree`）。该文件已在修复提交中删除，现在 Windows 下可正常 clone。

---

## 📁 项目结构

```text
edge-intelligent-traffic/
├── README.md                       # 项目说明（本文件）
├── 运行指南.md                      # 环境配置、部署流程与 FAQ
├── LICENSE                         # MIT
├── .gitignore
├── backend/                        # 后端服务
│   ├── README.md                   # ⭐ 接口契约与重建说明
│   ├── app.py                      # Flask 服务（参考重建实现）
│   ├── requirements.txt            # Python 依赖
│   ├── model/                      # 模型目录（训练后可在此放置权重）
│   └── dataset/                    # 整理后的数据集（由 organize_dataset.py 生成）
├── frontend/                       # 前端可视化界面
│   ├── index.html                  # 主页面（高德 v2.0 + 外链资源）
│   ├── index1.html                 # 早期原型（高德 v1.4.15，样式内联，仅供参考）
│   └── static/
│       ├── style.css
│       ├── scripts.js              # 地图交互与分析逻辑
│       └── config.example.js       # ⭐ 配置模板，需复制为 config.js
├── edge/                           # 边缘端推理
│   ├── edge_infer.py               # TorchScript 模型推理脚本
├── scripts/                        # 数据预处理
│   ├── organize_dataset.py         # EuroSAT / UC Merced → 4 类目录
│   └── preprocess_landsat.py       # Landsat 8 辐射定标与波段合成
├── images/                         # 演示截图
└── 边缘智能应用挑战赛-赛题说明.pdf
```

---

## ⚙️ 技术栈

| 领域 | 选型 |
| :--- | :--- |
| 后端框架 | Flask + flask-cors |
| 深度学习 | PyTorch / TorchVision |
| 前端地图 | 高德地图 JS API（index.html 用 v2.0；index1.html 用 v1.4.15） |
| 模型部署 | TorchScript 导出、动态量化（INT8） |
| 数据来源 | EuroSAT / UC Merced 遥感数据集、Landsat 8 L1 |

---

## 🚀 快速开始

### 0. 首次必做：配置高德地图 Key

**Key 已从代码中移除，不再硬编码。** 若不配置，页面会显示提示条——**地图不可用，但图像分析功能不受影响**。

```bash
cd frontend/static
cp config.example.js config.js      # Windows: copy config.example.js config.js
```

编辑 `config.js`，填入你在 [高德开放平台](https://lbs.amap.com/) 申请的 **Web端（JS API）** Key：

```javascript
window.AMAP_CONFIG = {
    key: '你的Key',
    securityJsCode: '',              // 仅当申请时选择了「安全密钥」校验才需填写
    backendUrl: 'http://localhost:5000'
};
```

`config.js` 已被 `.gitignore` 排除，不会被提交。

### 1. 启动后端

```bash
cd backend
python -m venv venv
# Windows: venv\Scripts\activate    |   Linux/macOS: source venv/bin/activate
pip install -r requirements.txt
python app.py
```

验证服务是否起来：

```bash
curl http://127.0.0.1:5000/health
# {"classes":["商业区","绿地/公园","工业区","居民区"],"demo_mode":true,"status":"ok"}
```

`demo_mode: true` 表示未加载到模型、正以随机结果运行，属正常现象（见上方「已知缺口 2」）。

也可手动测一次预测：

```bash
curl -X POST -F "image=@your_slice.png" http://127.0.0.1:5000/predict
# {"class":"工业区","confidence":0.5737,"demo_mode":true,"inference_ms":0.02}
```

### 2. 启动前端

**必须用 HTTP 服务打开，不要直接双击 HTML 文件**（`file://` 协议下 fetch 与地图 API 均受限）。

```bash
cd frontend
python -m http.server 8080          # 或使用 npx http-server -p 8080
```

浏览器访问 <http://localhost:8080>。

### 3. 边缘端推理

需先准备好 TorchScript 模型（缺失时会给出明确报错而非静默失败）：

```bash
cd edge
python edge_infer.py /path/to/slice.jpg
python edge_infer.py /path/to/slice.jpg --model /path/to/model_quantized.pt
```

---

## 🗂️ 数据准备

整理遥感数据集到训练所需的 4 类目录结构：

```bash
# 默认输出到 <仓库根>/backend/dataset，相对路径按当前目录解析
python scripts/organize_dataset.py --source-dir /path/to/EuroSAT

# 只统计不复制
python scripts/organize_dataset.py --source-dir /path/to/EuroSAT --dry-run

# 使用 UC Merced 数据集
python scripts/organize_dataset.py --source-dir /path/to/UCMerced --dataset UC_Merced
```

Landsat 8 预处理（**建议通过 `--mtl` 传入场景自己的 MTL 文件**，内置系数为示例值）：

```bash
python scripts/preprocess_landsat.py --scene-dir ./LC08_L1TP_... --output processed.tif
python scripts/preprocess_landsat.py --scene-dir ./LC08_L1TP_... --mtl ./..._MTL.txt --output processed.tif
```

---

## 🔌 接口契约摘要

| 项 | 值 |
| :--- | :--- |
| 端点 | `POST /predict` |
| 类型 | `multipart/form-data` |
| 字段名 | `image` |
| 成功响应 | `{"class": "商业区", "confidence": 0.9342}` |
| 失败响应 | `{"error": "..."}`，HTTP 400 |

`class` 取值限定为 `商业区 / 绿地/公园 / 工业区 / 居民区`。
完整契约、字段约束与重建注意事项见 [backend/README.md](backend/README.md)。

---

## 🧩 修复记录

本次整理修复了以下会导致项目无法正常 clone 或运行的问题：

| 问题 | 修复 |
| :--- | :--- |
| `edge/model_quantized.pt ` 文件名带尾空格，Windows 下 clone 直接失败 | 删除该 0 字节占位文件 |
| `backend/` 是无 URL 记录的 gitlink，clone 后为空目录，`submodule update` 报错 | 移除失效 gitlink，补充契约文档与参考实现 |
| `index.html` 引用 `static/script.js`，实际文件名为 `scripts.js`，导致交互逻辑全部 404 | 统一为 `scripts.js` |
| 高德地图 Key 与安全密钥明文硬编码在 HTML 中 | 改为从 `config.js`（已 gitignore）读取 |
| README 第 54 行多余的代码围栏，使运行指南内容被错误嵌入 README | 重写；运行指南收敛为单一文件 `运行指南.md` |
| 地图初始化失败会导致上传与分析按钮的事件绑定全部不执行 | 拆分为「地图」与「交互」两条独立初始化路径，地图不可用时分析功能仍可用 |
| `organize_dataset.py` 中 `UC_MERCED_MAPPING = { ... }` 为占位符，启用后会静默出错 | 补全完整映射；路径硬编码改为命令行参数 |
| `edge_infer.py` 类别顺序与 ImageFolder 字母序不一致，导致第 1、3 类预测结果互换 | 修正 `CLASS_NAMES` 顺序并在三处同步标注该约定 |
| 根目录缺少 LICENSE 与 .gitignore | 补充 MIT 许可证与忽略规则 |

---

## 📄 许可证

本项目采用 [MIT License](LICENSE)。

地图数据由高德开放平台提供，使用需遵守其服务条款。
