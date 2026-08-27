# D3：提示词文件化设计
> summary: 提示词文件化设计：从代码内联改为独立prompts/*.txt文件，PromptLoader支持文件加载与MySQL加载扩展，便于修改维护。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-kg-math-prerequisite-inference-D3-提示词文件化设计.md
> 类别：数据关联

> 检索摘要：提示词文件化设计：从代码内联改为独立prompts/*.txt文件，PromptLoader支持文件加载与MySQL加载扩展，便于修改维护。

**决策**: 提示词从代码内联改为独立文件，便于修改和后续扩展从 MySQL 加载。

```
edukg/core/llm_inference/prompts/
├── prerequisite.txt     # 前置关系推断
├── kp_match.txt         # 知识点匹配
├── definition_deps.txt  # 定义依赖抽取
└── textbook_kg.txt      # 教学知识点推断
```

**PromptLoader 类**：

```python
class PromptLoader:
    def load(self, name: str, use_cache: bool = True) -> str:
        """从文件加载提示词"""

    def _load_from_file(self, name: str) -> str:
        """从 prompts/{name}.txt 加载"""

    def _load_from_db(self, name: str) -> str:
        """从 MySQL 加载（TODO: 后续扩展）"""

    def format(self, template: str, **kwargs) -> str:
        """格式化提示词"""
```

> 证据：详见 `2.OpenSpec design 决策/design-python-kg-math-prerequisite-inference.md`（§D3：提示词文件化设计）
