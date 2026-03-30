## Context

知识图谱数据处理项目需要工程化基础设施支持断点续传、成本控制和并发安全。这些是 LLM 推断任务（kg-math-prerequisite-inference）的前置依赖。

当前状态：
- **LLM 调用**: 约 8,980 次，付费模型（DeepSeek）需要成本控制
- **处理时间**: 可能数小时，需要断点续传
- **并发风险**: 多进程同时运行可能造成重复调用

设计约束：
- 使用 MySQL 作为状态存储（已有环境）
- 支持 Linux/macOS/Windows 跨平台
- 锁超时防止死锁

## Goals / Non-Goals

**Goals:**
- 实现状态管理库（StateDB）
- 实现进程锁机制（ProcessLock）
- 实现成本监控服务（CostTracker）
- 提供幂等性保证

**Non-Goals:**
- 不实现分布式任务调度（使用简单脚本即可）
- 不实现 Web UI（CLI 交互）
- 不实现多租户隔离（单用户场景）

## Decisions

### D1: 数据库选型

**决策**: 使用 MySQL 替代 SQLite

**理由**:
- 已有 MySQL 环境，无需额外安装
- 支持更好的并发性能
- 支持更丰富的运维工具
- 数据更安全（有备份机制）

**替代方案**: SQLite
- **缺点**: 不支持高并发，运维工具少

### D2: 状态表设计

**决策**: 两层状态表（章节 + 子批次）

```
chapter_state (业务层)
├── chapter_id, status, progress
└── subbatch_state (技术层)
    ├── batch_id, status, cache_key
    └── llm_cache (LLM 结果缓存)
```

**理由**:
- 章节是业务认知单位，重跑最小单位
- 子批次是技术限制（token 限制），对用户透明

### D3: 进程锁实现

**决策**: 文件锁（portalocker）+ MySQL 锁双保险

```python
# 文件锁（推荐）
class ProcessLock:
    def __init__(self, lock_file: str):
        self.lock_fd = open(lock_file, 'w')
        portalocker.lock(self.lock_fd, portalocker.LOCK_EX | portalocker.LOCK_NB)
```

**理由**:
- 文件锁简单高效，适合单机
- MySQL 锁适合分布式场景

### D4: 缓存策略

**决策**: LLM 响应缓存到 MySQL + 文件双写

```python
# 先写文件，再写数据库
result_file = save_cache_file(cache_key, result)
state_db.save_cache(cache_key, result, result_file)
```

**理由**:
- 文件存储大 JSON 对象
- 数据库存储元数据便于查询
- 先写文件保证缓存不丢失

### D5: 成本单位

**决策**: 使用"分"作为成本单位

```sql
cost_cents INT DEFAULT 0 COMMENT '成本（分）'
```

**理由**:
- 避免浮点数精度问题
- 便于汇总计算

## Risks / Trade-offs

### Risk 1: 数据库连接池耗尽
**风险**: 高并发时连接池可能耗尽
**缓解**: 配置合理的连接池大小（默认 5），添加连接超时

### Risk 2: 锁超时设置不当
**风险**: 锁超时太短导致正常进程被误杀
**缓解**: 默认 1 小时超时，支持命令行配置

### Risk 3: 缓存键冲突
**风险**: 不同批次可能生成相同缓存键
**缓解**: 使用 SHA256 哈希，包含完整批次信息

## Migration Plan

**执行步骤**:
1. 创建 MySQL 数据库和表
2. 部署 core 模块（state_db, process_lock, cost_tracker）
3. 运行单元测试验证
4. 后续 change 集成使用

**回滚策略**:
```sql
DROP DATABASE IF EXISTS ai_edu_kg;
```

## Open Questions

无（设计已确定）