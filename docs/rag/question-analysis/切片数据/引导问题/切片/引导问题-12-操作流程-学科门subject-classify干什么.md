# 学科门 subject-classify 是干什么的？在链路什么位置？

> summary: 学科门 subject-classify 是干什么的？在链路什么位置？
> 权威度: 1.0
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/引导问题/引导问题-12-操作流程-学科门subject-classify干什么.md
> 类别：操作流程

---

## 回答

**核心结论**：学科门是 **decide 之前的门卫**——只判学科不解题，用 K12 十值闭集先筛掉非数学内容，保证答疑链路只服务数学，且数学题永远不被误拦。

**分层展开**：
- **位置**：学生发第一句/换新题时，Java 先调 `POST /api/tutoring/subject-classify`（decide 之前）——**非数学直接跳过，不建会话不落库**，不浪费 AI 调用。（依据：完善文档 02 落地真相 / 分析-03）
- **闭集**：`SubjectType(math/physics/chemistry/biology/chinese/english/politics/geography/history/other)` K12 十值。（依据：分析-03 / `models/tutoring.py:182-197`）
- **判错语义**：拿不准 → math；图片无法辨认/非学科 → other；**闭集外（地质/天文）→ None**（不是 other，语义= "不知道"）→ Java 按 math 放行，宁漏拦不误拦。（依据：分析-03 / 坑档案 J-QT8）
- **性能护栏**：写死 doubao mini、temp 0.3、**关思考 + 20s 超时 + 重试 0**，整个函数 try/except 绝不抛异常——学科门不能成为新卡点（开思考实测 50~145s）。（依据：完善文档 04 / 分析-03）

> 证据：详见 `7. 引导问题/问题列表.md`（第 12 问）｜ `4.完善文档/04-防作弊与异常防护.md` ｜ `3.代码/分析-03-subject-classify学科门.md`
