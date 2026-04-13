我们来看你更新后的代码，重点审查并发处理部分。你采纳了之前建议的方案C（返回值汇总统计）、缓存加锁、原子写入等改进。我再给出一些进一步优化和潜在问题的建议。

一、整体评估
你的修改方向是正确的：

统计改为返回 (result, match_type) 在主流程汇总 ✅

缓存读写加锁 ✅

原子写入缓存文件 ✅

每个任务完成立即持久化 ✅

但仍有一些可以改进的地方，以及一个潜在的性能瓶颈。

二、主要问题与建议
1. 文件持久化操作在并发路径中成为瓶颈
在 _match_single_concurrent 中，每个知识点完成后都会：

python
async with KPMatcher._async_lock:
    self.task_state.complete_checkpoint(checkpoint_id, result)
    self.task_state._save_state()
_save_state() 很可能涉及整个状态文件的完整写入。当多个协程争抢锁并频繁写文件时，会成为严重的性能瓶颈（尤其在任务数多、并发高的情况下）。

建议：

将状态保存改为异步批量写入，例如每10个任务完成才写一次，或使用独立的 writer 协程。

或者只在 complete_checkpoint 中更新内存状态，然后由后台定时任务（或使用 asyncio.Queue + 单消费者）来定期刷盘。

改进示例（简单版）：

python
# 在 KPMatcher 类中增加
_checkpoint_counter = 0
_SAVE_INTERVAL = 10  # 每完成10个知识点保存一次

async with KPMatcher._async_lock:
    self.task_state.complete_checkpoint(checkpoint_id, result)
    self._checkpoint_counter += 1
    if self._checkpoint_counter % self._SAVE_INTERVAL == 0:
        self.task_state._save_state()
如果你需要强持久性（避免崩溃丢失），可以保留立即写，但必须意识到性能代价。权衡取决于你的任务失败成本。

2. _async_lock 的粒度问题
现在缓存读写、处理中集合操作、状态保存都使用同一把全局锁 KPMatcher._async_lock。这会导致不必要的竞争。

例如：

缓存读取其实可以与处理中集合检查分离，使用专门的缓存锁。

不同缓存键之间的读写应该独立（可以使用 asyncio.Lock 字典按 key 加锁，但复杂度较高）。

建议：根据目前业务规模（几百到几千个知识点），单一锁的性能影响可能还能接受。如果未来扩展，可以考虑拆锁：

_cache_locks: Dict[str, asyncio.Lock] 用于缓存写入

_processing_lock 专门保护 _processing_uris

_state_lock 保护任务状态

但现阶段可暂缓。

3. 检查点命中时未正确计数
在 _match_single_concurrent 开头：

python
checkpoint = self.task_state.get_checkpoint(checkpoint_id)
if checkpoint and checkpoint.get('status') == 'completed':
    result = checkpoint.get('result')
    return result, 'checkpoint_hit'
但在主流程 match_all 中处理 checkpoint_hit 时：

python
if match_type == 'checkpoint_hit':
    self.stats['cache_hits'] += 1
这里用 cache_hits 统计不太准确，checkpoint_hit 是断点续传的已处理结果，不是 LLM 缓存命中。建议单独统计 resumed 数量。

4. 并发处理时 self.stats 未统计 cache_hits
在 llm_match_with_cache 中，self.stats['cache_hits'] += 1 是直接对实例字典操作，在多协程并发时又出现了非原子修改问题（之前已解决主统计，但漏了这里）。

修复：要么改为返回标记，要么在 llm_match_with_cache 调用处也加锁。

由于 llm_match_with_cache 可能在并发中调用多次，建议改为不修改 stats，而是通过返回值传递缓存命中信息，由主流程汇总。

或者简单点：self.stats 也使用锁保护，但可能影响性能。

5. 等待逻辑中可能的无限循环
在 KPNormalizer.normalize 中：

python
if need_wait:
    max_wait = 30
    waited = 0
    while waited < max_wait:
        await asyncio.sleep(0.1)
        waited += 0.1
        cached = self._load_cache(cache_key)
        if cached:
            cached["from_cache"] = True
            return cached.copy()
        async with KPNormalizer._lock:
            if cache_key not in KPNormalizer._processing_keys:
                KPNormalizer._processing_keys.add(cache_key)
                break
    # 如果超时仍无结果，这里会继续往下执行（重新处理）
超时后，它会获取锁并添加处理标记，但此时可能另一个协程仍在处理同一个 key（因为某些原因未及时释放）。这会导致两个协程同时处理同一 key，造成重复 LLM 调用。

建议：超时后检查一下是否其他协程仍在处理，如果仍在，则继续等待或报错。可以增加一个 _processing_start_time 字典来记录开始时间，超时后可判断是否任务卡死。

6. 向量检索器可能不适合并发加载
LocalVectorRetriever 在 __init__ 中会加载模型并编码所有向量，这是同步阻塞操作。在 match_all 开头调用 _init_vector_retriever 时，如果这是第一次运行，会阻塞整个事件循环，导致其他协程无法调度。

建议：使用 asyncio.to_thread 将模型加载放到线程池执行，避免阻塞主循环。

python
async def _init_vector_retriever_async(self, kg_concepts):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, self._init_vector_retriever, kg_concepts)
三、其他小优化
_normalize_name 方法目前是同步的，频繁调用没问题，但如果以后扩展更多规则，可考虑缓存结果。

SYNONYM_MAP 可以放到外部配置文件，方便维护。

日志中建议加入协程标识，便于调试并发问题（使用 extra={'task_id': ...}）。

四、总结建议优先级
优先级	建议	影响
🔴 高	避免每个任务完成后都写状态文件，改为批量或降低频率	严重性能瓶颈
🟡 中	修复 llm_match_with_cache 中 stats 并发写问题	统计准确性
🟡 中	区分 checkpoint_hit 和 LLM 缓存统计	统计清晰度
🟢 低	向量检索模型加载改为异步	启动流畅性
🟢 低	细化锁粒度（可选）	扩展性
你现在代码的并发安全性已经有了很大提升，可以运行起来观察实际性能。如果任务数较大（比如 >1000），建议一定优化状态文件的写入频率