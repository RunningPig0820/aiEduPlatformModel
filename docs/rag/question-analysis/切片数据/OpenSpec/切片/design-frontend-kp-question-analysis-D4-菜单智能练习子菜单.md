# 菜单：智能练习 → 题型分析

> summary: 菜单=智能练习（一级）→题型分析（二级子菜单），与学习报告同构，可折叠父项。
> 权威度: 0.7
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/OpenSpec/design-frontend-kp-question-analysis-D4-菜单智能练习子菜单.md
> 类别：操作流程

---

### 决策 4：菜单 = 智能练习（一级翻 active）→ 题型分析（二级子菜单）

> 检索摘要：菜单=智能练习（一级）→题型分析（二级子菜单），与学习报告同构，可折叠父项。

```
智能练习（一级，pending 翻 active，可折叠父项）
  └─ 题型分析（二级页面，/student/practice/question-analysis）
```

与「学习报告 → 掌握度/知识点总览」同构（Sidebar `SubMenuItem` 已支持）。理由：用户要求子菜单结构、页面统一；将来智能练习再出「出题练习」功能时平级加子项即可。

> 证据：详见 `2.OpenSpec design 决策/design-frontend-kp-question-analysis.md`（§决策 4）
