"""
知识点标准化预处理模块

将教材知识点名称推断为标准数学概念名称，提高与 EduKG 的匹配率。

使用场景：
- 教材知识点："1-5的认识"、"连加连减"、"秒的认识"
- 推断结果：["数的认识", "自然数", "数字"] 或 ["连续运算", "加减混合"] 等
- 然后用标准名称去向量检索 EduKG

流程：
教材知识点 → LLM推断(标准名称) → 向量检索 → LLM投票 → 匹配结果

改进（采纳 DeepSeek 建议）：
- 使用 asyncio.Lock 保护并发访问
- 原子写入缓存文件（临时文件 + rename）
- 批量并发处理（gather + Semaphore）
"""

import asyncio
import json
import logging
import hashlib
import tempfile
import os
from pathlib import Path
from typing import Dict, List, Optional

from edukg.core.llm_inference import DualModelVoter

logger = logging.getLogger(__name__)

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent

# 缓存目录
CACHE_DIR = PROJECT_ROOT / "data" / "edukg" / "math" / "5_教材目录(Textbook)" / "output" / "normalizer_cache"

# 提示词文件
PROMPT_FILE = PROJECT_ROOT / "core" / "llm_inference" / "prompts" / "kp_normalizer.txt"


def load_prompt_template() -> str:
    """加载提示词模板"""
    if not PROMPT_FILE.exists():
        raise FileNotFoundError(f"提示词文件不存在: {PROMPT_FILE}")

    with open(PROMPT_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    # 提取模板部分（在 ## 提示词模板 之后的内容）
    import re
    match = re.search(r'## 提示词模板\s*\n(.*?)\n## 使用场景', content, re.DOTALL)
    if match:
        # 提取代码块中的模板
        template_block = match.group(1)
        code_match = re.search(r'```\n(.*?)\n```', template_block, re.DOTALL)
        if code_match:
            return code_match.group(1).strip()

    # 如果提取失败，返回原始内容
    return content


# 加载提示词模板
NORMALIZER_PROMPT_TEMPLATE = load_prompt_template()


class KPNormalizer:
    """
    知识点标准化器

    使用 LLM 将教材知识点名称推断为标准概念名称。
    """

    # 处理中的缓存键（防止并发重复）- 使用 Lock 保护
    _processing_keys: set = set()
    _lock: asyncio.Lock = None  # 延迟初始化，避免模块加载时创建

    def __init__(self, use_cache: bool = True):
        """
        初始化标准化器

        Args:
            use_cache: 是否启用缓存
        """
        self.voter = DualModelVoter()
        self.use_cache = use_cache

        if use_cache:
            CACHE_DIR.mkdir(parents=True, exist_ok=True)

        # 延迟初始化 Lock（首次使用时创建）
        if KPNormalizer._lock is None:
            KPNormalizer._lock = asyncio.Lock()

    def _get_cache_key(self, kp_name: str, stage: str, grade: str) -> str:
        """生成缓存键"""
        content = f"{kp_name}_{stage}_{grade}"
        return hashlib.md5(content.encode()).hexdigest()

    def _load_cache(self, cache_key: str) -> Optional[Dict]:
        """加载缓存"""
        if not self.use_cache:
            return None

        cache_file = CACHE_DIR / f"{cache_key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.warning(f"缓存文件损坏: {cache_file}")
                return None
        return None

    def _save_cache(self, cache_key: str, result: Dict):
        """
        保存缓存（原子写入）

        使用临时文件 + rename 实现原子写入，防止并发写入导致文件损坏。
        """
        if not self.use_cache:
            return

        cache_file = CACHE_DIR / f"{cache_key}.json"

        # 创建临时文件
        fd, tmp_path = tempfile.mkstemp(suffix='.json', dir=CACHE_DIR, text=True)
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            # 原子替换（POSIX rename 是原子操作）
            os.replace(tmp_path, cache_file)
        except Exception as e:
            # 清理临时文件
            try:
                os.unlink(tmp_path)
            except:
                pass
            logger.error(f"缓存写入失败: {e}")

    async def normalize(self, kp_name: str, stage: str, grade: str) -> Dict:
        """
        标准化单个知识点名称

        Args:
            kp_name: 教材知识点名称
            stage: 学段（小学/初中/高中）
            grade: 年级

        Returns:
            {
                "original": "1-5的认识",
                "concepts": ["自然数", "数", "整数"],
                "best_match": "自然数",  # 用于向量检索
                "confidence": 0.9,
                "reason": "...",
                "from_cache": True/False
            }
        """
        # 检查缓存（先不加锁快速路径）
        cache_key = self._get_cache_key(kp_name, stage, grade)
        cached = self._load_cache(cache_key)

        if cached:
            logger.debug(f"命中缓存: {kp_name}")
            cached["from_cache"] = True
            return cached.copy()  # 返回副本，防止修改缓存内容

        # 使用 Lock 保护并发访问
        need_wait = False
        async with KPNormalizer._lock:
            if cache_key in KPNormalizer._processing_keys:
                need_wait = True
            else:
                KPNormalizer._processing_keys.add(cache_key)

        if need_wait:
            # 等待其他协程完成，同时轮询缓存
            max_wait = 60  # 最大等待60秒（延长等待时间）
            waited = 0
            while waited < max_wait:
                await asyncio.sleep(0.1)
                waited += 0.1
                cached = self._load_cache(cache_key)
                if cached:
                    cached["from_cache"] = True
                    return cached.copy()
                async with KPNormalizer._lock:
                    if cache_key not in KPNormalizer._processing_keys:
                        # 前面处理失败（已释放标记），我们可以接手
                        KPNormalizer._processing_keys.add(cache_key)
                        break

            # 超时后检查：是否仍在处理中？
            async with KPNormalizer._lock:
                if cache_key in KPNormalizer._processing_keys:
                    # 其他协程仍在处理，放弃处理避免重复调用
                    logger.warning(f"等待超时，其他协程仍在处理: {kp_name}, 返回默认结果")
                    return {
                        "original": kp_name,
                        "concepts": [kp_name],
                        "best_match": kp_name,
                        "confidence": 0.0,
                        "reason": "等待超时，放弃处理避免重复",
                        "from_cache": False
                    }
                else:
                    # 其他协程已释放但无结果，接手处理
                    KPNormalizer._processing_keys.add(cache_key)

        # 构造提示词
        prompt = NORMALIZER_PROMPT_TEMPLATE.format(
            kp_name=kp_name,
            stage=stage,
            grade=grade
        )

        # 调用 LLM（只用 DeepSeek，标准更严格）
        try:
            response = await self.voter._call_llm(self.voter.secondary_model, prompt)

            # 解析结果（从 response.content 提取）
            llm_output = response.get("content", "")
            parsed = self._parse_result(llm_output)

            # 添加原始信息
            parsed["original"] = kp_name
            parsed["stage"] = stage
            parsed["grade"] = grade
            parsed["from_cache"] = False

            # 保存缓存
            self._save_cache(cache_key, parsed)

            return parsed

        except Exception as e:
            logger.error(f"标准化失败: {kp_name}, 错误: {e}")
            return {
                "original": kp_name,
                "concepts": [kp_name],  # 失败时返回原名称
                "best_match": kp_name,
                "confidence": 0.0,
                "reason": f"推断失败: {e}",
                "from_cache": False
            }
        finally:
            # 移除处理中标记（使用 Lock 保护）
            async with KPNormalizer._lock:
                KPNormalizer._processing_keys.discard(cache_key)

    def _parse_result(self, llm_output: str) -> Dict:
        """解析 LLM 输出"""
        import re

        # 尝试提取 JSON（可能包含多层嵌套）
        json_matches = re.findall(r'\{[^{}]*\}', llm_output)
        for json_str in json_matches:
            try:
                parsed = json.loads(json_str)
                if 'concepts' in parsed:
                    # 确保 best_match 存在
                    parsed.setdefault('best_match', parsed['concepts'][0] if parsed['concepts'] else '')
                    parsed.setdefault('confidence', 0.0)
                    parsed.setdefault('reason', '')
                    return parsed
            except:
                continue

        # 解析失败，返回默认
        return {
            "concepts": [],
            "best_match": "",
            "confidence": 0.0,
            "reason": "解析失败"
        }

    async def normalize_batch(self, kps: List[Dict], max_concurrent: int = 5) -> List[Dict]:
        """
        批量标准化（并发处理）

        Args:
            kps: 教材知识点列表
            max_concurrent: 最大并发数（默认5）

        Returns:
            标准化结果列表
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def _process_one(kp: Dict, index: int) -> Dict:
            async with semaphore:
                name = kp.get("label", "")
                stage = kp.get("stage", "")
                grade = kp.get("grade", "")

                logger.debug(f"处理 [{index}]: {name}")
                result = await self.normalize(name, stage, grade)
                return result

        # 并发处理所有知识点
        tasks = [_process_one(kp, i) for i, kp in enumerate(kps)]
        results = await asyncio.gather(*tasks)

        return results


async def demo_normalize():
    """演示标准化效果"""
    normalizer = KPNormalizer()

    # 测试案例
    test_cases = [
        ("1-5的认识", "小学", "一年级"),
        ("连加连减", "小学", "一年级"),
        ("秒的认识", "小学", "三年级"),
        ("平行四边形的性质", "初中", "八年级"),
        ("一元二次方程的解法", "初中", "九年级"),
    ]

    print("=== 知识点标准化演示 ===")
    print()

    for name, stage, grade in test_cases:
        result = await normalizer.normalize(name, stage, grade)

        print(f"教材: {name} ({stage} {grade})")
        print(f"最佳匹配: {result.get('best_match', '')}")
        print(f"候选概念: {result.get('concepts', [])}")
        print(f"置信度: {result.get('confidence', 0)}")
        print(f"理由: {result.get('reason', '')}")
        print(f"缓存: {result.get('from_cache', False)}")
        print()


if __name__ == "__main__":
    asyncio.run(demo_normalize())