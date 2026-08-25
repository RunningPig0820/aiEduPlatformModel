# 坑档案

> summary: 解决PENDING题目落库冲突，修改topic_label可空
> 权威度: 0.8 ｜ 来源: 坑档案 ｜ 锚点: J8. PENDING 题目落库冲突
> 模块: ai-tutoring ｜ 节: 坑档案

---

### J8. PENDING 题目落库冲突
- **坑**：答疑 PENDING（题型未识别）题目落库报错。
- **根因**：V20 之前 `topic_label` NOT NULL，canonical=null 无法落。
- **解决**：V20 `topic_label` 改可空，PENDING 照常落库**信号不丢**，归属后批量聚集补。
- **证据**：`e94a6ab`；`TutoringAppService.java:789-807`。
