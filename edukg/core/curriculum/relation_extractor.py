"""
关系提取服务

使用 LLM 分析知识点之间的关系，生成符合 Neo4j 导入格式的 relations.json
支持 LLM 缓存，避免重复调用
支持断点续传和进度追踪

关系类型:
- RELATED_TO: Statement → Concept（定义关联）
- PART_OF: Concept → Concept（部分-整体）
- BELONGS_TO: Concept → Concept（所属关系）
- HAS_TYPE: Concept/Statement → Class（类型分类）
- SUB_CLASS_OF: Class → Class（概念层级）

状态文件: state/step_6_relation_extract.json
"""
import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Dict, Any, Union

from langchain_community.chat_models import ChatZhipuAI
from langchain_core.messages import HumanMessage, SystemMessage

from .config import settings
from .kg_builder import URIGenerator, KGConfig
from edukg.core.llmTaskLock import CachedLLM, TaskState


# 步骤6的状态文件名
STEP_6_STATE_ID = "step_6_relation_extract"

# 数学定义的 Class URI
MATH_DEFINITION_CLASS_URI = "http://edukg.org/knowledge/0.1/class/math#shuxuedingyi-b14b4ceb4747e9d5cc2534e9dc38faf1"
MATH_DEFINITION_CLASS_LABEL = "数学定义"


@dataclass
class RelationExtractionResult:
    """关系提取结果"""
    from_label: str
    from_uri: str
    relation: str
    to_label: str
    to_uri: str
    confidence: float = 1.0


# LLM Prompt
RELATION_PROMPT = """你是一个数学教育专家，请分析以下知识点之间的关系。

知识点列表:
{knowledge_points}

请分析这些知识点之间是否存在以下关系：

## partOf 关系（部分-整体关系）

**定义**: A -> partOf -> B 表示 "A是B的一部分" 或 "A是B的一种"

**正确示例**:
- 圆 -> partOf -> 图形 （圆是图形的一种）
- 三角形 -> partOf -> 多边形 （三角形是多边形的一种）
- 加法 -> partOf -> 运算 （加法是运算的一种）
- 线段 -> partOf -> 线 （线段是线的一种）

**错误示例（不要这样输出）**:
- ❌ 图形 -> partOf -> 圆 （图形不是圆的一部分！）
- ❌ 多边形 -> partOf -> 三角形 （多边形不是三角形的一部分！）

## belongsTo 关系（所属关系）

**定义**: A -> belongsTo -> B 表示 "A属于B类别" 或 "A归类于B"

**正确示例**:
- 凑十法 -> belongsTo -> 加法运算
- 抽样 -> belongsTo -> 统计方法

---

输出格式（JSON）：
{{
  "relations": [
    {{
      "from": "源知识点（较小的/具体的概念）",
      "relation": "partOf 或 belongsTo",
      "to": "目标知识点（较大的/抽象的概念）",
      "confidence": 0.0-1.0
    }}
  ]
}}

**重要规则**:
1. partOf 的方向: from是较小的概念，to是较大的概念（如：圆 -> partOf -> 图形）
2. 不要搞反方向！图形包含圆，不是图形属于圆
3. 只输出确定存在的关系
4. 不要输出反向关系（如同时输出 A→B 和 B→A）
5. 如果没有关系，返回空列表
"""


class RelationExtractor:
    """
    关系提取器

    使用 LLM 分析知识点关系，包括：
    1. Statement → Concept (RELATED_TO)
    2. Concept → Concept (PART_OF, BELONGS_TO)
    3. Concept → Class (HAS_TYPE)
    4. Statement → Class (HAS_TYPE)
    5. Class → Class (SUB_CLASS_OF)
    6. 生成 relations.json

    状态文件: state/step_6_relation_extract.json
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        config: Optional[KGConfig] = None,
        cache_dir: Union[str, Path] = None,
        use_cache: bool = True,
        state_dir: Union[str, Path] = None,
    ):
        """
        初始化关系提取器

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
        self.cache_dir = cache_dir or settings.CACHE_DIR
        self.use_cache = use_cache
        self.state_dir = state_dir or settings.STATE_DIR

        # 初始化 LLM
        if self.api_key:
            llm = ChatZhipuAI(
                model="glm-4-flash",
                api_key=self.api_key,
                temperature=0.1,
            )
            # 使用 CachedLLM 包装
            self.llm = CachedLLM(llm, cache_dir=cache_dir) if use_cache else llm
        else:
            self.llm = None

    def get_state(self) -> TaskState:
        """获取步骤6的状态管理器"""
        return TaskState(STEP_6_STATE_ID, state_dir=self.state_dir)

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
            "task_id": STEP_6_STATE_ID,
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
            return {"relations": []}

        try:
            # 使用 CachedLLM 或原始 LLM
            if isinstance(self.llm, CachedLLM):
                response = self.llm.invoke(prompt, use_cache=self.use_cache)
            else:
                response = self.llm.invoke([
                    SystemMessage(content="你是一个数学教育专家。"),
                    HumanMessage(content=prompt),
                ])

            content = response.content if hasattr(response, 'content') else str(response)

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

            return {"relations": []}

        except Exception as e:
            return {"relations": [], "error": str(e)}

    def generate_related_to_relation(
        self,
        statement_uri: str,
        statement_label: str,
        concept_uri: str,
        concept_label: str,
    ) -> dict:
        """
        生成 RELATED_TO 关系

        Args:
            statement_uri: Statement URI
            statement_label: Statement 标签
            concept_uri: Concept URI
            concept_label: Concept 标签

        Returns:
            关系定义字典
        """
        return {
            "from": {
                "uri": statement_uri,
                "label": statement_label,
            },
            "relation": "relatedTo",
            "to": {
                "uri": concept_uri,
                "label": concept_label,
            },
        }

    def generate_part_of_relation(
        self,
        part_uri: str,
        part_label: str,
        whole_uri: str,
        whole_label: str,
    ) -> dict:
        """
        生成 PART_OF 关系

        Args:
            part_uri: 部分 URI
            part_label: 部分标签
            whole_uri: 整体 URI
            whole_label: 整体标签

        Returns:
            关系定义字典
        """
        return {
            "from": {
                "uri": part_uri,
                "label": part_label,
            },
            "relation": "partOf",
            "to": {
                "uri": whole_uri,
                "label": whole_label,
            },
        }

    def generate_belongs_to_relation(
        self,
        child_uri: str,
        child_label: str,
        parent_uri: str,
        parent_label: str,
    ) -> dict:
        """
        生成 BELONGS_TO 关系

        Args:
            child_uri: 子类 URI
            child_label: 子类标签
            parent_uri: 父类 URI
            parent_label: 父类标签

        Returns:
            关系定义字典
        """
        return {
            "from": {
                "uri": child_uri,
                "label": child_label,
            },
            "relation": "belongsTo",
            "to": {
                "uri": parent_uri,
                "label": parent_label,
            },
        }

    def generate_has_type_relation(
        self,
        entity_uri: str,
        entity_label: str,
        class_uri: str,
        class_label: str,
    ) -> dict:
        """
        生成 HAS_TYPE 关系

        Args:
            entity_uri: 实体 URI (Concept 或 Statement)
            entity_label: 实体标签
            class_uri: Class URI
            class_label: Class 标签

        Returns:
            关系定义字典
        """
        return {
            "from": {
                "uri": entity_uri,
                "label": entity_label,
            },
            "relation": "HAS_TYPE",
            "to": {
                "uri": class_uri,
                "label": class_label,
            },
        }

    def generate_sub_class_of_relation(
        self,
        child_class_uri: str,
        child_class_label: str,
        parent_class_uri: str,
        parent_class_label: str,
    ) -> dict:
        """
        生成 SUB_CLASS_OF 关系

        Args:
            child_class_uri: 子类 URI
            child_class_label: 子类标签
            parent_class_uri: 父类 URI
            parent_class_label: 父类标签

        Returns:
            关系定义字典
        """
        return {
            "from": {
                "uri": child_class_uri,
                "label": child_class_label,
            },
            "relation": "SUB_CLASS_OF",
            "to": {
                "uri": parent_class_uri,
                "label": parent_class_label,
            },
        }

    def generate_statement_concept_relations(
        self,
        statements: list[dict],
        concepts: list[dict],
    ) -> list[dict]:
        """
        生成 Statement → Concept 的 RELATED_TO 关系

        Args:
            statements: Statement 列表
            concepts: Concept 列表

        Returns:
            关系列表
        """
        relations = []

        # 建立 label → uri 映射
        concept_map = {c["label"]: c["uri"] for c in concepts}

        for statement in statements:
            # Statement 标签格式: "{概念}的定义"
            label = statement["label"]
            if label.endswith("的定义"):
                concept_label = label[:-3]  # 去掉"的定义"

                if concept_label in concept_map:
                    relation = self.generate_related_to_relation(
                        statement_uri=statement["uri"],
                        statement_label=statement["label"],
                        concept_uri=concept_map[concept_label],
                        concept_label=concept_label,
                    )
                    relations.append(relation)

        return relations

    def generate_has_type_relations(
        self,
        concepts: list[dict],
        statements: list[dict],
        verbose: bool = False,
    ) -> list[dict]:
        """
        生成 HAS_TYPE 关系

        Args:
            concepts: Concept 列表
            statements: Statement 列表
            verbose: 是否显示进度

        Returns:
            HAS_TYPE 关系列表
        """
        relations = []

        # 1. Concept → Class (HAS_TYPE)
        # 只为新增概念生成，已存在的概念在 Neo4j 中已有 HAS_TYPE
        concept_count = 0
        for concept in concepts:
            inferred_class = concept.get("inferred_class")
            inferred_class_uri = concept.get("inferred_class_uri")

            if inferred_class and inferred_class_uri:
                relation = self.generate_has_type_relation(
                    entity_uri=concept["uri"],
                    entity_label=concept["label"],
                    class_uri=inferred_class_uri,
                    class_label=inferred_class,
                )
                relations.append(relation)
                concept_count += 1

        if verbose:
            print(f"  Concept → Class (HAS_TYPE): {concept_count} 个")

        # 2. Statement → Class (HAS_TYPE)
        # 所有 Statement 的类型都是"数学定义"
        for statement in statements:
            relation = self.generate_has_type_relation(
                entity_uri=statement["uri"],
                entity_label=statement["label"],
                class_uri=MATH_DEFINITION_CLASS_URI,
                class_label=MATH_DEFINITION_CLASS_LABEL,
            )
            relations.append(relation)

        if verbose:
            print(f"  Statement → Class (HAS_TYPE): {len(statements)} 个")

        return relations

    def generate_sub_class_of_relations(
        self,
        classes: list[dict],
        verbose: bool = False,
    ) -> list[dict]:
        """
        生成 SUB_CLASS_OF 关系

        Args:
            classes: Class 列表
            verbose: 是否显示进度

        Returns:
            SUB_CLASS_OF 关系列表
        """
        relations = []

        for cls in classes:
            parents = cls.get("parents", [])
            for parent_uri in parents:
                relation = self.generate_sub_class_of_relation(
                    child_class_uri=cls["uri"],
                    child_class_label=cls["label"],
                    parent_class_uri=parent_uri,
                    parent_class_label=cls.get("parent_label", "数学"),
                )
                relations.append(relation)

        if verbose:
            print(f"  Class → Class (SUB_CLASS_OF): {len(relations)} 个")

        return relations

    def add_subject_attribute(
        self,
        concepts: list[dict],
        statements: list[dict],
        subject: str = "math",
    ) -> None:
        """
        为 Concept 和 Statement 添加 subject 属性

        Args:
            concepts: Concept 列表
            statements: Statement 列表
            subject: 学科名称
        """
        for concept in concepts:
            concept["subject"] = subject

        for statement in statements:
            statement["subject"] = subject

    def extract_concept_relations(
        self,
        concepts: list[dict],
        batch_size: int = 20,
        verbose: bool = False,
        resume: bool = False,
    ) -> list[dict]:
        """
        提取 Concept 之间的关系（支持断点续传）

        Args:
            concepts: Concept 列表
            batch_size: 批次大小（每批作为一个 checkpoint）
            verbose: 是否显示进度
            resume: 是否从断点恢复

        Returns:
            关系列表
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
            pending_checkpoints = [f"checkpoint_{i+1}" for i in range(total_batches)]

        all_relations = []

        for batch_idx in range(total_batches):
            batch_id = f"checkpoint_{batch_idx + 1}"

            # 跳过已完成的检查点
            if batch_id not in pending_checkpoints:
                continue

            # 获取当前批次的 concepts
            start_idx = batch_idx * batch_size
            end_idx = min(start_idx + batch_size, len(concepts))
            batch = concepts[start_idx:end_idx]

            if verbose:
                progress = state.get_progress()
                print(f"处理批次 {batch_idx + 1}/{total_batches} (Concept {start_idx + 1}-{end_idx})... (已完成: {progress['completed']}, 待处理: {progress['pending']})")

            # 构建 prompt
            kp_names = [c["label"] for c in batch]

            # 如果使用 CachedLLM，需要把系统提示也加入 prompt
            if isinstance(self.llm, CachedLLM):
                full_prompt = f"你是一个数学教育专家。\n\n{RELATION_PROMPT.format(knowledge_points='\n'.join(kp_names))}"
            else:
                full_prompt = RELATION_PROMPT.format(knowledge_points="\n".join(kp_names))

            result = self._call_llm(full_prompt)
            batch_errors = []

            # 解析结果
            for rel in result.get("relations", []):
                from_label = rel.get("from")
                to_label = rel.get("to")
                relation_type = rel.get("relation")

                # 查找对应的 URI
                from_uri = None
                to_uri = None

                for c in batch:
                    if c["label"] == from_label:
                        from_uri = c["uri"]
                    if c["label"] == to_label:
                        to_uri = c["uri"]

                if from_uri and to_uri:
                    if relation_type == "partOf":
                        all_relations.append(
                            self.generate_part_of_relation(
                                part_uri=from_uri,
                                part_label=from_label,
                                whole_uri=to_uri,
                                whole_label=to_label,
                            )
                        )
                    elif relation_type == "belongsTo":
                        all_relations.append(
                            self.generate_belongs_to_relation(
                                child_uri=from_uri,
                                child_label=from_label,
                                parent_uri=to_uri,
                                parent_label=to_label,
                            )
                        )

            # 检查是否有错误
            if result.get("error"):
                batch_errors.append(result["error"])

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
            print(f"关系提取完成: {len(all_relations)} 个关系")
            if state.is_completed():
                print("所有批次已完成！")

        return all_relations

    def extract_all_relations(
        self,
        statements: list[dict],
        concepts: list[dict],
        classes: list[dict] = None,
        verbose: bool = False,
        resume: bool = False,
        batch_size: int = 20,
    ) -> list[dict]:
        """
        提取所有关系（支持断点续传）

        生成的关系类型:
        1. relatedTo: Statement → Concept
        2. partOf: Concept → Concept
        3. belongsTo: Concept → Concept
        4. HAS_TYPE: Concept/Statement → Class
        5. SUB_CLASS_OF: Class → Class

        Args:
            statements: Statement 列表
            concepts: Concept 列表
            classes: Class 列表（可选，用于生成 HAS_TYPE 和 SUB_CLASS_OF）
            verbose: 是否显示进度
            resume: 是否从断点恢复
            batch_size: 批次大小

        Returns:
            所有关系列表
        """
        relations = []

        # 1. Statement → Concept (RELATED_TO) - 不需要 LLM
        if verbose:
            print("生成 Statement → Concept 关系 (relatedTo)...")

        stmt_relations = self.generate_statement_concept_relations(
            statements, concepts
        )
        relations.extend(stmt_relations)

        if verbose:
            print(f"  relatedTo: {len(stmt_relations)} 个")

        # 2. Concept → Concept (PART_OF, BELONGS_TO) - 需要 LLM 和断点续传
        if verbose:
            print("提取 Concept → Concept 关系 (partOf, belongsTo)...")

        concept_relations = self.extract_concept_relations(
            concepts,
            verbose=verbose,
            resume=resume,
            batch_size=batch_size,
        )
        relations.extend(concept_relations)

        # 3. Concept/Statement → Class (HAS_TYPE) - 不需要 LLM
        if verbose:
            print("生成 HAS_TYPE 关系...")

        has_type_relations = self.generate_has_type_relations(
            concepts, statements, verbose=verbose
        )
        relations.extend(has_type_relations)

        # 4. Class → Class (SUB_CLASS_OF) - 不需要 LLM
        if classes:
            if verbose:
                print("生成 SUB_CLASS_OF 关系...")

            sub_class_relations = self.generate_sub_class_of_relations(
                classes, verbose=verbose
            )
            relations.extend(sub_class_relations)

        if verbose:
            print(f"\n=== 关系生成完成 ===")
            from collections import Counter
            rel_types = Counter(r['relation'] for r in relations)
            for rel_type, count in sorted(rel_types.items()):
                print(f"  {rel_type}: {count}")
            print(f"  总计: {len(relations)} 个")

        return relations

    def save_relations(
        self,
        relations: list[dict],
        output_path: str,
    ) -> None:
        """
        保存 relations.json

        Args:
            relations: 关系列表
            output_path: 输出文件路径
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "metadata": {
                "total_relations": len(relations),
                "description": "数学知识点关联关系",
                "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            },
            "relations": relations,
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"Relations 已保存到: {output_path} ({len(relations)} 个)")


# 命令行入口
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="关系提取 - 步骤6")
    parser.add_argument("--statements", help="Statements JSON 文件（--status 时可选）")
    parser.add_argument("--concepts", help="Concepts JSON 文件（--status 时可选）")
    parser.add_argument("--classes", default=None, help="Classes JSON 文件（可选，用于生成 HAS_TYPE 和 SUB_CLASS_OF）")
    parser.add_argument("--output", default="relations.json", help="输出文件")
    parser.add_argument("--debug", action="store_true", help="调试模式")
    parser.add_argument("--resume", action="store_true", help="从断点恢复")
    parser.add_argument("--status", action="store_true", help="仅查看状态，不执行")
    parser.add_argument("--state-dir", default=None, help="状态文件目录")
    parser.add_argument("--cache-dir", default=None, help="缓存目录")
    parser.add_argument("--batch-size", type=int, default=20, help="批次大小")

    args = parser.parse_args()

    # 创建提取器
    extractor = RelationExtractor(
        state_dir=args.state_dir or settings.STATE_DIR,
        cache_dir=args.cache_dir or settings.CACHE_DIR,
    )

    # 仅查看状态
    if args.status:
        summary = extractor.get_status_summary()
        print(f"\n=== 步骤6: 关系提取状态 ===")
        print(f"状态文件: {summary['state_file']}")
        print(f"任务状态: {summary['status']}")
        print(f"进度: {summary['progress']['completed']}/{summary['progress']['total']} 批次完成")
        print(f"  - 已完成: {summary['progress']['completed']}")
        print(f"  - 失败: {summary['progress']['failed']}")
        print(f"  - 待处理: {summary['progress']['pending']}")
        print(f"已完成: {summary['is_completed']}")
        exit(0)

    # 执行提取时需要 --statements 和 --concepts
    if not args.statements or not args.concepts:
        parser.error("--statements and --concepts are required when not using --status")

    # 检查文件存在
    if not Path(args.statements).exists():
        print(f"错误: Statements 文件不存在: {args.statements}")
        exit(1)

    if not Path(args.concepts).exists():
        print(f"错误: Concepts 文件不存在: {args.concepts}")
        exit(1)

    # 加载数据
    with open(args.statements, encoding="utf-8") as f:
        statements = json.load(f)

    with open(args.concepts, encoding="utf-8") as f:
        concepts_data = json.load(f)

    # 处理不同的 JSON 结构
    if isinstance(concepts_data, dict) and "concepts" in concepts_data:
        concepts = concepts_data["concepts"]
    else:
        concepts = concepts_data

    # 加载 Classes（如果提供）
    classes = None
    if args.classes and Path(args.classes).exists():
        with open(args.classes, encoding="utf-8") as f:
            classes_data = json.load(f)
        if isinstance(classes_data, dict) and "classes" in classes_data:
            classes = classes_data["classes"]
        else:
            classes = classes_data

    # 从断点恢复时显示进度
    if args.resume:
        progress = extractor.get_progress()
        if progress['total'] > 0:
            print(f"从断点恢复: 已完成 {progress['completed']}/{progress['total']} 批")
        else:
            print("没有可恢复的状态，开始新任务")

    # 添加 subject 属性
    extractor.add_subject_attribute(concepts, statements, subject="math")
    print("已添加 subject 属性到 Concept 和 Statement")

    # 提取关系
    relations = extractor.extract_all_relations(
        statements,
        concepts,
        classes=classes,
        verbose=True,
        resume=args.resume,
        batch_size=args.batch_size,
    )
    extractor.save_relations(relations, args.output)

    # 保存更新后的 concepts 和 statements（包含 subject 属性）
    if isinstance(concepts_data, dict):
        concepts_data["metadata"]["subject_added"] = True
        with open(args.concepts, "w", encoding="utf-8") as f:
            json.dump(concepts_data, f, ensure_ascii=False, indent=2)
        print(f"已更新 {args.concepts}")

    with open(args.statements, "w", encoding="utf-8") as f:
        json.dump(statements, f, ensure_ascii=False, indent=2)
    print(f"已更新 {args.statements}")