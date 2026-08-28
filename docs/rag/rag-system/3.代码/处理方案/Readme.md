# 3.代码 处理方案

> 状态：2026-08-28 代码深读 9 份完成（分析-01~09，三端：01~07 Python 引擎 + 08 Java 网关 + 09 前端白盒 UI）。
> 权威度：代码证据层 **0.8**，切片池 `doc_type=code_analysis`，不强制检索摘要。

## 一、流程

1. **深读模块代码（本模块代码层只读 `ai-edu-ai-service` Python 服务，无 Java/前端三端）**——**真读代码是第一铁律**，调用链/枚举/阈值/降级分支全部以实际读到的代码为准。代码真值源：
   - **核心逻辑** `ai-edu-ai-service/core/rag/`：`query.py`（823 行，双池检索/页面锚定/两道门/打分/降级）、`assistant.py`（652 行，编排/引导/会话）、`eval_agent.py`（389 行，评测 hit@k + answer_quality）、`guide_pool.py`（370 行，GUIDE_POOL["rag-system"] 引导池）
   - **离线流水线** `ai-edu-ai-service/scripts/rag/`：12 脚本（build_index.py / slice_corpus.py / slice_full.py / md_to_jsonl.py / rag_query.py / run_eval.py / eval_dataset.py / gen_summaries.py / gen_full_summaries.py / upload_cos.py / export_slices_md.py / recover_slices.py）
   - **API 入口** `ai-edu-ai-service/api/rag.py`（193 行）+ `api/rag_assistant.py`（213 行）
2. **按模块拆 7 大分析主题**：`01 整体架构` / `02 语料切片` / `03 索引` / `04 检索编排` / `05 引导` / `06 评测` / `07 API降级`
3. **通过提示词 `提示词/代码深读-分析文档-提示词.md` 生成分析-XX 文档**
   （含：高层业务调用链 mermaid(带异常分支)、枚举/常量/配置表格、隐性坑与注意事项、对账分类；每个主题开始前先明确本主题读哪些文件）
4. **产出供 RAG 切片池检索**（`doc_type=code_analysis`，权威 0.8，不强制检索摘要）+ 完善文档"落地真相"节引用 + 方案-代码对账的输入

## 二、7 大分析主题

| 主题 | 覆盖内容 | 主要读的代码 |
|---|---|---|
| 分析-01 整体架构 | 模块定位/文件职责划分/双池与权威度分层/guide_pool 与各模块关系/双池双索引（rag-full/rag-slice） | core/rag/ 全四文件 + api/rag.py + rag_assistant.py |
| 分析-02 语料切片 | 完善文档→切片逻辑/切片器/元数据（authority/doc_type/模块标签）/切片清单 | scripts/rag/slice_corpus.py、slice_full.py、md_to_jsonl.py、export_slices_md.py |
| 分析-03 索引 | build_index/embedding（dashscope 768 维）/COS 向量桶/索引幂等（--clear）/写延迟 | scripts/rag/build_index.py、upload_cos.py + core/rag 中 embedding 调用 |
| 分析-04 检索编排 | 双池检索（索引层 QA + 源文档池）/页面锚定（页面模式+全局模式）/两道门（权限门+范围门阈值 0.75/0.5）/打分/降级链 | core/rag/query.py、assistant.py、scripts/rag/rag_query.py |
| 分析-05 引导 | GUIDE_POOL["rag-system"] 5 组（intro/operation/data_relation/difficulty/rag）/引导问题=索引层入口/问题列表同步 | core/rag/guide_pool.py |
| 分析-06 评测 | eval_agent/hit@k（HIT_K）+ answer_quality（编造封顶 3 分）/trace/报告/run_eval 离线跑 | core/rag/eval_agent.py、scripts/rag/run_eval.py、eval_dataset.py |
| 分析-07 API降级 | api/rag.py + rag_assistant.py 端点/错误冒泡/吞异常降级/20s 内部超时/边界拒答/权限校验 | api/rag.py、api/rag_assistant.py + query.py 降级分支 |

> 差异区提示：`04 检索编排`（双池/页面锚定/两道门是面试最常问）与 `07 API降级`（降级矩阵）是 rag-system 的差异化主题，厚写。
