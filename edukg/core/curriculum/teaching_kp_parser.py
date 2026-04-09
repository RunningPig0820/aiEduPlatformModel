"""
教学知识点解析服务

将课标知识点解析为：
1. 核心知识点 (Concept) - 数学概念本身
2. 教学属性 (Attributes) - 范围、学段等限定

例如：
- "100以内数的认识" → Concept: "数" + Scope: "100以内" + Action: "认识"
- "三角形内角和" → Concept: "三角形" + Property: "内角和"
- "20以内加法" → Concept: "加法" + Scope: "20以内"

状态文件: state/step_3_teaching_kp_parse.json
"""
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, Dict, Any, Union

from langchain_community.chat_models import ChatZhipuAI
from langchain_core.messages import HumanMessage, SystemMessage

from .config import settings
from .kg_builder import URIGenerator, KGConfig
from edukg.core.neo4j.client import Neo4jClient, get_neo4j_client
from edukg.core.llmTaskLock import TaskState


# 步骤3的状态文件名
STEP_3_STATE_ID = "step_3_teaching_kp_parse"


@dataclass
class CoreConcept:
    """核心知识点"""
    label: str
    uri: Optional[str] = None
    is_existing: bool = False
    types: List[str] = field(default_factory=list)


@dataclass
class TeachingAttributes:
    """教学属性"""
    scope: Optional[str] = None          # 范围限定，如 "100以内"、"20以内"
    action: Optional[str] = None         # 教学动作，如 "认识"、"理解"、"掌握"
    property_name: Optional[str] = None  # 属性名称，如 "内角和"、"周长"
    method: Optional[str] = None         # 方法类型，如 "加法"、"减法"


@dataclass
class ParsedTeachingKP:
    """解析后的教学知识点"""
    # 原始信息
    original_label: str
    stage: str
    grade: str
    domain: str

    # 解析结果
    core_concept: Optional[CoreConcept] = None
    attributes: TeachingAttributes = field(default_factory=TeachingAttributes)

    # 匹配信息
    match_type: str = "none"  # exact, contains, semantic, new
    confidence: float = 0.0

    # 原始 URI（如果匹配到已存在的 Concept）
    matched_uri: Optional[str] = None


# LLM 解析 Prompt
PARSE_PROMPT = """你是一个数学教育专家，请分析以下教学知识点，提取核心概念和教学属性。

教学知识点: {knowledge_point}

请提取：
1. core_concept: 核心数学概念（去掉范围限定和教学动作）
2. scope: 范围限定（如 "100以内"、"20以内"、"万以内"）
3. action: 教学动作（如 "认识"、"理解"、"掌握"、"会"）
4. property: 属性名称（如 "内角和"、"周长"、"面积"）
5. method: 方法类型（如 "加法"、"减法"、"乘法"）

输出格式（JSON）：
{{
  "core_concept": "核心概念",
  "scope": "范围限定或null",
  "action": "教学动作或null",
  "property": "属性名称或null",
  "method": "方法类型或null",
  "confidence": 0.0-1.0
}}

注意：
1. 只输出 JSON，不要输出其他内容
2. 如果无法提取某项，设为 null
3. core_concept 应该是最简洁的数学概念

示例：
- "100以内数的认识" → {{"core_concept": "数", "scope": "100以内", "action": "认识", ...}}
- "三角形内角和" → {{"core_concept": "三角形", "property": "内角和", ...}}
- "20以内加法" → {{"core_concept": "加法", "scope": "20以内", ...}}
"""


class TeachingKPParser:
    """
    教学知识点解析器

    将课标知识点解析为核心概念 + 教学属性
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        config: Optional[KGConfig] = None,
        state_dir: Union[str, Path] = None,
    ):
        """
        初始化解析器

        Args:
            api_key: 智谱 API Key
            config: 知识图谱配置
            state_dir: 状态文件目录
        """
        self.api_key = api_key or settings.ZHIPU_API_KEY
        self.config = config or KGConfig()
        self.uri_generator = URIGenerator(
            version=self.config.version,
            subject=self.config.subject,
        )
        self.state_dir = state_dir or settings.STATE_DIR

        # Neo4j 客户端
        self.neo4j_client: Optional[Neo4jClient] = None

        # 缓存已存在的 Concept
        self._existing_concepts: Dict[str, Dict] = {}  # label -> {uri, types}

        # LLM
        self.llm = None
        if self.api_key:
            self.llm = ChatZhipuAI(
                model="glm-4-flash",
                api_key=self.api_key,
                temperature=0.1,
            )

    def _get_neo4j_client(self) -> Neo4jClient:
        """获取 Neo4j 客户端"""
        if self.neo4j_client is None:
            self.neo4j_client = get_neo4j_client()
        return self.neo4j_client

    def get_state(self) -> TaskState:
        """获取状态管理器"""
        return TaskState(STEP_3_STATE_ID, state_dir=self.state_dir)

    def load_existing_concepts(self, verbose: bool = False) -> int:
        """从 Neo4j 加载已存在的 Concept"""
        client = self._get_neo4j_client()

        query = """
        MATCH (c:Concept)
        RETURN c.uri AS uri, c.label AS label, c.types AS types
        """

        results = client.execute_read(query)

        self._existing_concepts = {}
        for row in results:
            label = row.get("label", "")
            if label:
                self._existing_concepts[label] = {
                    "uri": row.get("uri", ""),
                    "label": label,
                    "types": row.get("types", []),
                }

        if verbose:
            print(f"从 Neo4j 加载了 {len(self._existing_concepts)} 个已存在的 Concept")

        return len(self._existing_concepts)

    def _parse_with_llm(self, kp: str) -> Dict:
        """使用 LLM 解析知识点"""
        if not self.llm:
            return {
                "core_concept": kp,
                "scope": None,
                "action": None,
                "property": None,
                "method": None,
                "confidence": 0.5,
            }

        prompt = PARSE_PROMPT.format(knowledge_point=kp)

        try:
            response = self.llm.invoke([
                SystemMessage(content="你是一个数学教育专家。"),
                HumanMessage(content=prompt),
            ])

            content = response.content if hasattr(response, 'content') else str(response)

            # 解析 JSON
            json_pattern = r'\{[\s\S]*\}'
            matches = re.findall(json_pattern, content)
            if matches:
                return json.loads(matches[0])

        except Exception as e:
            print(f"LLM 解析出错: {e}")

        return {
            "core_concept": kp,
            "scope": None,
            "action": None,
            "property": None,
            "method": None,
            "confidence": 0.5,
        }

    def _match_concept(self, core_label: str) -> tuple[str, str, Dict]:
        """
        匹配核心概念到已存在的 Concept

        Returns:
            (match_type, matched_uri, concept_data)
        """
        # 1. 精确匹配
        if core_label in self._existing_concepts:
            return ("exact", self._existing_concepts[core_label]["uri"],
                    self._existing_concepts[core_label])

        # 2. 包含匹配
        for existing_label, data in self._existing_concepts.items():
            if existing_label in core_label or core_label in existing_label:
                return ("contains", data["uri"], data)

        # 3. 未匹配
        return ("new", None, {})

    def parse_knowledge_point(
        self,
        kp: str,
        stage: str,
        grade: str,
        domain: str,
    ) -> ParsedTeachingKP:
        """
        解析单个教学知识点

        Args:
            kp: 知识点名称
            stage: 学段
            grade: 年级
            domain: 领域

        Returns:
            解析结果
        """
        result = ParsedTeachingKP(
            original_label=kp,
            stage=stage,
            grade=grade,
            domain=domain,
        )

        # 使用 LLM 解析
        parsed = self._parse_with_llm(kp)
        core_label = parsed.get("core_concept", kp)
        confidence = parsed.get("confidence", 0.5)

        # 设置教学属性
        result.attributes = TeachingAttributes(
            scope=parsed.get("scope"),
            action=parsed.get("action"),
            property_name=parsed.get("property"),
            method=parsed.get("method"),
        )

        # 匹配核心概念
        match_type, matched_uri, concept_data = self._match_concept(core_label)
        result.match_type = match_type
        result.confidence = confidence
        result.matched_uri = matched_uri

        if match_type == "new":
            # 新概念，生成 0.2 URI
            new_uri = self.uri_generator.generate_instance_uri(core_label)
            result.core_concept = CoreConcept(
                label=core_label,
                uri=new_uri,
                is_existing=False,
                types=[],
            )
        else:
            # 已存在的概念
            result.core_concept = CoreConcept(
                label=concept_data.get("label", core_label),
                uri=matched_uri,
                is_existing=True,
                types=concept_data.get("types", []),
            )

        return result

    def parse_all(
        self,
        curriculum_kps_path: str,
        output_path: str,
        verbose: bool = False,
    ) -> Dict[str, Any]:
        """
        解析所有教学知识点

        Args:
            curriculum_kps_path: curriculum_kps.json 路径
            output_path: 输出文件路径
            verbose: 显示进度

        Returns:
            统计信息
        """
        # 加载 curriculum_kps
        with open(curriculum_kps_path, encoding="utf-8") as f:
            data = json.load(f)

        # 收集所有知识点
        all_kps = []
        for stage_data in data.get("stages", []):
            stage = stage_data.get("stage", "")
            grade = stage_data.get("grades", "")
            for domain_data in stage_data.get("domains", []):
                domain = domain_data.get("domain", "")
                for kp in domain_data.get("knowledge_points", []):
                    all_kps.append({
                        "kp": kp,
                        "stage": stage,
                        "grade": grade,
                        "domain": domain,
                    })

        if verbose:
            print(f"共 {len(all_kps)} 个教学知识点待解析")

        # 解析
        results = []
        stats = {
            "total": len(all_kps),
            "by_match_type": {"exact": 0, "contains": 0, "new": 0},
            "by_stage": {},
            "by_domain": {},
        }

        for i, item in enumerate(all_kps):
            if verbose and (i + 1) % 50 == 0:
                print(f"已解析 {i + 1}/{len(all_kps)} 个知识点...")

            parsed = self.parse_knowledge_point(
                kp=item["kp"],
                stage=item["stage"],
                grade=item["grade"],
                domain=item["domain"],
            )
            results.append(parsed)

            # 统计
            stats["by_match_type"][parsed.match_type] += 1

            if item["stage"] not in stats["by_stage"]:
                stats["by_stage"][item["stage"]] = 0
            stats["by_stage"][item["stage"]] += 1

            if item["domain"] not in stats["by_domain"]:
                stats["by_domain"][item["domain"]] = 0
            stats["by_domain"][item["domain"]] += 1

        # 转换为可序列化格式
        output_data = {
            "metadata": stats,
            "teaching_knowledge_points": [],
        }

        for r in results:
            kp_data = {
                "original_label": r.original_label,
                "stage": r.stage,
                "grade": r.grade,
                "domain": r.domain,
                "core_concept": {
                    "label": r.core_concept.label,
                    "uri": r.core_concept.uri,
                    "is_existing": r.core_concept.is_existing,
                    "types": r.core_concept.types,
                } if r.core_concept else None,
                "attributes": {
                    "scope": r.attributes.scope,
                    "action": r.attributes.action,
                    "property": r.attributes.property_name,
                    "method": r.attributes.method,
                },
                "match_type": r.match_type,
                "confidence": r.confidence,
            }
            output_data["teaching_knowledge_points"].append(kp_data)

        # 保存
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        if verbose:
            print(f"\n解析完成，保存到: {output_path}")
            print(f"  - 精确匹配: {stats['by_match_type']['exact']}")
            print(f"  - 包含匹配: {stats['by_match_type']['contains']}")
            print(f"  - 新增概念: {stats['by_match_type']['new']}")

        return stats


# 命令行入口
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="教学知识点解析 - Step 3")
    parser.add_argument("--kps", help="curriculum_kps.json 文件路径")
    parser.add_argument("--output", default="teaching_kps_parsed.json", help="输出文件")
    parser.add_argument("--verbose", action="store_true", help="显示进度")
    parser.add_argument("--state-dir", default=None, help="状态文件目录")

    args = parser.parse_args()

    # 创建解析器
    parser_obj = TeachingKPParser(state_dir=args.state_dir or settings.STATE_DIR)

    # 加载已存在的 Concept
    if args.verbose:
        print("加载 Neo4j 已存在的 Concept...")
    parser_obj.load_existing_concepts(verbose=args.verbose)

    # 解析
    if not args.kps:
        print("错误: 需要指定 --kps 参数")
        exit(1)

    stats = parser_obj.parse_all(
        curriculum_kps_path=args.kps,
        output_path=args.output,
        verbose=args.verbose,
    )

    print(f"\n完成！共解析 {stats['total']} 个教学知识点")