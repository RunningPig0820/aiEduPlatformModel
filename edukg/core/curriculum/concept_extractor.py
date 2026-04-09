"""
Concept 提取服务

从知识点列表生成 Concept 实体，添加 HAS_TYPE 关系，生成符合 Neo4j 导入格式的 concepts.json
支持断点续传和进度追踪

状态文件: state/step_4_concept_gen.json
"""
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Dict, Any, Union

from .kg_builder import URIGenerator, KGConfig
from .config import settings
from edukg.core.llmTaskLock import TaskState


# 步骤4的状态文件名
STEP_4_STATE_ID = "step_4_concept_gen"


@dataclass
class ConceptExtractionResult:
    """Concept 提取结果"""
    knowledge_point: str
    concept_uri: str
    class_id: str


class ConceptExtractor:
    """
    Concept 提取器

    从知识点列表生成 Concept 实体，包括：
    1. 生成 Concept URI
    2. 添加 HAS_TYPE 关系（关联到 Class）
    3. 生成 concepts.json

    状态文件: state/step_4_concept_gen.json
    """

    def __init__(
        self,
        config: Optional[KGConfig] = None,
        state_dir: Union[str, Path] = None,
    ):
        """
        初始化 Concept 提取器

        Args:
            config: 知识图谱配置
            state_dir: 状态文件目录
        """
        self.config = config or KGConfig()
        self.uri_generator = URIGenerator(
            version=self.config.version,
            subject=self.config.subject,
        )
        self.state_dir = state_dir or settings.STATE_DIR

    def get_state(self) -> TaskState:
        """获取步骤4的状态管理器"""
        return TaskState(STEP_4_STATE_ID, state_dir=self.state_dir)

    def get_progress(self) -> Dict[str, int]:
        """
        获取进度信息

        Returns:
            包含 total, completed, failed, pending 的字典
        """
        state = self.get_state()
        return state.get_progress()

    def get_status_summary(self) -> Dict[str, Any]:
        """
        获取状态摘要

        Returns:
            包含状态信息的字典
        """
        state = self.get_state()
        progress = state.get_progress()

        return {
            "task_id": STEP_4_STATE_ID,
            "status": state.get_status(),
            "progress": progress,
            "is_completed": state.is_completed(),
            "state_file": str(state.state_file),
        }

    def generate_concept(
        self,
        label: str,
        class_id: str,
        context: Optional[str] = None,
    ) -> dict:
        """
        生成单个 Concept 实体

        Args:
            label: 知识点名称
            class_id: 关联的 Class ID（不含 URI 前缀）
            context: 可选的上下文信息

        Returns:
            Concept 定义字典
        """
        uri = self.uri_generator.generate_instance_uri(label)

        return {
            "uri": uri,
            "label": label,
            "types": [class_id],
        }

    def batch_generate_concepts(
        self,
        knowledge_points: list[tuple[str, str]],
        batch_size: int = 50,
        verbose: bool = False,
        resume: bool = False,
    ) -> list[dict]:
        """
        批量生成 Concept 实体（支持断点续传）

        Args:
            knowledge_points: 知识点列表，每个元素是 (label, class_id) 元组
            batch_size: 批次大小（每批作为一个 checkpoint）
            verbose: 是否显示进度
            resume: 是否从断点恢复

        Returns:
            Concept 定义列表
        """
        # 获取状态
        state = self.get_state()

        # 计算批次数
        total_batches = (len(knowledge_points) + batch_size - 1) // batch_size

        if not resume or state.get_status() == TaskState.STATUS_PENDING:
            state.start(total=total_batches)

        # 获取待处理的检查点
        if resume:
            pending_checkpoints = state.resume()
            if verbose and pending_checkpoints:
                progress = state.get_progress()
                print(f"从断点恢复: 已完成 {progress['completed']}/{progress['total']} 批，待处理 {len(pending_checkpoints)} 批")
        else:
            pending_checkpoints = [f"checkpoint_{i+1}" for i in range(total_batches)]

        concepts = []

        for batch_idx in range(total_batches):
            batch_id = f"checkpoint_{batch_idx + 1}"

            # 跳过已完成的检查点
            if batch_id not in pending_checkpoints:
                continue

            # 获取当前批次的知识点
            start_idx = batch_idx * batch_size
            end_idx = min(start_idx + batch_size, len(knowledge_points))
            batch_kps = knowledge_points[start_idx:end_idx]

            if verbose:
                progress = state.get_progress()
                print(f"处理批次 {batch_idx + 1}/{total_batches} (知识点 {start_idx + 1}-{end_idx})... (已完成: {progress['completed']}, 待处理: {progress['pending']})")

            # 处理当前批次
            batch_concepts = []
            for label, class_id in batch_kps:
                concept = self.generate_concept(label, class_id)
                batch_concepts.append(concept)

            concepts.extend(batch_concepts)

            # 标记检查点完成
            state.complete_checkpoint(batch_id, {
                "batch_idx": batch_idx,
                "kp_range": [start_idx, end_idx],
            })

        if verbose:
            progress = state.get_progress()
            print(f"生成完成: {len(concepts)} 个 Concept")
            if state.is_completed():
                print("所有批次已完成！")

        return concepts

    def extract_concepts_from_kps(
        self,
        kps_with_types: list[dict],
        verbose: bool = False,
        resume: bool = False,
        batch_size: int = 50,
    ) -> list[dict]:
        """
        从知识点列表（带类型推断结果）提取 Concept（支持断点续传）

        Args:
            kps_with_types: 知识点列表，每个元素包含 knowledge_point, class_label, class_id
            verbose: 是否显示进度
            resume: 是否从断点恢复
            batch_size: 批次大小

        Returns:
            Concept 定义列表
        """
        # 转换为 (label, class_id) 元组列表
        kp_tuples = [
            (kp["knowledge_point"], kp["class_id"])
            for kp in kps_with_types
        ]

        return self.batch_generate_concepts(
            kp_tuples,
            verbose=verbose,
            resume=resume,
            batch_size=batch_size,
        )

    def save_concepts(
        self,
        concepts: list[dict],
        output_path: str,
    ) -> None:
        """
        保存 concepts.json

        Args:
            concepts: Concept 列表
            output_path: 输出文件路径
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(concepts, f, ensure_ascii=False, indent=2)

        print(f"Concepts 已保存到: {output_path} ({len(concepts)} 个)")


# 命令行入口
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Concept 提取 - 步骤4")
    parser.add_argument("--kps", help="知识点 JSON 文件（带类型，--status 时可选）")
    parser.add_argument("--output", default="concepts.json", help="输出文件")
    parser.add_argument("--debug", action="store_true", help="调试模式")
    parser.add_argument("--resume", action="store_true", help="从断点恢复")
    parser.add_argument("--status", action="store_true", help="仅查看状态，不执行")
    parser.add_argument("--state-dir", default=None, help="状态文件目录")
    parser.add_argument("--batch-size", type=int, default=50, help="批次大小")

    args = parser.parse_args()

    # 创建提取器
    extractor = ConceptExtractor(state_dir=args.state_dir or settings.STATE_DIR)

    # 仅查看状态
    if args.status:
        summary = extractor.get_status_summary()
        print(f"\n=== 步骤4: Concept 生成状态 ===")
        print(f"状态文件: {summary['state_file']}")
        print(f"任务状态: {summary['status']}")
        print(f"进度: {summary['progress']['completed']}/{summary['progress']['total']} 批次完成")
        print(f"  - 已完成: {summary['progress']['completed']}")
        print(f"  - 失败: {summary['progress']['failed']}")
        print(f"  - 待处理: {summary['progress']['pending']}")
        print(f"已完成: {summary['is_completed']}")
        exit(0)

    # 执行提取时需要 --kps
    if not args.kps:
        parser.error("--kps is required when not using --status")

    # 检查文件存在
    if not Path(args.kps).exists():
        print(f"错误: 知识点文件不存在: {args.kps}")
        exit(1)

    # 加载知识点
    with open(args.kps, encoding="utf-8") as f:
        kps_with_types = json.load(f)

    # 从断点恢复时显示进度
    if args.resume:
        progress = extractor.get_progress()
        if progress['total'] > 0:
            print(f"从断点恢复: 已完成 {progress['completed']}/{progress['total']} 批")
        else:
            print("没有可恢复的状态，开始新任务")

    # 提取
    concepts = extractor.extract_concepts_from_kps(
        kps_with_types,
        verbose=True,
        resume=args.resume,
        batch_size=args.batch_size,
    )
    extractor.save_concepts(concepts, args.output)