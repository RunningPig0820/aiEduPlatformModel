# 坑档案 K5 评测集 jsonl 被 gitignore 挡 复盘

> summary: 评测集 gitignore 复盘
> 来源: 切片 ｜ 锚点: 坑点复盘与口述
> 节: 坑档案 K5 评测集 jsonl 被 gitignore 挡
> COS路径: rag-slices/interview/rag-system/坑档案/坑档案-K5-评测集gitignore-复盘.md
> 类别：开发难点（9 视角闭集）
> target: 面试项目问答

---

## 坑点复盘
**现象**：评测集 jsonl 文件无法提交进 git——`data/` 整目录被 .gitignore 忽略，git add 被挡。

**触发链路**：评测集放在 data 目录下 → .gitignore 把 data/ 整目录按"大文件"忽略 → 该入库的小配置（评测集）被误伤，提交不了。

**根因**：.gitignore 的 data/ 规则是给大文件设计的，但一竿子打死，误伤了需要入库的评测集小文件。

**解决思路与权衡**：改成 `data/*` + 例外放行 `data/eval/`——大文件仍忽略、评测集强制入库。权衡点：把"运行时产物忽略、固定配置入库"的边界在 ignore 规则里显式表达，语义清晰。

## 面试口述要点
评测集 jsonl 被 .gitignore 挡住无法提交——data/ 整目录规则按"大文件"设计，误伤了该入库的评测集。解法是 `data/*` + `!data/eval/` 例外，大文件仍忽略、评测集强制入库。教训是 ignore 规则要区分"运行时产物"和"固定配置"，别用一刀切目录规则。

> 证据：详见 `5.难点/坑档案-开发与验证.md`（K5）｜ `3.代码/分析-06-评测.md` ｜ `4.完善文档/08-数据规模与指标.md`
