# 评估报告白盒展示(字段全集与无报告语义)
> summary: 报告接口返回最新baseline(hit@3/质量分/avg耗时/avg成本/条数/版本/judged),尚未跑评测返回明确的"暂无评估报告"提示不报错
> 权威度: 0.7
> 模块: rag-system
> COS路径: rag-slices/rag-system/OpenSpec/design-java-rag-project-intro-assistant-补充-12-评估报告白盒展示.md
> 类别：开发难点

---

### 评估报告白盒展示(字段全集与无报告语义)
> 检索摘要：报告接口返回最新baseline(hit@3/质量分/avg耗时/avg成本/条数/版本/judged),尚未跑评测返回明确的"暂无评估报告"提示不报错

目标 D10 已定义 `GET /api/rag/assistant/eval/report` 白盒展示。本块独有:接口返回最新报告**含 judged 字段**(hit@3、质量分、avg 耗时、avg 成本、**条数、版本、judged**);WHEN 尚未跑过评测 → THEN 返回明确的"暂无评估报告"提示,**不报错**。

> 证据：详见 `2.OpenSpec design 决策/原来的文件/design-java-rag-project-intro-assistant.md`（§补充(原 spec-java-rag-project-intro-assistant-eval 独有内容)/评估报告白盒展示）
