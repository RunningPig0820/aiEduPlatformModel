# 数据是怎么进 Neo4j 的？完整流程画一遍？

> summary: 操作流程引导问题回答：单向离线流水线 Phase0 爬取→Phase1 拆分/生成/清洗/增强/推断→Phase2 匹配→Phase3 导入(MERGE 幂等)→校验(verify/DAG)→向量索引；断点续传用 TaskState JSON 文件非 MySQL 状态表
> 权威度: 1.0（合成问答答案切片，非原始证据）
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/引导问题/引导问题-9-操作流程-数据是怎么进Neo4j的完整流程画一遍.md
> 类别：操作流程

**核心结论**：单向离线流水线 Phase0 爬取 → Phase1 拆分/生成/清洗/增强/推断/合并/属性 → Phase2 匹配 → Phase3 导入 Neo4j（11 脚本 MERGE 幂等）→ 校验（verify + DAG 环检测）→ 向量索引，最终落地 7 类节点/8 类关系（6757/20887）。

## 分层展开
主流程文字流程图（复用语料原始图，`4.完善文档/02`）：

```
数据来源(四类) ──────────────────────────▶ Phase0 爬取(renjiaoshe_math_crawler 断点续爬)
  EduKG TTL v0.1(ttl/*.ttl + relations/*.ttl + entities/*.json)    │ 23 册教材 JSON(小学12+初中6+高中人教A版2019 5)
  main.ttl v3.0(教材出处, 约16MB)                                      ▼
  人教版爬虫(小学初中目录)                          Phase1 拆分/生成/清洗/增强/推断/合并/属性
  课标2022(OCR 补小学)                                split_main_ttl / split_material_ttl(按学科)
                                                       generate_textbook_data(节点/关系 JSON)
        ┌─────────────────────────────────────────▶ clean_textbook_data(--analyze→--clean 防误删)
        │                                             → enhance_chapters(专题) → infer_textbook_kp(双模型投票)
        │                                             → merge_inferred_kps(合并) → enhance_kp_attributes(推断后增强)
        ▼
  Phase2 匹配: build_vector_index(bge 512) → normalize_textbook_kp(LLM 标准化)
        → match_textbook_kp(精确匹配 → 向量粗筛 top-20 → 双模型投票) → matches_kg_relations.json
        ▼
  Phase3 导入: import/ 11 个脚本按依赖顺序 MERGE 幂等 → Neo4j(7类节点/8类关系)
        ▼
  校验: verify_import(重复URI/v0.2) + analyze_textbook_matching(匹配率) + validate_dag(环检测)
        ▼
  向量: 匹配侧 kg_vectors.npy(512维) 本地预构建 + checksum 校验 / 服务侧 dashscope 768 维写 COS 桶
```
（依据：完善文档 02 主流程文字流程图）

- **各阶段谁负责/产出**：拆分 split_main_ttl/split_material_ttl 产 main-math.ttl(14019 triples)/material-math.ttl(6024 triples)；生成 generate_textbook_data 产节点/关系 JSON；清洗 clean_textbook_data（DataCleaner）产 duplicate_detection_report.json；增强 enhance_chapters + enhance_kp_attributes（纯规则）；推断 infer_textbook_kp 双模型产 textbook_kps_inferred.json(433 节→1616 条、平均置信 0.934)；匹配 match_textbook_kp 产 matches_kg_relations.json(1905 条)；导入 import/ 11 脚本 MERGE 幂等；校验 verify_import/analyze_textbook_matching/validate_dag（依据：完善文档 02 落地真相表）
- **断点续传（⚠️ 翻转）**：方案 D12 规划 MySQL 承接任务状态，代码落地是 llmTaskLock 的 TaskState 用 JSON 文件落 `output/progress/`（临时文件+rename 原子写+备份）；MySQL 状态表在 Python 管道里不存在；`infer_textbook_kp.py` 无 `--resume` 参数（依据：完善文档 02 落地真相）
- **匹配率口径（⚠️ 翻转）**：语雀 canonical 为 97.1%（1690/1740），当前数据文件 96.96%（1847/1905），是同链路不同数据快照，对外讲"~97%"准确（依据：完善文档 02 落地真相）

## 追问防御
- **可能追问：哪一步最容易出问题？** → 属性增强顺序 bug（先增强只覆盖 22%）、匹配率 17% 的语义错位；以及导入脚本默认数据路径与 README 不符（跑脚本用 `--file` 显式指定最稳）（依据：完善文档 02 追问与防御 / 局部翻转）
- **可能追问：重跑会不会重复数据？** → 导入全用 MERGE 幂等 + uri/id 唯一约束，可重跑；断点续传靠 TaskState 检查点文件，非 MySQL（依据：完善文档 02 落地真相）

> 证据：详见 `4.完善文档/02-知识图谱数据入库主流程.md` ｜ `3.代码/分析-01-知识图谱整体架构与数据链路.md` ｜ `3.代码/分析-02-TTL数据拆分与Neo4jSchema.md`
