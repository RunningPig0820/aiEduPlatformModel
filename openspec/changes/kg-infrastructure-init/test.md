# 断点续传基础设施 测试用例设计

## 1. 测试概述

### 1.1 测试目标
验证 `kg-infrastructure-init` 模块的所有业务场景，确保断点续传、LLM 缓存、进程锁功能的正确性和健壮性。

### 1.2 测试方式
- **单元测试**：使用 pytest 测试各模块核心功能
- **Mock LLM**：使用 mock 替代真实 LLM 调用
- **临时目录**：使用 `tmp_path` fixture 创建临时测试目录
- **无外部依赖**：不依赖真实数据库或 LLM 服务

### 1.3 测试环境配置
- pytest 配置：`pytest.ini`
- Python 版本：3.11+
- 测试框架：pytest + pytest-mock
- Mock 策略：LLM 调用使用 mock，文件操作使用临时目录

---

## 2. 测试数据

| 参数 | 值 | 说明 |
|-----|-----|-----|
| TEST_TASK_ID | `test_extraction` | 测试任务ID |
| TEST_CHECKPOINT_ID | `chunk_001` | 测试检查点ID |
| TEST_PROMPT | `提取以下知识点...` | 测试LLM提示词 |
| TEST_LLM_RESPONSE | `{"result": "success"}` | 测试LLM响应 |
| TEST_TOTAL_CHECKPOINTS | 5 | 测试总检查点数 |
| TEST_TIMEOUT | 10 | 测试锁超时时间（秒） |

---

## 3. 测试用例清单

### 3.1 TaskState 状态管理

| 用例编号 | 场景描述 | 前置条件 | 输入 | 预期结果 |
|---------|---------|---------|------|---------|
| STATE-001 | 新建任务状态 | 无任务状态文件 | `task_id="test"` | 创建新状态文件，status=pending |
| STATE-002 | 开始任务 | status=pending | `start(total=5)` | status=in_progress，创建5个检查点 |
| STATE-003 | 完成检查点 | status=in_progress | `complete_checkpoint("chunk_1", result)` | 检查点status=completed，进度+1 |
| STATE-004 | 失败检查点 | status=in_progress | `fail_checkpoint("chunk_2", "error")` | 检查点status=failed，记录错误 |
| STATE-005 | 获取进度 | 有已完成的检查点 | `get_progress()` | 返回 {total, completed, failed, pending} |
| STATE-006 | 任务完成 | 所有检查点已完成 | `is_completed()` | 返回 True |
| STATE-007 | 任务未完成 | 有待处理的检查点 | `is_completed()` | 返回 False |
| STATE-008 | 获取下一个检查点 | 有待处理的检查点 | `get_next_checkpoint()` | 返回第一个pending的ID |
| STATE-009 | 恢复任务 | 中途失败后重启 | `resume()` | 返回pending检查点列表 |
| STATE-010 | 状态持久化 | 有状态变更 | 重启后重新加载 | 状态文件正确加载 |
| STATE-011 | 原子写入 | 写入过程中断 | 模拟写入中断 | 状态文件不被损坏 |
| STATE-012 | 状态备份 | 更新状态 | 状态变更 | 创建备份文件 |

### 3.2 LLMCache 缓存模块

| 用例编号 | 场景描述 | 前置条件 | 输入 | 预期结果 |
|---------|---------|---------|------|---------|
| CACHE-001 | 生成缓存键 | 无 | `get_cache_key("test prompt")` | 返回 SHA256[:16] 哈希值 |
| CACHE-002 | 相同提示词相同键 | 无 | 两次相同prompt | 返回相同的缓存键 |
| CACHE-003 | 不同提示词不同键 | 无 | 两次不同prompt | 返回不同的缓存键 |
| CACHE-004 | 保存缓存 | 无缓存文件 | `save_cache(key, result)` | 创建缓存文件 |
| CACHE-005 | 加载缓存 | 缓存文件存在 | `load_cache(key)` | 返回缓存内容 |
| CACHE-006 | 加载不存在缓存 | 缓存文件不存在 | `load_cache(key)` | 返回 None |
| CACHE-007 | 缓存命中 | 缓存存在 | `CachedLLM.invoke(prompt)` | 返回缓存结果，不调用LLM |
| CACHE-008 | 缓存未命中 | 缓存不存在 | `CachedLLM.invoke(prompt)` | 调用LLM，保存结果到缓存 |
| CACHE-009 | 禁用缓存 | 缓存存在 | `invoke(prompt, use_cache=False)` | 调用LLM，不使用缓存 |
| CACHE-010 | 清理缓存 | 有缓存文件 | `clear_cache(cache_dir)` | 删除所有缓存文件 |
| CACHE-011 | 清理指定天数缓存 | 有旧缓存 | `clear_cache(older_than=7)` | 只删除7天前的缓存 |
| CACHE-012 | 缓存格式验证 | 缓存文件损坏 | 加载损坏文件 | 返回 None 或抛出异常 |

### 3.3 ProcessLock 进程锁

| 用例编号 | 场景描述 | 前置条件 | 输入 | 预期结果 |
|---------|---------|---------|------|---------|
| LOCK-001 | 获取锁 | 无锁文件 | `ProcessLock.__enter__` | 创建锁文件，获取锁 |
| LOCK-002 | 释放锁 | 锁已获取 | `ProcessLock.__exit__` | 删除锁文件，释放锁 |
| LOCK-003 | 上下文管理器 | 无锁 | `with ProcessLock(...)` | 自动获取和释放锁 |
| LOCK-004 | 锁超时检测 | 锁文件存在超过timeout | 检查锁文件时间戳 | 自动清理残留锁 |
| LOCK-005 | 防止重复获取 | 锁已被其他进程持有 | 尝试获取锁 | 等待或抛出超时异常 |
| LOCK-006 | 锁文件包含进程信息 | 获取锁 | 创建锁文件 | 锁文件包含PID和时间戳 |
| LOCK-007 | 手动获取释放 | 无锁 | `acquire()` + `release()` | 正常获取和释放 |
| LOCK-008 | 异常时自动释放 | 锁已获取，发生异常 | 模拟异常 | 锁自动释放 |

### 3.4 API 接口测试

| 用例编号 | 场景描述 | 前置条件 | 输入 | 预期结果 |
|---------|---------|---------|------|---------|
| API-001 | 查询任务进度-存在 | 任务状态文件存在 | `GET /api/infra/task/{id}/progress` | 返回进度信息 |
| API-002 | 查询任务进度-不存在 | 任务状态文件不存在 | `GET /api/infra/task/{id}/progress` | 返回 20001 错误码 |
| API-003 | 清理缓存-成功 | 有缓存文件 | `DELETE /api/infra/cache` (已登录) | 返回删除数量 |
| API-004 | 清理缓存-未登录 | 无认证 | `DELETE /api/infra/cache` | 返回 10004 错误码 |
| API-005 | 清理缓存-指定天数 | 有旧缓存 | `DELETE /api/infra/cache?older_than=7` | 只删除旧缓存 |
| API-006 | 重置任务状态-成功 | 任务状态存在 | `DELETE /api/infra/task/{id}/state` | 返回备份信息 |
| API-007 | 重置任务状态-未登录 | 无认证 | `DELETE /api/infra/task/{id}/state` | 返回 10004 错误码 |

---

## 4. 错误码对照表

| 错误码 | 常量名 | 说明 |
|-------|-------|------|
| 00000 | SUCCESS | 成功 |
| 10001 | INVALID_PARAMS | 参数无效 |
| 10002 | NOT_FOUND | 实体不存在 |
| 10003 | VALIDATION_ERROR | 参数校验失败 |
| 10004 | UNAUTHORIZED | 未授权 |
| 20001 | TASK_NOT_FOUND | 任务不存在 |
| 20002 | DIR_NOT_FOUND | 目录不存在 |
| 20003 | LOCK_TIMEOUT | 锁超时 |
| 20004 | TASK_IN_PROGRESS | 任务进行中 |
| 20005 | CACHE_READ_ERROR | 缓存读取失败 |

---

## 5. 测试用例统计

| 模块 | 用例数量 |
|-----|---------|
| TaskState 状态管理 | 12 |
| LLMCache 缓存模块 | 12 |
| ProcessLock 进程锁 | 8 |
| API 接口 | 7 |
| **总计** | **39** |

---

## 6. 测试执行顺序

测试按文件名和方法名顺序执行：

```
tests/test_llmTaskLock/test_state_manager.py    : TaskState 测试 (STATE-001 ~ STATE-012)
tests/test_llmTaskLock/test_llm_cache.py        : LLMCache 测试 (CACHE-001 ~ CACHE-012)
tests/test_llmTaskLock/test_process_lock.py     : ProcessLock 测试 (LOCK-001 ~ LOCK-008)
tests/test_llmTaskLock/test_infra_api.py        : API 接口测试 (API-001 ~ API-007)
```

---

## 7. 辅助方法

### 7.1 创建临时状态目录
```python
@pytest.fixture
def temp_state_dir(tmp_path):
    """创建临时状态目录"""
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    return str(state_dir)
```

### 7.2 创建临时缓存目录
```python
@pytest.fixture
def temp_cache_dir(tmp_path):
    """创建临时缓存目录"""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    return str(cache_dir)
```

### 7.3 Mock LLM
```python
@pytest.fixture
def mock_llm(mocker):
    """创建 Mock LLM"""
    mock = mocker.MagicMock()
    mock.invoke.return_value = {"result": "mocked response"}
    return mock
```

### 7.4 创建测试任务状态
```python
def create_test_state(state_dir: str, task_id: str = "test") -> TaskState:
    """创建测试任务状态"""
    from edukg.core.llmTaskLock import TaskState
    state = TaskState(task_id, state_dir)
    state.start(total=TEST_TOTAL_CHECKPOINTS)
    return state
```

### 7.5 创建测试缓存
```python
def create_test_cache(cache_dir: str, prompt: str = TEST_PROMPT) -> str:
    """创建测试缓存"""
    from edukg.core.llmTaskLock.llm_cache import get_cache_key, save_cache
    cache_key = get_cache_key(prompt)
    save_cache(cache_key, TEST_LLM_RESPONSE, cache_dir)
    return cache_key
```

---

## 8. 运行测试

```bash
# 运行单个测试文件
pytest tests/test_llmTaskLock/test_state_manager.py -v

# 运行单个测试方法
pytest tests/test_llmTaskLock/test_state_manager.py::test_start_task -v

# 运行所有测试
pytest tests/test_llmTaskLock/ -v

# 运行并显示覆盖率
pytest tests/test_llmTaskLock/ --cov=edukg.core.llmTaskLock --cov-report=term-missing

# 运行特定模块测试
pytest tests/test_llmTaskLock/ -v -k "state"     # 只运行状态管理测试
pytest tests/test_llmTaskLock/ -v -k "cache"     # 只运行缓存测试
pytest tests/test_llmTaskLock/ -v -k "lock"      # 只运行进程锁测试

# 生成测试报告
pytest tests/test_llmTaskLock/ --html=report.html --self-contained-html
```

---

## 9. 测试覆盖率目标

| 模块 | 目标覆盖率 |
|-----|----------|
| llmTaskLock/state_manager.py | ≥ 90% |
| llmTaskLock/llm_cache.py | ≥ 90% |
| llmTaskLock/process_lock.py | ≥ 85% |
| **整体** | ≥ 85% |

---

*文档生成时间: 2026-04-07*