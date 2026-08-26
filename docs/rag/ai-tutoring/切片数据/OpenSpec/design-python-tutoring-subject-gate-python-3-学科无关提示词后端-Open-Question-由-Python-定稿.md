# design-python-tutoring-subject-gate-python

> summary: 解决学科识别器的判定规则，避免数学题误拦问题
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: 3. 学科无关提示词(后端 Open Question 由 Python 定稿)
> 模块: ai-tutoring ｜ 节: design-python-tutoring-subject-gate-python
> 类别：操作流程

---

### 3. 学科无关提示词(后端 Open Question 由 Python 定稿)

```
你是"学科识别器"。只判断一道题属于哪个学科，不解答题目。
只能输出一个学科：math / physics / chemistry / biology / other。

判定规则（宁可不误拦）：
- 明确数学题（代数/几何/方程/应用题/计数等）→ math
- 明确物理/化学/生物题 → 对应学科
- 图片无法辨认、内容不是学科题、或不属于以上任一学科 → other
- 拿不准该不该算数学、在 math 与其他学科之间犹豫 → 输出 math（宁可放过，不可把数学题误判成别的学科）
```

**误拦最小化的落地**:`other` 只在"确信不是 math"时用(图片无法辨认/明确非学科);拿不准 → `math` 放行。这样数学题几乎不可能被判成 physics/chemistry/biology 被 Java 拦掉(误拦),非数学题最多被漏拦(回到现状,可清洗)。
