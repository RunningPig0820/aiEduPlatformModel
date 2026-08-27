# 13.2.2 按课程单元划分
> summary: 重跑最小单位=章节（业务认知），内部按 token 限制拆子批次（技术限制），支持跳过已完成/已跳过章节断点续传。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-04-10-knowledge-graph-data-research-状态管理-mysql-3.md
> 类别：数据存储

> 检索摘要：重跑最小单位=章节（业务认知），内部按 token 限制拆子批次（技术限制），支持跳过已完成/已跳过章节断点续传。

设计原则：重跑最小单位 = 章节（业务认知），内部可拆分子批次（技术限制）。
def process_by_chapter(subject: str, version: str, state_db):
    """
    按章节处理，支持断点续传
    """
    chapters = get_chapters(subject)

    for chapter in chapters:
        chapter_id = f"{subject}_{chapter['id']}"

        # 1. 检查章节状态
        chapter_status = state_db.get_chapter_status(chapter_id)
        if chapter_status == 'completed':
            logging.info(f"跳过已完成章节: {chapter['name']}")
            continue
        if chapter_status == 'skipped':
            logging.info(f"跳过已标记跳过: {chapter['name']}")
            continue

        # 2. 标记章节处理中
        state_db.mark_chapter_processing(chapter_id)

        # 3. 获取该章节知识点
        kps = get_knowledge_points_in_chapter(chapter)

        # 4. 按 token 限制拆分子批次
        sub_batches = split_by_token_limit(kps, max_tokens=4000)

        chapter_failed = False
        for i, sub_batch in enumerate(sub_batches):
            batch_id = f"{chapter_id}_batch{i+1}"

            # 检查子批次状态
            if state_db.is_subbatch_completed(batch_id):
                continue

            # 处理子批次
            try:
                result = process_subbatch(sub_batch, batch_id, state_db)
                state_db.mark_subbatch_completed(batch_id, result['cache_key'], result['file'])
            except Exception as e:
                state_db.mark_subbatch_failed(batch_id, str(e))
                chapter_failed = True
                break

        # 5. 更新章节状态
        if chapter_failed:
            state_db.mark_chapter_failed(chapter_id)
        else:
            state_db.mark_chapter_completed(chapter_id)

    return state_db.get_progress(subject, version)

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-10-knowledge-graph-data-research.md`（§13.2 状态管理（MySQL））
