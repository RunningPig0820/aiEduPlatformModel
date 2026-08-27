# 两层 PENDING 语义混用

> summary: analyze 识别 PENDING 与 getMastery 掌握度 PENDING 语义相反，前端共用 status 变量导致状态展示全错，需分层判断（D14）。
> 权威度: 0.8
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/语雀/语雀-前端联调问题单-问题4-两层PENDING语义混用.md
> 类别：开发难点

---

### 问题4：两层 PENDING 语义混用
> 检索摘要：analyze 识别 PENDING 与 getMastery 掌握度 PENDING 语义相反，前端共用 status 变量导致状态展示全错，需分层判断（D14）。

| 属性 | 内容 |
|---|---|
| 现象 | 前端用一个 status 变量处理两类 PENDING，状态展示全错 |
| 触发流程 | analyze 返回 PENDING（题型没认出）与 getMastery 返回 PENDING（知识点待确认）都被当"待确认" |
| 根因 | 两个接口 PENDING 含义相反，共用一个判断变量必然混 |
| 修复方案 | 分层判断（D14）：识别层 PENDING → 展示候选/空态到此为止；掌握度层 PENDING → 待确认 |
| 状态 | ✅ 已修复（方案定稿）`前端需适配` |
| 证据 | 语雀-方案设计2-问题1 坑2 |

> 证据：详见 `1.语雀/语雀-前端联调问题单.md`（§问题4）｜ 语雀-决策记录.md D14 ｜ 完善文档 05-数据落库与掌握度.md ｜ 坑档案 J-QT3
