"""
知识点提取服务

使用 LLM (glm-4-flash) 从 OCR 文本中提取结构化知识点
"""
import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from langchain_community.chat_models import ChatZhipuAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser

from .config import settings


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
EXTRACTION_PROMPT = """你是一个教育专家，专门从课程标准中提取知识点。

请从以下课标文本中提取所有知识点，按照学段和领域进行组织。

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

课标文本：
{text}
"""


class LLMExtractor:
    """
    知识点提取服务

    使用 LLM 从课标文本中提取结构化知识点
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "glm-4-flash"):
        """
        初始化 LLM 提取器

        Args:
            api_key: 智谱 API Key，默认从环境变量读取
            model: 模型名称，默认 glm-4-flash（免费）
        """
        self.api_key = api_key or settings.ZHIPU_API_KEY

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
    ) -> CurriculumKnowledgePoints:
        """
        从文本中提取知识点

        Args:
            text: OCR 识别的文本
            verbose: 是否显示进度

        Returns:
            CurriculumKnowledgePoints: 提取的知识点结构
        """
        # 分块处理
        chunks = self._chunk_text(text)

        if verbose:
            print(f"文本分为 {len(chunks)} 块进行处理")

        all_stages = []

        for i, chunk in enumerate(chunks, 1):
            if verbose:
                print(f"正在处理第 {i}/{len(chunks)} 块...")

            prompt = EXTRACTION_PROMPT.format(text=chunk)

            try:
                response = self.llm.invoke([
                    SystemMessage(content="你是一个教育专家，专门从课程标准中提取知识点。"),
                    HumanMessage(content=prompt),
                ])

                result = self._extract_json_from_response(response.content)
                stages = result.get("stages", [])
                all_stages.append(stages)

            except Exception as e:
                print(f"处理第 {i} 块时出错: {e}")
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

        return result

    def extract_from_ocr_result(
        self,
        ocr_result_path: str,
        verbose: bool = True,
    ) -> CurriculumKnowledgePoints:
        """
        从 OCR 结果文件中提取知识点

        Args:
            ocr_result_path: OCR 结果 JSON 文件路径
            verbose: 是否显示进度

        Returns:
            CurriculumKnowledgePoints: 提取的知识点结构
        """
        ocr_result_path = Path(ocr_result_path)
        if not ocr_result_path.exists():
            raise FileNotFoundError(f"OCR 结果文件不存在: {ocr_result_path}")

        with open(ocr_result_path, encoding="utf-8") as f:
            ocr_data = json.load(f)

        # 合并所有页面的文本
        text = "\n\n".join([
            page.get("text", "")
            for page in ocr_data.get("pages", [])
        ])

        if verbose:
            print(f"从 {ocr_result_path.name} 读取了 {len(text)} 个字符")

        result = self.extract_knowledge_points(text, verbose)
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

    parser = argparse.ArgumentParser(description="知识点提取")
    parser.add_argument("--ocr-result", required=True, help="OCR 结果 JSON 文件路径")
    parser.add_argument("--output", default="curriculum_kps.json", help="输出文件路径")
    parser.add_argument("--debug", action="store_true", help="调试模式")

    args = parser.parse_args()

    extractor = LLMExtractor()
    result = extractor.extract_from_ocr_result(
        ocr_result_path=args.ocr_result,
        verbose=True,
    )
    extractor.save_result(result, args.output)