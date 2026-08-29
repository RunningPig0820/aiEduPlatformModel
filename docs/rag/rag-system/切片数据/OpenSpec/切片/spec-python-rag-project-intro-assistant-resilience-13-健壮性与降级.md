# 健壮性与降级（超时降级）
> summary: 健壮性与降级（超时降级）
> 权威度: 0.7
> 模块: rag-system
> COS路径: rag-slices/rag-system/OpenSpec/spec-python-rag-project-intro-assistant-resilience-13-健壮性与降级.md
> 类别：开发难点

---

## 文档说明
> 本文件由 OpenSpec 设计素材（spec-python-rag-project-intro-assistant-resilience.md）按业务主题「健壮性与降级」重切合并（超时降级部分）。
> 设计阶段素材：真实实现以权威度 0.8 的 canonical 真相源 + 代码为准（代码已部分落地）；含 已落地 / 构想未实现 / 待决策 内容，引用需核对代码。

### Purpose：弹性规范（超时/断连不阻塞不烧钱）
> 检索摘要：弹性规范要解决什么问题——超时/断连下不无限阻塞、不空转烧钱？

分层超时（召回 2s / 生成 8s）、断连取消（is_disconnected）、超时降级话术写死（0 token）、tokens_usage 透明计费 + trace_id 断线补查。保证对话超时/断开时不无限阻塞、不空转烧钱。

> 证据：详见 `2.OpenSpec design 决策/原来的文件/spec-python-rag-project-intro-assistant-resilience.md`（§Purpose）

### Requirement: 分层超时
> 检索摘要：分层超时怎么设——召回单路各 2s、生成层 8s，超时分别如何降级？

系统 SHALL 对链路各阶段设硬超时：召回层（向量/BM25 单路）各 2s，生成层 8s。任何阶段超时不得无限阻塞。

#### Scenario: 召回单路超时降级
- **WHEN** 向量召回超 2s 未返回
- **THEN** 该路降级为空继续 BM25，链路继续，rerank 标记 degraded

#### Scenario: 生成超时返回召回清单
- **WHEN** 生成层超 8s 未完成
- **THEN** 不走 LLM，直接固定降级话术："我找到了以下相关资料，但生成完整答案超时了，您可以直接点击查看原文：块1、块2、块3"，附精排块清单

> 证据：详见 `2.OpenSpec design 决策/原来的文件/spec-python-rag-project-intro-assistant-resilience.md`（§Requirement: 分层超时）

### Requirement: 超时降级话术写死
> 检索摘要：超时降级话术为什么写死——严禁调 LLM、降级路径 0 token 零成本？

系统 SHALL 将超时降级话术写死在代码，严禁调 LLM 生成，降级路径 0 token。

#### Scenario: 降级零成本
- **WHEN** 生成超时降级
- **THEN** 写死话术 + 召回清单，无 LLM 调用

> 证据：详见 `2.OpenSpec design 决策/原来的文件/spec-python-rag-project-intro-assistant-resilience.md`（§Requirement: 超时降级话术写死）
