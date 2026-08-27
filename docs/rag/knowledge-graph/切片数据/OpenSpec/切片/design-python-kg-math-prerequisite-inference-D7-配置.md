# D7：配置 (config.py)
> summary: 配置config.py：主模型glm-4-flash与副模型deepseek-chat，投票阈值0.8/0.6，批量BATCH_SIZE=10与断点续传保存间隔10。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-kg-math-prerequisite-inference-D7-配置.md
> 类别：数据关联

> 检索摘要：配置config.py：主模型glm-4-flash与副模型deepseek-chat，投票阈值0.8/0.6，批量BATCH_SIZE=10与断点续传保存间隔10。

```python
# 模型配置
PRIMARY_MODEL = "glm-4-flash"      # 免费
SECONDARY_MODEL = "deepseek-chat"  # DeepSeek-V3

# 投票阈值
CONFIDENCE_THRESHOLD_HIGH = 0.8
CONFIDENCE_THRESHOLD_LOW = 0.6

# 批量处理
BATCH_SIZE = 10
RATE_LIMIT_DELAY = 1.0

# 断点续传
CHECKPOINT_INTERVAL = 10  # 每 N 个保存进度
PROGRESS_DIR = "edukg/data/edukg/math/6_推理结果/output/progress/"
```

> 证据：详见 `2.OpenSpec design 决策/design-python-kg-math-prerequisite-inference.md`（§D7：配置 (config.py)）
