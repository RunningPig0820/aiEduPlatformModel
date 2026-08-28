# 中价值 spec 归档（3 份，供对账/坑档案引用）

> 用途：**中价值证据**——接口契约与已知问题，RAG 语料不直接使用（太细给联调不给面试），但方案-代码对账与坑档案的关键引用源。
> 价值判定时间：2026-08-28。

| 文件 | 用途 | 引用方 |
|---|---|---|
| `api-java-rag-project-intro-assistant.md` | Java 网关侧接口契约（角色门/SSE 中继/turns 补查/source 代理） | 方案-代码对账（Java 侧落地核验） |
| `api-python-rag-project-intro-assistant.md` | Python 侧 `/api/rag/assistant/*` 契约（事件时序冻结/ask/guide/done 结构/归属定死） | 方案-代码对账（代码深读 分析-04/05/07 对账要点核验） |
| `known-issues-java-rag-project-intro-assistant.md` | 三端联调真实问题 7 条（切片打标/文档地址/COS 迁移/流程图缺失/功能内容缺失/引用位置/引导太随机/指代词硬路由 bug，含修复建议） | 坑档案（K# 候选）+ 对账（方案有/代码无 佐证） |

> 恢复为高价值：若后续将接口细节纳入 RAG 语料（问题7 明确"spec/api 太细不进"），可移回根目录，但当前维持中价值。
