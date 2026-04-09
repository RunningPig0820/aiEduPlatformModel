"""
Step 5: 新增概念的 Class 类型推断

为 20 个新增概念推断 Class 类型

输入:
  - concepts_v3.json (新增的 20 个概念)
  - 已有的 38 个 Class 列表

输出:
  - classes_v3.json (新推断的 Class)
  - concepts_with_class.json (带 Class 的概念列表)
"""
import json
from pathlib import Path
from typing import Optional, List, Dict, Any, Union

from langchain_community.chat_models import ChatZhipuAI
from langchain_core.messages import HumanMessage, SystemMessage

from .config import settings
from .kg_builder import URIGenerator, KGConfig
from edukg.core.llmTaskLock import CachedLLM


# 已有的 38 个 Class 列表
EXISTING_CLASSES = [
    {"label": "代数概念", "id": "daishugainian-37b08a6862907ffaa006ff9800bf7e13"},
    {"label": "点", "id": "dian-9658ed8fa424c113006a2866498f481e"},
    {"label": "概率概念", "id": "gailugainian-81db9020e9385f6da531adcd03674802"},
    {"label": "函数", "id": "hanshu-807668ddbb4ab44b00a187454d01e3df"},
    {"label": "角", "id": "jiao-ac9bca4ce94bb69495866988c9f0a6db"},
    {"label": "集合", "id": "jihe-6479ab71bb39247300ea7c4cd0ef18b9"},
    {"label": "几何概念", "id": "jihegainian-e8bbf33dc8df3bcbbba95101e98a2775"},
    {"label": "几何体", "id": "jiheti-22a356e5ec4e5555c6c4d90bf2e85018"},
    {"label": "几何图形", "id": "jihetuxing-87cc20beb977b683fd0c77dd6cf0a375"},
    {"label": "逻辑概念", "id": "luojigainian-cdfc2210b6cc71f21103c988be937a09"},
    {"label": "数学", "id": "math"},
    {"label": "面", "id": "mian-a6ecafe63eb610b1cfb3e9db2ffca1b6"},
    {"label": "命题", "id": "mingti-1b68815986ebd90d02d0fe10a336bf13"},
    {"label": "事件", "id": "shijian-1bde9411df24ce5849347646644f6db7"},
    {"label": "数", "id": "shu-bec758cd6ac15f49e774b8c28ef31a74"},
    {"label": "数列", "id": "shulie-eb60c163e6e4abeba7899f60bf8a6280"},
    {"label": "数学单位", "id": "shuxuedanwei-6b3002563cb21fae872cc8601071c4dd"},
    {"label": "数学定理", "id": "shuxuedingli-d7efa6467a1cb775026237ea82988b61"},
    {"label": "数学定律", "id": "shuxuedinglu-91a916ea152ed5b26b4782277a549e7e"},
    {"label": "数学定义", "id": "shuxuedingyi-b14b4ceb4747e9d5cc2534e9dc38faf1"},
    {"label": "数学方法", "id": "shuxuefangfa-b83f25d3fe0436916bdf21ad8e3bdc1c"},
    {"label": "数学法则", "id": "shuxuefaze-646a50c01e136382da3d8fe612c2e715"},
    {"label": "数学概念", "id": "shuxuegainian-117c187fe4c4046bc9978c6d0d1c2504"},
    {"label": "数学公理", "id": "shuxuegongli-a527b8a485fb172d772143a1d83bb66b"},
    {"label": "数学公式", "id": "shuxuegongshi-aed26794e8839211cdeb46545c4f4518"},
    {"label": "数学关系", "id": "shuxueguanxi-d7578c8de203af6151c80491a847cba5"},
    {"label": "数学家", "id": "shuxuejia-bc60afaf1ead8b7b8b5a22e717b3cd68"},
    {"label": "数学命题", "id": "shuxuemingti-1b153b8f349555f4ecd3e31102996278"},
    {"label": "数学算法", "id": "shuxuesuanfa-b1be2da4d73279d277dec3a1a51b26fd"},
    {"label": "数学问题", "id": "shuxuewenti-3e8aec9571746607ddce8c436e27f023"},
    {"label": "数学性质", "id": "shuxuexingzhi-c48cfa5ba6ca2840521262b5cfe9a9be"},
    {"label": "数学原理", "id": "shuxueyuanli-4f38404bd3bd96d2550babc3f063b86f"},
    {"label": "数学运算", "id": "shuxueyunsuan-c8336453933522d7677f399004737825"},
    {"label": "算法概念", "id": "suanfagainian-9fd1940dc00d51d8508d5c34763671fa"},
    {"label": "统计概念", "id": "tongjigainian-439a9a746a794fe6945e225abe357718"},
    {"label": "线", "id": "xian-b5b5ec57d04bb6260342bb3b9a220ac7"},
    {"label": "向量", "id": "xiangliang-779126ea9773ce4ca72a53e1f7f8b99e"},
    {"label": "圆锥曲线", "id": "yuanzhuiquxian-8d0058b62ea4e63a15047ec7196e44ca"},
]

# Class 层级结构（父类映射）
CLASS_PARENTS = {
    "数学概念": "数学",
    "数学方法": "数学",
    "数学定义": "数学",
    "数学运算": "数学",
    "几何概念": "数学概念",
    "代数概念": "数学概念",
    "统计概念": "数学概念",
    "概率概念": "数学概念",
    "算法概念": "数学概念",
    "逻辑概念": "数学概念",
    "几何图形": "几何概念",
    "函数": "代数概念",
    "数": "代数概念",
    "数列": "代数概念",
    "向量": "代数概念",
    "集合": "代数概念",
    "命题": "代数概念",
    "事件": "代数概念",
    "点": "几何图形",
    "线": "几何图形",
    "角": "几何图形",
    "面": "几何图形",
    "圆锥曲线": "线",
    "几何体": "几何概念",
    "数学命题": "数学",
    "数学定理": "数学命题",
    "数学定律": "数学命题",
    "数学公理": "数学命题",
    "数学公式": "数学命题",
    "数学法则": "数学命题",
    "数学性质": "数学命题",
    "数学原理": "数学命题",
    "数学算法": "数学方法",
    "数学单位": "数学",
    "数学关系": "数学",
    "数学家": "数学",
    "数学问题": "数学",
}

# LLM Prompt
CLASS_INFERENCE_PROMPT = """你是一个数学教育专家，需要判断知识点属于哪个概念类别。

现有概念类别列表：
{class_list}

知识点: {knowledge_point}

请判断这个知识点属于哪个概念类别。
1. 如果能匹配现有类别，返回类别名称和置信度
2. 如果现有类别都不合适，建议一个新的类别名称

输出格式（JSON）：
{{
  "class": "类别名称",
  "confidence": 0.0-1.0,
  "reason": "判断理由",
  "suggest_new": false/true,
  "parent_class": "父类名称（仅新增类别时需要）"
}}

注意：
1. confidence 表示置信度，0-1 之间
2. 只有当现有类别都不合适时才设置 suggest_new: true
3. 新增类别时必须指定父类（从现有类别中选择）
4. 只输出 JSON，不要输出其他内容
"""


class ClassInferrer:
    """
    Class 类型推断器

    为新增概念推断 Class 类型
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        cache_dir: Union[str, Path] = None,
    ):
        self.api_key = api_key or settings.ZHIPU_API_KEY
        self.cache_dir = cache_dir or settings.CACHE_DIR
        self.uri_generator = URIGenerator(version="0.2", subject="math")

        # 已有 Class
        self.existing_classes = {c["label"]: c for c in EXISTING_CLASSES}
        self.class_parents = CLASS_PARENTS

        # LLM
        self.llm = None
        if self.api_key:
            llm = ChatZhipuAI(
                model="glm-4-flash",
                api_key=self.api_key,
                temperature=0.1,
            )
            self.llm = CachedLLM(llm, cache_dir=self.cache_dir)

    def get_class_list_for_prompt(self) -> str:
        """获取 Class 列表用于 prompt"""
        return ", ".join(self.existing_classes.keys())

    def infer_class(self, concept_label: str) -> Dict[str, Any]:
        """
        推断单个概念的 Class

        Args:
            concept_label: 概念标签

        Returns:
            推断结果
        """
        class_list = self.get_class_list_for_prompt()
        prompt = f"你是一个数学教育专家。\n\n{CLASS_INFERENCE_PROMPT.format(class_list=class_list, knowledge_point=concept_label)}"

        if not self.llm:
            return {
                "class": "数学概念",
                "confidence": 0.5,
                "suggest_new": False,
                "reason": "未配置 LLM",
            }

        try:
            response = self.llm.invoke(prompt, use_cache=True)
            content = response if isinstance(response, str) else str(response)

            # 解析 JSON
            import re
            json_pattern = r'\{[\s\S]*\}'
            matches = re.findall(json_pattern, content)
            if matches:
                return json.loads(matches[0])

        except Exception as e:
            print(f"LLM 推断出错: {e}")

        return {
            "class": "数学概念",
            "confidence": 0.5,
            "suggest_new": False,
            "reason": f"推断失败",
        }

    def get_existing_class_uri(self, class_label: str) -> Optional[str]:
        """获取已有 Class 的 URI"""
        if class_label in self.existing_classes:
            return f"http://edukg.org/knowledge/0.1/class/math#{self.existing_classes[class_label]['id']}"
        return None

    def get_parent_uri(self, class_label: str) -> str:
        """获取父类 URI"""
        parent_label = self.class_parents.get(class_label, "数学")
        parent_uri = self.get_existing_class_uri(parent_label)
        if parent_uri:
            return parent_uri
        return "http://edukg.org/knowledge/0.1/class/math#math"

    def infer_all(
        self,
        concepts_path: str,
        output_classes_path: str,
        output_concepts_path: str,
        verbose: bool = False,
    ) -> Dict[str, Any]:
        """
        推断所有新增概念的 Class

        Args:
            concepts_path: concepts_v3.json 路径
            output_classes_path: classes 输出路径
            output_concepts_path: 更新后的 concepts 输出路径
            verbose: 显示进度

        Returns:
            统计信息
        """
        # 加载概念
        with open(concepts_path, encoding="utf-8") as f:
            data = json.load(f)

        concepts = data.get("concepts", [])
        new_concepts = [c for c in concepts if not c.get("is_existing", True)]

        if verbose:
            print(f"共 {len(new_concepts)} 个新增概念需要推断 Class")

        # 推断
        new_classes = {}
        stats = {
            "total_new_concepts": len(new_concepts),
            "matched_existing_class": 0,
            "suggested_new_class": 0,
        }

        for i, concept in enumerate(new_concepts):
            label = concept["label"]

            if verbose:
                print(f"[{i+1}/{len(new_concepts)}] 推断: {label}")

            result = self.infer_class(label)
            class_label = result.get("class", "数学概念")
            suggest_new = result.get("suggest_new", False)

            if suggest_new:
                # 新 Class
                if class_label not in new_classes:
                    parent_uri = self.get_parent_uri(result.get("parent_class", "数学概念"))
                    class_uri = self.uri_generator.generate_class_uri(class_label)

                    new_classes[class_label] = {
                        "uri": class_uri,
                        "id": class_uri.split("#")[1],
                        "label": class_label,
                        "parents": [parent_uri],
                        "type": "owl:Class",
                    }
                    if verbose:
                        print(f"  → 新 Class: {class_label}")

                stats["suggested_new_class"] += 1
                concept["inferred_class"] = class_label
                concept["inferred_class_uri"] = new_classes[class_label]["uri"]
                concept["is_new_class"] = True

            else:
                # 已有 Class
                class_uri = self.get_existing_class_uri(class_label)
                if class_uri:
                    concept["inferred_class"] = class_label
                    concept["inferred_class_uri"] = class_uri
                    concept["is_new_class"] = False
                    stats["matched_existing_class"] += 1
                    if verbose:
                        print(f"  → 已有 Class: {class_label}")
                else:
                    # Class 不存在，创建新的
                    if class_label not in new_classes:
                        parent_uri = self.get_parent_uri(class_label)
                        class_uri = self.uri_generator.generate_class_uri(class_label)
                        new_classes[class_label] = {
                            "uri": class_uri,
                            "id": class_uri.split("#")[1],
                            "label": class_label,
                            "parents": [parent_uri],
                            "type": "owl:Class",
                        }
                    concept["inferred_class"] = class_label
                    concept["inferred_class_uri"] = new_classes[class_label]["uri"]
                    concept["is_new_class"] = True

        # 保存 classes
        output_classes_path = Path(output_classes_path)
        output_classes_path.parent.mkdir(parents=True, exist_ok=True)

        classes_data = {
            "subject": "math",
            "subject_name": "数学",
            "class_count": len(new_classes),
            "classes": list(new_classes.values()),
        }

        with open(output_classes_path, "w", encoding="utf-8") as f:
            json.dump(classes_data, f, ensure_ascii=False, indent=2)

        # 保存更新后的 concepts
        output_concepts_path = Path(output_concepts_path)
        output_concepts_path.parent.mkdir(parents=True, exist_ok=True)

        data["metadata"]["class_inference_stats"] = stats
        data["metadata"]["new_classes_count"] = len(new_classes)

        with open(output_concepts_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        if verbose:
            print(f"\n=== Step 5: Class 推断完成 ===")
            print(f"新增概念: {stats['total_new_concepts']}")
            print(f"匹配已有 Class: {stats['matched_existing_class']}")
            print(f"创建新 Class: {stats['suggested_new_class']}")
            print(f"输出文件: {output_classes_path}")

        return stats


# 命令行入口
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Step 5: Class 类型推断")
    parser.add_argument("--concepts", default="concepts_v3.json", help="输入文件")
    parser.add_argument("--output-classes", default="classes_v3.json", help="Class 输出文件")
    parser.add_argument("--output-concepts", default="concepts_with_class.json", help="概念输出文件")
    parser.add_argument("--verbose", action="store_true", help="显示详细输出")

    args = parser.parse_args()

    inferrer = ClassInferrer()
    inferrer.infer_all(
        concepts_path=args.concepts,
        output_classes_path=args.output_classes,
        output_concepts_path=args.output_concepts,
        verbose=args.verbose,
    )