"""
TTL 生成服务

生成 RDF/TTL 格式的知识点数据
"""
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class TTLConfig:
    """TTL 配置"""
    namespace: str = "http://edukg.org/curriculum/math#"
    prefix: str = "curriculum"
    rdf_prefix: str = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    rdfs_prefix: str = "http://www.w3.org/2000/01/rdf-schema#"


class TTLGenerator:
    """
    TTL 生成服务

    将知识点转换为 RDF/TTL 格式
    """

    def __init__(self, config: Optional[TTLConfig] = None):
        """
        初始化 TTL 生成器

        Args:
            config: TTL 配置
        """
        self.config = config or TTLConfig()

    def _escape_uri(self, text: str) -> str:
        """
        转义 URI 中的特殊字符

        Args:
            text: 原始文本

        Returns:
            转义后的 URI 安全文本
        """
        # 替换空格和特殊字符
        replacements = {
            " ": "_",
            "(": "",
            ")": "",
            "（": "",
            "）": "",
            "，": "_",
            "、": "_",
            "：": "_",
            ":": "_",
            "/": "_",
            "\\": "_",
            "\"": "",
            "'": "",
            "\n": "",
            "\r": "",
        }

        for old, new in replacements.items():
            text = text.replace(old, new)

        return text.strip("_")

    def _generate_triple(
        self,
        subject: str,
        predicate: str,
        obj: str,
        is_uri: bool = True,
    ) -> str:
        """
        生成 RDF 三元组

        Args:
            subject: 主语
            predicate: 谓语
            obj: 宾语
            is_uri: 宾语是否为 URI

        Returns:
            TTL 格式的三元组
        """
        if is_uri:
            return f"{subject} {predicate} {obj} ."
        else:
            return f'{subject} {predicate} "{obj}" .'

    def generate_ttl(
        self,
        curriculum_kps_path: str,
        output_path: str,
        verbose: bool = True,
    ) -> None:
        """
        从 curriculum_kps.json 生成 TTL 文件

        Args:
            curriculum_kps_path: 知识点 JSON 文件路径
            output_path: 输出 TTL 文件路径
            verbose: 是否显示进度
        """
        curriculum_kps_path = Path(curriculum_kps_path)
        if not curriculum_kps_path.exists():
            raise FileNotFoundError(f"知识点文件不存在: {curriculum_kps_path}")

        with open(curriculum_kps_path, encoding="utf-8") as f:
            data = json.load(f)

        lines = []
        ns = self.config.namespace
        prefix = self.config.prefix

        # 添加前缀声明
        lines.append(f"@prefix {prefix}: <{ns}> .")
        lines.append(f"@prefix rdf: <{self.config.rdf_prefix}> .")
        lines.append(f"@prefix rdfs: <{self.config.rdfs_prefix}> .")
        lines.append("")

        kp_count = 0

        for stage_data in data.get("stages", []):
            stage_name = stage_data.get("stage", "")
            stage_uri = f"{prefix}:{self._escape_uri(stage_name)}"

            # 创建学段实例
            lines.append(f"{stage_uri} a {prefix}:Stage ;")
            lines.append(f'    rdfs:label "{stage_name}" .')
            lines.append("")

            for domain_data in stage_data.get("domains", []):
                domain_name = domain_data.get("domain", "")
                domain_uri = f"{prefix}:{self._escape_uri(domain_name)}"

                # 创建领域实例
                lines.append(f"{domain_uri} a {prefix}:Domain ;")
                lines.append(f'    rdfs:label "{domain_name}" .')
                lines.append("")

                for kp in domain_data.get("knowledge_points", []):
                    if not kp:
                        continue

                    kp_uri = f"{prefix}:{self._escape_uri(kp)}"
                    kp_count += 1

                    # 创建知识点实例
                    lines.append(f"{kp_uri} a {prefix}:KnowledgePoint ;")
                    lines.append(f'    rdfs:label "{kp}" ;')
                    lines.append(f"    {prefix}:belongsToStage {stage_uri} ;")
                    lines.append(f"    {prefix}:belongsToDomain {domain_uri} .")
                    lines.append("")

        # 写入文件
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        if verbose:
            print(f"TTL 生成完成: {kp_count} 个知识点")
            print(f"文件保存到: {output_path}")

    def generate_from_comparison_report(
        self,
        comparison_report_path: str,
        output_path: str,
        only_new: bool = True,
        verbose: bool = True,
    ) -> None:
        """
        从对比报告生成 TTL 文件（只包含新知识点）

        Args:
            comparison_report_path: 对比报告文件路径
            output_path: 输出 TTL 文件路径
            only_new: 是否只包含新知识点
            verbose: 是否显示进度
        """
        comparison_report_path = Path(comparison_report_path)
        if not comparison_report_path.exists():
            raise FileNotFoundError(f"对比报告文件不存在: {comparison_report_path}")

        with open(comparison_report_path, encoding="utf-8") as f:
            data = json.load(f)

        lines = []
        ns = self.config.namespace
        prefix = self.config.prefix

        # 添加前缀声明
        lines.append(f"@prefix {prefix}: <{ns}> .")
        lines.append(f"@prefix rdf: <{self.config.rdf_prefix}> .")
        lines.append(f"@prefix rdfs: <{self.config.rdfs_prefix}> .")
        lines.append("")

        kp_count = 0

        for result in data.get("results", []):
            if only_new and result.get("status") != "new":
                continue

            kp = result.get("knowledge_point", "")
            if not kp:
                continue

            kp_uri = f"{prefix}:{self._escape_uri(kp)}"
            kp_count += 1

            # 创建知识点实例
            lines.append(f"{kp_uri} a {prefix}:KnowledgePoint ;")
            lines.append(f'    rdfs:label "{kp}" .')

            # 添加建议类型
            suggested_types = result.get("suggested_types", [])
            if suggested_types:
                for st in suggested_types:
                    lines.append(f'    {prefix}:suggestedType "{st}" .')

            lines.append("")

        # 写入文件
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        if verbose:
            print(f"TTL 生成完成: {kp_count} 个新知识点")
            print(f"文件保存到: {output_path}")


# 命令行入口
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="TTL 生成")
    parser.add_argument("--kps", required=True, help="curriculum_kps.json 文件路径")
    parser.add_argument("--output", default="curriculum_kps.ttl", help="输出 TTL 文件路径")
    parser.add_argument("--debug", action="store_true", help="调试模式")

    args = parser.parse_args()

    generator = TTLGenerator()
    generator.generate_ttl(
        curriculum_kps_path=args.kps,
        output_path=args.output,
        verbose=True,
    )