# 坑档案-J-KG8-断点续传llmTaskLock

> summary: 断点续传llmTaskLock
> 来源: 坑档案 ｜ 锚点: J-KG8 ｜ 节: 5.难点/坑档案.md
> COS路径: rag-slices/knowledge-graph/坑档案/坑档案-J-KG8-断点续传llmTaskLock.md
> 类别：开发难点
> target: 开发对账

---

**1. 问题现象**：教学知识点推断预估 2-3 小时、图谱匹配 1-2 小时，中途断网/进程被杀后**从头重跑**，已花的 LLM 费用和进度全丢。

**2. 触发流程**：`infer_textbook_kp.py`/`match_textbook_kp.py` 跑长任务 → 中断（网络/超时/手动 Ctrl-C）→ 重启脚本发现又是从 0 开始。

**3. 根因分析**：修前任务**无状态**——每批循环都是临时变量，LLM 调用结果既不落盘进度也不缓存；长任务天然易中断，中断即全损。`problems_and_solutions.md` §六记录："LLM 任务耗时较长，中断后需要重新执行"。

**4. 排查过程**：一次推断跑到一半进程被 OOM 杀，重跑发现进度归零、相同 prompt 又调了一遍 LLM——既费时又费钱。

**5. 解决方案 & 改动点**：集成 `edukg/core/llmTaskLock` 三件套：① `TaskState`（`state_manager.py:20-279`）按 task_id 落 JSON，记录 checkpoints（每完成一个 section/kp 即 `complete_checkpoint`），重启后 `resume` 过滤已完成项——匹配侧见 `kp_matcher.py:1113-1125`（从 checkpoints 恢复 results + completed_uris）、推断侧见 `textbook_kp_inferer.infer_batch`；状态写入用**临时文件 + rename 原子写 + 备份**（`state_manager.py:97-120`）防写坏；② `ProcessLock`（`process_lock.py`）串行模式下文件锁防多进程并发写同一进度；③ `CachedLLM`/`llm_cache.py` 按 prompt MD5 缓存投票结果（`llm_cache.py`），相同知识点对不重复调 API（匹配侧 `kp_matcher.py:704-724` 缓存读写加 asyncio.Lock 防并发损坏）。提交：`0114a5d [知识图谱]-[llm任务锁开发]`、`1bb1b28 [知识图谱]-[断点续传]`。

**6. 面试口述要点**：长 LLM 任务的三层防护：**进度检查点**（每单位完成即落盘，粒度越细丢得越少）、**结果缓存**（同 prompt 不二次花钱）、**进程锁**（多实例不互相覆盖）。写进度要原子（tmp+rename），否则中断那一下正好把状态文件写坏。面试可强调：缓存键是 prompt 全文 MD5（`kp_matcher.py:710`），保证"同一知识点对 + 同一候选"才命中，语义变了不误命中。
