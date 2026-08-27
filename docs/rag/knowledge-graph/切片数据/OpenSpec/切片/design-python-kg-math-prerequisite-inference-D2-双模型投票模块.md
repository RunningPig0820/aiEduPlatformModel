# D2：双模型投票模块 (dual_model_voter.py)
> summary: 双模型投票模块：主模型glm-4-flash+副模型deepseek-chat，返回consensus/result/confidence；一致且置信度≥0.8为PREREQUISITE，<0.8为CANDIDATE，不一致不采纳。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-kg-math-prerequisite-inference-D2-双模型投票模块.md
> 类别：数据关联

> 检索摘要：双模型投票模块：主模型glm-4-flash+副模型deepseek-chat，返回consensus/result/confidence；一致且置信度≥0.8为PREREQUISITE，<0.8为CANDIDATE，不一致不采纳。

```python
class DualModelVoter:
    """双模型投票器"""

    def __init__(
        self,
        primary_model: str = "glm-4-flash",
        secondary_model: str = "deepseek-chat",
        llm_gateway: Any = None  # 支持依赖注入
    ):
        self.primary_model = primary_model
        self.secondary_model = secondary_model
        self._llm_gateway = llm_gateway

    async def vote(self, prompt: str) -> Dict:
        """
        两模型投票

        Returns:
            {
                'consensus': bool,       # 是否达成一致
                'result': Any,           # 投票结果
                'confidence': float,     # 置信度
                'primary_response': ..., # 主模型响应
                'secondary_response': ... # 副模型响应
            }
        """
```

**投票规则**：

| 两模型结果 | 置信度 | 状态 |
|------------|--------|------|
| 一致 | ≥ 0.8 | PREREQUISITE |
| 一致 | < 0.8 | PREREQUISITE_CANDIDATE |
| 不一致 | - | 不采纳 |

> 证据：详见 `2.OpenSpec design 决策/design-python-kg-math-prerequisite-inference.md`（§D2：双模型投票模块 (dual_model_voter.py)）
