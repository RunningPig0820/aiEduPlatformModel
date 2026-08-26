# RAG 执行计划：数据质量梳理 → COS 写入 → 入向量（双池）→ 引导问题功能

> 状态：**任务记录**（2026-08-26 定稿，待逐步执行）
> 用途：当前多任务并线，按依赖顺序推进，避免互相干扰。**用户引导任务执行。**

## 执行顺序（用户确认）

```
阶段 1 数据质量梳理 → 阶段 2 COS 写入 → 阶段 3 入向量（双池）→ 阶段 4 引导问题功能
```

| 阶段 | 内容 | 依赖 |
|---|---|---|
| 1 | 数据质量梳理（修数据，生成干净 jsonl） | — |
| 2 | COS 写入（传定稿文档到普通桶，前端"查看原文"用） | 依赖 1 |
| 3 | 入向量（双池：rag-full 23 块 + rag-slice 324 块，双池召回） | 依赖 1 |
| 4 | 引导问题功能（前端/后端交互逻辑，独立线，最后回头处理） | 无 |

**关键判断**：阶段 2（普通桶文档）与阶段 3（向量桶索引）互不依赖，但都依赖阶段 1 数据定稿。

---

## 用户决策（2026-08-26 确认）

- **COS 目标桶** = `ai-edu-1318177119`（Java 普通桶，region ap-guangzhou）
- **入向量** = 直接做双池（不是单索引）
- **执行顺序** = 数据质量 → COS 写入 → 入向量 → 引导问题功能

---

## 阶段 1：数据质量梳理

**目标**：修数据问题，生成干净的 jsonl + 切片数据。

- [ ] 1.1 补完善文档 01 "为什么做"段（痛点→业务价值→闭环价值，tasks.md 1.8 P1）
- [ ] 1.2 修切片文件"原文不存在"路径（tasks.md 1.9 R1-R4 路径语义统一）
- [ ] 1.3 重新切片 → 生成干净 jsonl（含 category 标签、pool 字段）
  - ⚠️ 重跑 slice_corpus 会丢完善文档 01 手工增强段 → **先备份 jsonl，01 段先补回源文件再切**
- [ ] 1.4 同步更新 `切片数据/` 视图（export_slices_md.py）

## 阶段 2：COS 写入（文档上传普通桶）

**目标**：把定稿切片文档上传 COS 普通桶，前端"查看原文"走 COS 不依赖本地路径。

- [x] 2.1 目标桶确认：`ai-edu-1318177119`（region ap-guangzhou）
- [x] 2.2 可写凭据：复用 `COS_VECTORS_SECRET_ID/KEY`，探针实测可写普通桶（无需新子账号）
- [x] 2.3 上传脚本：`scripts/rag/upload_cos.py` 读 `> COS路径:` 头 → `CosS3Client.put_object`，317 文件全量上传成功、幂等（2026-08-26）
- [x] 2.5 验收（COS 侧）：抽查 12/12 与本地 sha256 一致
- [ ] 2.4 前端读取：改"查看原文"走 COS URL（或后端代理 COS 透传），去掉 `/api/rag/source` 本地 StaticFiles
- [ ] 2.5 验收（前端侧）：随机抽查 file_path → COS 取文件可达，前端不再报"原文不存在"

## 阶段 3：入向量（双池，两个独立索引）

**目标**：全量池（整体问题）+ 切片池（细节问题），双池召回 RRF 融合。
**决策已定稿（2026-08-26）**：切片池 **294**（`切片数据/` 已切 md，**不重跑 slice_corpus**，不含完善文档）；全量池 **23**；**同一 `rag-1318177119` 桶双索引** `rag-full` + `rag-slice`（已建好）；**category 筛选已去掉**（评测验证后）；旧 `rag-index` 已清空。任务清单见 `每模块流水线-tasks.md` **1.13**。

- [x] 3.1 数据准备：**D1** `md_to_jsonl.py`（切片数据 md → `rag_slices.jsonl`，294 块，pool=slice）+ **D2** `slice_full.py`（语雀5+完善文档8+代码10 整篇 → `rag_slices_full.jsonl`，23 块，pool=full）+ **D3** 旧 jsonl 备份
- [x] 3.2 settings：**C1** `COS_VECTORS_INDEXES` 加 `"rag-full"` / `"rag-slice"`（同 `COS_VECTORS_RAG_BUCKET`）
- [x] 3.3 vector_store：**C2** `_resolve_bucket_index` 特判改 `startswith("rag")`
- [x] 3.4 build_index：**B1** `--pool full|slice` 分池写入；make_key 池前缀
- [x] 3.5 query.py：**Q1-Q6** `_key_of` 池前缀；`retrieve_vector` 加参；`retrieve_dual`；`orchestrate` 第三路 RRF + module Filter（category 筛选已去掉）
- [x] 3.6 调用方：**Q7** assistant.recall / rag_query.py / api/rag.py / query.rag_query 接入双池
- [x] 3.7 前置：`rag-full`/`rag-slice` 索引已建
- [x] 3.8 验证：**B2** 入桶（rag-full 23 条 + rag-slice 294 条）+ **B3** 清空 rag-index + **V1-V4** 方向/测试/文档对齐（V4 本次完成）

## 阶段 4：引导问题功能（后续独立线）

前端/后端交互逻辑，数据底座已备好（90 引导问题已入 jsonl），此阶段回头处理功能实现。

---

## 涉及文件（各阶段对应）

| 文件 | 阶段 |
|---|---|
| `docs/rag/ai-tutoring/4.完善文档/01-模块定位与核心价值.md` | 1 |
| `scripts/rag/slice_corpus.py` | 1 |
| `scripts/rag/export_slices_md.py` | 1 |
| `scripts/rag/slice_full.py`（新增） | 3 |
| `scripts/rag/build_index.py` | 3 |
| `config/settings.py` | 3 |
| `core/tutoring/vector_store.py` | 3 |
| `core/rag/query.py` | 3 |
| `core/rag/assistant.py` | 3 |
| `scripts/rag/rag_query.py` + `api/rag.py` | 3 |
| `docs/rag/ai-tutoring/5.难点/坑档案.md` | 1 |
| 测试：`tests/rag/test_rag_query.py`、`tests/tutoring/unit/test_vector_store.py` | 3 |

## 验证

1. 阶段 1：jsonl 干净（含 category + 01 增强段保留），切片视图同步
2. 阶段 2：`切片数据/` 全量 md 上传 ai-edu-1318177119 可达；前端"查看原文"走 COS 通
3. 阶段 3：rag-full 23 条 + rag-slice 324 条；双池查询方向验证；测试全绿
4. 阶段 4：引导问题功能（前端/后端）联调

## 注意事项

- 阶段 1 先备份 jsonl；重跑切片丢 01 段风险（tasks.md 1.12）
- 阶段 3 需 COS 控制台先建两个新索引（768/float32/cosine）
- 阶段 2 与阶段 3 互不依赖（普通桶文档 vs 向量桶），但都依赖阶段 1 数据定稿
