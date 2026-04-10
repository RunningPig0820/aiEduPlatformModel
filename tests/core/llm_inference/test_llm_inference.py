"""
LLM 推理模块单元测试

测试双模型投票和前置关系推断的核心逻辑。
"""
import pytest
import asyncio
import json
from unittest.mock import AsyncMock, patch, MagicMock

from edukg.core.llm_inference.dual_model_voter import (
    DualModelVoter,
    vote_with_retry,
    LLMCallError,
)
from edukg.core.llm_inference.prerequisite_inferer import (
    PrerequisiteInferer,
    estimate_inference_cost,
)


class TestDualModelVoter:
    """双模型投票器测试"""

    def test_init(self):
        """测试初始化"""
        voter = DualModelVoter()
        assert voter.primary_model == "glm-4-flash"
        assert voter.secondary_model == "deepseek-chat"

    def test_init_custom_models(self):
        """测试自定义模型初始化"""
        voter = DualModelVoter(
            primary_model="glm-4.5-air",
            secondary_model="deepseek-coder"
        )
        assert voter.primary_model == "glm-4.5-air"
        assert voter.secondary_model == "deepseek-coder"

    def test_parse_json_response(self):
        """测试 JSON 响应解析"""
        voter = DualModelVoter()

        # 直接 JSON
        content = '{"is_prerequisite": true, "confidence": 0.9, "reason": "测试"}'
        result = voter._parse_json_response(content)
        assert result['is_prerequisite'] == True
        assert result['confidence'] == 0.9

        # 带代码块
        content = '''
        ```json
        {"is_prerequisite": false, "confidence": 0.7, "reason": "测试"}
        ```
        '''
        result = voter._parse_json_response(content)
        assert result['is_prerequisite'] == False
        assert result['confidence'] == 0.7

        # 无效内容
        content = 'invalid content'
        result = voter._parse_json_response(content)
        assert result is None

    def test_vote_prerequisite(self):
        """测试前置关系投票规则"""
        voter = DualModelVoter()

        # 两模型一致，高置信度 → PREREQUISITE
        glm_result = {'is_prerequisite': True, 'confidence': 0.9}
        deepseek_result = {'is_prerequisite': True, 'confidence': 0.8}
        result = voter.vote_prerequisite(glm_result, deepseek_result)
        assert result[0] == "PREREQUISITE"
        assert abs(result[1] - 0.85) < 0.01

        # 两模型一致，中置信度 → PREREQUISITE_CANDIDATE
        glm_result = {'is_prerequisite': True, 'confidence': 0.7}
        deepseek_result = {'is_prerequisite': True, 'confidence': 0.6}
        result = voter.vote_prerequisite(glm_result, deepseek_result)
        assert result[0] == "PREREQUISITE_CANDIDATE"
        assert abs(result[1] - 0.65) < 0.01

        # 两模型不一致 → None
        glm_result = {'is_prerequisite': True, 'confidence': 0.9}
        deepseek_result = {'is_prerequisite': False, 'confidence': 0.8}
        result = voter.vote_prerequisite(glm_result, deepseek_result)
        assert result is None

        # GLM 认为不是前置关系 → None
        glm_result = {'is_prerequisite': False, 'confidence': 0.9}
        deepseek_result = {'is_prerequisite': True, 'confidence': 0.8}
        result = voter.vote_prerequisite(glm_result, deepseek_result)
        assert result is None

    def test_vote_match(self):
        """测试知识点匹配投票规则"""
        voter = DualModelVoter()

        # 两模型一致 → 匹配成功
        glm_result = {'is_match': True, 'confidence': 0.9}
        deepseek_result = {'is_match': True, 'confidence': 0.8}
        result = voter.vote_match(glm_result, deepseek_result)
        assert result[0] == True
        assert abs(result[1] - 0.85) < 0.01

        # 两模型不一致 → None
        glm_result = {'is_match': True, 'confidence': 0.9}
        deepseek_result = {'is_match': False, 'confidence': 0.8}
        result = voter.vote_match(glm_result, deepseek_result)
        assert result is None

    @pytest.mark.asyncio
    async def test_vote_mock_mode(self):
        """测试模拟模式下的投票"""
        voter = DualModelVoter()
        # 不设置 LLM Gateway，使用模拟模式

        prompt = "测试 Prompt"
        result = await voter.vote(prompt)

        # 模拟模式应该返回一致的结果
        assert result['consensus'] == True
        assert result['result']['decision'] == True
        assert result['confidence'] == 0.8


class TestPrerequisiteInferer:
    """前置关系推断器测试"""

    def test_init(self):
        """测试初始化"""
        inferer = PrerequisiteInferer()
        assert inferer.voter is not None

    def test_extract_from_definition(self):
        """测试定义依赖抽取"""
        inferer = PrerequisiteInferer()

        definition = "一元二次方程是指形如 ax² + bx + c = 0 的方程，其中 a、b、c 为常数。"
        kp_names = ["方程", "一元二次方程", "常数", "二次函数", "变量"]

        # 使用 min_length=2 以匹配 2 字符的知识点名称
        result = inferer.extract_from_definition(definition, kp_names, min_length=2)

        assert "方程" in result
        assert "一元二次方程" in result
        assert "常数" in result
        assert "二次函数" not in result  # 未出现在定义中

    def test_extract_from_definition_min_length(self):
        """测试最小长度过滤"""
        inferer = PrerequisiteInferer()

        definition = "这是一个测试定义"
        kp_names = ["测试", "是", "一", "定义"]  # "是" 和 "一" 太短

        result = inferer.extract_from_definition(definition, kp_names, min_length=2)

        assert "测试" in result
        assert "定义" in result
        assert "是" not in result
        assert "一" not in result

    def test_infer_from_textbook_order(self):
        """测试教材顺序推断"""
        inferer = PrerequisiteInferer()

        chapters = [
            {
                'id': 'chapter-1',
                'sections': [
                    {'id': 'section-1', 'order': 1, 'kps': [{'uri': 'kp-1', 'name': 'KP1'}]},
                    {'id': 'section-2', 'order': 2, 'kps': [{'uri': 'kp-2', 'name': 'KP2'}]},
                ]
            }
        ]

        results = inferer.infer_from_textbook_order(chapters)

        # section-1 在 section-2 前面，所以 kp-1 → kp-2 是 TEACHES_BEFORE
        assert len(results) == 1
        assert results[0]['relation_type'] == 'TEACHES_BEFORE'
        assert results[0]['kp_a_uri'] == 'kp-1'
        assert results[0]['kp_b_uri'] == 'kp-2'

    def test_estimate_inference_cost(self):
        """测试成本估算"""
        result = estimate_inference_cost(1000)

        assert result['kp_count'] == 1000
        assert result['estimated_pairs'] == 2000
        assert result['llm_calls'] == 4000
        assert 'estimated_cost_rmb' in result


class TestDAGValidation:
    """DAG 验证测试"""

    def test_no_cycle(self):
        """测试无环情况"""
        # 创建临时关系数据
        relations = [
            {'kp_a_uri': 'A', 'kp_b_uri': 'B', 'relation_type': 'PREREQUISITE', 'confidence': 0.9},
            {'kp_a_uri': 'B', 'kp_b_uri': 'C', 'relation_type': 'PREREQUISITE', 'confidence': 0.9},
            {'kp_a_uri': 'A', 'kp_b_uri': 'C', 'relation_type': 'PREREQUISITE', 'confidence': 0.8},
        ]

        from edukg.core.llm_inference.config import OUTPUT_DIR, FINAL_PREREQ_FILE
        import os

        # 保存临时文件
        output_dir = os.path.join(os.path.dirname(__file__), 'test_output')
        os.makedirs(output_dir, exist_ok=True)

        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(relations, f)
            temp_file = f.name

        # 验证
        from edukg.scripts.kg_inference.validate_dag import DAGValidator
        validator = DAGValidator()
        validator.load_relations(temp_file)

        cycles = validator.detect_cycles()
        assert len(cycles) == 0

        # 清理
        os.unlink(temp_file)

    def test_with_cycle(self):
        """测试有环情况"""
        relations = [
            {'kp_a_uri': 'A', 'kp_b_uri': 'B', 'relation_type': 'PREREQUISITE', 'confidence': 0.9},
            {'kp_a_uri': 'B', 'kp_b_uri': 'C', 'relation_type': 'PREREQUISITE', 'confidence': 0.9},
            {'kp_a_uri': 'C', 'kp_b_uri': 'A', 'relation_type': 'PREREQUISITE', 'confidence': 0.9},
        ]

        import tempfile
        import os

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(relations, f)
            temp_file = f.name

        from edukg.scripts.kg_inference.validate_dag import DAGValidator
        validator = DAGValidator()
        validator.load_relations(temp_file)

        cycles = validator.detect_cycles()
        assert len(cycles) > 0

        # 清理
        os.unlink(temp_file)


# 运行测试的命令
if __name__ == '__main__':
    pytest.main([__file__, '-v'])