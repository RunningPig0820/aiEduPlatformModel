# Mapper 扫描路径拆分

> summary: @MapperScan 拆分为两个 basePackages，edukg.mapper 路径指定 annotationClass 为 DS 注解。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-backend-2026-06-03-knowledge-graph-datasource-D5-mapper-扫描路径拆分.md
> 类别：架构设计

---

### D5：Mapper 扫描路径拆分

> 检索摘要：@MapperScan 拆分为两个 basePackages，edukg.mapper 路径指定 annotationClass 为 DS 注解。

**决策**: `@MapperScan` 拆分为两个：
```java
@SpringBootApplication
@MapperScan(basePackages = "com.ai.edu.infrastructure.persistence.mapper", annotationClass = DS.class)
@MapperScan(basePackages = "com.ai.edu.infrastructure.persistence.edukg.mapper")
public class AiEduPlatformApplication { ... }
```

> 证据：详见 `2.OpenSpec design 决策/design-backend-2026-06-03-knowledge-graph-datasource.md`（§D5）
