# design-python-tutoring-subject-gate-python

> summary: 定义学科分类接口的请求响应模型与校验规则
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: 2. 请求/响应模型(models/tutoring.py)
> 模块: ai-tutoring ｜ 节: design-python-tutoring-subject-gate-python
> COS路径: ai-tutoring/rag-slices/OpenSpec/design-python-tutoring-subject-gate-python-2-请求-响应模型models-tutoringpy.md
> 类别：架构设计

---

### 2. 请求/响应模型(models/tutoring.py)

```
class SubjectType(str, Enum):  # 闭集,Python 侧权威
    MATH="math" PHYSICS="physics" CHEMISTRY="chemistry" BIOLOGY="biology" OTHER="other"

class SubjectClassifyRequest(BaseModel):
    content: Optional[str] = None
    image_url: Optional[str] = None
    # validator: content 与 image_url 至少一个非空(全空 → 422)

class SubjectClassifyResponse(BaseModel):
    subject: Optional[str] = None   # 闭集之一;失败/非法 → None(Java 按 math 放行)
```

**subject 用 `Optional[str]` 而非 `Optional[SubjectType]`**:非法输出(模型吐了闭集外学科,如 "geography")在 Python 侧归一化为 `None`,不让 Pydantic 抛枚举校验异常。语义:非法 = 拿不到结果 = 放行(漏拦方向,安全)。
