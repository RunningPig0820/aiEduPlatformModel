# tutoring-subject-gate-python 实施任务

## 1. 模型与核心逻辑

- [x] 1.1 models/tutoring.py 新增 `SubjectType` 枚举（math/physics/chemistry/biology/other）+ `SubjectClassifyRequest`（content/image_url 至少一个非空 validator）+ `SubjectClassifyResponse`（subject: Optional[str]）
- [x] 1.2 core/tutoring/subject_classify.py 新增 `classify_subject(request, llm=None)`：学科无关提示词（只判学科不解题；拿不准→math；图片无法辨认/非学科→other），绝不抛异常，失败/闭集外输出 → 空 subject
- [x] 1.3 文本 + 图片双通道：无图纯文本 HumanMessage；有图多模态（HumanMessage([{text},{image_url}])），复用 decide 看图路径
- [x] 1.4 模型统一 + 慢修复：LLMFactory.create doubao `doubao-seed-2-0-mini-260428` / temp 0.3 + `extra_body thinking disabled` + `request_timeout=20` + `max_retries=0`

## 2. 端点接入

- [x] 2.1 api/tutoring.py 注册 `POST /subject-classify`，`verify_internal_token`，返回 `SubjectClassifyResponse`

## 3. 测试（对齐后端 test.md PSC-001~005）

- [x] 3.1 test_subject_classify.py：文本物理题→physics、文本数学题→math、图片多模态→学科、LLM 异常→空 subject 不抛、模型参数统一（thinking off + 20s + retry 0）
- [x] 3.2 test_subject_classify_api.py：缺 token 403、非法 token 403、全空参数 422、正常返回 subject、失败→空 subject

## 4. 验证与交付

- [x] 4.1 全量离线单测全绿（tutoring unit + 相关回归）
- [x] 4.2 真实功能验证：文本物理题→physics、文本数学题→math、图片题→学科、超时/失败→空 subject（Java 按 math 放行）
