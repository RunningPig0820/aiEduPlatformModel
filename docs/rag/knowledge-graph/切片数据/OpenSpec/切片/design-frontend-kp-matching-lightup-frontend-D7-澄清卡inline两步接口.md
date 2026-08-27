# 澄清卡 inline 两步接口

> summary: 答疑澄清卡用 inline 非阻塞，两步接口 POST /api/kp/resolve 展示题型候选 + POST /api/kp/vote 落 student_vote，可跳过弃权。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-frontend-kp-matching-lightup-frontend-D7-澄清卡inline两步接口.md
> 类别：架构设计

---

### 7. 澄清卡用 inline 非阻塞，两步接口（resolve + vote）

> 检索摘要：答疑澄清卡用 inline 非阻塞，两步接口 POST /api/kp/resolve 展示题型候选 + POST /api/kp/vote 落 student_vote，可跳过弃权。

答疑澄清卡渲染在聊天线程内（`KpChips` 附近），非阻塞、可忽略。区别于现有 modal（结束答疑/第二次要答案）——那些是「单向门」要拦人，澄清是「你顺便选一下」，性质不同。

数据流（后端已确认，两个端点）：
- 展示候选：`POST /api/kp/resolve` 返回 `status=PENDING` 且 `candidates` 非空 → 渲染澄清卡（**题型**候选，只含 label，不暴露 kp_uri）。
- 提交选择：学生选某题型 → `POST /api/kp/vote`（`{ topicLabel, selectedLabel }`）落 `source=student_vote`；跳过 → 不调任何接口（弃权）。
- `student_grade` 为预留死字段：后端 controller 只取 `label`，年级锚定由后端 `resolveGrade(studentId)` 从会话自查，前端不传。

> 证据：详见 `2.OpenSpec design 决策/design-frontend-kp-matching-lightup-frontend.md`（§7. 澄清卡用 inline 非阻塞，两步接口（resolve + vote））
