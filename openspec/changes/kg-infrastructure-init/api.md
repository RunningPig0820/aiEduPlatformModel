# 断点续传基础设施 API 接口文档

> 基础路径: `/api/infra`
>
> 更新日期: 2026-04-07

---

## 目录

- [通用响应结构](#通用响应结构)
- [1. 查询任务进度](#1-查询任务进度)
- [2. 清理缓存](#2-清理缓存)
- [3. 重置任务状态](#3-重置任务状态)
- [Python 模块接口](#python-模块接口)
- [错误码说明](#错误码说明)

---

## 通用响应结构

所有接口均返回统一的 JSON 格式：

```json
{
  "code": "00000",
  "message": "success",
  "data": { ... }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| code | String | 状态码，`00000` 表示成功，其他为错误码 |
| message | String | 提示信息 |
| data | Object | 业务数据，可能为 null |

---

## 1. 查询任务进度

### 基本信息

| 项目 | 值 |
|------|-----|
| HTTP 方法 | `GET` |
| 接口路径 | `/api/infra/task/{task_id}/progress` |
| Content-Type | `application/json` |
| 需要登录 | 否 |

### 请求参数

**Path**

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|------|------|------|----------|------|
| task_id | String | 是 | 非空字符串 | 任务ID，如 `curriculum_extraction` |

### 响应参数

成功时 `data` 返回：

```json
{
  "task_id": "curriculum_extraction",
  "status": "in_progress",
  "progress": {
    "total": 15,
    "completed": 5,
    "failed": 1,
    "pending": 9
  },
  "started_at": "2026-04-07T10:00:00Z",
  "updated_at": "2026-04-07T10:30:00Z",
  "eta": "约 45 分钟"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| task_id | String | 任务ID |
| status | String | 任务状态：`pending`/`in_progress`/`completed`/`failed` |
| progress | Object | 进度详情 |
| progress.total | Integer | 总检查点数 |
| progress.completed | Integer | 已完成数 |
| progress.failed | Integer | 失败数 |
| progress.pending | Integer | 待处理数 |
| started_at | String | 开始时间（ISO 8601） |
| updated_at | String | 最后更新时间 |
| eta | String | 预估剩余时间（可选） |

### 请求示例

**cURL:**
```bash
curl -X GET http://localhost:8000/api/infra/task/curriculum_extraction/progress
```

**JavaScript (fetch):**
```javascript
const response = await fetch('/api/infra/task/curriculum_extraction/progress');
const result = await response.json();
console.log(result.data.progress);
```

### 常见错误

| code | message | 说明 |
|------|---------|------|
| 20001 | 任务不存在 | 指定的 task_id 没有对应的状态文件 |

---

## 2. 清理缓存

### 基本信息

| 项目 | 值 |
|------|-----|
| HTTP 方法 | `DELETE` |
| 接口路径 | `/api/infra/cache` |
| Content-Type | `application/json` |
| 需要登录 | 是 |

### 请求参数

**Query**

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|------|------|------|----------|------|
| cache_dir | String | 否 | 有效目录路径 | 缓存目录，默认 `cache/` |
| older_than | Integer | 否 | 正整数 | 清理 N 天前的缓存，默认全部 |

### 响应参数

成功时 `data` 返回：

```json
{
  "deleted_count": 156,
  "deleted_size": "12.5 MB",
  "remaining_count": 23
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| deleted_count | Integer | 删除的缓存文件数 |
| deleted_size | String | 删除的总大小 |
| remaining_count | Integer | 剩余缓存文件数 |

### 请求示例

**cURL:**
```bash
curl -X DELETE "http://localhost:8000/api/infra/cache?older_than=7" \
  -H "Authorization: Bearer <token>"
```

**JavaScript (fetch):**
```javascript
const response = await fetch('/api/infra/cache?older_than=7', {
  method: 'DELETE',
  headers: { 'Authorization': `Bearer ${token}` }
});
const result = await response.json();
```

### 常见错误

| code | message | 说明 |
|------|---------|------|
| 20002 | 目录不存在 | 指定的缓存目录不存在 |
| 10004 | 未登录 | 需要管理员权限 |

---

## 3. 重置任务状态

### 基本信息

| 项目 | 值 |
|------|-----|
| HTTP 方法 | `DELETE` |
| 接口路径 | `/api/infra/task/{task_id}/state` |
| Content-Type | `application/json` |
| 需要登录 | 是 |

### 请求参数

**Path**

| 字段 | 类型 | 必填 | 校验规则 | 说明 |
|------|------|------|----------|------|
| task_id | String | 是 | 非空字符串 | 任务ID |

### 响应参数

成功时 `data` 返回：

```json
{
  "task_id": "curriculum_extraction",
  "reset_at": "2026-04-07T11:00:00Z",
  "backup_file": "state/curriculum_extraction_backup_20260407.json"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| task_id | String | 任务ID |
| reset_at | String | 重置时间 |
| backup_file | String | 备份文件路径（可选） |

### 请求示例

**cURL:**
```bash
curl -X DELETE http://localhost:8000/api/infra/task/curriculum_extraction/state \
  -H "Authorization: Bearer <token>"
```

### 常见错误

| code | message | 说明 |
|------|---------|------|
| 20001 | 任务不存在 | 指定的任务状态文件不存在 |
| 10004 | 未登录 | 需要管理员权限 |

---

## Python 模块接口

> 供其他 Python 模块内部调用，非 HTTP API

### TaskState 类

```python
from edukg.core.llmTaskLock import TaskState

# 初始化
state = TaskState(
    task_id="curriculum_extraction",
    state_dir="state/"
)

# 开始任务
state.start(total=15)

# 完成检查点
state.complete_checkpoint("chunk_1", {"result": "..."})

# 标记失败
state.fail_checkpoint("chunk_2", "网络超时")

# 获取下一个待处理
next_id = state.get_next_checkpoint()

# 查询进度
progress = state.get_progress()

# 是否完成
if state.is_completed():
    print("任务已完成")

# 恢复未完成的检查点
pending = state.resume()
```

| 方法 | 参数 | 返回值 | 说明 |
|------|------|------|------|
| `start(total)` | total: int | None | 开始新任务 |
| `complete_checkpoint(id, result)` | id: str, result: any | None | 完成检查点 |
| `fail_checkpoint(id, error)` | id: str, error: str | None | 标记失败 |
| `get_next_checkpoint()` | - | str or None | 获取下一个待处理ID |
| `is_completed()` | - | bool | 任务是否完成 |
| `get_progress()` | - | dict | 进度信息 |
| `resume()` | - | list[str] | 恢复未完成的检查点 |

### CachedLLM 类

```python
from edukg.core.llmTaskLock import CachedLLM
from langchain_community.chat_models import ChatZhipuAI

# 初始化
llm = ChatZhipuAI(model="glm-4-flash")
cached_llm = CachedLLM(llm, cache_dir="cache/")

# 调用（自动缓存）
result = cached_llm.invoke(prompt)

# 不使用缓存
result = cached_llm.invoke(prompt, use_cache=False)

# 清理缓存
CachedLLM.clear_cache(cache_dir="cache/")
```

| 方法 | 参数 | 返回值 | 说明 |
|------|------|------|------|
| `invoke(prompt, use_cache)` | prompt: str, use_cache: bool=True | dict | 调用LLM，自动缓存 |
| `clear_cache(cache_dir)` | cache_dir: str | int | 清理缓存，返回删除数量 |

### ProcessLock 类

```python
from edukg.core.llmTaskLock import ProcessLock

# 上下文管理器方式
with ProcessLock("state/curriculum.lock", timeout=3600):
    # 执行任务，防止多进程冲突
    process_curriculum()

# 手动方式
lock = ProcessLock("state/curriculum.lock")
lock.acquire()
try:
    process_curriculum()
finally:
    lock.release()
```

| 方法 | 参数 | 返回值 | 说明 |
|------|------|------|------|
| `__enter__` | - | self | 获取锁 |
| `__exit__` | - | None | 释放锁 |
| `acquire()` | - | None | 手动获取锁 |
| `release()` | - | None | 手动释放锁 |

---

## 错误码说明

### 通用错误码 (1xxxx)

| code | message | 说明 |
|------|---------|------|
| 00000 | success | 成功 |
| 10000 | 系统错误 | 服务器内部错误 |
| 10001 | 参数错误 | 请求参数格式不正确 |
| 10002 | 实体不存在 | 请求的资源不存在 |
| 10003 | 参数无效 | 参数校验失败 |
| 10004 | 未登录 | 用户未登录或 Token 过期 |

### 断点续传模块错误码 (2xxxx)

| code | message | 说明 |
|------|---------|------|
| 20001 | 任务不存在 | 指定的任务ID没有状态文件 |
| 20002 | 目录不存在 | 指定的缓存/状态目录不存在 |
| 20003 | 锁超时 | 进程锁等待超时 |
| 20004 | 任务进行中 | 任务正在运行，无法重置 |
| 20005 | 缓存读取失败 | 缓存文件损坏或格式错误 |

---

## 前端调用注意事项

### 1. 认证管理

本系统使用 JWT Token 进行认证，前端需要：

- **携带 Token**: 所有需要登录的接口，请求时必须携带 `Authorization: Bearer <token>` 头
- **Token 刷新**: Token 过期后需调用刷新接口获取新 Token
- **跨域配置**: 开发环境需配置 CORS

```javascript
// fetch 请求示例
const token = localStorage.getItem('token');
fetch('/api/infra/cache', {
  method: 'DELETE',
  headers: {
    'Authorization': `Bearer ${token}`
  }
});
```

### 2. 进度轮询

查询任务进度时建议：

- **轮询间隔**: 每 5-10 秒查询一次
- **停止条件**: `status` 为 `completed` 或 `failed` 时停止
- **超时处理**: 超过预估时间未完成，显示异常提示

```javascript
async function pollProgress(taskId) {
  const response = await fetch(`/api/infra/task/${taskId}/progress`);
  const result = await response.json();

  if (result.data.status === 'in_progress') {
    // 更新UI进度条
    updateProgressUI(result.data.progress);
    // 继续轮询
    setTimeout(() => pollProgress(taskId), 5000);
  } else if (result.data.status === 'completed') {
    showSuccessMessage();
  } else {
    showErrorMessage(result.message);
  }
}
```

---

*文档生成时间: 2026-04-07*