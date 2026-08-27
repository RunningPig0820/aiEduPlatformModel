# 13.2.3 进度可视化
> summary: 进度可视化按学科/版本展示完成百分比、处理中/失败章节数，并提供命令行入口 show-progress/retry-failed/skip-chapter。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-04-10-knowledge-graph-data-research-状态管理-mysql-4.md
> 类别：数据存储

> 检索摘要：进度可视化按学科/版本展示完成百分比、处理中/失败章节数，并提供命令行入口 show-progress/retry-failed/skip-chapter。

def show_progress(subject: str, version: str, state_db: StateDB):
    """
    显示处理进度
    """
    progress = state_db.get_progress(subject, version)

    if not progress:
        print("暂无进度数据")
        return

    print(f"\n{'='*50}")
    print(f"学科: {progress['subject']} | 版本: {progress['version']}")
    print(f"进度: {progress['progress_percent']}% ({progress['completed_chapters']}/{progress['total_chapters']} 章节)")
    print(f"处理中: {progress['processing_chapters']} | 失败: {progress['failed_chapters']}")
    print(f"{'='*50}\n")

    # 显示失败章节
    failed = state_db.get_failed_chapters(subject, version)

    if failed:
        print("失败章节:")
        for f in failed:
            print(f"  - {f['chapter_name']}: {f['error_message']}")

# 命令行入口
def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--show-progress', action='store_true')
    parser.add_argument('--retry-failed', action='store_true')
    parser.add_argument('--skip-chapter', type=str, help='跳过指定章节')
    args = parser.parse_args()

    if args.show_progress:
        show_progress(subject, version, state_db)
    elif args.retry_failed:
        retry_failed_chapters(subject, version, state_db)
    elif args.skip_chapter:
        state_db.skip_chapter(args.skip_chapter)

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-10-knowledge-graph-data-research.md`（§13.2 状态管理（MySQL））
