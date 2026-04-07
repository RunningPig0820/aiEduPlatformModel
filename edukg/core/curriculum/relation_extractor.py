"""
关系提取服务

使用 LLM 分析知识点之间的关系，生成符合 Neo4j 导入格式的 relations.json

关系类型:
- RELATED_TO: Statement → Concept
- PART_OF: Concept → Concept（部分-整体）
- BELONGS_TO: Concept → Concept（所属关系）
"""
import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from langchain_community.chat_models import ChatZhipuAI
from langchain_core.messages import HumanMessage, SystemMessage

from .config import settings
from .kg_builder import URIGenerator, KGConfig


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
1. partOf: 部分与整体的关系（如：20以内加法 → 加法）
2. belongsTo: 所属关系（如：凑十法 → 进位加法）

输出格式（JSON）：
{{
  "relations": [
    {{
      "from": "源知识点",
      "relation": "partOf 或 belongsTo",
      "to": "目标知识点",
      "confidence": 0.0-1.0
    }}
  ]
}}

注意：
1. 只输出确定存在的关系
2. confidence 表示关系的确定性程度
3. 不要输出反向关系（如同时输出 A→B 和 B→A）
4. 如果没有关系，返回空列表
"""


class RelationExtractor:
    """
    关系提取器

    使用 LLM 分析知识点关系，包括：
    1. Statement → Concept (RELATED_TO)
    2. Concept → Concept (PART_OF, BELONGS_TO)
    3. 生成 relations.json
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        config: Optional[KGConfig] = None,
    ):
        """
        初始化关系提取器

        Args:
            api_key: 智谱 API Key，默认从环境变量读取
            config: 知识图谱配置
        """
        self.api_key = api_key or settings.ZHIPU_API_KEY
        self.config = config or KGConfig()
        self.uri_generator = URIGenerator(
            version=self.config.version,
            subject=self.config.subject,
        )

        # 初始化 LLM
        if self.api_key:
            self.llm = ChatZhipuAI(
                model="glm-4-flash",
                api_key=self.api_key,
                temperature=0.1,
            )
        else:
            self.llm = None

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
            response = self.llm.invoke([
                SystemMessage(content="你是一个数学教育专家。"),
                HumanMessage(content=prompt),
            ])

            content = response.content

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

    def extract_concept_relations(
        self,
        concepts: list[dict],
        batch_size: int = 20,
        verbose: bool = False,
    ) -> list[dict]:
        """
        提取 Concept 之间的关系

        Args:
            concepts: Concept 列表
            batch_size: 批次大小
            verbose: 是否显示进度

        Returns:
            关系列表
        """
        all_relations = []

        # 分批处理
        for i in range(0, len(concepts), batch_size):
            batch = concepts[i:i + batch_size]

            if verbose and i > 0:
                print(f"关系提取进度: {i}/{len(concepts)}")

            # 构建 prompt
            kp_names = [c["label"] for c in batch]
            prompt = RELATION_PROMPT.format(knowledge_points="\n".join(kp_names))

            result = self._call_llm(prompt)

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

        return all_relations

    def extract_all_relations(
        self,
        statements: list[dict],
        concepts: list[dict],
        verbose: bool = False,
    ) -> list[dict]:
        """
        提取所有关系

        Args:
            statements: Statement 列表
            concepts: Concept 列表
            verbose: 是否显示进度

        Returns:
            所有关系列表
        """
        relations = []

        # 1. Statement → Concept (RELATED_TO)
        if verbose:
            print("生成 Statement → Concept 关系...")

        stmt_relations = self.generate_statement_concept_relations(
            statements, concepts
        )
        relations.extend(stmt_relations)

        # 2. Concept → Concept (PART_OF, BELONGS_TO)
        if verbose:
            print("提取 Concept → Concept 关系...")

        concept_relations = self.extract_concept_relations(
            concepts, verbose=verbose
        )
        relations.extend(concept_relations)

        if verbose:
            print(f"共提取 {len(relations)} 个关系")

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

    parser = argparse.ArgumentParser(description="关系提取")
    parser.add_argument("--statements", required=True, help="Statements JSON 文件")
    parser.add_argument("--concepts", required=True, help="Concepts JSON 文件")
    parser.add_argument("--output", default="relations.json", help="输出文件")
    parser.add_argument("--debug", action="store_true", help="调试模式")

    args = parser.parse_args()

    # 加载数据
    with open(args.statements, encoding="utf-8") as f:
        statements = json.load(f)

    with open(args.concepts, encoding="utf-8") as f:
        concepts = json.load(f)

    extractor = RelationExtractor()
    relations = extractor.extract_all_relations(statements, concepts, verbose=True)
    extractor.save_relations(relations, args.output)