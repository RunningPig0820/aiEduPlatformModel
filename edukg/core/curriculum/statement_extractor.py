"""
Statement 提取服务

使用 LLM 生成知识点的定义描述，生成符合 Neo4j 导入格式的 statements.json
支持 LLM 缓存，避免重复调用
支持断点续传和进度追踪

状态文件: state/step_5_statement_gen.json
"""
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Dict, Any

from langchain_community.chat_models import ChatZhipuAI
from langchain_core.messages import HumanMessage, SystemMessage

from .config import settings
from .kg_builder import URIGenerator, KGConfig
from edukg.core.llmTaskLock import CachedLLM, TaskState


# 步骤5的状态文件名
STEP_5_STATE_ID = "step_5_statement_gen"


@dataclass
class StatementExtractionResult:
    """Statement 提取结果"""
    concept_label: str
    statement_uri: str
    definition: str


# LLM Prompt
DEFINITION_PROMPT = """你是一个数学教育专家，请为以下知识点生成准确的定义。

知识点: {knowledge_point}

请生成一个简洁、准确的定义，适合中学生理解。

输出格式（JSON）：
{{
  "definition": "定义内容",
  "confidence": 0.0-1.0
}}

注意：
1. 定义应该简洁明了，一般不超过100字
2. 如果是方法类知识点，说明其作用和步骤
3. 如果是概念类知识点，说明其本质特征
4. 只输出 JSON，不要输出其他内容
"""


class StatementExtractor:
    """
    Statement 提取器

    使用 LLM 生成知识点定义，包括：
    1. 调用 LLM 生成定义
    2. 生成 Statement URI
    3. 建立 Statement → Concept 的关联
    4. 生成 statements.json

    状态文件: state/step_5_statement_gen.json
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        config: Optional[KGConfig] = None,
        cache_dir: str = "cache/",
        use_cache: bool = True,
        state_dir: str = "state/",
    ):
        """
        初始化 Statement 提取器

        Args:
            api_key: 智谱 API Key，默认从环境变量读取
            config: 知识图谱配置
            cache_dir: 缓存目录
            use_cache: 是否使用 LLM 缓存
            state_dir: 状态文件目录
        """
        self.api_key = api_key or settings.ZHIPU_API_KEY
        self.config = config or KGConfig()
        self.uri_generator = URIGenerator(
            version=self.config.version,
            subject=self.config.subject,
        )
        self.cache_dir = cache_dir
        self.use_cache = use_cache
        self.state_dir = state_dir

        # 初始化 LLM
        if self.api_key:
            llm = ChatZhipuAI(
                model="glm-4-flash",
                api_key=self.api_key,
                temperature=0.3,  # 稍高温度，生成更自然的定义
            )
            # 使用 CachedLLM 包装
            self.llm = CachedLLM(llm, cache_dir=cache_dir) if use_cache else llm
        else:
            self.llm = None

    def get_state(self) -> TaskState:
        """获取步骤5的状态管理器"""
        return TaskState(STEP_5_STATE_ID, state_dir=self.state_dir)

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
            "task_id": STEP_5_STATE_ID,
            "status": state.get_status(),
            "progress": progress,
            "is_completed": state.is_completed(),
            "state_file": str(state.state_file),
        }

    def _call_llm(self, prompt: str) -> dict:
        """
        调用 LLM 并解析响应

        Args:
            prompt: 提示词

        Returns:
            解析后的 JSON 字典
        """
        if not self.llm:
            return {
                "definition": "",
                "confidence": 0.0,
            }

        try:
            # 使用 CachedLLM 或原始 LLM
            if isinstance(self.llm, CachedLLM):
                response = self.llm.invoke(prompt, use_cache=self.use_cache)
            else:
                response = self.llm.invoke([
                    SystemMessage(content="你是一个数学教育专家。"),
                    HumanMessage(content=prompt),
                ])

            # 解析响应
            if hasattr(response, 'content'):
                content = response.content
            else:
                content = str(response)

            # 解析 JSON
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # 尝试从 markdown 代码块提取
                json_pattern = r'```json\s*([\s\S]*?)\s*```'
                matches = re.findall(json_pattern, content)
                if matches:
                    try:
                        return json.loads(matches[0])
                    except json.JSONDecodeError:
                        pass

                # 尝试找到 JSON 对象
                json_pattern = r'\{[\s\S]*\}'
                matches = re.findall(json_pattern, content)
                for match in matches:
                    try:
                        return json.loads(match)
                    except json.JSONDecodeError:
                        continue

            return {
                "definition": content[:200],  # 使用原始响应作为定义
                "confidence": 0.5,
            }

        except Exception as e:
            return {
                "definition": "",
                "confidence": 0.0,
                "error": str(e),
            }

    def generate_definition(
        self,
        knowledge_point: str,
        context: Optional[str] = None,
    ) -> dict:
        """
        生成知识点定义

        Args:
            knowledge_point: 知识点名称
            context: 可选的上下文信息

        Returns:
            包含 definition 和 confidence 的字典
        """
        prompt = DEFINITION_PROMPT.format(knowledge_point=knowledge_point)

        if context:
            prompt += f"\n\n上下文信息：{context}"

        # 如果使用 CachedLLM，需要把系统提示也加入 prompt
        if isinstance(self.llm, CachedLLM):
            full_prompt = f"你是一个数学教育专家。\n\n{prompt}"
        else:
            full_prompt = prompt

        result = self._call_llm(full_prompt)

        # 如果生成失败，使用默认定义
        if not result.get("definition"):
            result["definition"] = f"{knowledge_point}是数学中的一个重要知识点。"
            result["confidence"] = 0.3

        return result

    def generate_statement(
        self,
        concept_label: str,
        concept_uri: str,
        definition: str,
    ) -> dict:
        """
        生成 Statement 实体

        Args:
            concept_label: 关联的 Concept 标签
            concept_uri: 关联的 Concept URI
            definition: 定义内容

        Returns:
            Statement 定义字典
        """
        # Statement 标签: "{概念}的定义"
        statement_label = f"{concept_label}的定义"

        uri = self.uri_generator.generate_statement_uri(statement_label)

        return {
            "uri": uri,
            "label": statement_label,
            "types": ["shuxuedingyi-b14b4ceb4747e9d5cc2534e9dc38faf1"],  # 数学定义的 ID
            "content": definition,
        }

    def batch_generate_statements(
        self,
        concepts: list[dict],
        batch_size: int = 10,
        verbose: bool = False,
        resume: bool = False,
    ) -> list[dict]:
        """
        批量生成 Statement（支持断点续传）

        Args:
            concepts: Concept 列表，每个元素包含 label, uri
            batch_size: 批次大小（每批作为一个 checkpoint）
            verbose: 是否显示进度
            resume: 是否从断点恢复

        Returns:
            Statement 定义列表
        """
        # 获取状态
        state = self.get_state()

        # 计算批次数
        total_batches = (len(concepts) + batch_size - 1) // batch_size

        if not resume or state.get_status() == TaskState.STATUS_PENDING:
            state.start(total=total_batches)

        # 获取待处理的检查点
        if resume:
            pending_checkpoints = state.resume()
            if verbose and pending_checkpoints:
                progress = state.get_progress()
                print(f"从断点恢复: 已完成 {progress['completed']}/{progress['total']} 批，待处理 {len(pending_checkpoints)} 批")
        else:
            pending_checkpoints = [f"batch_{i+1}" for i in range(total_batches)]

        statements = []

        for batch_idx in range(total_batches):
            batch_id = f"batch_{batch_idx + 1}"

            # 跳过已完成的检查点
            if batch_id not in pending_checkpoints:
                continue

            # 获取当前批次的 concepts
            start_idx = batch_idx * batch_size
            end_idx = min(start_idx + batch_size, len(concepts))
            batch_concepts = concepts[start_idx:end_idx]

            if verbose:
                progress = state.get_progress()
                print(f"处理批次 {batch_idx + 1}/{total_batches} (Concept {start_idx + 1}-{end_idx})... (已完成: {progress['completed']}, 待处理: {progress['pending']})")

            # 处理当前批次
            batch_statements = []
            batch_errors = []

            for concept in batch_concepts:
                try:
                    # 生成定义
                    def_result = self.generate_definition(concept["label"])

                    # 生成 Statement
                    statement = self.generate_statement(
                        concept_label=concept["label"],
                        concept_uri=concept["uri"],
                        definition=def_result["definition"],
                    )
                    batch_statements.append(statement)
                except Exception as e:
                    batch_errors.append(str(e))
                    # 失败时使用默认定义
                    statement = self.generate_statement(
                        concept_label=concept["label"],
                        concept_uri=concept["uri"],
                        definition=f"{concept['label']}是数学中的一个重要知识点。",
                    )
                    batch_statements.append(statement)

            statements.extend(batch_statements)

            # 标记检查点完成
            if batch_errors:
                state.complete_checkpoint(batch_id, {
                    "batch_idx": batch_idx,
                    "concept_range": [start_idx, end_idx],
                    "errors": batch_errors,
                })
            else:
                state.complete_checkpoint(batch_id, {
                    "batch_idx": batch_idx,
                    "concept_range": [start_idx, end_idx],
                })

        if verbose:
            progress = state.get_progress()
            print(f"生成完成: {len(statements)} 个 Statement")
            if state.is_completed():
                print("所有批次已完成！")

        return statements

    def extract_statements_from_concepts(
        self,
        concepts: list[dict],
        verbose: bool = False,
        resume: bool = False,
        batch_size: int = 10,
    ) -> list[dict]:
        """
        从 Concept 列表提取 Statement（支持断点续传）

        Args:
            concepts: Concept 列表
            verbose: 是否显示进度
            resume: 是否从断点恢复
            batch_size: 批次大小

        Returns:
            Statement 定义列表
        """
        return self.batch_generate_statements(
            concepts,
            verbose=verbose,
            resume=resume,
            batch_size=batch_size,
        )

    def save_statements(
        self,
        statements: list[dict],
        output_path: str,
    ) -> None:
        """
        保存 statements.json

        Args:
            statements: Statement 列表
            output_path: 输出文件路径
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(statements, f, ensure_ascii=False, indent=2)

        print(f"Statements 已保存到: {output_path} ({len(statements)} 个)")


# 命令行入口
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Statement 提取 - 步骤5")
    parser.add_argument("--concepts", help="Concepts JSON 文件（--status 时可选）")
    parser.add_argument("--output", default="statements.json", help="输出文件")
    parser.add_argument("--debug", action="store_true", help="调试模式")
    parser.add_argument("--resume", action="store_true", help="从断点恢复")
    parser.add_argument("--status", action="store_true", help="仅查看状态，不执行")
    parser.add_argument("--state-dir", default="state/", help="状态文件目录")
    parser.add_argument("--cache-dir", default="cache/", help="缓存目录")
    parser.add_argument("--batch-size", type=int, default=10, help="批次大小")

    args = parser.parse_args()

    # 创建提取器
    extractor = StatementExtractor(
        state_dir=args.state_dir,
        cache_dir=args.cache_dir,
    )

    # 仅查看状态
    if args.status:
        summary = extractor.get_status_summary()
        print(f"\n=== 步骤5: Statement 生成状态 ===")
        print(f"状态文件: {summary['state_file']}")
        print(f"任务状态: {summary['status']}")
        print(f"进度: {summary['progress']['completed']}/{summary['progress']['total']} 批次完成")
        print(f"  - 已完成: {summary['progress']['completed']}")
        print(f"  - 失败: {summary['progress']['failed']}")
        print(f"  - 待处理: {summary['progress']['pending']}")
        print(f"已完成: {summary['is_completed']}")
        exit(0)

    # 执行提取时需要 --concepts
    if not args.concepts:
        parser.error("--concepts is required when not using --status")

    # 检查文件存在
    if not Path(args.concepts).exists():
        print(f"错误: Concepts 文件不存在: {args.concepts}")
        exit(1)

    # 加载 concepts
    with open(args.concepts, encoding="utf-8") as f:
        concepts = json.load(f)

    # 从断点恢复时显示进度
    if args.resume:
        progress = extractor.get_progress()
        if progress['total'] > 0:
            print(f"从断点恢复: 已完成 {progress['completed']}/{progress['total']} 批")
        else:
            print("没有可恢复的状态，开始新任务")

    # 提取
    statements = extractor.extract_statements_from_concepts(
        concepts,
        verbose=True,
        resume=args.resume,
        batch_size=args.batch_size,
    )
    extractor.save_statements(statements, args.output)