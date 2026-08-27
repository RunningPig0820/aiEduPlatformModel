# Flyway 迁移脚本按库分组

> summary: Flyway 迁移脚本按库分组 db/migration/user 与 kg，知识图谱用自定义 Bean 创建第二个 Flyway 实例。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-backend-2026-06-03-knowledge-graph-datasource-D6-flyway-迁移脚本按库分组.md
> 类别：架构设计

---

### D6：Flyway 迁移脚本按库分组

> 检索摘要：Flyway 迁移脚本按库分组 db/migration/user 与 kg，知识图谱用自定义 Bean 创建第二个 Flyway 实例。

**决策**: 迁移脚本目录结构：
```
db/
├── migration/
│   ├── user/
│   │   └── V1__Init_Demo_Users.sql
│   └── kg/
│       └── V1__Init_Knowledge_Graph.sql
```

知识图谱的 Flyway 配置指定连接 `ai_edu_kg`：
```yaml
spring:
  flyway:
    enabled: false           # 用户库 Flyway（禁用）
    locations: classpath:db/migration/user

  flyway-kg:                 # 知识图谱 Flyway（自定义 Bean）
    enabled: false            # 当前禁用，手动执行
    locations: classpath:db/migration/kg
    url: ${KG_DB_URL}
```

由于 Spring Boot 仅支持一个原生 Flyway Bean，知识图谱的 Flyway 通过自定义配置类创建第二个 Bean。

> 证据：详见 `2.OpenSpec design 决策/design-backend-2026-06-03-knowledge-graph-datasource.md`（§D6）
