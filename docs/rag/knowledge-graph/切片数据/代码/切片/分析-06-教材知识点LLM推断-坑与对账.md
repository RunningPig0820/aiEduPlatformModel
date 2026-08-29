# 分析-06-教材知识点LLM推断-坑与对账
> summary: 教材知识点LLM推断坑与对账
> 来源: 切片 ｜ 锚点: 坑与对账
> 节: 分析-06-教材知识点LLM推断
> COS路径: rag-slices/knowledge-graph/代码/分析-06-教材知识点LLM推断-坑与对账.md
> 类别：开发难点
> target: 开发对账

---

## 隐性坑与注意事项

- **推断≠严格一致性校验**：`knowledge_points` 分支只要求"两模型都有输出"，不比对内容——GLM 输出 3 条、DeepSeek 输出 5 条仍"consensus=True"采纳 GLM 的 3 条。想校验内容一致性需另改 `_check_consensus`。
- **置信度来自模型自报**：推断置信度是 LLM 自填的 `confidence` 两模型平均，不是外部验证，0.934 只代表模型自身把握度。
- **断点续传按节、不按 Prompt 级缓存去重**：恢复是 TaskState 检查点优先；`llm_cache` 是第二道（相同 Prompt 直接命中）。
- **`--resume` 默认开启**：想全量重跑必须 `--no-resume`，否则已完成检查点全跳过。
- **进程锁依赖 portalocker**：未安装直接 `raise ImportError`（process_lock.py:49-53）。
- **缓存键是 Prompt 的 SHA256**：改提示词模板 = 旧缓存全部失效（缓存键随内容变化），重跑会重新调 LLM。
- **推断结果必须 merge 才生效**：infer 只输出 `textbook_kps_inferred.json`，不合并，下一步强制 `merge_inferred_kps.py`（infer_textbook_kp.py:313）。

## 对账要点（复盘）

### 方案 vs 实现

- **断点续传三件套（D11）**：语雀/design 口径为 TaskState + CachedLLM + ProcessLock → 实际 `llmTaskLock/` 三模块全落地，推断/匹配复用。**落地：断点续传三件套与方案一致，全落地并复用。**
- **状态存储（D11/D12）**：语雀 D12 称"MySQL 替代早期 SQLite" → 实际 `TaskState` 用 JSON 文件存 `output/progress/`，无 MySQL。**翻转：Python 管道状态存储实为 JSON 文件，非 MySQL。**
- **前置依赖权重（D9）**：语雀 D9"定义依赖 0.85" → 实际 `prerequisite_inferer.py fuse_results` 定义依赖升级 PREREQUISITE 用 `confidence=0.9`（:302），LLM 升级 +0.1 封顶 1.0（:320）。**翻转：前置依赖权重从 0.85 → 0.9（D9 已自注）。**
- **推断阈值（D7）**：语雀 D7 提"阈值 0.5/0.6/0.8" → 实际推断任务（knowledge_points 分支）**无硬阈值**，只要求两模型都有输出；0.8/0.6 阈值仅在 `vote_prerequisite` 方法内（当前管线未调用）。**翻转：阈值不作用于推断路径。**

### 注释 vs 运行行为

- **缓存命中统计**：语雀称推断缓存命中高 → 实际 `textbook_kps_inferred.json` 中 from_cache=0（该批次缓存未命中）。**数据观察：该批次推断缓存未命中（from_cache=0），与"命中高"描述不符。**

> 证据：详见 `3.代码/分析-06-教材知识点LLM推断.md`（§隐性坑与注意事项 / §对账要点）
