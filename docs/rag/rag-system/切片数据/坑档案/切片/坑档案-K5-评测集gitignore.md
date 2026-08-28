# 坑档案 K5 评测集 jsonl 被 gitignore 挡

> summary: 评测集 jsonl 被 gitignore 挡：data/ 整目录忽略误伤该入库的小配置，改 `data/*` + `!data/eval/` 例外强制入库
> 权威度: 0.8 ｜ 来源: 坑档案 ｜ 锚点: K5. 评测集 jsonl 被 gitignore 挡
> 模块: rag-system ｜ 节: 坑档案
> COS路径: rag-slices/rag-system/坑档案/坑档案-K5-评测集gitignore.md
> 类别：开发难点
> target: 开发对账

---

**坑**：评测集 `data/eval/ai-tutoring.jsonl` 无法 `git add`——`data/` 整目录被 .gitignore 忽略（挡大文件 npz/jsonl）。
**根因**：`data/` 规则设计为"大文件"，但误伤了**该入库的小配置**（评测集）。
**解决**：改为 `data/*` + 例外 `!data/eval/`，大文件仍忽略、评测集强制入库——语义清晰（运行时产物忽略，固定配置入库）。
**证据**：`ea5fd03`
