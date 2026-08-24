## Why

AI 答疑无学科门：decide 是数学专用提示词（"你是数学答疑的决策器"），一旦学生发非数学题，数学 agent 会硬分类、硬引导，污染掌握度数据。且**不同学科需要不同提示词**（数学引导 ≠ 物理解题），学科必须**先于** decide 判定，才能选对提示词、拦下非数学题。

当前 subject_hint 是死参数（Java 恒传 "math"，decide 提示词里未使用），无任何结构化学科判定。

## What Changes

- **新增 Python `subject-classify` 端点**（decide 之前，学科无关）：输入题目（**文本和图片都支持**），输出 `subject`（math/physics/chemistry/biology/other）。
- **Java 拍题/换题时先判学科再走 decide**：`subject==math` → 建/续会话 + 数学 decide；非 math → **跳过**（不建/不续、不记录，返回「目前仅支持数学」）。
- **三个 LLM 调用统一模型**：decide / question_understand / subject-classify 都用 `doubao-seed-2-0-mini-260428`（temp 0.3）——前两者现状已同款，新增分类器沿用。
- 会话记录真实 `subject`（不再无条件默认 math）。

## Capabilities

### New Capabilities

- `tutoring-subject-gate`：AI 答疑学科门。覆盖学科分类端点（subject-classify）、decide 前判定与 Java 分流、非数学题跳过行为、模型统一。

### Modified Capabilities

- 无（现有 specs 均为 kg-*/org-*，无需求级变更）。

## Impact

- **Python**（aiEduPlatformModel `ai-tutoring`）：新增 `subject-classify` 端点（文本+图片，同款模型）；decide/understand 模型统一确认。
- **Java**：答疑编排加学科分流（decide 之前）；新契约 DTO（subject-classify 请求/响应）；会话 subject 记录真实值。
- **行为**：非数学题不再建/续会话、不落题目/掌握度/错误事件，返回「仅支持数学」。
- **不涉及**：analyze-question 题型分析（本期不改）；多学科提示词（本期只有 math，架构留好）。
