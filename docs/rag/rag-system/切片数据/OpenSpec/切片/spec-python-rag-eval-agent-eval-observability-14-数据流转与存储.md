# 数据流转与存储（评测 trace 落盘）
> summary: 数据流转与存储（评测 trace）：每次评测运行落 trace（JSONL）记录 query/检索池/召回条目+得分/hit/生成答案/引用/usage/耗时/判分，可单条回溯定位问题。
> 权威度: 0.7
> 模块: rag-system
> COS路径: rag-slices/rag-system/OpenSpec/spec-python-rag-eval-agent-eval-observability-14-数据流转与存储.md
> 类别：数据关联

---

### 评测 trace
> 检索摘要：每次评测运行落 trace（JSONL）记录 query、检索池、召回条目+得分、hit 结果、生成答案、引用、usage、耗时、判分，可单条回溯定位问题。

系统 SHALL 为每次评测运行落 trace（JSONL），记录：query、检索池、召回条目+得分、hit 结果、生成答案、引用、usage、耗时、判分。

#### Scenario: trace 落盘

- **WHEN** 一条评测完成
- **THEN** 该条完整过程 SHALL 追加写入 trace 文件（可单条回溯定位问题）

> 证据：详见 `2.OpenSpec design 决策/原来的文件/spec-python-rag-eval-agent-eval-observability.md`（§评测 trace）
