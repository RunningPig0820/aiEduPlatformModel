# D9：前端对接：API 接口定义 + DTO 结构

> summary: 决策：后端负责API设计与DTO定义，前端同学按API文档开发；知识点详情DTO含2层父级（小节+章节）不过度展示。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-backend-2026-06-03-knowledge-graph-ui-D9-前端对接-api接口定义-dto结构.md
> 类别：架构设计

> 检索摘要：决策：后端负责API设计与DTO定义，前端同学按API文档开发；知识点详情DTO含2层父级（小节+章节）不过度展示。

**决策**: 后端负责 API 设计和 DTO 定义，前端同学根据 API 文档开发页面。

**知识点详情 DTO**：
```java
// 知识点详情 DTO - 包含 2 层父级
public class KgKnowledgePointDetailDTO {
    private String uri;           // URI 作为唯一标识
    private String label;
    private String difficulty;
    private String importance;
    private String cognitiveLevel;
    // 2 层父级，不过度展示
    private String sectionUri;
    private String sectionLabel;  // 直接父级：小节
    private String chapterUri;
    private String chapterLabel;  // 爷爷级：章节
}
```

> 证据：详见 `2.OpenSpec design 决策/design-backend-2026-06-03-knowledge-graph-ui.md`（§D9：前端对接：API 接口定义 + DTO 结构）
