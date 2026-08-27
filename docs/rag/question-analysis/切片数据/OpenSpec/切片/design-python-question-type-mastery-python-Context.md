# 背景：向量操作走 Python 桥

> summary: COS 无 Java SDK，向量操作走 Python 桥；本期用途=题型动态聚集，embedding 复用 dashscope 已接配置。
> 权威度: 0.7
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/OpenSpec/design-python-question-type-mastery-python-Context.md
> 类别：项目介绍

---

### 背景：向量操作走 Python 桥

> 检索摘要：COS 无 Java SDK，向量操作走 Python 桥；本期用途=题型动态聚集，embedding 复用 dashscope 已接配置。

- 后端方案 `question-type-mastery-backend`（Decision 5）确定：COS 向量检索无 Java SDK（只有 Python/Go 的 `CosVectorsClient`），向量操作走 Python 桥。Java 经 `TopicVectorStore` 端口 HTTP 调 Python，不碰 embedding API / COS SDK。
- 本期唯一业务用途 = **题型动态聚集**（把散题型名归一成 canonical）；**相似题检索明确不做**（后端 Non-Goal，题目向量本期不落库）。
- 现状代码事实：
  - `core/gateway/factory.py` 只创建 `BaseChatModel`（对话），**无任何 embedding 类**。
  - dashscope 已接：`factory.py:148` 用 `dashscope.aliyuncs.com/compatible-mode/v1` 走 OpenAI 兼容协议；`settings.DASHSCOPE_API_KEY` 已有（`.env.example` 已含）。→ **embedding 复用同一 base + 同一 key**。
  - `requirements.txt` 无任何 COS 依赖；`api/rag.py` 有 mock `embed` 端点（TODO，未接 main.py），不要复用。
  - `api/tutoring.py` 三端点（decide/generate SSE、question-understand 同步 JSON）统一 `x-internal-token` 鉴权 + snake_case——向量端点照此惯例。

> 证据：详见 `2.OpenSpec design 决策/design-python-question-type-mastery-python.md`（§背景）｜ 语雀-决策记录.md D13
