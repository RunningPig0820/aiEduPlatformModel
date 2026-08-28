# 坑档案 K4 conda 默认环境 langchain 版本冲突 复盘

> summary: langchain 版本冲突复盘
> 来源: 切片 ｜ 锚点: 坑点复盘与口述
> 节: 坑档案 K4 conda 默认环境 langchain 版本冲突
> COS路径: rag-slices/interview/rag-system/坑档案/坑档案-K4-langchain版本冲突-复盘.md
> 类别：开发难点（9 视角闭集）
> target: 面试项目问答

---

## 坑点复盘
**现象**：用默认 python（conda）跑测试，langchain_openai 导入时报 `cannot import name 'LangSmithParams'`，测试直接崩。

**触发链路**：RAG 生成依赖 langchain → 测试环境混用 conda 默认环境与 user-site 安装的包 → import 时版本冲突。

**根因**：user-site 的 langchain_openai 与 conda 的 langchain-core 版本不匹配——一个环境里两套 langchain 互相踩。

**解决思路与权衡**：统一用项目自建 venv（langchain-core 1.2.20 + langchain-openai 1.1.11 匹配），更新所有命令和环境警告，全量测试通过。权衡点：与其绕开 langchain 手写 openai 直连，不如把环境隔离修好，直接用现成 LLM 工厂。

## 面试口述要点
RAG 生成想用 langchain 现成能力，但默认环境 langchain 版本冲突——user-site 的 langchain_openai 和 conda 的 langchain-core 不匹配。之前一直想绕开 langchain 手写 openai 直连，其实修好环境隔离就能用现成 LLMFactory。教训是环境隔离是前提，别在错误环境里做架构绕行。

> 证据：详见 `5.难点/坑档案-开发与验证.md`（K4）｜ `3.代码/分析-01-整体架构与调用链.md` ｜ `4.完善文档/05-技术实现.md`
