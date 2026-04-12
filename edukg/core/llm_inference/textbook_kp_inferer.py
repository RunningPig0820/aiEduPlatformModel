"""
教学知识点推断器

从教材章节信息推断学生应掌握的知识点。
支持断点续传和 LLM 调用缓存。
"""
import asyncio
import json
import logging
import hashlib
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Set

from edukg.core.llm_inference import DualModelVoter
from edukg.core.llm_inference.prompt_templates import format_textbook_kg_prompt
from edukg.core.llmTaskLock import TaskState, ProcessLock, get_cache_key, save_cache, load_cache

logger = logging.getLogger(__name__)

# 默认进度目录
DEFAULT_PROGRESS_DIR = Path(__file__).parent.parent.parent / "data" / "edukg" / "math" / "5_教材目录(Textbook)" / "output" / "progress"


class TextbookKPInferer:
    """
    教学知识点推断器

    从教材章节信息推断学生应掌握的知识点。
    支持断点续传和 LLM 调用缓存。

    使用方法:
        inferer = TextbookKPInferer()
        result = await inferer.infer_section(
            stage="小学",
            grade="三年级",
            semester="上册",
            chapter_name="时、分、秒",
            section_name="秒的认识",
            existing_kps=[]
        )
    """

    def __init__(
        self,
        voter: DualModelVoter = None,
        progress_dir: Path = None,
        cache_dir: Path = None
    ):
        """
        初始化教学知识点推断器

        Args:
            voter: DualModelVoter 实例（可选，默认创建新实例）
            progress_dir: 进度文件目录
            cache_dir: LLM 缓存目录
        """
        self.voter = voter or DualModelVoter()
        self.progress_dir = progress_dir or DEFAULT_PROGRESS_DIR
        self.cache_dir = cache_dir or (self.progress_dir.parent / "llm_cache")

        # 确保目录存在
        self.progress_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # 任务状态管理
        self.task_state = TaskState(
            "infer_kp",
            state_dir=self.progress_dir
        )

        # 进程锁
        self.process_lock = ProcessLock(
            str(self.progress_dir / "infer_kp.lock")
        )

    def _make_section_id(
        self,
        stage: str,
        grade: str,
        semester: str,
        chapter_name: str,
        section_name: str
    ) -> str:
        """
        生成章节唯一 ID

        Args:
            stage: 学段
            grade: 年级
            semester: 册次
            chapter_name: 章节名称
            section_name: 小节名称

        Returns:
            唯一的 ID 字符串
        """
        combined = f"{stage}|{grade}|{semester}|{chapter_name}|{section_name}"
        return hashlib.md5(combined.encode()).hexdigest()[:16]

    def _get_cached_result(self, prompt: str) -> Optional[Dict]:
        """
        获取缓存的 LLM 结果

        Args:
            prompt: 提示词

        Returns:
            缓存的结果或 None
        """
        cache_key = get_cache_key(prompt)
        return load_cache(cache_key, self.cache_dir)

    def _save_cached_result(self, prompt: str, result: Dict):
        """
        保存 LLM 结果到缓存

        Args:
            prompt: 提示词
            result: 结果数据
        """
        cache_key = get_cache_key(prompt)
        save_cache(cache_key, result, self.cache_dir, prompt=prompt)

    def _parse_json_response(self, content: str) -> Optional[Dict]:
        """
        解析 JSON 响应

        Args:
            content: LLM 返回的文本内容

        Returns:
            解析后的 JSON 字典，解析失败返回 None
        """
        # 尝试直接解析
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        # 尝试提取 JSON 块
        json_pattern = r'\{[^{}]*\}'
        matches = re.findall(json_pattern, content)
        for match in matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue

        # 尝试提取 ```json ``` 块中的内容
        json_block_pattern = r'```json\s*(.*?)\s*```'
        match = re.search(json_block_pattern, content, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        # 尝试解析 Python dict 格式（单引号）
        try:
            import ast
            dict_pattern = r'\{.*\}'
            match = re.search(dict_pattern, content, re.DOTALL)
            if match:
                return ast.literal_eval(match.group(0))
        except (SyntaxError, ValueError):
            pass

        logger.warning(f"无法解析 JSON 响应: {content[:100]}...")
        return None

    async def infer_section(
        self,
        stage: str,
        grade: str,
        semester: str,
        chapter_name: str,
        section_name: str,
        existing_kps: List[str] = None,
        use_cache: bool = True
    ) -> Dict:
        """
        推断单个小节的教学知识点

        Args:
            stage: 学段（小学/初中/高中）
            grade: 年级（一年级/七年级/必修第一册）
            semester: 册次（上册/下册）
            chapter_name: 章节名称
            section_name: 小节名称
            existing_kps: 已有知识点列表
            use_cache: 是否使用缓存

        Returns:
            {
                'knowledge_points': [...],
                'confidence': 0.0-1.0,
                'notes': '推断依据',
                'from_cache': bool
            }
        """
        existing_kps = existing_kps or []

        # 格式化 Prompt
        prompt = format_textbook_kg_prompt(
            stage=stage,
            grade=grade,
            semester=semester,
            chapter_name=chapter_name,
            section_name=section_name,
            existing_kps=existing_kps
        )

        # 检查缓存
        if use_cache:
            cached_result = self._get_cached_result(prompt)
            if cached_result:
                logger.debug(f"使用缓存结果: {section_name}")
                cached_result['from_cache'] = True
                return cached_result

        # 执行投票
        vote_result = await self.voter.vote(prompt)

        if not vote_result['consensus']:
            logger.warning(f"推断失败（投票不一致）: {section_name}")
            return {
                'knowledge_points': existing_kps,
                'confidence': 0.0,
                'notes': '投票不一致，保留已有知识点',
                'error': vote_result.get('error', '两模型判断不一致')
            }

        # 解析结果
        result = vote_result['result']
        parsed = self._parse_json_response(str(result))

        if parsed is None:
            logger.warning(f"推断失败（解析失败）: {section_name}")
            return {
                'knowledge_points': existing_kps,
                'confidence': 0.0,
                'notes': '解析失败，保留已有知识点'
            }

        # 构建返回结果
        output = {
            'knowledge_points': parsed.get('knowledge_points', existing_kps),
            'confidence': parsed.get('confidence', 0.5),
            'notes': parsed.get('notes', ''),
            'from_cache': False
        }

        # 保存到缓存
        if use_cache:
            self._save_cached_result(prompt, output)

        return output

    async def infer_batch(
        self,
        sections: List[Dict],
        resume: bool = True,
        checkpoint_interval: int = 10
    ) -> List[Dict]:
        """
        批量推断教学知识点

        Args:
            sections: 章节列表，格式为 [{
                'stage': ..., 'grade': ..., 'semester': ...,
                'chapter_name': ..., 'section_name': ...,
                'existing_kps': [...], 'section_id': ...
            }, ...]
            resume: 是否支持断点续传
            checkpoint_interval: 每 N 个保存一次进度

        Returns:
            推断结果列表
        """
        results = []

        # 加载已完成的章节
        completed_ids: Set[str] = set()
        if resume:
            state = self.task_state.get_state()
            for checkpoint in state.get('checkpoints', []):
                if checkpoint.get('status') == 'completed':
                    result_data = checkpoint.get('result')
                    if result_data:
                        results.append(result_data)
                        completed_ids.add(result_data.get('section_id', ''))

        # 筛选待处理的章节
        pending_sections = [s for s in sections if s.get('section_id') not in completed_ids]

        if pending_sections:
            logger.info(f"开始推断 {len(sections)} 个章节，已完成 {len(completed_ids)}，待处理 {len(pending_sections)}")
        else:
            logger.info(f"所有 {len(sections)} 个章节已推断完成")
            return results

        # 初始化任务状态
        if not self.task_state.is_completed():
            self.task_state.start(total=len(pending_sections))

        # 使用进程锁保护
        with self.process_lock:
            processed_count = 0

            for section in pending_sections:
                section_id = section.get('section_id', '')

                # 显示进度
                processed_count += 1
                if processed_count % checkpoint_interval == 0 or processed_count == 1:
                    logger.info(f"进度: {processed_count}/{len(pending_sections)} ({processed_count / len(pending_sections) * 100:.1f}%) - {section.get('section_name', '')}")

                # 执行推断
                result = await self.infer_section(
                    stage=section.get('stage', ''),
                    grade=section.get('grade', ''),
                    semester=section.get('semester', ''),
                    chapter_name=section.get('chapter_name', ''),
                    section_name=section.get('section_name', ''),
                    existing_kps=section.get('existing_kps', [])
                )

                # 添加元数据
                result['section_id'] = section_id
                result['stage'] = section.get('stage', '')
                result['grade'] = section.get('grade', '')
                result['semester'] = section.get('semester', '')
                result['chapter_name'] = section.get('chapter_name', '')
                result['section_name'] = section.get('section_name', '')

                results.append(result)

                # 记录完成
                checkpoint_id = f"section_{section_id}"
                self.task_state.complete_checkpoint(checkpoint_id, result)

                # 定期保存进度
                if processed_count % checkpoint_interval == 0:
                    self.task_state._save_state()

            # 最终保存
            self.task_state._save_state()

        # 统计
        from_cache = sum(1 for r in results if r.get('from_cache'))
        avg_confidence = sum(r.get('confidence', 0) for r in results) / len(results) if results else 0

        logger.info(f"推断完成: 共 {len(results)} 个章节，缓存命中 {from_cache}，平均置信度 {avg_confidence:.2f}")

        return results

    def save_results(self, results: List[Dict], filepath: str):
        """
        保存推断结果

        Args:
            results: 推断结果列表
            filepath: 文件路径
        """
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        logger.info(f"保存推断结果: {filepath} ({len(results)} 条)")

    def show_progress(self):
        """显示当前进度"""
        state = self.task_state.get_state()
        progress = state.get('progress', {})

        logger.info("\n=== 当前进度 ===")
        logger.info(f"任务状态: {state.get('status', 'unknown')}")
        logger.info(f"总章节数: {progress.get('total', 0)}")
        logger.info(f"已完成: {progress.get('completed', 0)}")
        logger.info(f"待处理: {progress.get('pending', 0)}")

        if progress.get('completed', 0) > 0:
            logger.info(f"完成率: {progress['completed'] / progress.get('total', 1) * 100:.1f}%")