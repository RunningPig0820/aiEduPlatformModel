# 存疑挂起闭环

> summary: 存疑挂起闭环前端契约增强：WEAK 降级 PENDING、candidates 镜像校验 vote 不 10003、vote 转正 PENDING。
> 权威度: 0.7
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/OpenSpec/design-frontend-kp-question-analysis-D6-存疑挂起闭环.md
> 类别：开发难点

---

### 决策 6：存疑挂起闭环（后端已交付，联调后新增）

> 检索摘要：存疑挂起闭环前端契约增强：WEAK 降级 PENDING、candidates 镜像校验 vote 不 10003、vote 转正 PENDING。

后端 `kp-question-analysis-backend` 已交付「存疑挂起 → 学生选择/后续任务补充」闭环，前端契约增强（**无破坏性变更**）：

```
学生贴题 → analyze-question
  ├─ 权威命中（题型库/镜像）→ status=RESOLVED，展示关联知识点
  └─ 存疑/冷启动 → status=PENDING，candidates（保证可 vote）
                  + 后端自动落 PENDING obs「挂起来」（进 pending-kps，不丢）
      ├─ 学生选候选 → vote → 该 PENDING 转正 RESOLVED → 跨学生达阈值沉淀题型库
      └─ 学生不选 → 后端维护任务 LLM 重判 → 转 WEAK → 共现转正
```

**后端行为变更（前端需知晓）：**
- **WEAK 降级**：冷启动 LLM 猜测（曾返回 RESOLVED conf=70）现在**返回 PENDING**——只作为候选待确认，不再冒充权威答案。PENDING 态出现频率变高，前端按 PENDING 分支处理（有 candidates / 空 candidates 两种）。
- **candidates 镜像校验**：analyze 返回的候选全部经后端 kg 镜像校验，**vote 不会报 10003**。
- **vote 转正**：vote 成功会把该生该题型的 PENDING obs 转正为 RESOLVED（待确认清单即时消失），提示「已记录，将参与题型整理」（跨学生达阈值才沉淀题型库，非即时）。
- **确定性**：后端用「全候选遍历（顺序无关）+ 提示词收敛 + 数据锚优先」，不依赖缓存；status 稳定，candidates 冷启动下可能波动（预期）。

**前端新增面（tasks 组 8）：** ① PENDING 候选可点投票（核心）；② `pending-kps` 待确认清单加「确认」交互（方案 a，复用 vote，需产品确认）；③ 题型库空态文案；④ WEAK 降级适配回归。

> 证据：详见 `2.OpenSpec design 决策/design-frontend-kp-question-analysis.md`（§决策 6）｜ 坑档案 J-QT3 ｜ 语雀-决策记录.md D11
