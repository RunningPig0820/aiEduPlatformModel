# 13.4 LLM 推理断点续传
> summary: LLM 批处理带缓存断点续传：先查状态/缓存，再标记处理中，成功保存缓存与成本，失败按重试次数降级。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-04-10-knowledge-graph-data-research-llm-推理断点续传.md
> 类别：操作流程

> 检索摘要：LLM 批处理带缓存断点续传：先查状态/缓存，再标记处理中，成功保存缓存与成本，失败按重试次数降级。

步骤级断点：
def process_llm_batches(candidates, state_db, cache_dir):
    """带缓存的 LLM 批处理"""
    for batch in candidates:
        batch_key = batch_id(batch)

        # 检查状态
        status = state_db.get_status(batch_key)
        if status == 'completed':
            logging.info(f"跳过已完成批次: {batch_key}")
            continue

        # 检查缓存
        cache_key = get_cache_key(batch, prompt_version='v2')
        cached = state_db.get_cached_response(cache_key)
        if cached:
            logging.info(f"使用缓存结果: {cache_key}")
            state_db.mark_completed(batch_key, cached['result_file'])
            continue

        # 标记处理中
        state_db.mark_processing(batch_key)

        try:
            result = call_llm(batch)
            # 保存缓存
            cache_path = save_cache(cache_key, result)
            state_db.mark_completed(batch_key, cache_path)
            # 记录成本
            state_db.track_cost(result['tokens'], result['cost'])
        except Exception as e:
            retry = state_db.get_retry_count(batch_key) + 1
            if retry < MAX_RETRIES:
                state_db.mark_pending(batch_key, retry_count=retry)
            else:
                state_db.mark_failed(batch_key, error=str(e))
                # 写入失败日志
                save_failed_batch(batch, str(e))

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-10-knowledge-graph-data-research.md`（§13.4 LLM 推理断点续传）
