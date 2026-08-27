# 坑档案-J-KG12-年级查询DISTINCT冲突

> summary: 年级查询DISTINCT冲突
> 来源: 坑档案 ｜ 锚点: J-KG12 ｜ 节: 5.难点/坑档案.md
> COS路径: rag-slices/knowledge-graph/坑档案/坑档案-J-KG12-年级查询DISTINCT冲突.md
> 类别：开发难点
> target: 开发对账

---

**1. 问题现象**：知识图谱年级下拉查询报 `ERROR 3065`——`Expression #1 of ORDER BY clause is not in SELECT list... conflicts with DISTINCT`，年级列表接口直接 500。

**2. 触发流程**：前端打开图谱总览 → Java 查该 subject 下的去重年级列表 → `SELECT DISTINCT grade FROM t_kg_textbook ... ORDER BY sort`。

**3. 根因分析**：数据库 `sql_mode` 含 `ONLY_FULL_GROUP_BY` 时，`DISTINCT` 与 `ORDER BY sort`（sort 不在 DISTINCT 列中）冲突。提交 `04a9c60` 信息："sql_mode 含 ONLY_FULL_GROUP_BY 时 ORDER BY 引用非 SELECT 列与 DISTINCT 冲突(ERROR 3065)"。

**4. 排查过程**：接口 500 日志报 ERROR 3065；确认线上 MySQL sql_mode 含 ONLY_FULL_GROUP_BY；对比本地（无此 sql_mode）复现不了——**环境相关 bug**。

**5. 解决方案 & 改动点**：`selectDistinctGradesBySubject / selectDistinctGradesByEditionSubject` 改为 `GROUP BY grade ORDER BY MIN(sort)`（`ai-edu-backend/ai-edu-infrastructure/src/main/java/com/ai/edu/infrastructure/persistence/edukg/mapper/KgTextbookMapper.java:33-34,43-44`）——用聚合函数 `MIN(sort)` 表达"按组内最小 sort 排序"，兼容 ONLY_FULL_GROUP_BY。实测去重 23→14 且按教材 sort 排序正确。提交：`04a9c60 [知识点]-[kg-textbook-sort]`。

**6. 面试口述要点**：SQL 的"本地能跑线上挂"多半是 `sql_mode` 差异——`ONLY_FULL_GROUP_BY` 是线上 MySQL 5.7+ 默认。`DISTINCT + ORDER BY 非选择列` 这种写法不具可移植性，改成 `GROUP BY + 聚合函数排序`（`ORDER BY MIN(sort)`）是标准解法。面试可讲"先确认环境差异、再改 SQL 兼容写法"的排查路径。
