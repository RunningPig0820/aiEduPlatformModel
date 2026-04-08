"""
Class 提取服务

使用 LLM 推断知识点类型，生成符合 Neo4j 导入格式的 classes.json
支持 LLM 缓存，避免重复调用
支持断点续传和进度追踪

状态文件: state/step_3_class_inference.json
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


# 步骤3的状态文件名
STEP_3_STATE_ID = "step_3_class_inference"


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


@dataclass
class ClassExtractionResult:
    """Class 提取结果"""
    knowledge_point: str
    class_label: str
    confidence: float
    is_new_class: bool
    parent_class: Optional[str] = None
    reason: str = ""


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


class ClassExtractor:
    """
    Class 提取器

    使用 LLM 推断知识点类型，支持：
    1. 匹配现有 Class
    2. 建议新增 Class
    3. 生成符合 Neo4j 格式的 classes.json

    状态文件: state/step_3_class_inference.json
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
        初始化 Class 提取器

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

        # 加载现有 Class
        self.existing_classes = EXISTING_CLASSES
        self.class_parents = CLASS_PARENTS

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
        """获取步骤3的状态管理器"""
        return TaskState(STEP_3_STATE_ID, state_dir=self.state_dir)

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
            "task_id": STEP_3_STATE_ID,
            "status": state.get_status(),
            "progress": progress,
            "is_completed": state.is_completed(),
            "state_file": str(state.state_file),
        }

    def get_class_list_for_prompt(self) -> str:
        """
        获取 Class 列表用于 prompt

        Returns:
            格式化的 Class 列表字符串
        """
        return ", ".join([c["label"] for c in self.existing_classes])

    def _call_llm(self, prompt: str) -> dict:
        """
        调用 LLM 并解析响应

        Args:
            prompt: 提示词

        Returns:
            解析后的 JSON 字典
        """
        if not self.llm:
            # 如果没有 LLM，返回默认值
            return {
                "class": "数学概念",
                "confidence": 0.5,
                "reason": "未配置 LLM，使用默认类别",
            }

        # 使用 CachedLLM 或原始 LLM
        if isinstance(self.llm, CachedLLM):
            response = self.llm.invoke(prompt, use_cache=self.use_cache)
        else:
            response = self.llm.invoke([
                SystemMessage(content="你是一个数学教育专家。"),
                HumanMessage(content=prompt),
            ])

        # 解析 JSON
        if hasattr(response, 'content'):
            content = response.content
        else:
            content = str(response)

        # 尝试提取 JSON
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

        # 解析失败，返回默认值
        return {
            "class": "数学概念",
            "confidence": 0.5,
            "reason": f"LLM 响应解析失败: {content[:100]}",
        }

    def infer_type(
        self,
        knowledge_point: str,
        context: Optional[str] = None,
    ) -> ClassExtractionResult:
        """
        推断单个知识点的类型

        Args:
            knowledge_point: 知识点名称
            context: 可选的上下文信息

        Returns:
            ClassExtractionResult: 推断结果
        """
        class_list = self.get_class_list_for_prompt()

        prompt = CLASS_INFERENCE_PROMPT.format(
            class_list=class_list,
            knowledge_point=knowledge_point,
        )

        if context:
            prompt += f"\n\n上下文信息：{context}"

        # 如果使用 CachedLLM，需要把系统提示也加入 prompt
        if isinstance(self.llm, CachedLLM):
            full_prompt = f"你是一个数学教育专家。\n\n{prompt}"
        else:
            full_prompt = prompt

        result = self._call_llm(full_prompt)

        return ClassExtractionResult(
            knowledge_point=knowledge_point,
            class_label=result.get("class", "数学概念"),
            confidence=result.get("confidence", 0.5),
            is_new_class=result.get("suggest_new", False),
            parent_class=result.get("parent_class"),
            reason=result.get("reason", ""),
        )

    def batch_infer_types(
        self,
        knowledge_points: List[str],
        batch_size: int = 10,
        verbose: bool = False,
        resume: bool = False,
    ) -> List[ClassExtractionResult]:
        """
        批量推断知识点类型（支持断点续传）

        Args:
            knowledge_points: 知识点列表
            batch_size: 批次大小（每批作为一个 checkpoint）
            verbose: 是否显示进度
            resume: 是否从断点恢复

        Returns:
            提取结果列表
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
            pending_checkpoints = [f"batch_{i+1}" for i in range(total_batches)]

        results = []

        for batch_idx in range(total_batches):
            batch_id = f"batch_{batch_idx + 1}"

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
            batch_results = []
            batch_errors = []

            for kp in batch_kps:
                try:
                    result = self.infer_type(kp)
                    batch_results.append(result)
                except Exception as e:
                    batch_errors.append(str(e))
                    # 失败时使用默认值
                    batch_results.append(ClassExtractionResult(
                        knowledge_point=kp,
                        class_label="数学概念",
                        confidence=0.5,
                        is_new_class=False,
                        reason=f"推断失败: {str(e)}",
                    ))

            results.extend(batch_results)

            # 标记检查点完成
            if batch_errors:
                state.complete_checkpoint(batch_id, {
                    "batch_idx": batch_idx,
                    "kp_range": [start_idx, end_idx],
                    "errors": batch_errors,
                })
            else:
                state.complete_checkpoint(batch_id, {
                    "batch_idx": batch_idx,
                    "kp_range": [start_idx, end_idx],
                })

        if verbose:
            progress = state.get_progress()
            print(f"推断完成: {len(results)} 个知识点")
            if state.is_completed():
                print("所有批次已完成！")

        return results

    def generate_class_definition(
        self,
        label: str,
        parent_uri: str,
    ) -> dict:
        """
        生成 Class 定义

        Args:
            label: Class 标签
            parent_uri: 父类 URI

        Returns:
            Class 定义字典
        """
        uri = self.uri_generator.generate_class_uri(label)
        id_str = uri.split("#")[1]

        return {
            "uri": uri,
            "id": id_str,
            "subject": self.config.subject,
            "label": label,
            "description": label,
            "parents": [parent_uri],
            "type": "owl:Class",
        }

    def get_existing_class_uri(self, class_label: str) -> Optional[str]:
        """
        获取现有 Class 的 URI

        Args:
            class_label: Class 标签

        Returns:
            URI 或 None
        """
        for cls in self.existing_classes:
            if cls["label"] == class_label:
                return f"http://edukg.org/knowledge/0.1/class/math#{cls['id']}"
        return None

    def get_parent_uri(self, class_label: str) -> str:
        """
        获取父类 URI

        Args:
            class_label: Class 标签

        Returns:
            父类 URI
        """
        parent_label = self.class_parents.get(class_label, "数学")

        # 先查找现有 Class
        parent_uri = self.get_existing_class_uri(parent_label)
        if parent_uri:
            return parent_uri

        # 如果父类不存在，使用数学
        return self.get_existing_class_uri("数学") or "http://edukg.org/knowledge/0.1/class/math#math"

    def extract_classes_from_kps(
        self,
        knowledge_points: List[str],
        verbose: bool = False,
        resume: bool = False,
        batch_size: int = 10,
    ) -> List[dict]:
        """
        从知识点列表提取 Class（支持断点续传）

        Args:
            knowledge_points: 知识点列表
            verbose: 是否显示进度
            resume: 是否从断点恢复
            batch_size: 批次大小

        Returns:
            新增的 Class 定义列表
        """
        # 批量推断类型
        results = self.batch_infer_types(
            knowledge_points,
            verbose=verbose,
            resume=resume,
            batch_size=batch_size,
        )

        # 收集需要新增的 Class
        new_classes = {}
        for result in results:
            if result.is_new_class and result.class_label not in new_classes:
                # 获取父类 URI
                parent_uri = self.get_parent_uri(result.parent_class) if result.parent_class else self.get_parent_uri(result.class_label)

                new_classes[result.class_label] = self.generate_class_definition(
                    label=result.class_label,
                    parent_uri=parent_uri,
                )

        if verbose:
            print(f"推断完成: {len(results)} 个知识点，{len(new_classes)} 个新 Class")

        return list(new_classes.values())

    def save_classes(
        self,
        classes: list[dict],
        output_path: str,
    ) -> None:
        """
        保存 classes.json

        Args:
            classes: Class 列表
            output_path: 输出文件路径
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "subject": self.config.subject,
            "subject_name": "数学",
            "class_count": len(classes),
            "classes": classes,
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"Classes 已保存到: {output_path}")


# 命令行入口
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Class 提取 - 步骤3")
    parser.add_argument("--kps", help="知识点 JSON 文件（--status 时可选）")
    parser.add_argument("--output", default="classes.json", help="输出文件")
    parser.add_argument("--debug", action="store_true", help="调试模式")
    parser.add_argument("--resume", action="store_true", help="从断点恢复")
    parser.add_argument("--status", action="store_true", help="仅查看状态，不执行")
    parser.add_argument("--state-dir", default="state/", help="状态文件目录")
    parser.add_argument("--cache-dir", default="cache/", help="缓存目录")
    parser.add_argument("--batch-size", type=int, default=10, help="批次大小")

    args = parser.parse_args()

    # 创建提取器
    extractor = ClassExtractor(
        state_dir=args.state_dir,
        cache_dir=args.cache_dir,
    )

    # 仅查看状态
    if args.status:
        summary = extractor.get_status_summary()
        print(f"\n=== 步骤3: 类型推断状态 ===")
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
        data = json.load(f)

    # 提取知识点列表
    kps = []
    for stage in data.get("stages", []):
        for domain in stage.get("domains", []):
            kps.extend(domain.get("knowledge_points", []))

    # 去重
    kps = list(set(kps))

    # 从断点恢复时显示进度
    if args.resume:
        progress = extractor.get_progress()
        if progress['total'] > 0:
            print(f"从断点恢复: 已完成 {progress['completed']}/{progress['total']} 批")
        else:
            print("没有可恢复的状态，开始新任务")

    # 提取
    classes = extractor.extract_classes_from_kps(
        kps,
        verbose=True,
        resume=args.resume,
        batch_size=args.batch_size,
    )
    extractor.save_classes(classes, args.output)