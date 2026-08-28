# 问题提示(RAG 定向引导方向与静态池对齐)
> summary: 开始引导展示RAG定向引导chips(定位/架构/数据流/评测/坑)静态池0token非SSE,结束建议LLM失败静态池兜底对齐Python 6引导方向
> 权威度: 0.7
> 模块: rag-system
> COS路径: rag-slices/rag-system/OpenSpec/design-java-rag-project-intro-assistant-补充-14-问题提示RAG定向引导.md
> 类别：数据关联

---

### 问题提示(RAG 定向引导方向与静态池对齐)
> 检索摘要：开始引导展示RAG定向引导chips(定位/架构/数据流/评测/坑)静态池0token非SSE,结束建议LLM失败静态池兜底对齐Python 6引导方向

目标 D11 已定义开始/结束引导以底座池为唯一来源、必含 ≥1 条 RAG 方向。本块独有:
- **开始引导 RAG 定向方向**:会话入口(未提问)前端展示 RAG 定向引导 chips——**定位/架构/数据流/评测/坑**(5 个方向,静态池、0 token、非 SSE 拉取 `GET /api/rag/assistant/guide`)。
- **静态池兜底对齐 Python 6 引导方向**:suggestions LLM 调用失败 → 返回静态池预写建议(**对齐 Python 6 引导方向**),链路不中断。

> 证据：详见 `2.OpenSpec design 决策/原来的文件/design-java-rag-project-intro-assistant.md`（§补充(原 spec-java-rag-project-intro-assistant-guardrails 独有内容)/问题提示）
