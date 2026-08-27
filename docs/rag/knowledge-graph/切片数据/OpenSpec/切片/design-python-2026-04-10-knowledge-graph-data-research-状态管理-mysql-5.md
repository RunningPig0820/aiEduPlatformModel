# 13.2.4 手动跳过章节
> summary: 手动跳过章节调用 skip_chapter 标记 skipped 状态，后续重跑自动跳过不处理。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-04-10-knowledge-graph-data-research-状态管理-mysql-5.md
> 类别：数据存储

> 检索摘要：手动跳过章节调用 skip_chapter 标记 skipped 状态，后续重跑自动跳过不处理。

def skip_chapter(state_db: StateDB, chapter_id: str, reason: str = ""):
    """
    手动跳过某章节（不处理）
    """
    state_db.skip_chapter(chapter_id, reason)
    logging.info(f"已跳过章节: {chapter_id}")

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-10-knowledge-graph-data-research.md`（§13.2 状态管理（MySQL））
