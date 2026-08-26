# design-python-ai-tutoring

> summary: 解决拍题OCR前置预处理及百度OCR接口适配问题
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: 11. 拍题 OCR 前置
> 模块: ai-tutoring ｜ 节: design-python-ai-tutoring
> COS路径: ai-tutoring/rag-slices/OpenSpec/design-python-ai-tutoring-11-拍题-OCR-前置.md
> 类别：操作流程

---

### 11. 拍题 OCR 前置

照片 → OCR 识别题目文本 → **学生确认/修改** → 作为对话历史**首条 user 消息**进答疑(当前题目由 Python 从 history 推断,见决策 13)。OCR 是答疑之前的独立预处理,不进 decide/generate 契约。数学公式 OCR 质量是公认痛点,识别结果必须让学生确认。
- **实现发现(task 7.1)**:用**百度 OAuth access_token + general_basic REST 接口**(httpx),而非 baidu-aip 的 `AipOcr` —— 后者强制要求 APP_ID 而当前 env 只有 API_KEY+SECRET_KEY(且 baidu-aip 未安装)。access_token 按 expires_in 缓存,避免每请求拉取。`settings.py` 补充 `BAIDU_OCR_API_KEY/SECRET_KEY` 字段
