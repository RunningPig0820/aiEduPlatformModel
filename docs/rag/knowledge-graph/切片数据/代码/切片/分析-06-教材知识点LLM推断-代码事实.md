# 分析-06-教材知识点LLM推断-代码事实
> summary: 教材知识点LLM推断代码事实
> 来源: 切片 ｜ 锚点: 代码事实
> 节: 分析-06-教材知识点LLM推断
> COS路径: rag-slices/knowledge-graph/代码/分析-06-教材知识点LLM推断-代码事实.md
> 类别：架构设计
> target: 开发对账

---

## 代码事实

### CLI 入口（`infer_textbook_kp.py`）
| 命令 | 作用 | 证据 |
|---|---|---|
| `python infer_textbook_kp.py` | 推断所有缺失章节（断点续传默认开） | infer_textbook_kp.py:283-294 |
| `python infer_textbook_kp.py --stage primary/middle/high` | 按学段筛选（stage_map：小学/初中/高中） | infer_textbook_kp.py:141-144, 285 |
| `python infer_textbook_kp.py --dry-run` | 仅分析缺失章节，不推断 | infer_textbook_kp.py:214-219 |
| `python infer_textbook_kp.py --stats` | 显示当前进度与结果统计 | infer_textbook_kp.py:263-280 |
| `python infer_textbook_kp.py --no-resume` | 禁用断点续传，从头跑 | infer_textbook_kp.py:288-294 |

### 关键机制
1. **缺失判定**（`infer_textbook_kp.py:159-164`）：小学 `grade in [一~六年级]` 且 `len(existing_kps)==0` 才推断；高中同；初中明确"无需推断"（注释：初中 7-9 年级知识点完整约 252 个）。
2. **双模型投票特判路径**（`dual_model_voter.py:288-316`）：推断任务是 `knowledge_points` 分支——**不比较内容是否一致**，只要两模型都输出非空 `knowledge_points` 就采纳**主模型(GLM)**结果，置信度取两模型 `confidence` 平均值。任一无输出 → `consensus=False`，`error='某模型未输出知识点'`。
3. **推断失败降级**（`textbook_kp_inferer.py:225-244`）：投票不一致 → 保留已有知识点、`confidence=0.0`；`_parse_json_response` 解析失败（5 级 fallback：直接 json → 正则 `{...}` → ```` ```json ```` → ast.literal_eval，见 textbook_kp_inferer.py:125-170）→ 同样保留已有知识点。
4. **断点续传**（`textbook_kp_inferer.py:260-356`）：`TaskState("infer_kp")` 存检查点 `section_{section_id}`；恢复时从 `state.get('checkpoints')` 捞 completed 结果，过滤 `pending_sections`；每 `checkpoint_interval=10` 节 `_save_state()` 一次（textbook_kp_inferer.py:316, 344-348）。
5. **进程锁**（`textbook_kp_inferer.py:73-75, 308`）：`ProcessLock(output/progress/infer_kp.lock)` 包住批量循环，防多进程并发跑同一推断。
6. **LLM 缓存**（`textbook_kp_inferer.py:101-123`）：`get_cache_key(prompt)=SHA256(prompt)[:16]`（llm_cache.py:30），缓存文件存 `output/llm_cache/`；命中返回缓存并打 `from_cache=True`。
7. **LLM Gateway 延迟加载**（`dual_model_voter.py:75-91`）：`LLMFactory()` 动态导入；ImportError 时降级"模拟模式"（`_mock_call` 返回固定 `{"is_prerequisite": true,...}`，仅测试用，dual_model_voter.py:137-156）。
8. **合并入库**（`merge_inferred_kps.py`）：推断结果按 `section_id` 归位、按 `label` 去重，生成 `textbook-{primary|middle|high}-{seq:05d}` URI（merge_inferred_kps.py:75-87），`source='llm_inferred'`，重写 `in_unit_relations.json`。

### 枚举/常量/配置
| 类型 | 名称 | 取值 | 出处 |
|---|---|---|---|
| 模型 | PRIMARY_MODEL | glm-4-flash（免费主模型） | config.py:9 |
| 模型 | SECONDARY_MODEL | deepseek-chat（副模型） | config.py:11 |
| 阈值 | CONFIDENCE_THRESHOLD_HIGH | 0.8（≥→PREREQUISITE，用于前置投票方法） | config.py:15 |
| 阈值 | CONFIDENCE_THRESHOLD_LOW | 0.6（≥→PREREQUISITE_CANDIDATE） | config.py:17 |
| 批量 | BATCH_SIZE / RATE_LIMIT_DELAY | 10 / 1.0s | config.py:21,23 |
| 重试 | MAX_RETRIES / RETRY_DELAY | 3 / 2.0s | config.py:25,27 |
| 缓存键 | get_cache_key | SHA256(prompt) 前 16 位 | llm_cache.py:30 |
| 检查点 | checkpoint_interval | 10 节保存一次 | textbook_kp_inferer.py:264,316 |
| 进程锁 | ProcessLock timeout | 3600 秒 | process_lock.py:42 |
| 缓存 TTL | load_cache cache_ttl | 默认 None（永不过期） | llm_cache.py:83 |
| Prompt 约束 | 知识点数量 | 3-8 条/节，重点章节≤10 | prompts/textbook_kg.txt:18 |
| Prompt 约束 | 知识点长度 | 5-15 字 | prompts/textbook_kg.txt:16 |
| 输出 | 推断结果文件 | `output/textbook_kps_inferred.json` | infer_textbook_kp.py:240-241 |
| 输出 | 合并报告 | `output/merge_report.json` | merge_inferred_kps.py:236-239 |

> 实际数据（`output/textbook_kps_inferred.json`）：433 节（小学 361 + 高中 72），1616 个知识点，平均置信度 0.934，3 条带 error。合并后 `textbook_kps.json` 共 1905 条（llm_inferred 1616 + original 254 + rule_extract_empty_chapter 35）。

### 边界与降级
- 断点续传时 `completed_ids` 来自 TaskState 检查点，已完成的节直接跳过（textbook_kp_inferer.py:283-292）。
- 投票返回 `consensus=False` 的三种来源：LLM 调用异常（`LLMCallError`）、JSON 解析失败（`error='响应解析失败'`）、判断不一致——前两者由 `vote_with_retry` 重试（最多 MAX_RETRIES=3，解析失败重试、不一致不重试，dual_model_voter.py:492-507）。
- `infer_textbook_kp.py:315-323`：缺章节/知识点/教材文件 → `FileNotFoundError` 提示先跑 generate_textbook_data.py。

## 设计要点

- **免费模型当主模型**：GLM-4-flash 免费、DeepSeek 付费，投票结果采纳主模型输出，只在"有分歧风险"的匹配/前置任务里才让 DeepSeek 拿否决权（见分析-07）。
- **断点续传三件套解耦**：TaskState（状态）+ CachedLLM（缓存）+ ProcessLock（互斥）独立成 `core/llmTaskLock`，同一套基建复用给推断/匹配/标准化多个任务。
- **JSON 文件状态、不依赖外部服务**：state_manager 用原子写（临时文件+rename+备份）落 `output/progress/*.json`，无 MySQL 依赖，离线管道自洽。
- **状态机完备**：任务 pending/in_progress/completed/failed + 检查点 pending/completed/failed，`resume()` 取 pending+failed（state_manager.py:250-260）。

> 证据：详见 `3.代码/分析-06-教材知识点LLM推断.md`（§代码事实 / §设计要点）
