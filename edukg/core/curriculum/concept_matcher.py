"""
知识点匹配服务

从课标知识点中提取、去重、匹配 Neo4j 已存在知识点，
生成带 URI 的 concepts.json。

匹配策略：
1. 精确匹配：label 完全相同
2. 包含匹配：A 包含 B 或 B 包含 A
3. 语义匹配：LLM 判断语义相似

状态文件: state/step_4_concept_matching.json
"""
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Dict, Any, Set, Union

from langchain_community.chat_models import ChatZhipuAI
from langchain_core.messages import HumanMessage, SystemMessage

from .config import settings
from .kg_builder import URIGenerator, KGConfig
from edukg.core.neo4j.client import Neo4jClient, get_neo4j_client
from edukg.core.llmTaskLock import TaskState


# 步骤4的状态文件名
STEP_4_STATE_ID = "step_4_concept_matching"


@dataclass
class MatchResult:
    """匹配结果"""
    knowledge_point: str
    is_matched: bool
    match_type: str  # exact, contains, semantic, none
    matched_uri: Optional[str] = None
    matched_label: Optional[str] = None
    confidence: float = 1.0
    new_uri: Optional[str] = None


# 语义匹配 Prompt
SEMANTIC_MATCH_PROMPT = """你是一个数学教育专家，需要判断两个知识点是否语义相近。

知识点1: {kp1}
知识点2: {kp2}

请判断这两个知识点是否表示相同的数学概念。
考虑因素：
1. 是否指代同一个数学对象（如"圆"和"圆的认识"）
2. 是否是同一概念的不同表述（如"加法"和"加法运算"）
3. 排除明显不同的概念（如"加法"和"减法"）

输出格式（JSON）：
{{
  "is_similar": true/false,
  "confidence": 0.0-1.0,
  "reason": "判断理由"
}}

只输出 JSON，不要输出其他内容。
"""


class ConceptMatcher:
    """
    知识点匹配器

    从课标知识点中：
    1. 提取并去重知识点
    2. 匹配 Neo4j 已存在的 Concept
    3. 生成带 URI 的概念列表

    状态文件: state/step_4_concept_matching.json
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        config: Optional[KGConfig] = None,
        state_dir: Union[str, Path] = None,
    ):
        """
        初始化知识点匹配器

        Args:
            api_key: 智谱 API Key，默认从环境变量读取
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
        self._existing_concepts: Dict[str, Dict] = {}  # label -> {uri, label}

        # LLM（用于语义匹配）
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
        """获取步骤4的状态管理器"""
        return TaskState(STEP_4_STATE_ID, state_dir=self.state_dir)

    def load_existing_concepts(self, verbose: bool = False) -> int:
        """
        从 Neo4j 加载已存在的 Concept

        Args:
            verbose: 是否显示进度

        Returns:
            加载的 Concept 数量
        """
        client = self._get_neo4j_client()

        query = """
        MATCH (c:Concept)
        RETURN c.uri AS uri, c.label AS label
        """

        results = client.execute_read(query)

        self._existing_concepts = {}
        for row in results:
            label = row.get("label", "")
            if label:
                self._existing_concepts[label] = {
                    "uri": row.get("uri", ""),
                    "label": label,
                }

        if verbose:
            print(f"从 Neo4j 加载了 {len(self._existing_concepts)} 个已存在的 Concept")

        return len(self._existing_concepts)

    def extract_knowledge_points(
        self,
        curriculum_kps_path: str,
        verbose: bool = False,
    ) -> List[str]:
        """
        从 curriculum_kps.json 提取知识点并去重

        Args:
            curriculum_kps_path: curriculum_kps.json 文件路径
            verbose: 是否显示进度

        Returns:
            去重后的知识点列表
        """
        with open(curriculum_kps_path, encoding="utf-8") as f:
            data = json.load(f)

        all_kps: Set[str] = set()

        for stage in data.get("stages", []):
            for domain in stage.get("domains", []):
                for kp in domain.get("knowledge_points", []):
                    if kp and isinstance(kp, str):
                        all_kps.add(kp)

        kps_list = sorted(list(all_kps))

        if verbose:
            print(f"从 {curriculum_kps_path} 提取了 {len(all_kps)} 个不重复的知识点")

        return kps_list

    def _exact_match(self, kp: str) -> Optional[Dict]:
        """
        精确匹配

        Args:
            kp: 知识点名称

        Returns:
            匹配结果或 None
        """
        if kp in self._existing_concepts:
            return self._existing_concepts[kp]
        return None

    def _contains_match(self, kp: str) -> Optional[Dict]:
        """
        包含匹配

        Args:
            kp: 知识点名称

        Returns:
            匹配结果或 None
        """
        # 检查是否有已存在的 Concept 包含该知识点
        for existing_label, existing_data in self._existing_concepts.items():
            # kp 包含 existing_label（如 "圆的认识" 包含 "圆"）
            if existing_label in kp:
                return existing_data
            # existing_label 包含 kp（如 "圆" 包含在 "圆的认识" 中）
            if kp in existing_label:
                return existing_data

        return None

    def _semantic_match(self, kp: str, candidates: List[str]) -> Optional[Dict]:
        """
        语义匹配（使用 LLM）

        Args:
            kp: 知识点名称
            candidates: 候选匹配列表

        Returns:
            匹配结果或 None
        """
        if not self.llm or not candidates:
            return None

        # 批量匹配（每次最多5个候选）
        batch_candidates = candidates[:5]

        prompt = f"""你是一个数学教育专家，需要判断知识点 "{kp}" 与以下哪些知识点语义相近。

候选知识点：
{chr(10).join([f"{i+1}. {c}" for i, c in enumerate(batch_candidates)])}

请返回最相近的知识点编号，如果没有相近的返回 0。

输出格式（JSON）：
{{
  "best_match_index": 0-5,
  "confidence": 0.0-1.0,
  "reason": "判断理由"
}}

只输出 JSON，不要输出其他内容。
"""

        try:
            response = self.llm.invoke([
                SystemMessage(content="你是一个数学教育专家。"),
                HumanMessage(content=prompt),
            ])

            content = response.content if hasattr(response, 'content') else str(response)

            # 解析 JSON
            import re
            json_pattern = r'\{[\s\S]*\}'
            matches = re.findall(json_pattern, content)
            if matches:
                result = json.loads(matches[0])
                best_idx = result.get("best_match_index", 0)
                if 1 <= best_idx <= len(batch_candidates):
                    matched_label = batch_candidates[best_idx - 1]
                    return self._existing_concepts.get(matched_label)

        except Exception as e:
            print(f"语义匹配出错: {e}")

        return None

    def match_knowledge_point(
        self,
        kp: str,
        use_semantic: bool = True,
    ) -> MatchResult:
        """
        匹配单个知识点

        Args:
            kp: 知识点名称
            use_semantic: 是否使用语义匹配

        Returns:
            匹配结果
        """
        # 1. 精确匹配
        matched = self._exact_match(kp)
        if matched:
            return MatchResult(
                knowledge_point=kp,
                is_matched=True,
                match_type="exact",
                matched_uri=matched["uri"],
                matched_label=matched["label"],
                confidence=1.0,
            )

        # 2. 包含匹配
        matched = self._contains_match(kp)
        if matched:
            return MatchResult(
                knowledge_point=kp,
                is_matched=True,
                match_type="contains",
                matched_uri=matched["uri"],
                matched_label=matched["label"],
                confidence=0.8,
            )

        # 3. 语义匹配（可选）
        if use_semantic and self.llm:
            # 找可能的候选（基于简单规则筛选）
            candidates = []
            for existing_label in self._existing_concepts.keys():
                # 简单启发式：有共同字符
                if any(c in existing_label for c in kp if len(c) > 1):
                    candidates.append(existing_label)
                if len(candidates) >= 10:
                    break

            if candidates:
                matched = self._semantic_match(kp, candidates)
                if matched:
                    return MatchResult(
                        knowledge_point=kp,
                        is_matched=True,
                        match_type="semantic",
                        matched_uri=matched["uri"],
                        matched_label=matched["label"],
                        confidence=0.7,
                    )

        # 4. 未匹配，生成新 URI
        new_uri = self.uri_generator.generate_instance_uri(kp)
        return MatchResult(
            knowledge_point=kp,
            is_matched=False,
            match_type="none",
            new_uri=new_uri,
            confidence=1.0,
        )

    def match_all(
        self,
        knowledge_points: List[str],
        use_semantic: bool = True,
        verbose: bool = False,
    ) -> List[MatchResult]:
        """
        批量匹配知识点

        Args:
            knowledge_points: 知识点列表
            use_semantic: 是否使用语义匹配
            verbose: 是否显示进度

        Returns:
            匹配结果列表
        """
        results = []

        for i, kp in enumerate(knowledge_points):
            if verbose and (i + 1) % 50 == 0:
                print(f"已匹配 {i + 1}/{len(knowledge_points)} 个知识点...")

            result = self.match_knowledge_point(kp, use_semantic=use_semantic)
            results.append(result)

        if verbose:
            matched_count = sum(1 for r in results if r.is_matched)
            new_count = len(results) - matched_count
            print(f"匹配完成: {matched_count} 个已存在，{new_count} 个新增")

        return results

    def generate_concepts_json(
        self,
        results: List[MatchResult],
        output_path: str,
        verbose: bool = False,
    ) -> Dict[str, Any]:
        """
        生成 concepts.json

        Args:
            results: 匹配结果列表
            output_path: 输出文件路径
            verbose: 是否显示进度

        Returns:
            统计信息
        """
        concepts = []
        stats = {
            "total": len(results),
            "matched": 0,
            "new": 0,
            "by_match_type": {
                "exact": 0,
                "contains": 0,
                "semantic": 0,
                "none": 0,
            },
        }

        for result in results:
            if result.is_matched:
                # 已存在的 Concept，使用 0.1 版本 URI
                concept = {
                    "label": result.knowledge_point,
                    "uri": result.matched_uri,
                    "version": "0.1",
                    "match_type": result.match_type,
                    "matched_to": result.matched_label,
                    "confidence": result.confidence,
                }
                stats["matched"] += 1
            else:
                # 新 Concept，使用 0.2 版本 URI
                concept = {
                    "label": result.knowledge_point,
                    "uri": result.new_uri,
                    "version": "0.2",
                    "match_type": "new",
                    "confidence": result.confidence,
                }
                stats["new"] += 1

            stats["by_match_type"][result.match_type] += 1
            concepts.append(concept)

        # 保存文件
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "metadata": {
                "total": stats["total"],
                "matched": stats["matched"],
                "new": stats["new"],
                "by_match_type": stats["by_match_type"],
            },
            "concepts": concepts,
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        if verbose:
            print(f"Concepts 已保存到: {output_path}")
            print(f"  - 已匹配（使用 0.1 URI）: {stats['matched']}")
            print(f"  - 新增（使用 0.2 URI）: {stats['new']}")

        return stats


# 命令行入口
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="知识点匹配 - 步骤4")
    parser.add_argument("--kps", help="curriculum_kps.json 文件路径")
    parser.add_argument("--output", default="concepts.json", help="输出文件")
    parser.add_argument("--no-semantic", action="store_true", help="禁用语义匹配")
    parser.add_argument("--status", action="store_true", help="仅查看状态，不执行")
    parser.add_argument("--state-dir", default=None, help="状态文件目录")
    parser.add_argument("--verbose", action="store_true", help="显示详细进度")

    args = parser.parse_args()

    # 创建匹配器
    matcher = ConceptMatcher(state_dir=args.state_dir or settings.STATE_DIR)

    # 仅查看状态
    if args.status:
        state = matcher.get_state()
        progress = state.get_progress()
        print(f"\n=== 步骤4: 知识点匹配状态 ===")
        print(f"状态文件: {state.state_file}")
        print(f"任务状态: {state.get_status()}")
        print(f"进度: {progress['completed']}/{progress['total']}")
        exit(0)

    # 执行匹配时需要 --kps
    if not args.kps:
        parser.error("--kps is required when not using --status")

    if not Path(args.kps).exists():
        print(f"错误: 文件不存在: {args.kps}")
        exit(1)

    # 1. 加载已存在的 Concept
    if args.verbose:
        print("步骤 1: 加载 Neo4j 已存在的 Concept...")
    matcher.load_existing_concepts(verbose=args.verbose)

    # 2. 提取知识点
    if args.verbose:
        print("\n步骤 2: 提取知识点并去重...")
    kps = matcher.extract_knowledge_points(args.kps, verbose=args.verbose)

    # 3. 匹配知识点
    if args.verbose:
        print("\n步骤 3: 匹配知识点...")
    results = matcher.match_all(
        kps,
        use_semantic=not args.no_semantic,
        verbose=args.verbose,
    )

    # 4. 生成 concepts.json
    if args.verbose:
        print("\n步骤 4: 生成 concepts.json...")
    stats = matcher.generate_concepts_json(results, args.output, verbose=args.verbose)

    print(f"\n完成！共处理 {stats['total']} 个知识点")