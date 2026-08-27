# 模块归属（DDD 域定位）

> summary: 方案业务落在 learning 域，派生 3 表+掌握度落 ai_edu_learning，解析管线在 infrastructure/ai/tutoring 集成层，权威图谱 Neo4j 归 edukg 域只读。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-backend-kp-matching-lightup-模块归属.md
> 类别：架构设计

> 检索摘要：方案业务落在 learning 域，派生 3 表+掌握度落 ai_edu_learning，解析管线在 infrastructure/ai/tutoring 集成层，权威图谱 Neo4j 归 edukg 域只读。

方案核心业务落在 **learning 域**；答疑入口与权威图谱边界如下：

| 组件 | 归属 | 说明 |
|------|------|------|
| 派生数据 3 表 + 掌握度 + 点亮 + 审核 | **learning 域** | 数据落 `ai_edu_learning`；掌握度本属 learning（knowledge mastery tracking） |
| 解析管线 `TutoringKpResolverImpl` | `infrastructure/ai/tutoring`（答疑 AI 集成层） | 跨域服务：消费答疑 label → 调用 learning 仓储 → 产物落 learning |
| 权威图谱 Neo4j + kg-sync 镜像 | **edukg 域（只读）** | 派生层只借 `kp_uri`，零写入 |

**learning 域 4 层落点**：

- domain：`com.ai.edu.domain.learning`（`DerivedKpObs` / `QuestionType` / `QuestionTypeKp` 实体 + 仓储接口）
- infrastructure：`com.ai.edu.infrastructure.persistence.learning`（MyBatis-Plus 实现 + Flyway）
- application：`com.ai.edu.application.service.learning`（聚合 / 维护服务）
- interface：`com.ai.edu.interfaces.api.learning`（resolve / pending / confirm / mastery 控制器）

> 注：`tutoring` 不是 domain 域，答疑 Java 网关在 `infrastructure/ai/tutoring`，属 AI 集成层而非业务域。

> 证据：详见 `2.OpenSpec design 决策/design-backend-kp-matching-lightup.md`（§模块归属（DDD 域定位））
