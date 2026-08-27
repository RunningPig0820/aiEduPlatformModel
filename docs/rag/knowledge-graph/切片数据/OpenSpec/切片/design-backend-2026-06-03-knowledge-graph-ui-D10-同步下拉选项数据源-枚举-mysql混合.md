# D10：同步下拉选项数据源（枚举 + MySQL 混合）

> summary: 决策：同步对话框下拉用枚举+MySQL混合：学科/学段/教材来自Java枚举，年级从t_kg_textbook DISTINCT grade查询，首次需先全量同步。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-backend-2026-06-03-knowledge-graph-ui-D10-同步下拉选项数据源-枚举-mysql混合.md
> 类别：数据存储

> 检索摘要：决策：同步对话框下拉用枚举+MySQL混合：学科/学段/教材来自Java枚举，年级从t_kg_textbook DISTINCT grade查询，首次需先全量同步。

**决策**: 同步对话框中的下拉选项数据源采用**枚举 + MySQL 混合**方式：
- **学科列表**：在 Java 枚举类中定义（固定值，学科种类不会变化）
- **学段列表**：在 Java 枚举类中定义（小学/初中/高中，固定三个值）
- **教材列表**：在 Java 枚举类中定义（固定值，教材相对固定）
- **年级列表**：从 MySQL `t_kg_textbook` 表 `DISTINCT grade` 查询（年级取决于实际同步的教材数据）

**枚举类定义**：
```java
// 学科枚举
public enum KgSubjectEnum {
    MATH("math", "数学", 1),
    CHINESE("chinese", "语文", 2),
    ENGLISH("english", "英语", 3),
    PHYSICS("physics", "物理", 4),
    CHEMISTRY("chemistry", "化学", 5),
    BIOLOGY("biology", "生物", 6);

    private final String code;
    private final String label;
    private final int orderIndex;
}

// 学段枚举
public enum KgPhaseEnum {
    PRIMARY("primary", "小学", 1),
    MIDDLE("middle", "初中", 2),
    HIGH("high", "高中", 3);

    private final String code;
    private final String label;
    private final int orderIndex;
}

// 教材枚举
public enum KgTextbookEnum {
    PEP_MATH_PRIMARY_G1("pep-math-primary-g1-v1", "人教版小学数学一年级上册", "math", "一年级", "primary", 1),
    BSV_MATH_PRIMARY_G1("bsv-math-primary-g1-v1", "北师大版小学数学一年级上册", "math", "一年级", "primary", 2);

    private final String uri;
    private final String label;
    private final String subject;
    private final String grade;
    private final String phase;
    private final int orderIndex;
}
```

**同步前置要求**:
- 首次使用时，管理员需**先执行一次全量同步**，将 Neo4j 中的教材数据同步到 `t_kg_textbook`
- 全量同步完成后，年级下拉选项才有数据
- 学科和学段下拉选项始终可用（来自枚举）

**下拉选项 API**:
- `GET /api/kg/dimensions/subjects` → 从 `KgSubjectEnum` 枚举读取，按 orderIndex 排序
- `GET /api/kg/dimensions/grades` → `SELECT DISTINCT grade FROM t_kg_textbook WHERE status='active' ORDER BY grade`
- `GET /api/kg/dimensions/phases` → 从 `KgPhaseEnum` 枚举读取，按 orderIndex 排序
- `GET /api/kg/dimensions/textbooks` → 从 `KgTextbookEnum` 枚举读取，按 orderIndex 排序

> 证据：详见 `2.OpenSpec design 决策/design-backend-2026-06-03-knowledge-graph-ui.md`（§D10：同步下拉选项数据源（枚举 + MySQL 混合））
