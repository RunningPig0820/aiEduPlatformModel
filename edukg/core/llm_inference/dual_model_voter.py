"""
双模型投票核心模块

支持 GLM-4-flash + DeepSeek 两模型投票，用于前置关系推断和知识点匹配。
"""
import asyncio
import json
import logging
import re
from typing import Dict, Any, Optional, Tuple, List

from edukg.core.llm_inference.config import (
    PRIMARY_MODEL,
    SECONDARY_MODEL,
    CONFIDENCE_THRESHOLD_HIGH,
    CONFIDENCE_THRESHOLD_LOW,
    RATE_LIMIT_DELAY,
    MAX_RETRIES,
    RETRY_DELAY,
)

logger = logging.getLogger(__name__)


class LLMCallError(Exception):
    """LLM 调用错误"""
    pass


class DualModelVoter:
    """
    双模型投票器

    使用 GLM-4-flash（主模型）+ DeepSeek（副模型）进行投票，
    两模型一致才采纳结果。

    使用方法:
        voter = DualModelVoter()
        result = await voter.vote(prompt)
        if result['consensus']:
            print(f"投票结果: {result['result']}, 置信度: {result['confidence']}")
    """

    def __init__(
        self,
        primary_model: str = PRIMARY_MODEL,
        secondary_model: str = SECONDARY_MODEL,
        llm_gateway: Any = None
    ):
        """
        初始化双模型投票器

        Args:
            primary_model: 主模型名称（默认: glm-4-flash）
            secondary_model: 副模型名称（默认: deepseek-chat）
            llm_gateway: LLM Gateway 实例（可选，不传则延迟加载）
        """
        self.primary_model = primary_model
        self.secondary_model = secondary_model
        self._llm_gateway = llm_gateway

    def _get_llm_gateway(self):
        """
        获取 LLM Gateway 实例

        优先使用构造函数注入的实例，否则延迟加载。
        延迟加载可以避免模块加载时的循环依赖。
        """
        if self._llm_gateway is None:
            # 动态导入 LLM Gateway
            try:
                from ai_edu_ai_service.core.gateway.factory import LLMFactory
                self._llm_gateway = LLMFactory()
            except ImportError:
                logger.warning("无法导入 LLM Gateway，使用模拟模式")
                self._llm_gateway = None
        return self._llm_gateway

    async def _call_llm(self, model_name: str, prompt: str) -> Dict[str, Any]:
        """
        调用单个 LLM 模型

        Args:
            model_name: 模型名称
            prompt: Prompt 文本

        Returns:
            模型响应结果

        Raises:
            LLMCallError: LLM 调用失败
        """
        gateway = self._get_llm_gateway()

        if gateway is None:
            # 模拟模式（用于测试）
            logger.warning(f"模拟调用 {model_name}")
            return await self._mock_call(model_name, prompt)

        try:
            # 使用 LangChain 调用
            from langchain_core.messages import HumanMessage

            # 创建 ChatModel
            chat_model = gateway.create_chat_model(model_name)

            # 调用模型
            response = await chat_model.ainvoke([HumanMessage(content=prompt)])

            return {
                "model": model_name,
                "content": response.content,
                "success": True
            }

        except Exception as e:
            logger.error(f"{model_name} 调用失败: {e}")
            raise LLMCallError(f"{model_name} 调用失败: {e}")

    async def _mock_call(self, model_name: str, prompt: str) -> Dict[str, Any]:
        """
        模拟 LLM 调用（用于测试）

        Args:
            model_name: 模型名称
            prompt: Prompt 文本

        Returns:
            模拟响应结果
        """
        # 模拟延迟
        await asyncio.sleep(0.1)

        # 返回模拟结果
        return {
            "model": model_name,
            "content": '{"is_prerequisite": true, "confidence": 0.8, "reason": "模拟响应"}',
            "success": True
        }

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

        logger.warning(f"无法解析 JSON 响应: {content[:100]}...")
        return None

    async def vote(self, prompt: str) -> Dict[str, Any]:
        """
        两模型投票

        Args:
            prompt: Prompt 文本

        Returns:
            {
                'consensus': bool,       # 是否达成一致
                'result': Any,           # 投票结果（JSON）
                'confidence': float,     # 置信度（取两模型的平均值）
                'primary_response': Dict, # 主模型响应
                'secondary_response': Dict # 副模型响应
            }
        """
        # 并行调用两个模型
        try:
            primary_response, secondary_response = await asyncio.gather(
                self._call_llm(self.primary_model, prompt),
                self._call_llm(self.secondary_model, prompt)
            )
        except LLMCallError as e:
            logger.error(f"投票失败: {e}")
            return {
                'consensus': False,
                'result': None,
                'confidence': 0.0,
                'primary_response': None,
                'secondary_response': None,
                'error': str(e)
            }

        # 解析响应
        primary_result = self._parse_json_response(primary_response['content'])
        secondary_result = self._parse_json_response(secondary_response['content'])

        if primary_result is None or secondary_result is None:
            logger.warning("响应解析失败")
            return {
                'consensus': False,
                'result': None,
                'confidence': 0.0,
                'primary_response': primary_response,
                'secondary_response': secondary_response,
                'error': '响应解析失败'
            }

        # 检查一致性和计算置信度
        return self._check_consensus(primary_result, secondary_result, primary_response, secondary_response)

    def _check_consensus(
        self,
        primary_result: Dict,
        secondary_result: Dict,
        primary_response: Dict,
        secondary_response: Dict
    ) -> Dict[str, Any]:
        """
        检查两模型是否达成一致

        Args:
            primary_result: 主模型解析结果
            secondary_result: 副模型解析结果
            primary_response: 主模型原始响应
            secondary_response: 副模型原始响应

        Returns:
            投票结果字典
        """
        # 提取关键判断
        primary_decision = primary_result.get('is_prerequisite', primary_result.get('is_match', None))
        secondary_decision = secondary_result.get('is_prerequisite', secondary_result.get('is_match', None))

        primary_confidence = primary_result.get('confidence', 0.5)
        secondary_confidence = secondary_result.get('confidence', 0.5)

        # 检查是否一致
        consensus = (primary_decision == secondary_decision and primary_decision is not None)

        if consensus:
            # 一致时，取置信度平均值
            avg_confidence = (primary_confidence + secondary_confidence) / 2

            # 构建结果
            result = {
                'decision': primary_decision,
                'confidence': avg_confidence,
                'primary_reason': primary_result.get('reason', ''),
                'secondary_reason': secondary_result.get('reason', ''),
            }

            # 添加其他字段（dependencies 等）
            for key in ['dependencies']:
                if key in primary_result:
                    result[key] = primary_result[key]

            return {
                'consensus': True,
                'result': result,
                'confidence': avg_confidence,
                'primary_response': primary_response,
                'secondary_response': secondary_response,
            }
        else:
            # 不一致，不采纳
            return {
                'consensus': False,
                'result': None,
                'confidence': 0.0,
                'primary_response': primary_response,
                'secondary_response': secondary_response,
                'error': '两模型判断不一致'
            }

    def vote_prerequisite(
        self,
        glm_result: Dict,
        deepseek_result: Dict
    ) -> Optional[Tuple[str, float]]:
        """
        前置关系投票规则

        规则:
        - 两模型一致 + confidence >= 0.8 → PREREQUISITE
        - 两模型一致 + confidence >= 0.6 → PREREQUISITE_CANDIDATE
        - 两模型不一致 → None（不采纳）

        Args:
            glm_result: GLM 模型结果
            deepseek_result: DeepSeek 模型结果

        Returns:
            (relation_type, confidence) 或 None
        """
        glm_decision = glm_result.get('is_prerequisite')
        deepseek_decision = deepseek_result.get('is_prerequisite')

        glm_confidence = glm_result.get('confidence', 0.0)
        deepseek_confidence = deepseek_result.get('confidence', 0.0)

        # 必须都认为是前置关系才采纳
        if glm_decision != True or deepseek_decision != True:
            return None

        # 计算平均置信度
        avg_confidence = (glm_confidence + deepseek_confidence) / 2

        # 分类
        if avg_confidence >= CONFIDENCE_THRESHOLD_HIGH:
            return ("PREREQUISITE", avg_confidence)
        elif avg_confidence >= CONFIDENCE_THRESHOLD_LOW:
            return ("PREREQUISITE_CANDIDATE", avg_confidence)
        else:
            return None

    def vote_match(
        self,
        glm_result: Dict,
        deepseek_result: Dict
    ) -> Optional[Tuple[bool, float]]:
        """
        知识点匹配投票规则

        规则:
        - 两模型一致 + confidence >= 0.7 → 匹配成功
        - 两模型不一致 → None（不采纳）

        Args:
            glm_result: GLM 模型结果
            deepseek_result: DeepSeek 模型结果

        Returns:
            (is_match, confidence) 或 None
        """
        glm_decision = glm_result.get('is_match')
        deepseek_decision = deepseek_result.get('is_match')

        glm_confidence = glm_result.get('confidence', 0.0)
        deepseek_confidence = deepseek_result.get('confidence', 0.0)

        # 必须都认为匹配才采纳
        if glm_decision != True or deepseek_decision != True:
            return None

        # 计算平均置信度
        avg_confidence = (glm_confidence + deepseek_confidence) / 2

        return (True, avg_confidence)


async def vote_with_retry(
    voter: DualModelVoter,
    prompt: str,
    max_retries: int = MAX_RETRIES,
    retry_delay: float = RETRY_DELAY
) -> Dict[str, Any]:
    """
    带重试的投票

    Args:
        voter: DualModelVoter 实例
        prompt: Prompt 文本
        max_retries: 最大重试次数
        retry_delay: 重试间隔（秒）

    Returns:
        投票结果
    """
    for attempt in range(max_retries):
        try:
            result = await voter.vote(prompt)

            # 如果达成一致，直接返回
            if result['consensus']:
                return result

            # 如果是解析失败，重试
            if result.get('error') == '响应解析失败':
                logger.warning(f"解析失败，重试 ({attempt + 1}/{max_retries})")
                await asyncio.sleep(retry_delay)
                continue

            # 如果是判断不一致，不重试
            return result

        except Exception as e:
            logger.warning(f"投票异常，重试 ({attempt + 1}/{max_retries}): {e}")
            await asyncio.sleep(retry_delay)

    # 所有重试失败
    return {
        'consensus': False,
        'result': None,
        'confidence': 0.0,
        'error': '重试次数耗尽'
    }