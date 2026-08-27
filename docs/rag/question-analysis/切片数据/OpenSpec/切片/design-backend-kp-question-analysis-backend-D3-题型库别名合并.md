# 题型库别名合并

> summary: 题型库别名合并：kp 分布重叠≥70% 判变体折叠进 canonical + 别名表，查询统一走别名，canonical 只增不改。
> 权威度: 0.7
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/OpenSpec/design-backend-kp-question-analysis-backend-D3-题型库别名合并.md
> 类别：数据关联

---

### D3：题型库别名合并——kp 分布重叠 → canonical + 别名表

> 检索摘要：题型库别名合并：kp 分布重叠≥70% 判变体折叠进 canonical + 别名表，查询统一走别名，canonical 只增不改。

#### 新表结构

新表 `t_kp_question_type_alias`（learning 库，V16 迁移）：

| 字段 | 类型 | 说明 |
|---|---|---|
| id | BIGINT PK | 自增 |
| alias_label | VARCHAR UNIQUE | 变体题型名（已归一化） |
| question_type_id | BIGINT FK | canonical 题型 |
| created_at | DATETIME | 审计 |

#### 聚合流程改造

聚合 `aggregateTopic` 建新 CANDIDATE 前改为：

```
① findByTopicLabelOrAlias(label)  命中 → 更新现有条目（现状，别名命中同样走到这）
② 未命中 → 与现有 CANDIDATE/STABLE 题型比 kp_uri 集合重叠：
      | 重叠 ≥ 70%（可配置）→ 视同变体：插入 alias + 本桶观测折叠进该条目
      |    kp 分布（upsert QuestionTypeKp 统计合并）+ updateStats
      | 无相似 → 新建 CANDIDATE（现状）
```

> 证据：详见 `2.OpenSpec design 决策/design-backend-kp-question-analysis-backend.md`（§D3）｜ 语雀-决策记录.md D22 ｜ 完善文档 06-题型动态聚集与向量.md
