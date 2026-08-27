# application.yml 配置结构

> summary: application.yml 用 dynamic 多数据源配置声明 user 与 kg 两个数据源，primary=user 且 strict 严格模式开启。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-backend-2026-06-03-knowledge-graph-datasource-D4-application-yml-配置结构.md
> 类别：架构设计

---

### D4：application.yml 配置结构

> 检索摘要：application.yml 用 dynamic 多数据源配置声明 user 与 kg 两个数据源，primary=user 且 strict 严格模式开启。

```yaml
spring:
  datasource:
    dynamic:
      primary: user          # 默认数据源
      strict: true           # 严格模式：未匹配的数据源抛异常
      datasource:
        user:
          url: jdbc:mysql://gz-cdb-e8peyaxv.sql.tencentcdb.com:23316/ai_edu_user?...
          username: dev
          password: dev2026+
          driver-class-name: com.mysql.cj.jdbc.Driver
        kg:
          url: jdbc:mysql://gz-cdb-e8peyaxv.sql.tencentcdb.com:23316/ai_edu_kg?...
          username: dev
          password: dev2026+
          driver-class-name: com.mysql.cj.jdbc.Driver
      hikari:
        minimum-idle: 5
        maximum-pool-size: 20
```

> 证据：详见 `2.OpenSpec design 决策/design-backend-2026-06-03-knowledge-graph-datasource.md`（§D4）
