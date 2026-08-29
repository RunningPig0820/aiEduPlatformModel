# 断点续传与工程化

> summary: 断点续传与工程化
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-kg-infrastructure-init-12-断点续传与工程化.md
> 类别：开发难点

本文为知识图谱数据处理项目工程化基础设施初始化设计稿（design-python-2026-04-08-kg-infrastructure-init，面向课程/教材处理的断点续传与 LLM 调用管理），属设计阶段素材（已落地/构想未实现/待决策并存），业务真实实现请以权威度 0.8 的 canonical 真相源文档为准。核心决策：JSON 文件存储任务状态、SHA256 文件缓存、portalocker 进程锁，落地 llmTaskLock 模块（TaskState/CachedLLM/ProcessLock），支持免费与付费模型且不依赖 Redis。

## 问题背景：中途失败需重头开始

curriculum（课标处理）模块 OCR 文件 321KB/189 页，知识点提取与类型推断等需要 100+ 次 glm-4-flash 调用，中途失败需要重头开始，因此必须引入断点续传。后续教材处理模块（知识点匹配、先修关系推断）同样依赖此基础设施，先修关系推断可能使用付费模型。

## 设计约束

- 支持 Linux/macOS/Windows 跨平台
- 支持免费和付费模型
- 锁超时防止死锁
- 简单易用，不依赖外部服务（如 Redis）

## Goals / Non-Goals

**Goals：**
- 实现任务状态管理（TaskState）
- 实现 LLM 缓存机制（LLMCache）
- 实现断点续传支持
- 实现进度显示和恢复

**Non-Goals：**
- 不实现分布式任务调度
- 不实现 Web UI
- 不实现复杂的成本监控（免费模型不需要）

## llmTaskLock 三件套总览

断点续传由 llmTaskLock 模块承载，三件套分工：
- TaskState：任务状态管理，JSON 文件落盘，支撑断点续传与进度恢复
- CachedLLM：带缓存的 LLM 调用包装器，先查缓存再调模型，自动保存结果
- ProcessLock：portalocker 文件锁，防止多进程同时运行，带 timeout 超时防死锁
- 状态存储选型：JSON 文件而非 MySQL（简单易用、无需额外服务、适合单机、便于调试）
- 缓存键：prompt 的 SHA256 前 16 位，保证唯一性与可调试性
