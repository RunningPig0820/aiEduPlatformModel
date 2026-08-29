# COS 向量桶字段说明

> 用途：记录 COS 向量桶（CosVectorsClient）的索引配置、写入 metadata、查询返回字段。
> 来源：`ai-edu-ai-service/scripts/rag/build_index.py` + `core/tutoring/vector_store.py` + `core/rag/query.py` + `config/settings.py`（2026-08-26 核对）。

---

## 1. 索引路由表（settings.COS_VECTORS_INDEXES）

| vector_type | 索引名 | 桶 | 用途 |
|---|---|---|---|
| `topic` | `topic-index` | `COS_VECTORS_BUCKET`（question-bank-1318177119） | 题型名向量聚集（canonical 归并） |
| `rag` | `rag-index` | `COS_VECTORS_RAG_BUCKET`（rag-1318177119） | RAG 问答语料（AI答疑/知识图谱/组织中心，多模块同索引按 `doc_type` 区分） |
| `question` | `question-index` | （预留） | 相似题，未建 |

路由逻辑：`vector_store._resolve_bucket_index(vector_type) → (bucket, index)`；`rag` 走独立 RAG 桶，其余走默认桶，未知 vector_type → `ValueError`。

---

## 2. 块 key（build_index.make_key，写入时生成）

```
key = "ai-tutoring/{file}/{anchor}#{chunk_idx}"
```

- `file`：源文件名（去 .md）
- `anchor`：块锚点（标题）
- `chunk_idx`：同 (file, anchor) 内序号（段落拆块/同锚点多块防 key 冲突）
- 同 key 上传 = upsert 覆盖；key **不带版本**（版本走 metadata）

---

## 3. 写入 metadata（build_index.py，每块写入 COS 的 metadata 字段）

| 字段 | 含义 | 示例 |
|---|---|---|
| `version` | 语料版本 = `YYYY-MM-DD-<语料sha1[:6]>`，语料变→版本变 | `2026-08-26-a1b2c3` |
| `doc_type` | 模块标识（多模块同索引区分，取 jsonl `tags.module`） | `ai-tutoring` |
| `module` | 模块锚点闭集 id（与 doc_type 同源，显式写入） | `ai-tutoring`/`knowledge-graph`/`question-analysis`/`rag-system` |
| `category` | **类型（9 类闭集标签）**，多路召回按类别筛选用 | `开发难点`/`架构设计`/`项目介绍`/`操作流程`/`数据关联`/`业务流程`/`业务视角`/`数据存储`/`未来演进` |
| `source` | 语料来源 | `完善文档`/`语雀`/`OpenSpec`/`代码`/`坑档案` |
| `authority` | 权威度 | `1.0`/`0.8`/`0.7` |
| `section` | 节（完善文档取 01~08，其余取文件名） | `05` |
| `file` | 源文件名（去 .md） | `05-数据落库与掌握度` |
| `file_path` | 相对语料根 `docs/rag/ai-tutoring/` 的路径（前端定位源文件） | `4.完善文档/05-数据落库与掌握度.md` |
| `anchor` | 块锚点 | `05-数据落库与掌握度` |
| `summary` | LLM 生成的"解决什么问题"一句话 | `解决掌握度按题型累计平均的落库口径...` |

> **text 全文不进 metadata**——COS 向量索引 metadata ~20KB/条限制，块最大 ~6000 字超限。text 留在 `rag_slices.jsonl`，检索命中后按 key 反查。

---

## 4. jsonl 块 tags（slice_corpus._tags，索引的源头结构）

`rag_slices.jsonl` 每块 `tags` 含 9 字段：

| 字段 | 说明 |
|---|---|
| `module` | 模块锚点闭集 id：`ai-tutoring`/`knowledge-graph`/`question-analysis`/`rag-system` |
| `category` | **类型（9 类闭集标签）**——2026-08-26 从切片文件头 `> 类别：` 反写进 jsonl（234 块全部补齐，分布见下） |
| `section` | 同 metadata.section |
| `source` | 同 metadata.source |
| `authority` | 同 metadata.authority |
| `file` | 同 metadata.file |
| `file_path` | 同 metadata.file_path |
| `anchor` | 同 metadata.anchor |

> jsonl 当前 category 分布（234 块）：架构设计 84 / 开发难点 70 / 操作流程 18 / 数据存储 16 / 项目介绍 15 / 数据关联 11 / 业务流程 11 / 业务视角 5 / 未来演进 4。
> ⚠️ 切片脚本 `slice_corpus.py` 未产 category（手动反写），需 1.11 T1 统一到切片流程。

---

## 5. 查询返回字段（vector_store.query_vector）

COS `query_vectors`（ReturnMetaData=True + ReturnDistance=True）返回每条：

| 字段 | 说明 |
|---|---|
| `key` | 块 key（第 2 节） |
| `metadata` | 写入时的 metadata（第 3 节） |
| `distance` | cosine distance，**越小越相似**（升序排列） |

`query.py` 消费 metadata 字段：`anchor/authority/file/file_path/section/source`（含 `_idx` 本地序号）。

---

## 6. ✅ 已补齐（2026-08-26）

| 补齐项 | 位置 | 状态 |
|---|---|---|
| `category`（类型） | jsonl 每块 `tags` | ✅ 234 块全部反写（从切片文件头 `> 类别：`） |
| `category`（类型） | build_index.py metadata | ✅ 已加，重建索引后生效（供检索按类别筛选） |
| `module` | build_index.py metadata | ✅ 已加（doc_type 改为取 tags.module，与 jsonl 对齐） |

> **下一步**：重建索引 `python scripts/rag/build_index.py --clear` 后，rag-index 每条 metadata 才含 `category` + `module`。多路召回按类别筛选（tasks.md 1.11 T3/T4）依赖该字段。

---

## 7. 大文档摘要召回机制（2026-08-29 定稿，sop 留档）

> 背景：全量池 rag-full 的整篇文档（语雀 canonical 9 / 代码分析 11 / 完善文档拆段 36），部分正文超 embedding 输入上限。机制：**条件式 embed + 摘要粗召回 + 切片池全文兜底**。

### 7.1 条件式 embed（build_index.py FULL_EMBED_MAX_CHARS=5000）

- `summary + text ≤ 5000 字符` → `embed(summary+全文)`：全文向量化（完善文档 36 段全部、小语雀/代码）
- `summary + text > 5000 字符` → 只 `embed(summary)`：大文档（语雀 9 整篇 5580~15893 / 代码 11 整篇 5589~13087）防 dashscope 8192 token 静默截断
- 阈值依据：中文约 1 token/字符，5000 字符≈5000 token 留安全余量；embedding 输入超 8192 token 会被静默截断，不可用
- **jsonl 阶段不截断**：jsonl 每块存**完整 text + summary**（反查全文/BM25 用）；阈值判断只在向量化（build_index）时做

### 7.2 大文档检索 = 三路召回（内容不丢）

| 召回路 | 用什么 | 定位 |
|---|---|---|
| 全量池向量 | summary（大文档只 embed summary） | 文档级粗召回（"这篇讲了啥"） |
| 切片池向量 | text 全文（切片全 ≤5000，297 块 embed 全文） | 细节精确召回（具体机制/数字/权衡） |
| BM25 | 本地 jsonl 全文分词 | 关键词精确命中（断电/断网仍可用） |

### 7.3 生成阶段

- 命中任意块 → 按 key 从本地 jsonl **反查全文**（`text_by_key`，metadata 不含 text 因 COS filterable metadata ≤2048B）
- 生成时单块 text 截断 `MAX_GEN_TEXT=1200` 字符喂 LLM（query.py:770，控制上下文长度）

### 7.4 双池分工（为什么大文档用摘要不是缺陷）

- 大文档（语雀/代码整篇）只 embed summary 是**有意的粗召回**：细节答案由切片池全文承担（语雀 56 块/代码 71 块/OpenSpec 81 块等）
- 若大文档也拆块全文向量化 → 与切片池大量重复（同批内容两处），浪费 embedding 成本
- 判断标准：**切片池负责"能精确回答"，全量池负责"文档级兜底 + 权威 1.0 正文"（完善文档）**
