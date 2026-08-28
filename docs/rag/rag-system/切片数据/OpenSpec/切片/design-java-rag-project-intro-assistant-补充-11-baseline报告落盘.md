# baseline 报告可复现与对比(落盘路径)
> summary: 每次语料/参数/提示词变更后重跑--compare生成对比报告(hit@k/质量分/成本/耗时↑↓=),trace落jsonl聚合报告落reports/<version>.json结构与run_eval.py一致
> 权威度: 0.7
> 模块: rag-system
> COS路径: rag-slices/rag-system/OpenSpec/design-java-rag-project-intro-assistant-补充-11-baseline报告落盘.md
> 类别：开发难点

---

### baseline 报告可复现与对比(落盘路径)
> 检索摘要：每次语料/参数/提示词变更后重跑--compare生成对比报告(hit@k/质量分/成本/耗时↑↓=),trace落jsonl聚合报告落reports/<version>.json结构与run_eval.py一致

目标 Context 已提 `run_eval.py --compare` 版本对比。本块独有:系统 SHALL 复用 `run_eval.py` 的可复现执行与版本对比能力(`--compare`),**每次语料/参数/提示词变更后重跑评测生成对比报告**(对比 hit@k/质量分/成本/耗时 ↑/↓/=);**trace 落盘 jsonl、聚合报告落盘 `reports/<version>.json`**,结构与既有 `run_eval.py` 一致。

> 证据：详见 `2.OpenSpec design 决策/原来的文件/design-java-rag-project-intro-assistant.md`（§补充(原 spec-java-rag-project-intro-assistant-eval 独有内容)/baseline 报告可复现与对比）
