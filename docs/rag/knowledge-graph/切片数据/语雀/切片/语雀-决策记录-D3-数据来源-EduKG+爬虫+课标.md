# 数据来源：EduKG TTL + main.ttl + 人教版爬虫 + 课标

> summary: 图谱数据从哪来？EduKG TTL 语义层 + main.ttl 教材出处 + 人教版爬虫补小初 + 课标/题库/好未来参考。
> 权威度: 0.8
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/语雀/语雀-决策记录-D3-数据来源-EduKG+爬虫+课标.md
> 类别：架构设计

---

### D3 数据来源：EduKG TTL + main.ttl + 人教版爬虫 + 课标
> 检索摘要：图谱数据从哪来？EduKG TTL 语义层 + main.ttl 教材出处 + 人教版爬虫补小初 + 课标/题库/好未来参考。

| 属性 | 内容 |
|---|---|
| 背景 | 单一数据源覆盖不全：main.ttl 只有高中教材标注（28,438 条），小学初中缺失 |
| 演进 | 早期仅 EduKG TTL → 演进为四类来源 |
| 拍板理由 | 开源低成本；人教版爬虫（教师之家）补小初教材目录；课标 2022/2017 作层级基准 |
| 系统影响 | 语义层（TTL v0.1）+ 教材结构层（爬虫+main.ttl）；全学科 56,391 知识点 |
| 证据 | 证据：语雀-方案设计1/2/3.md / design-python-2026-04-10-textbook-crawler.md |

> 证据：详见 `1.语雀/语雀-决策记录.md`（§D3）
