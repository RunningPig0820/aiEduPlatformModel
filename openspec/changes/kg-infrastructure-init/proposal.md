> **执行顺序: 4/5** | **设计成本: 无** | **前置依赖: kg-math-native-relations**

## Why

知识图谱数据处理项目需要工程化基础设施来支持：
1. **断点续传**：LLM 推断任务可能因网络、API 限流等原因中断，需要从断点继续
2. **成本控制**：付费模型（DeepSeek）的调用结果必须持久化，防止重复计费
3. **并发安全**：防止误启动多进程，造成重复调用和数据冲突
4. **进度可视化**：实时监控处理进度，便于运维

原设计文档第十三章"任务执行与容错设计"在拆分后缺失，本 change 补充这部分工程化能力。

**核心原则**：
- 幂等性：脚本可重复执行，不产生重复数据或重复 LLM 调用
- 原子性：事务保证数据一致性
- 可观测性：进度可查询、成本可追踪

## What Changes

1. **状态管理库 (StateDB)**
   - MySQL 数据库表设计（processing_state, llm_cache, cost_tracking, chapter_state, subbatch_state）
   - StateDB 类实现（章节状态、子批次状态、LLM 缓存、成本追踪）
   - 进度查询和失败重试接口

2. **进程锁机制 (ProcessLock)**
   - 文件锁实现（portalocker）
   - MySQL 分布式锁实现（可选）
   - 锁超时和自动释放

3. **成本监控服务 (CostTracker)**
   - 实时成本累积
   - 成本告警阈值
   - 成本报告输出

4. **数据库连接管理 (MySQLManager)**
   - 连接池配置
   - 事务上下文管理器
   - 配置文件模板

## Capabilities

### New Capabilities

- `state-db`: 状态管理能力，支持断点续传、进度查询、失败重试
- `process-lock`: 进程锁能力，防止并发冲突
- `cost-tracker`: 成本监控能力，实时追踪 LLM 调用成本
- `mysql-manager`: MySQL 连接池管理能力

### Modified Capabilities

无（这是基础设施，不修改现有能力）

## Impact

- **新目录**: `edukg/scripts/kg_construction/core/`
- **新模块**: `state_db.py`, `process_lock.py`, `cost_tracker.py`, `db_connection.py`
- **新配置**: `config/database.yaml`
- **MySQL**: 新建数据库 `ai_edu_kg`，5 张表
- **后续依赖**: `kg-math-prerequisite-inference` 依赖此基础设施