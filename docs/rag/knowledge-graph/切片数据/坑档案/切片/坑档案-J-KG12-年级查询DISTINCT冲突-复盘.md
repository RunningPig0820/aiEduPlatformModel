# 坑档案-J-KG12-年级查询DISTINCT冲突-复盘

> summary: 年级查询DISTINCT冲突复盘
> 来源: 切片 ｜ 锚点: 坑点复盘与口述
> 节: 坑档案 J-KG12 年级查询DISTINCT冲突
> COS路径: rag-slices/interview/knowledge-graph/坑档案/坑档案-J-KG12-年级查询DISTINCT冲突-复盘.md
> 类别：开发难点
> target: 面试项目问答

---

## 坑点复盘
**现象**：知识图谱年级下拉查询报 ERROR 3065——ORDER BY 子句引用非 SELECT 列与 DISTINCT 冲突，年级列表接口直接 500。

**触发链路**：前端打开图谱总览 → Java 查该学科下去重年级列表 → SELECT DISTINCT grade ... ORDER BY sort。

**根因**：线上数据库 sql_mode 含 ONLY_FULL_GROUP_BY 时，DISTINCT 与 ORDER BY sort（sort 不在 DISTINCT 列中）冲突；本地无此 sql_mode 复现不了——环境相关 bug。

**解决思路与权衡**：改成 GROUP BY grade ORDER BY MIN(sort)，用聚合函数表达"按组内最小 sort 排序"，兼容 ONLY_FULL_GROUP_BY；实测去重 23→14 且按教材 sort 排序正确。

## 面试口述要点
SQL 的"本地能跑线上挂"多半是 sql_mode 差异——ONLY_FULL_GROUP_BY 是线上 MySQL 5.7+ 默认。DISTINCT + ORDER BY 非选择列这种写法不具可移植性，改成 GROUP BY + 聚合函数排序（ORDER BY MIN(sort)）是标准解法。排查路径是先确认环境差异、再改 SQL 兼容写法。

> 证据：详见 `5.难点/坑档案.md`（J-KG12）｜ `3.代码/分析-11-Java同步与前端页面.md`
