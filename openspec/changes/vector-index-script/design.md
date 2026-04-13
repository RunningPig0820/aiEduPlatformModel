## Context

### 当前状态

`LocalVectorRetriever` 在 `kp_matcher.py` 中定义，每次调用 `match_all()` 时：

1. 检查是否已初始化 → 若未初始化则懒加载
2. 加载 `sentence-transformers` 模型（约 300MB）
3. 预计算所有图谱知识点的向量（5000 × 512 维）
4. 整个过程耗时 30-60 秒

### 问题

- 每次运行匹配脚本都重复加载模型
- 每次都重新计算向量（图谱知识点不变）
- 无法独立调试向量检索效果

## Goals / Non-Goals

**Goals:**
1. 创建独立的向量索引构建脚本
2. 索引持久化存储，支持复用
3. `KPMatcher` 支持加载预构建索引
4. 支持增量更新索引（图谱知识点变化时）
5. **构建进度显示**（用户体验优化）
6. **CLI 暴露 `--candidate-top-n` 参数**（动态调整粗筛候选数）

**Non-Goals:**
1. 不实现分布式向量索引（当前图谱规模小）
2. 不使用 FAISS 等专业向量库（numpy 暴力搜索足够）
3. 不支持多模型切换（固定使用 bge-small-zh-v1.5）

## Decisions

### D1: 索引文件格式

**决策**: 使用 numpy 二进制格式存储向量

| 格式 | 优点 | 缺点 |
|------|------|------|
| **numpy .npy** | 加载快、内存友好、Python原生 | 需numpy依赖 |
| JSON | 可读性好 | 加载慢、占用大 |
| pickle | Python通用 | 安全风险 |

**选择**: `kg_vectors.npy` + `kg_texts.json` + `index_meta.json`

### D2: 索引存储位置

**决策**: 存储在 `output/vector_index/` 目录

```
output/vector_index/
├── kg_vectors.npy       # 向量矩阵 (5000, 512)
├── kg_texts.json        # 知识点文本列表
├── kg_concepts.json     # 图谱知识点元数据（uri, label）
└── index_meta.json      # 索引元数据
```

### D3: 增量更新策略

**决策**: 基于时间戳检测变化

```python
# index_meta.json
{
    "model_name": "BAAI/bge-small-zh-v1.5",
    "vector_dim": 512,
    "concept_count": 5000,
    "created_at": "2026-04-12T10:00:00",
    "neo4j_checksum": "abc123"  # 图谱数据校验和
}
```

**检测逻辑**:
- 加载索引时检查 `neo4j_checksum`
- 若 checksum 不匹配，提示用户重新构建

### D4: KPMatcher 加载策略

**决策**: 支持三种加载方式

```python
class KPMatcher:
    def __init__(self, use_vector_retrieval=True, use_prebuilt_index=False):
        # 1. 不使用向量检索
        # 2. 使用向量检索（懒加载）
        # 3. 使用预构建索引（加载文件）
```

**命令行参数**:
```bash
python match_textbook_kp.py --use-prebuilt-index  # 使用预构建索引
python match_textbook_kp.py --force-build-index   # 强制重新构建
```

## Dependencies

### 安装

```bash
pip install sentence-transformers numpy
```

**依赖说明**:

| 依赖包 | 版本要求 | 说明 |
|-------|---------|------|
| `sentence-transformers` | ≥ 2.0 | 提供 Embedding 模型加载 |
| `numpy` | ≥ 1.20 | 向量存储与相似度计算 |

### 首次运行

首次运行需要下载 Embedding 模型（约 300MB）：

```bash
# 安装依赖
pip install sentence-transformers numpy

# 构建索引（首次会自动下载模型）
python edukg/scripts/kg_data/build_vector_index.py
```

**模型下载说明**:
- 模型: `BAAI/bge-small-zh-v1.5`
- 大小: ~300MB
- 来源: Hugging Face Hub
- 需要网络畅通

### 内存要求

| 项目 | 内存占用 |
|-----|---------|
| Embedding 模型 | ~2.5 GB |
| 向量索引 | ~10 MB |
| 其他 | < 1 GB |
| **总计** | **约 3.5 GB** |

**最低配置**: 8GB 内存机器可运行

## Risks / Trade-offs

### R1: 索引文件过期

**风险**: 图谱知识点变化后，索引文件未更新导致匹配结果错误

**缓解**:
- 存储 `neo4j_checksum` 检验和
- 加载时检测不匹配，提示用户重新构建
- 提供 `--force-build-index` 参数强制重建

### R2: 内存占用

**风险**: 预构建索引 + 匹配运行可能占用较多内存

**缓解**:
- 索引文件约 10MB，模型约 2.5GB
- 总计约 3.5GB，8GB 机器可运行
- 若内存不足，自动回退到 difflib

### R3: 模型版本兼容

**风险**: 不同版本的 sentence-transformers 可能产生不同向量

**缓解**:
- 在 `index_meta.json` 中记录模型版本
- 加载时检查模型名称一致性