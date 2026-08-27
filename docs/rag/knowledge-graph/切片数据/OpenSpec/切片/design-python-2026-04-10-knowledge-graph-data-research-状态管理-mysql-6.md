# 13.2.5 原子性操作保证
> summary: 结果文件与状态更新原子性用 MySQL 事务+两阶段提交，先写缓存再处理业务状态避免重复付费。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-04-10-knowledge-graph-data-research-状态管理-mysql-6.md
> 类别：数据存储

> 检索摘要：结果文件与状态更新原子性用 MySQL 事务+两阶段提交，先写缓存再处理业务状态避免重复付费。

问题：如果结果文件写入成功，但状态更新失败怎么办？
解决方案：使用 MySQL 事务 + 两阶段提交。
def process_subbatch_with_atomic(sub_batch, batch_id, state_db: StateDB, cache_dir, provider, model):
    """
    原子性处理子批次（MySQL 事务）
    """
    cache_key = compute_cache_key(sub_batch)

    # 阶段1: 检查缓存
    cached = state_db.get_cached_response(cache_key)
    if cached:
        return {'cache_key': cache_key, 'file': cached['result_file']}

    # 阶段2: 调用 LLM
    result = call_llm(sub_batch)

    # 阶段3: 保存结果文件
    result_file = f"{cache_dir}/{cache_key}.json"
    with open(result_file, 'w') as f:
        json.dump(result, f)

    # 阶段4: 原子性更新（MySQL 事务）
    try:
        with state_db.db.transaction() as conn:
            with conn.cursor() as cursor:
                # 4.1 保存缓存记录
                cursor.execute("""
                    INSERT INTO llm_cache
                    (cache_key, provider, model, batch_uris, response, created_at)
                    VALUES (%s, %s, %s, %s, %s, NOW())
                """, (cache_key, provider, model,
                      json.dumps([kp.uri for kp in sub_batch]),
                      json.dumps(result)))

                # 4.2 更新子批次状态
                cursor.execute("""
                    UPDATE subbatch_state
                    SET status = 'completed',
                        cache_key = %s,
                        result_file = %s,
                        completed_at = NOW()
                    WHERE batch_id = %s
                """, (cache_key, result_file, batch_id))

    except Exception as e:
        # 事务自动回滚
        logging.error(f"事务失败: {e}")
        raise

    return {'cache_key': cache_key, 'file': result_file}

关键保证：
● 事务失败 → 缓存未记录 → 下次重跑会重新调用（可能重复付费）
● 事务成功 → 缓存已记录 → 下次重跑直接使用缓存

更安全的做法：先写缓存，再处理业务状态。
def safer_process_subbatch(sub_batch, batch_id, state_db, cache_dir):
    """
    更安全的处理顺序：先保存缓存，再更新业务状态
    """
    cache_key = compute_cache_key(sub_batch)

    # 1. 调用 LLM
    result = call_llm(sub_batch)

    # 2. 立即保存缓存（独立事务，优先保证）
    result_file = save_cache_file(cache_dir, cache_key, result)
    state_db.save_cache(cache_key, result, result_file)  # 独立事务

    # 3. 更新业务状态（即使失败，缓存已保存）
    state_db.mark_subbatch_completed(batch_id, cache_key, result_file)

    return result

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-10-knowledge-graph-data-research.md`（§13.2 状态管理（MySQL））
