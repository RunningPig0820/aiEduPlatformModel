# analyze-question接口契约（续）

> summary: analyze-question 契约：编排=理解→全候选遍历→前2候选消歧（LLM 预算收敛）→PENDING+candidates 镜像校验；WEAK 降级不冒充 RESOLVED。
> 权威度: 0.7
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/OpenSpec/design-backend-kp-question-analysis-backend-D5-analyze-question接口契约-2.md
> 类别：开发难点

---

### D5：analyze-question 接口契约（续）

> 检索摘要：analyze-question 契约：编排=理解→全候选遍历→前2候选消歧（LLM 预算收敛）→PENDING+candidates 镜像校验；WEAK 降级不冒充 RESOLVED。

#### 行为要点

**行为要点（联调后定稿）**：
- **WEAK 降级**：冷启动 LLM 猜测返回 `PENDING`（KpResolution 加 `weak` 标记，不再冒充权威 RESOLVED），只作候选待确认。
- **candidates 镜像校验**：analyze 返回前经 `inMirror`（精确→LIKE）校验，非镜像 label 丢弃 → vote 不报 10003。
- **LLM 预算**：题型库全量遍历（DB 廉价），`resolveReadOnly`（含 LLM 消歧）只给前 2 个候选 → 冷启动最坏 1 次理解 + 2 次消歧 ≈ 3 次 LLM（原最坏 6 次）。
- **确定性**：同文本 status 稳定（无数据锚恒 PENDING）；candidates 冷启动下可能波动（LLM 非确定，数据锚积累后收敛）。`AiEduChatRequest` 无 temperature，不调参。

#### 复用与新增

复用：`recordStudentVote`（确认）、`ocr`（拍题）、题型库分页/关联接口（浏览）。新增：`KpQuestionAnalysisAppService`、`KpResolutionController` 加 `POST /analyze-question`。

> 证据：详见 `2.OpenSpec design 决策/design-backend-kp-question-analysis-backend.md`（§D5，下半）｜ 完善文档 02-题型分析主流程怎么走.md ｜ 坑档案 J-QT5
