# URI 命名规范 v3.1（edukg.org，分版本前缀）

> summary: 图谱节点 URI 怎么定？统一 http://edukg.org/knowledge/3.1/{type}/math#{id}，版本 v0.1 原始/v3.1 自建教材，ID 编码含出版社-年级-学期。
> 权威度: 0.8
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/语雀/语雀-决策记录-D4-URI命名规范v3.1.md
> 类别：架构设计

---

### D4 URI 命名规范 v3.1（edukg.org，分版本前缀）
> 检索摘要：图谱节点 URI 怎么定？统一 http://edukg.org/knowledge/3.1/{type}/math#{id}，版本 v0.1 原始/v3.1 自建教材，ID 编码含出版社-年级-学期。

| 属性 | 内容 |
|---|---|
| 背景 | 多来源节点需唯一标识，v0.1（EduKG 原始）与自建教材（v3.1）需区分 |
| 演进 | v0.1 → v0.2（小学新增，{拼音}-{md5}）→ v3.0（EduKG TTL 教材）→ v3.1（自建人教，代码常量 URI_VERSION="3.1"） |
| 拍板理由 | 正式数据一律 `edukg.org/knowledge/`（edukb.org 仅下载脚本/旧 TTL 兼容分析）；ID 编码 Textbook `renjiao-g1s`、Chapter `-1`、Section `-1-1`、KP `textbook-primary-00001` |
| 系统影响 | 所有节点带 URI 主键；URI 永不修改（改动走合并流程）；v3.2 预留新知识点/多版本教材 |
| 证据 | 证据：edukg/core/textbook/config.py:10-11 / design-python-2026-04-15-kg-math-complete-graph.md D8 |

> 证据：详见 `1.语雀/语雀-决策记录.md`（§D4）
