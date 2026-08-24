# design-python-ai-tutoring

> summary: 面试问答中介绍AI辅导模型配对的配置驱动规则
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: 6. 模型配对(配置驱动)
> 模块: ai-tutoring ｜ 节: design-python-ai-tutoring

---

### 6. 模型配对(配置驱动)

测试阶段 decide/generate 都用 deepseek-v4-flash 走流程(非免费,单次成本低);生产建议 decide=(zhipu, glm-4-flash)或(bailian, qwen-turbo)、generate=(bailian, qwen-math-turbo)。新增 env: `TUTORING_DECIDE_PROVIDER/MODEL`、`TUTORING_GENERATE_PROVIDER/MODEL`、温度。decide 是判断密集任务(判对错是硬判断),"快"= 同能力等级里选便宜的,不是选最便宜的。
