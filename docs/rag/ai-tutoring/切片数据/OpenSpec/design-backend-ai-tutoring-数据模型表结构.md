# design-backend-ai-tutoring

> summary: 面试问AI答疑的数据模型，答属学习域用ai_edu_learning库
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: 数据模型（表结构）
> 模块: ai-tutoring ｜ 节: design-backend-ai-tutoring
> 类别：数据存储

---

## 数据模型（表结构）

> **域归属**：AI 答疑作为**学习域（learning bounded context）内的功能模块**落地（掌握度 / 错误事件是学习域核心数据）。三张表物理位于 **`ai_edu_learning`** 数据库；持久化层 Mapper 需 `@DS("learning")` 路由（`application.yml` 需新增 `learning` 数据源，见 tasks 11.1）。实现代码放 `com.ai.edu.domain.learning` 下的答疑子模块。
