# design-backend-tutoring-subject-gate

> summary: 讲学科判定需独立端点，避免decide混用学科逻辑
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: 1. 学科判定 = 独立 subject-classify 端点，在 decide 之前
> 模块: ai-tutoring ｜ 节: design-backend-tutoring-subject-gate
> 类别：操作流程

---

### 1. 学科判定 = 独立 subject-classify 端点，在 decide 之前

**Why**：decide 是数学提示词，不能用来判物理题的学科（"用数学人设问物理题"）。学科必须由**学科无关**的小分类器先判，再按学科选提示词。本期只有 math，非 math 直接跳过。

```
拍题 / 换题（新题文字/图片）
  ↓
① Python subject-classify（学科无关提示词）→ subject
  ↓
② Java 分流：
   ├─ subject == math → 建/续会话(subject=math) → 数学 decide → 护栏 → generate
   └─ subject != math → 跳过：不建/不续、不记录，返回「仅支持数学」
```

**备选（否决）**：decide 内输出 subject → 学科决定提示词时需二次 decide（先数学判学科再换提示词重跑），浪费且逻辑绕；本设计一次分类、一次决定，干净。
