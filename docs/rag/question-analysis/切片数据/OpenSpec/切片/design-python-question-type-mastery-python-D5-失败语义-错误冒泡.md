# D5：失败语义 = 错误冒泡

> summary: 向量端点错误冒泡不吞异常（与 question-understand 相反），Java 桥侧有降级；embedding 与 COS 失败日志分开。
> 权威度: 0.7
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/OpenSpec/design-python-question-type-mastery-python-D5-失败语义-错误冒泡.md
> 类别：开发难点

---

### D5：失败语义 = 错误冒泡（与 question-understand 相反）

> 检索摘要：向量端点错误冒泡不吞异常（与 question-understand 相反），Java 桥侧有降级；embedding 与 COS 失败日志分开。

question-understand 是「绝不抛异常 → 空结果降级」（视觉识别弱，Java 有 PENDING 兜底）。**向量端点不复制此模式**：它是内部基础设施，Java 桥侧已有降级策略（回退字符规则 + 原样落库）。Python 正常抛 HTTP 错误码即可，但要**日志区分**：

- embedding 失败（dashscope）vs COS 读写失败——日志 tag 分开，便于 spike/联调定位。

> 证据：详见 `2.OpenSpec design 决策/design-python-question-type-mastery-python.md`（§D5）｜ 语雀-决策记录.md D13 ｜ 坑档案 J-QT1
