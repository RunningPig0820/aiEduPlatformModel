# 向量索引 CLI 文档

> 本模块为命令行工具，不提供 HTTP API

---

## 1. build_vector_index.py - 向量索引构建脚本

### 基本信息

| 项目 | 值 |
|------|-----|
| 路径 | `edukg/scripts/kg_data/build_vector_index.py` |
| 类型 | 命令行脚本 |
| 依赖 | `sentence-transformers`, `numpy` |

### 命令行参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `--status` | Flag | 否 | 显示现有索引状态 |
| `--force` | Flag | 否 | 强制重建索引 |
| `--model` | String | 否 | 指定 Embedding 模型（默认 `BAAI/bge-small-zh-v1.5`） |

### 输出文件

索引构建完成后输出到 `output/vector_index/`：

| 文件 | 说明 |
|------|------|
| `kg_vectors.npy` | 向量矩阵 (N, 512) numpy 格式 |
| `kg_texts.json` | 知识点文本列表 |
| `kg_concepts.json` | 图谱知识点元数据（uri, label） |
| `index_meta.json` | 索引元数据 |

### 使用示例

**构建索引**:
```bash
python edukg/scripts/kg_data/build_vector_index.py
```

**查看索引状态**:
```bash
python edukg/scripts/kg_data/build_vector_index.py --status
```

**强制重建**:
```bash
python edukg/scripts/kg_data/build_vector_index.py --force
```

**使用其他模型**:
```bash
python edukg/scripts/kg_data/build_vector_index.py --model BAAI/bge-large-zh
```

---

## 2. match_textbook_kp.py - 知识点匹配脚本（新增参数）

### 新增命令行参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `--use-prebuilt-index` | Flag | 否 | 使用预构建的向量索引 |
| `--force-build-index` | Flag | 否 | 强制重建索引后再匹配 |
| `--no-vector-retrieval` | Flag | 否 | 禁用向量检索，使用 difflib |

### 使用示例

**使用预构建索引**:
```bash
python edukg/scripts/kg_data/match_textbook_kp.py --use-prebuilt-index --resume
```

**强制重建索引后匹配**:
```bash
python edukg/scripts/kg_data/match_textbook_kp.py --force-build-index --resume
```

**禁用向量检索（回退到 difflib）**:
```bash
python edukg/scripts/kg_data/match_textbook_kp.py --no-vector-retrieval --resume
```

---

## 错误码说明

### CLI 错误码

| 错误 | 说明 |
|------|------|
| `IndexNotFoundError` | 预构建索引文件不存在 |
| `IndexOutdatedError` | 索引已过期（checksum 不匹配） |
| `ModelNotFoundError` | Embedding 模型下载失败 |

---

## 注意事项

### 1. 首次运行

首次运行 `build_vector_index.py` 需要下载模型（约 300MB）：

```bash
# 确保网络畅通
pip install sentence-transformers
python build_vector_index.py
```

### 2. 索引更新

当 EduKG 图谱知识点发生变化时，需要重建索引：

```bash
python build_vector_index.py --force
```

### 3. 内存要求

向量检索需要约 3.5GB 内存（模型 2.5GB + 索引 10MB）