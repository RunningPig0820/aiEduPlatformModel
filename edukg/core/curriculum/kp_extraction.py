"""
知识点提取服务

使用 LLM (glm-4-flash) 从 OCR 文本中提取结构化知识点
支持断点续传和进度追踪

状态文件: state/step_2_kp_extraction.json
"""
import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, Dict, Any, Union

from langchain_community.chat_models import ChatZhipuAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser

from .config import settings
from edukg.core.llmTaskLock import TaskState


# 步骤2的状态文件名
STEP_2_STATE_ID = "step_2_kp_extraction"


@dataclass
class KnowledgePoint:
    """知识点"""
    name: str
    stage: str  # 学段
    domain: str  # 领域


@dataclass
class CurriculumKnowledgePoints:
    """课标知识点结构"""
    source: str
    extracted_at: str
    total_stages: int
    total_knowledge_points: int
    stages: list[dict] = field(default_factory=list)


# 结构化 Prompt
EXTRACTION_PROMPT = """你是一个数学教育专家，专门从课程标准中提取**核心数学知识点**。

请从以下课标文本中提取数学核心知识点，按照学段和领域进行组织。

⚠️ **重要过滤规则**：
1. **只提取核心数学概念**：数、运算、几何图形、统计、概率、函数、方程等
2. **排除以下内容**：
   - 教学活动/主题活动（如"数学游戏分享"、"主题活动2：曹冲称象的故事"）
   - 教学故事/案例（如"曹冲称象的故事"、"数学史料"）
   - 教学目标描述（如"形成量感、空间观念和初步的几何直观"）
   - 开篇话语/前言内容
   - 跨学科应用场景（如"体育运动与心率"、"理解GDP等经济学概念的意义"）
   - 教学建议/教学方法
3. **知识点必须是具体的数学概念或技能**，如"20以内加法"、"轴对称图形"等

输出格式要求（JSON）：
{{
  "stages": [
    {{
      "stage": "第一学段",
      "grades": "1-2年级",
      "domains": [
        {{
          "domain": "数与代数",
          "knowledge_points": ["20以内数的认识", "加减法"]
        }},
        {{
          "domain": "图形与几何",
          "knowledge_points": ["认识图形", "位置与方向"]
        }}
      ]
    }}
  ]
}}

注意事项：
1. 学段包括：第一学段(1-2年级)、第二学段(3-4年级)、第三学段(5-6年级)、第四学段(7-9年级)
2. 领域包括：数与代数、图形与几何、统计与概率、综合与实践
3. 知识点要具体、准确，使用课标中的原话
4. 如果文本中没有明确提到学段，请根据内容推断
5. 只输出 JSON，不要输出其他内容
6. 如果某块文本没有核心数学知识点，返回空列表

课标文本：
{text}
"""


# 学段页码范围（根据文档结构）
STAGE_PAGE_RANGES = {
    "第一学段": (25, 35),   # 大约页码范围
    "第二学段": (36, 50),
    "第三学段": (51, 70),
    "第四学段": (71, 100),
}


class PageChunker:
    """
    页面分块器

    将 OCR 结果按页或页面范围分块，支持语义边界
    """

    def __init__(self, pages_per_chunk: int = 10):
        """
        初始化分块器

        Args:
            pages_per_chunk: 每块包含的页数，默认10页
        """
        self.pages_per_chunk = pages_per_chunk

    def chunk_by_page_count(
        self,
        pages: List[Dict[str, Any]],
        pages_per_chunk: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        按页数分块

        Args:
            pages: OCR 页面列表
            pages_per_chunk: 每块页数

        Returns:
            分块后的列表，每个元素包含 page_range 和 text
        """
        chunks = []
        for i in range(0, len(pages), pages_per_chunk):
            chunk_pages = pages[i:i + pages_per_chunk]
            chunk_text = "\n\n".join([
                p.get("text", "")
                for p in chunk_pages
            ])
            chunks.append({
                "id": f"chunk_{i // pages_per_chunk + 1}",
                "page_range": (
                    chunk_pages[0].get("page_num", i + 1),
                    chunk_pages[-1].get("page_num", i + len(chunk_pages)),
                ),
                "text": chunk_text,
                "page_count": len(chunk_pages),
            })
        return chunks

    def chunk_by_stage(
        self,
        pages: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        按学段分块（基于内容检测）

        Args:
            pages: OCR 页面列表

        Returns:
            按学段分块的列表
        """
        # 学段关键词
        stage_keywords = [
            ("第一学段", "1~2年级"),
            ("第二学段", "3~4年级"),
            ("第三学段", "5~6年级"),
            ("第四学段", "7~9年级"),
        ]

        # 找到每个学段的起始页
        stage_starts = {}
        for page in pages:
            text = page.get("text", "")
            page_num = page.get("page_num", 0)
            for stage_name, grades in stage_keywords:
                if stage_name in text and stage_name not in stage_starts:
                    stage_starts[stage_name] = page_num

        # 按学段分块
        chunks = []
        sorted_stages = sorted(stage_starts.items(), key=lambda x: x[1])

        for i, (stage_name, start_page) in enumerate(sorted_stages):
            # 结束页是下一个学段的起始页，或最后一页
            if i + 1 < len(sorted_stages):
                end_page = sorted_stages[i + 1][1] - 1
            else:
                end_page = pages[-1].get("page_num", len(pages))

            # 收集该学段的页面
            stage_pages = [
                p for p in pages
                if start_page <= p.get("page_num", 0) <= end_page
            ]

            if stage_pages:
                chunk_text = "\n\n".join([
                    p.get("text", "")
                    for p in stage_pages
                ])
                chunks.append({
                    "id": f"stage_{i + 1}",
                    "stage_name": stage_name,
                    "page_range": (start_page, end_page),
                    "text": chunk_text,
                    "page_count": len(stage_pages),
                })

        return chunks


class LLMExtractor:
    """
    知识点提取服务

    使用 LLM 从课标文本中提取结构化知识点

    状态文件: state/step_2_kp_extraction.json
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "glm-4-flash",
        state_dir: Union[str, Path] = None,
    ):
        """
        初始化 LLM 提取器

        Args:
            api_key: 智谱 API Key，默认从环境变量读取
            model: 模型名称，默认 glm-4-flash（免费）
            state_dir: 状态文件目录
        """
        self.api_key = api_key or settings.ZHIPU_API_KEY
        self.state_dir = state_dir or settings.STATE_DIR

        if not self.api_key:
            raise ValueError(
                "智谱 API Key 未配置，请设置 ZHIPU_API_KEY 环境变量"
            )

        self.model = model
        self.llm = ChatZhipuAI(
            model=model,
            api_key=self.api_key,
            temperature=0.1,  # 低温度，稳定输出
            max_tokens=4096,
        )

        # 页面分块器
        self.chunker = PageChunker()

    def get_state(self) -> TaskState:
        """获取步骤2的状态管理器"""
        return TaskState(STEP_2_STATE_ID, state_dir=self.state_dir)

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
            "task_id": STEP_2_STATE_ID,
            "status": state.get_status(),
            "progress": progress,
            "is_completed": state.is_completed(),
            "state_file": str(state.state_file),
        }

    def _chunk_text(self, text: str, max_chars: int = 8000) -> list[str]:
        """
        将长文本分块

        Args:
            text: 原始文本
            max_chars: 每块最大字符数

        Returns:
            分块后的文本列表
        """
        if len(text) <= max_chars:
            return [text]

        chunks = []
        # 按段落分割
        paragraphs = text.split("\n\n")

        current_chunk = ""
        for para in paragraphs:
            if len(current_chunk) + len(para) + 2 <= max_chars:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = para + "\n\n"

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def _extract_json_from_response(self, response: str) -> dict:
        """
        从 LLM 响应中提取 JSON

        Args:
            response: LLM 响应文本

        Returns:
            解析后的 JSON 字典
        """
        # 尝试直接解析
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        # 尝试提取 JSON 块
        json_pattern = r'```json\s*([\s\S]*?)\s*```'
        matches = re.findall(json_pattern, response)
        if matches:
            try:
                return json.loads(matches[0])
            except json.JSONDecodeError:
                pass

        # 尝试找到 JSON 对象
        json_pattern = r'\{[\s\S]*\}'
        matches = re.findall(json_pattern, response)
        for match in matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue

        raise ValueError("无法从响应中提取有效的 JSON")

    def _merge_stages(self, stages_list: list[list[dict]]) -> list[dict]:
        """
        合并多个分块的学段结果

        Args:
            stages_list: 多个学段列表

        Returns:
            合并后的学段列表
        """
        merged = {}

        for stages in stages_list:
            for stage in stages:
                stage_name = stage.get("stage", "")
                if not stage_name:
                    continue

                if stage_name not in merged:
                    merged[stage_name] = {
                        "stage": stage_name,
                        "grades": stage.get("grades", ""),
                        "domains": {},
                    }

                for domain in stage.get("domains", []):
                    domain_name = domain.get("domain", "")
                    if not domain_name:
                        continue

                    if domain_name not in merged[stage_name]["domains"]:
                        merged[stage_name]["domains"][domain_name] = []

                    # 合并知识点，去重
                    kps = domain.get("knowledge_points", [])
                    for kp in kps:
                        if kp and kp not in merged[stage_name]["domains"][domain_name]:
                            merged[stage_name]["domains"][domain_name].append(kp)

        # 转换回列表格式
        result = []
        for stage_name in [
            "第一学段", "第二学段", "第三学段", "第四学段"
        ]:
            if stage_name in merged:
                stage_data = merged[stage_name]
                domains = []
                for domain_name, kps in stage_data["domains"].items():
                    domains.append({
                        "domain": domain_name,
                        "knowledge_points": kps,
                    })
                result.append({
                    "stage": stage_name,
                    "grades": stage_data["grades"],
                    "domains": domains,
                })

        return result

    def extract_knowledge_points(
        self,
        text: str,
        verbose: bool = True,
        state: Optional[TaskState] = None,
        resume: bool = False,
    ) -> CurriculumKnowledgePoints:
        """
        从文本中提取知识点

        Args:
            text: OCR 识别的文本
            verbose: 是否显示进度
            state: TaskState 实例（可选，默认使用 step_2 状态）
            resume: 是否从断点恢复

        Returns:
            CurriculumKnowledgePoints: 提取的知识点结构
        """
        # 分块处理
        chunks = self._chunk_text(text)

        if verbose:
            print(f"文本分为 {len(chunks)} 块进行处理")

        # 使用 step_2 专用状态
        if state is None:
            state = self.get_state()

        if not resume or state.get_status() == TaskState.STATUS_PENDING:
            state.start(total=len(chunks))

        # 获取待处理的检查点
        if resume:
            pending_checkpoints = state.resume()
            if verbose and pending_checkpoints:
                progress = state.get_progress()
                print(f"从断点恢复: 已完成 {progress['completed']}/{progress['total']} 块，待处理 {len(pending_checkpoints)} 块")
        else:
            pending_checkpoints = [f"checkpoint_{i+1}" for i in range(len(chunks))]

        all_stages = []

        for i, chunk in enumerate(chunks, 1):
            checkpoint_id = f"checkpoint_{i}"

            # 跳过已完成的检查点
            if checkpoint_id not in pending_checkpoints:
                continue

            if verbose:
                progress = state.get_progress()
                print(f"正在处理第 {i}/{len(chunks)} 块... (已完成: {progress['completed']}, 待处理: {progress['pending']})")

            prompt = EXTRACTION_PROMPT.format(text=chunk)

            try:
                response = self.llm.invoke([
                    SystemMessage(content="你是一个教育专家，专门从课程标准中提取知识点。"),
                    HumanMessage(content=prompt),
                ])

                result = self._extract_json_from_response(response.content)
                stages = result.get("stages", [])
                all_stages.append(stages)

                # 标记检查点完成
                state.complete_checkpoint(checkpoint_id, {"stages": stages})

            except Exception as e:
                print(f"处理第 {i} 块时出错: {e}")
                state.fail_checkpoint(checkpoint_id, str(e))
                continue

        # 合并结果
        merged_stages = self._merge_stages(all_stages)

        # 统计知识点数量
        total_kps = 0
        for stage in merged_stages:
            for domain in stage.get("domains", []):
                total_kps += len(domain.get("knowledge_points", []))

        result = CurriculumKnowledgePoints(
            source="课标文本",
            extracted_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            total_stages=len(merged_stages),
            total_knowledge_points=total_kps,
            stages=merged_stages,
        )

        if verbose:
            print(f"提取完成：{len(merged_stages)} 个学段，{total_kps} 个知识点")
            if state.is_completed():
                print("所有检查点已完成！")

        return result

    def extract_from_pages(
        self,
        pages: List[Dict[str, Any]],
        chunk_strategy: str = "page_count",
        pages_per_chunk: int = 10,
        verbose: bool = True,
        resume: bool = False,
    ) -> CurriculumKnowledgePoints:
        """
        从页面列表提取知识点（支持多种分块策略）

        Args:
            pages: OCR 页面列表，每个元素包含 page_num 和 text
            chunk_strategy: 分块策略
                - "page_count": 按页数分块（默认）
                - "stage": 按学段分块
            pages_per_chunk: 每块页数（仅 page_count 策略）
            verbose: 是否显示进度
            resume: 是否从断点恢复

        Returns:
            CurriculumKnowledgePoints: 提取的知识点结构
        """
        # 根据策略分块
        if chunk_strategy == "stage":
            chunks = self.chunker.chunk_by_stage(pages)
        else:
            chunks = self.chunker.chunk_by_page_count(pages, pages_per_chunk)

        if verbose:
            print(f"使用 {chunk_strategy} 策略分为 {len(chunks)} 块")
            for chunk in chunks:
                if "stage_name" in chunk:
                    print(f"  - {chunk['id']}: {chunk['stage_name']} (页 {chunk['page_range'][0]}-{chunk['page_range'][1]})")
                else:
                    print(f"  - {chunk['id']}: 页 {chunk['page_range'][0]}-{chunk['page_range'][1]}")

        # 获取状态
        state = self.get_state()

        if not resume or state.get_status() == TaskState.STATUS_PENDING:
            state.start(total=len(chunks))

        # 获取待处理的检查点
        if resume:
            pending_checkpoints = state.resume()
            if verbose and pending_checkpoints:
                progress = state.get_progress()
                print(f"从断点恢复: 已完成 {progress['completed']}/{progress['total']} 块，待处理 {len(pending_checkpoints)} 块")
        else:
            pending_checkpoints = [chunk["id"] for chunk in chunks]

        all_stages = []

        for chunk in chunks:
            chunk_id = chunk["id"]

            # 跳过已完成的检查点
            if chunk_id not in pending_checkpoints:
                continue

            if verbose:
                progress = state.get_progress()
                page_range = chunk.get("page_range", (0, 0))
                print(f"正在处理 {chunk_id} (页 {page_range[0]}-{page_range[1]})... (已完成: {progress['completed']}, 待处理: {progress['pending']})")

            prompt = EXTRACTION_PROMPT.format(text=chunk["text"])

            try:
                response = self.llm.invoke([
                    SystemMessage(content="你是一个教育专家，专门从课程标准中提取知识点。"),
                    HumanMessage(content=prompt),
                ])

                result = self._extract_json_from_response(response.content)
                stages = result.get("stages", [])
                all_stages.append(stages)

                # 标记检查点完成
                state.complete_checkpoint(chunk_id, {
                    "stages": stages,
                    "page_range": page_range,
                })

            except Exception as e:
                print(f"处理 {chunk_id} 时出错: {e}")
                state.fail_checkpoint(chunk_id, str(e))
                continue

        # 合并结果
        merged_stages = self._merge_stages(all_stages)

        # 统计知识点数量
        total_kps = 0
        for stage in merged_stages:
            for domain in stage.get("domains", []):
                total_kps += len(domain.get("knowledge_points", []))

        result = CurriculumKnowledgePoints(
            source="课标文本",
            extracted_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            total_stages=len(merged_stages),
            total_knowledge_points=total_kps,
            stages=merged_stages,
        )

        if verbose:
            print(f"提取完成：{len(merged_stages)} 个学段，{total_kps} 个知识点")
            if state.is_completed():
                print("所有检查点已完成！")

        return result

    def extract_from_ocr_result(
        self,
        ocr_result_path: str,
        verbose: bool = True,
        resume: bool = False,
        chunk_strategy: str = "page_count",
        pages_per_chunk: int = 10,
    ) -> CurriculumKnowledgePoints:
        """
        从 OCR 结果文件中提取知识点

        Args:
            ocr_result_path: OCR 结果 JSON 文件路径
            verbose: 是否显示进度
            resume: 是否从断点恢复
            chunk_strategy: 分块策略 ("page_count" 或 "stage")
            pages_per_chunk: 每块页数

        Returns:
            CurriculumKnowledgePoints: 提取的知识点结构
        """
        ocr_result_path = Path(ocr_result_path)
        if not ocr_result_path.exists():
            raise FileNotFoundError(f"OCR 结果文件不存在: {ocr_result_path}")

        with open(ocr_result_path, encoding="utf-8") as f:
            ocr_data = json.load(f)

        pages = ocr_data.get("pages", [])

        if verbose:
            print(f"从 {ocr_result_path.name} 读取了 {len(pages)} 页")

        result = self.extract_from_pages(
            pages=pages,
            chunk_strategy=chunk_strategy,
            pages_per_chunk=pages_per_chunk,
            verbose=verbose,
            resume=resume,
        )
        result.source = ocr_data.get("pdf_path", str(ocr_result_path))

        return result

    def save_result(
        self,
        result: CurriculumKnowledgePoints,
        output_path: str,
    ) -> None:
        """
        保存提取结果到 JSON 文件

        Args:
            result: 提取的知识点结构
            output_path: 输出文件路径
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "source": result.source,
            "extracted_at": result.extracted_at,
            "total_stages": result.total_stages,
            "total_knowledge_points": result.total_knowledge_points,
            "stages": result.stages,
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"知识点提取结果已保存到: {output_path}")


# 命令行入口
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="知识点提取 - 步骤2")
    parser.add_argument("--ocr-result", help="OCR 结果 JSON 文件路径（--status 时可选）")
    parser.add_argument("--output", default="curriculum_kps.json", help="输出文件路径")
    parser.add_argument("--debug", action="store_true", help="调试模式")
    parser.add_argument("--resume", action="store_true", help="从断点恢复")
    parser.add_argument("--status", action="store_true", help="仅查看状态，不执行")
    parser.add_argument("--state-dir", default=None, help="状态文件目录")
    parser.add_argument(
        "--chunk-strategy",
        choices=["page_count", "stage"],
        default="page_count",
        help="分块策略: page_count (按页数) 或 stage (按学段)"
    )
    parser.add_argument(
        "--pages-per-chunk",
        type=int,
        default=10,
        help="每块页数 (仅 page_count 策略)"
    )
    parser.add_argument("--verbose", action="store_true", help="显示详细进度")

    args = parser.parse_args()

    # 创建提取器
    extractor = LLMExtractor(state_dir=args.state_dir or settings.STATE_DIR)

    # 仅查看状态
    if args.status:
        summary = extractor.get_status_summary()
        print(f"\n=== 步骤2: 知识点提取状态 ===")
        print(f"状态文件: {summary['state_file']}")
        print(f"任务状态: {summary['status']}")
        print(f"进度: {summary['progress']['completed']}/{summary['progress']['total']} 完成")
        print(f"  - 已完成: {summary['progress']['completed']}")
        print(f"  - 失败: {summary['progress']['failed']}")
        print(f"  - 待处理: {summary['progress']['pending']}")
        print(f"已完成: {summary['is_completed']}")
        exit(0)

    # 执行提取时需要 --ocr-result
    if not args.ocr_result:
        parser.error("--ocr-result is required when not using --status")

    # 检查文件存在
    if not Path(args.ocr_result).exists():
        print(f"错误: OCR 结果文件不存在: {args.ocr_result}")
        exit(1)

    # 从断点恢复时显示进度
    if args.resume:
        progress = extractor.get_progress()
        if progress['total'] > 0:
            print(f"从断点恢复: 已完成 {progress['completed']}/{progress['total']} 块")
        else:
            print("没有可恢复的状态，开始新任务")

    # 执行提取
    result = extractor.extract_from_ocr_result(
        ocr_result_path=args.ocr_result,
        verbose=args.verbose,
        resume=args.resume,
        chunk_strategy=args.chunk_strategy,
        pages_per_chunk=args.pages_per_chunk,
    )
    extractor.save_result(result, args.output)