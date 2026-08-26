# design-python-tutoring-subject-gate-python

> summary: 说明学科分类端点的同构实现结构
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: 1. 端点结构 = question_understand 同构(stateless,绝不抛异常)
> 模块: ai-tutoring ｜ 节: design-python-tutoring-subject-gate-python
> 类别：架构设计

---

### 1. 端点结构 = question_understand 同构(stateless,绝不抛异常)

```
POST /api/tutoring/subject-classify        (api/tutoring.py, verify_internal_token)
  → core/tutoring/subject_classify.classify_subject(request, llm=None)
      → LLMFactory.create("doubao", _CLASSIFY_MODEL, temperature=0.3,
                          extra_body={"thinking":{"type":"disabled"}},
                          request_timeout=20, max_retries=0)
      → HumanMessage 文本 或 多模态(text+image_url)
      → 解析 subject,校验闭集
      → 任何异常 → SubjectClassifyResponse(subject=None)
```

与 question_understand 完全同构:模型写死 doubao、`llm` 参数注入测试、try/except 兜底空结果、`logger` 记录失败。**照搬其慢修复参数**(thinking off / timeout / retry 0)——这是本次实现不可省略的一环。
