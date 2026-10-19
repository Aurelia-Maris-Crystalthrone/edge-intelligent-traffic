# 后端服务（Backend Service）

> ## ⚠️ 状态说明：本目录源码已丢失，当前为契约文档与参考重建实现
>
> 本目录原先在 Git 中以 **gitlink（mode `160000`）** 的形式存在，指向 commit
> `8773e0985be01b448e4ae4abe6879cc969f8a60d`，但仓库中**没有 `.gitmodules`**，
> 该 commit 对象也不存在于本仓库的对象库中。因此：
>
> - `git clone` 后 `backend/` 是一个**空目录**；
> - `git submodule update --init` 会报 `No url found for submodule path 'backend'`；
> - 原始代码无法从 Git 历史恢复。
>
> 该失效的 gitlink 已在修复提交中从索引移除。下面的内容是从
> **前端调用代码**与**边缘端推理脚本**反向推断出的接口契约，以及一份
> **参考重建实现**（`app.py`），用于让仓库恢复到可运行状态。

---

## 一、接口契约

### `POST /predict`

分析上传的卫星遥感图像切片，返回功能区分类结果。

**请求**

| 项 | 值 |
| :--- | :--- |
| Method | `POST` |
| Content-Type | `multipart/form-data` |
| 字段名 | `image`（**必须是这个名字**） |
| 编码位置 | `frontend/static/scripts.js` 第 96–99 行 |

```http
POST /predict HTTP/1.1
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary

------WebKitFormBoundary
Content-Disposition: form-data; name="image"; filename="slice.png"
Content-Type: image/png

<binary image data>
------WebKitFormBoundary--
```

**响应（成功）** — `200 OK`

```json
{
  "class": "商业区",
  "confidence": 0.9342
}
```

| 字段 | 类型 | 约束 |
| :--- | :--- | :--- |
| `class` | `string` | **必须**为下列四者之一，否则前端 `typeColor[data.class]` 取到 `undefined`，标记配色变黑 |
| `confidence` | `float` | 取值区间 `[0, 1]`。前端按 `(confidence * 100).toFixed(1)` 转成百分比显示 |

`class` 的合法取值（`edge/edge_infer.py:13`）：

```
"商业区", "居民区", "工业区", "绿地/公园"
```

**响应（失败）**

前端优先读取 JSON 体中的 `error` 字段：

```json
{ "error": "未选择文件或文件格式不支持" }
```

若返回非 2xx 状态码或网络不可达，`scripts.js` 会落入 `catch` 分支并显示
「分析失败，请检查后端服务是否启动」。

### 服务地址

后端默认监听 **`http://localhost:5000`**（硬编码于 `scripts.js:99`）。
当前存在 CORS 跨域（`frontend` 静态服务端口与 `5000` 不同），旧 FAQ 提到
原实现使用了 `flask_cors`，故参考实现保留了 `CORS(app)`。

---

## 二、推理预处理约定

重建实现**必须**与训练时保持一致，参数取自 `edge/edge_infer.py:26-32`：

```python
transforms.Compose([
    transforms.Resize((64, 64)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225]),
])
```

输出形状 `[1, 3, 64, 64]`，经 `softmax(dim=1)` 后取 `max` 得到类别与置信度。

---

## 三、重建时需要注意的两个陷阱

这两个问题是原始代码结构中遗留的，重建时务必处理，否则模型会「看似能跑但结果全错」。

### 陷阱 1：类别顺序错位

`edge_infer.py` 里的 `CLASS_NAMES` 顺序是：

```python
CLASS_NAMES = ["商业区", "居民区", "工业区", "绿地/公园"]   # 索引 0,1,2,3
```

但 `scripts/organize_dataset.py` 生成的数据集目录名是**英文**：
`commercial` / `green` / `industrial` / `residential`。
`torchvision.datasets.ImageFolder` 默认按**字母序**分配索引，实际得到：

| ImageFolder 索引 | 目录名 | 真实含义 | `CLASS_NAMES[索引]` | 是否一致 |
| :---: | :--- | :--- | :--- | :---: |
| 0 | `commercial` | 商业区 | 商业区 | ✅ |
| 1 | `green` | 绿地/公园 | **居民区** | ❌ |
| 2 | `industrial` | 工业区 | 工业区 | ✅ |
| 3 | `residential` | 居民区 | **绿地/公园** | ❌ |

**修复方式**：训练时显式锁定顺序，例如
`ImageFolder(root, transform=..., target_transform=None)` 之后覆盖
`dataset.classes = ["商业区", "居民区", "工业区", "绿地/公园"]` 并把目录名改名为中文，
或在推理侧建立 `MODEL_INDEX → CLASS_NAMES` 的显式映射表，不要依赖隐式顺序。

### 陷阱 2：输入尺寸 64×64 与 ResNet50 不匹配

运行指南提到模型架构是 **ResNet50 迁移学习**，但预处理把图像缩放到 **64×64**。
ResNet50 在 64×64 输入下经过多次下采样后特征图会退化为 2×2，通常应取 224×224。
两者取其一：把 `Resize` 改为 `(224, 224)`，或换用适配小图的轻量 CNN。

---

## 四、重建步骤

```bash
cd backend
python -m venv venv
# Windows: venv\Scripts\activate   |   Linux/macOS: source venv/bin/activate
pip install -r requirements.txt
python app.py
```

首次启动若无模型文件，`app.py` 会进入 **Demo 模式**（随机返回结果），
以便在没有模型的情况下也能验证前后端连通性。

模型文件路径按优先级尝试（与 `edge_infer.py:15-19` 保持一致）：

1. `model/eurosat_resnet50.pth`
2. `edge/model_quantized.pt`

> 这两个文件当前**都不在仓库中**，需自行训练生成。仓库历史里曾存在一个
> 名为 `edge/model_quantized.pt `（**末尾带空格**）的 0 字节占位文件，
> 它会导致 Windows 下 `git clone` 直接 checkout 失败，已在修复中删除。

## 五、参考实现说明

`app.py` 是根据上述契约**重新编写的最小可用实现**，并非原始参赛代码。
其用途是：让 `python app.py` 能起来、让前端 `/predict` 请求有正确响应，
从而把仓库恢复到「clone 下来就能跑」的状态。重建真实模型时只需替换
`load_model()` 中的加载逻辑。
