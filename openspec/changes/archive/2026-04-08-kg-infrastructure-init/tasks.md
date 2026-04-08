## 1. 模块目录结构

- [x] 1.1 创建 `edukg/core/llmTaskLock/` 目录
- [x] 1.2 创建 `edukg/core/llmTaskLock/__init__.py` 模块导出
- [x] 1.3 创建 `edukg/core/llmTaskLock/README.md` 模块文档

## 2. 状态管理模块 (state_manager.py)

- [x] 2.1 创建 `edukg/core/llmTaskLock/state_manager.py`
- [x] 2.2 实现 `TaskState` 类初始化
  - `__init__(task_id, state_dir)` 初始化
  - `_load_state()` 加载现有状态
- [x] 2.3 实现任务生命周期方法
  - `start(total)` 开始任务，创建检查点
  - `complete_checkpoint(id, result)` 完成检查点
  - `fail_checkpoint(id, error)` 标记失败
- [x] 2.4 实现进度查询方法
  - `get_next_checkpoint()` 获取下一个待处理
  - `is_completed()` 是否完成
  - `get_progress()` 获取进度
- [x] 2.5 实现恢复方法
  - `resume()` 恢复未完成的检查点
- [x] 2.6 实现状态文件读写
  - `_save_state()` 保存状态到 JSON
  - `_backup_state()` 状态备份机制
  - 原子写入（先写临时文件，再重命名）

## 3. LLM 缓存模块 (llm_cache.py)

- [x] 3.1 创建 `edukg/core/llmTaskLock/llm_cache.py`
- [x] 3.2 实现缓存键生成
  - `get_cache_key(prompt)` - SHA256[:16] 哈希
- [x] 3.3 实现缓存读写
  - `save_cache(key, result, cache_dir)` - 保存到文件
  - `load_cache(key, cache_dir)` - 从文件加载
- [x] 3.4 实现 `CachedLLM` 包装器类
  - `__init__(llm, cache_dir)` 初始化
  - `invoke(prompt, use_cache=True)` 调用 LLM
- [x] 3.5 实现缓存清理
  - `clear_cache(cache_dir)` - 清理全部缓存
  - `clear_cache(cache_dir, older_than=N)` - 清理旧缓存

## 4. 进程锁模块 (process_lock.py)

- [x] 4.1 添加 `portalocker` 依赖到 requirements.txt
- [x] 4.2 创建 `edukg/core/llmTaskLock/process_lock.py`
- [x] 4.3 实现 `ProcessLock` 类
  - `__init__(lock_file, timeout=3600)` 初始化
  - `__enter__` / `__exit__` 上下文管理器
- [x] 4.4 实现手动获取释放
  - `acquire()` 获取锁
  - `release()` 释放锁
- [x] 4.5 实现锁超时检测
  - 检查锁文件时间戳
  - 自动清理残留锁

## 5. 模块导出更新

- [x] 5.1 更新 `edukg/core/__init__.py` 导出 llmTaskLock
- [x] 5.2 在 `edukg/core/llmTaskLock/__init__.py` 导出核心类
  - TaskState, CachedLLM, ProcessLock

## 6. 集成到 curriculum 模块

- [x] 6.1 更新 `kp_extraction.py` 使用 `TaskState`
  - 在 `extract_knowledge_points()` 中添加状态管理
  - 每个分块作为一个检查点
  - 支持从断点恢复
- [x] 6.2 更新 `class_extractor.py` 使用 `CachedLLM`
  - 类型推断结果缓存
  - 避免重复调用
- [x] 6.3 更新 `statement_extractor.py` 使用 `CachedLLM`
  - 定义生成结果缓存
- [x] 6.4 更新 `kg_main.py` 添加断点续传支持
  - 添加 `--resume` 参数
  - 添加 `--clear-cache` 参数

## 7. 单元测试

- [x] 7.1 创建 `tests/test_llmTaskLock/test_state_manager.py`
  - 测试状态保存和加载
  - 测试断点恢复
  - 测试进度查询
- [x] 7.2 创建 `tests/test_llmTaskLock/test_llm_cache.py`
  - 测试缓存键生成
  - 测试缓存读写
  - 测试缓存命中
- [x] 7.3 创建 `tests/test_llmTaskLock/test_process_lock.py`
  - 测试锁获取和释放
  - 测试超时清理
- [x] 7.4 验证所有测试通过 `pytest tests/test_llmTaskLock/ -v`

---

## 任务统计

| 阶段 | 任务数量 | 状态 |
|------|----------|------|
| 模块目录结构 | 3 | ✅ 完成 |
| 状态管理模块 | 6 | ✅ 完成 |
| LLM 缓存模块 | 5 | ✅ 完成 |
| 进程锁模块 | 5 | ✅ 完成 |
| 模块导出更新 | 2 | ✅ 完成 |
| 集成到 curriculum | 4 | ✅ 完成 |
| 单元测试 | 4 | ✅ 完成 |
| **总计** | **29** | **29/29 ✅** |