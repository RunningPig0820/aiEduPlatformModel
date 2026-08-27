# 十六、技术栈更新
> summary: 技术栈更新：状态存储 MySQL、缓存键 SHA256、进程锁 portalocker/MySQL表锁、YAML配置、错误日志 MySQL 表、控制台告警。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-04-10-knowledge-graph-data-research-技术栈更新.md
> 类别：架构设计

> 检索摘要：技术栈更新：状态存储 MySQL、缓存键 SHA256、进程锁 portalocker/MySQL表锁、YAML配置、错误日志 MySQL 表、控制台告警。

技术项	选择	说明
状态存储	MySQL	已有环境，事务支持，并发性能好
缓存键算法	SHA256	替代 MD5，避免碰撞
进程锁	portalocker / MySQL 表锁	跨平台文件锁 或 分布式锁
配置格式	YAML	外置配置，灵活调整
错误日志	MySQL 表	结构化存储，便于重试脚本
告警方式	控制台日志	个人项目首选

#### 16.1 数据库依赖
> 检索摘要：脚本新增依赖：pymysql>=1.0.2、pyyaml>=6.0、portalocker>=2.7.0，写入 requirements-scripts.txt 不污染主服务。

# requirements-scripts.txt 新增
pymysql>=1.0.2
pyyaml>=6.0
portalocker>=2.7.0

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-10-knowledge-graph-data-research.md`（§十六、技术栈更新）
