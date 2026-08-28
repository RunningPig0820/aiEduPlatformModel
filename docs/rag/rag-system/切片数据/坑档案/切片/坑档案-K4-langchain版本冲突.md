# 坑档案 K4 conda 默认环境 langchain 版本冲突

> summary: langchain 版本冲突：conda 默认环境 langchain_openai 与 langchain-core 不匹配报 LangSmithParams ImportError（统一 venv 解决，全量 315 通过）
> 权威度: 0.8 ｜ 来源: 坑档案 ｜ 锚点: K4. conda 默认环境 langchain 版本冲突
> 模块: rag-system ｜ 节: 坑档案
> COS路径: rag-slices/rag-system/坑档案/坑档案-K4-langchain版本冲突.md
> 类别：开发难点
> target: 开发对账

---

**坑**：默认 `python`（conda）跑测试，`langchain_openai`（user-site 1.1.12）import 时报 `cannot import name 'LangSmithParams' from 'langchain_core'`。
**根因**：user-site 的 langchain_openai 与 conda 的 langchain-core（0.1.23）版本不匹配——一个环境两套 langchain，互相踩。
**解决**：统一用 `ai-edu-ai-service/venv`（langchain-core 1.2.20 + langchain-openai 1.1.11 匹配），CLAUDE.md 更新所有命令 + 环境警告；全量 315 通过（仅真实 API 测试需密钥）。
**价值**：环境隔离是前提——之前 RAG 生成一直想绕开 langchain 写 openai 直连，其实修好环境就能用现成 LLMFactory。
**证据**：`56a84bf`（CLAUDE.md venv 统一）+ 本会话环境诊断
