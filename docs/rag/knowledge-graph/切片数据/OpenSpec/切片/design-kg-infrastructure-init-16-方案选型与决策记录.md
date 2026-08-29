# 方案选型与决策记录

> summary: 方案选型与决策记录
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-kg-infrastructure-init-16-方案选型与决策记录.md
> 类别：架构设计

图谱基础设施初始化设计稿（design-python-2026-04-08-kg-infrastructure-init）记录 5 项关键决策 D1~D5，属设计阶段素材（权威 0.7，已落地/构想未实现/待决策并存），业务真实实现请以权威度 0.8 的 canonical 真相源文档为准。贯穿约束：支持 Linux/macOS/Windows 跨平台、免费与付费模型、锁超时防死锁、不依赖外部服务（如 Redis）。

## D1 存储方案 → JSON 文件

**决策**：使用 JSON 文件存储任务状态（不依赖 MySQL）。
**理由**：简单易用无需额外服务、适合单机场景、便于调试和查看、课标处理任务规模不大。
**替代方案 MySQL**：更可靠、支持并发，但需要额外配置、增加复杂度。

## D2 缓存策略 → SHA256 缓存键

**决策**：LLM 响应缓存到文件，使用 prompt 的 SHA256 前 16 位作缓存键。
**理由**：文件缓存简单可靠；SHA256 键保证唯一性；便于调试（可直接查看文件）。
**接口**：get_cache_key/save_cache/load_cache。

## D3 进程锁实现 → portalocker

**决策**：使用文件锁（portalocker）。
**理由**：跨平台支持、简单高效、防止多进程同时运行；带 timeout 超时机制防死锁。

## D4 任务状态接口 → TaskState

**决策**：统一的任务状态接口。
**方法**：start/complete_checkpoint/fail_checkpoint/get_next_checkpoint/is_completed/get_progress/resume，支撑断点续传与进度恢复。

## D5 LLM 调用包装器 → CachedLLM

**决策**：带 cache 的 LLM 调用包装器。
**机制**：invoke 先查缓存再调模型，结果自动保存，支持 use_cache 开关。
