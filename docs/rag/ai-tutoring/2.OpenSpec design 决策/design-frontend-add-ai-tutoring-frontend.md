## Context

学生端 AI 答疑由后端 `ai-tutoring` 方案(兄弟仓库)提供完整能力:Java 网关编排(安全 → decide → 护栏 → generate),SSE **类型先行流式**协议(`meta` → `token` → `done`),拍题 OCR 前置,掌握度落库。前端 `ai-edu-front`(React + Vite + daisyUI)已有 `/student/ai-qa` 路由常量与侧边栏菜单(status=pending),但**没有页面**,点击 404。

本设计解决"前端如何消费这套协议并承载苏格拉底式引导的交互"。前端只消费后端已定契约,**不改后端**;两个已识别的契约缺口(活跃会话查询接口、OCR 开关配置)经讨论**不做后端新增**,分别用本地持久化与常驻拍照按钮规避。

约束:
- 学生端角色色 = success(绿);整页风格走现代网页 AI 智能体交互(ChatGPT/DeepSeek web 风)
- 现有 `AIChatPanel`(通用管理助手抽屉)与 `llm.js` SSE 客户端**不改不动**,答疑是独立功能
- 复用 `request.js`(axios 非流式)、`remark-math` + `rehype-katex`(公式)、daisyUI + Tailwind、`EmptyState`/`Toast`
- 不引入新 npm 依赖

## Goals / Non-Goals

**Goals:**
- 整页答疑页面,AI 智能体交互风格,支持数学公式渲染与流式输出
- 消费类型先行 SSE:按 `meta.type` 渲染类型徽标,`denied` 场景按降级 type 渲染
- 拍题 OCR 前置:上传 → 识别文本确认/修改 → 作为首条消息发起会话
- 护栏可见性:轮次进度(≤20)、请求答案(第 1 次思路 / 第 2 次答案,第 2 次弹确认)、换题分隔提示、收尾总结卡片
- 断点恢复:localStorage 本地记录(DeepSeek 式)+ 服务端对账,不依赖后端新接口
- 知识点 chips 条件渲染(有 `masterySignals` 才显示),无前端知识点模块依赖

**Non-Goals:**
- 不实现后端 Python decide/generate/OCR(另仓排期)
- 不做语音问答(pageMeta 曾列,不在后端答疑范围)
- 不做图谱叠加页面本身(掌握度接口留给未来学生端知识图谱页消费)
- 不新增"换一题"按钮(换题=贴新题,语义判断在后端 decide)
- 不做多会话完整侧边栏/历史服务端列表(方案 A:仅本地最近 N 条)

## Decisions

### 1. 页面形态:整页单栏聊天 + 当前题目置顶卡片

整页(非抽屉):答疑已在学生侧边栏占一席,教学场景需要公式展示、当前题目常驻、轮次上下文;400px 抽屉过窄,且 `AIChatPanel` 定位是通用助手,两者分离。

布局:
```
┌────────────────────────────────────────────────────────────┐
│  header: AI答疑                    [第 X/20 轮] [结束答疑]   │
├────────────────────────────────────────────────────────────┤
│  ┌ 当前题目(纯展示,= 首条用户消息,可折叠)─────────────┐      │
│  │  <题目文本>                                      │      │
│  └─────────────────────────────────────────────────┘      │
│  <聊天线程:消息气泡列表 + 流式光标>                        │
│  🎯 <知识点 chips 行,有信号才渲染>                        │
├────────────────────────────────────────────────────────────┤
│  [📷] 输入或粘贴题目…                     [请求答案] [发送]  │
└────────────────────────────────────────────────────────────┘
```
手机端:当前题目卡片默认折叠为一行摘要;输入区常驻底部(仿移动端聊天)。

### 2. 独立 tutoring SSE 客户端,不复用 llm.js

`llm.js` 的 `streamChat` 只处理 `token`/`done`,不认识 `meta` 且无 `denied` 概念。新增 `api/modules/tutoring.js`,用原生 `fetch`(credentials:'include')实现通用 SSE 解析,按事件名分发:

```js
// 通用 SSE 读取器:解析 event:/data: 行,按 event 名调用对应 handler
function readSSE(response, { onMeta, onToken, onDone, onError }) {
  // event: meta → onMeta(JSON)
  // event: token → onToken(data.content)
  // event: done → onDone(data)
  // event: error → onError(new Error(...))
}
```
客户端导出(非流式走 `request.js` axios,流式走 fetch):
- `startSession(message, handlers)` → `POST /api/tutoring/sessions`(SSE)
- `sendMessage(sessionId, content, handlers)` → `POST /api/tutoring/sessions/{id}/messages`(SSE)
- `requestAnswer(sessionId, handlers)` → `POST /api/tutoring/sessions/{id}/request-answer`(SSE)
- `getSession(sessionId)` → axios
- `archiveSession(sessionId)` → axios
- `getMastery(studentId)` → axios(未来图谱用)
- `recognize(file)` → `POST /api/tutoring/ocr`(FormData,axios,**超时放宽到 30s**)

每次 SSE 调用返回 `cancel()` 函数(组件卸载/停止生成时调用)。

### 3. 前端会话状态机(UI 侧)

后端是"生命周期 3 态 + 护栏计数器",前端在页面内维护**交换级状态**驱动渲染:

```
         ┌────────────────────────────────────────────┐
         │  UI state: activeSession / noSession / ended │
         └────────────────────────────────────────────┘
   发送消息(或 start/request-answer)
         │
         ▼
      phase = SENDING         输入禁用,user 气泡入队
         │
         ▼
  收到 meta → phase = STREAMING
      meta.type 决定徽标;denied 字段可选提示"已调整为思路"
         │
         ▼
  token 累积 → 流式气泡实时渲染(markdown + katex)
         │
         ▼
  done → phase = IDLE
      更新 roundCount/状态;若 ARCHIVED → 切 ended 视图(总结卡片)
      写 localStorage
```
- `switch` → 渲染"已切换到新题 · 从第 1 轮重新计数"分隔,本地 answerRequestCount 归零
- `end`/ARCHIVED → 结束视图 + 总结卡片
- 任意阶段收到 50002/50003/50004/50005 → 错误映射(见决策 7)

### 4. 类型徽标(meta.type → 文案 + 颜色)

| type | 徽标文案 | 样式 | 说明 |
|---|---|---|---|
| hint | 引导 | primary(绿系/主题色) | 常规引导 |
| approach | 思路 | info | 不给完整演算 |
| reveal | 答案 | **warning** | 完整答案,结束时提示"本次答疑已结束" |
| concept | 概念 | neutral | 概念讲解 |
| switch | 换题 | divider 提示,非气泡徽标 | 换题分隔条 |
| end | 总结 | success | 收尾总结 |

`denied` 场景:meta.type 已是降级后的 type(如 approach),前端按该 type 渲染即可,`denied` 字段仅作可选的一次性轻提示(如"已为你调整为先展示思路")。徽标**纯展示、不可点击**——避免学生对后端语义产生额外操作预期。

**会话结束判定(后端确认 2026-08-06)**:`meta.status` 或 `done.status` 为 **ARCHIVED 或 TERMINATED 均视为会话结束**——输入区禁用、可发起新会话,前端**不只认 TERMINATED**。终止路径(`TERMINATED` + `reply`,无 token、**无 done**)对发起与中途同样生效;实测:安全命中 → TERMINATED,无关/非数学 → ARCHIVED 收尾(B4:Python decide 对无关内容返回带 end_reason 的 end,属 Python 侧问题,前端需兼容)。

### 5. 拍题 OCR 前置

- 输入区 📷 按钮**常驻显示**(经讨论,OCR 基本不会关闭,不读配置;若后端关闭,调用返回错误码走通用提示)
- 点击 → 隐藏 `input[type=file] accept="image/*"`(移动端自动唤起相机/相册)
- 上传 `POST /api/tutoring/ocr` → 弹 `OcrConfirmModal`:识别文本置于可编辑 textarea + 置信度指示
- 确认 → 文本进入消息通道:
  - 无活跃会话 → 作为 `startSession(message)` 的首条消息
  - 已有活跃会话 → 作为 `sendMessage` 的内容(decide 自行判 switch)
- 取消/识别失败 → 关闭弹窗,toast 引导"请重新上传清晰照片"
- 识别结果**必须经学生确认**才进入答疑(后端契约要求)

### 6. 请求答案 + 轮次 + 结束

- 输入区右侧 `[请求答案]` 按钮,点击调 `requestAnswer`
- `answerRequestCount` 以 `meta.answerRequestCount`(服务端,后端已确认 SseMetaDTO 携带)为准,本地仅作未收到 meta 时的兜底;`meta.type=switch` 时归零
- 第 2 次点击(服务端计数 ≥1)→ **弹确认**:"获取完整答案后本次答疑将结束,确定?" → 确认后发送
- header 显示 `第 X/20 轮` 进度(roundCount 来自 meta/done 与服务端对账)
- `[结束答疑]` → 轻确认 → `archiveSession` → ended 视图

### 7. 错误映射

| 错误 | 前端表现 |
|---|---|
| 50002 会话不存在 | 本地快照降级为历史回看,引导"发起新会话" |
| 50003 已结束/已归档 | 展示该会话 ended 视图,不可再发消息 |
| 50004 创建过于频繁 | toast"请先完成当前答疑" |
| 50005 agent 失败 | toast"网络波动,请重试";保留该 user 气泡并附"重试"(重发同内容);会话保持 ACTIVE |
| 50006 OCR 无效 | toast"请重新上传清晰照片" |
| SSE 中途断开 | 流式气泡显示"回复中断"+"重试"按钮(重发最近一条 user 消息) |

### 8. 断点恢复:localStorage 快照 + 服务端对账

规避"无活跃会话查询接口"缺口,不新增后端接口。

localStorage schema(`ai_tutoring_sessions`,上限 10 条,先进先出):
```json
[{
  "id": 1001,
  "title": "鸡兔同笼,共35头94脚…",   // 首条用户消息截断
  "status": "ACTIVE",
  "messages": [{ "role": "user|ai", "content": "...", "type": "hint"?, "createdAt": 1710000000000 }],
  "roundCount": 3,
  "updatedAt": 1710000000000
}]
```

进入页面时序:
1. 读 localStorage → 有 ACTIVE 会话 → **秒渲染本地快照**(离线也可见,DeepSeek 感)
2. 同时 `GET /sessions/{id}` 对账:
   - ACTIVE → 校正 roundCount/answerRequestCount/status;若服务端 recentMessages 多于本地(多设备)则补齐
   - 50003 → 切 ended 视图(本地保留为历史)
   - 50002 → 本地降级为历史,引导新会话
3. 无本地会话 → 空状态引导("拍题或输入一道数学题" + 示例)
4. 每次 `done` / 归档后写 localStorage

轻量历史入口(方案 A):页面内提供"历史"下拉/抽屉,可回看最近会话;历史回看只读。

### 9. 知识点 chips 条件渲染

- 数据源:`meta.eval.masterySignals`(后端已放行的信号,含 kpLabel + signal)
- 规则(压噪):仅在 `done` 后更新;最多 4 个 chip,超出折叠 `+N`;信号 → 颜色(mastered 绿 / practicing 黄 / struggling 红)
- **无信号数组 → 整行不渲染**。纯字符串渲染,零前端知识点模块依赖;后端 Python 未排期、暂不发信号时自动隐藏,不阻塞
- 与未来学生端知识图谱页共享 `GET /students/{id}/mastery`,但本页不实现叠加

### 10. 收尾总结卡片

`done.status=ARCHIVED` 或 `archive` 响应含 `summary{knowledgePoints, weakPoints}` 与 `endReason`,渲染总结卡片:
- 涉及知识点(已掌握/练习中)、薄弱点、轮次、掌握度变化提示
- `[再来一题]` → 开新会话(`startSession`),清空当前线程
- `[回看对话]` 暂不做(transcript_url 留后续)

### 11. 组件结构

```
pages/student/AiQa.jsx              — 页面容器:useTutoringSession + 布局
components/student/ai-qa/
  CurrentQuestionCard.jsx           — 当前题目置顶卡片(纯展示、可折叠)
  ChatThread.jsx                    — 消息列表 + 流式光标 + 空状态
  MessageBubble.jsx                 — 用户/AI 气泡;AI 带 TypeBadge + markdown/katex + 重试
  TypeBadge.jsx                     — type → 文案/颜色映射
  KpChips.jsx                       — 知识点 chips(条件渲染)
  ChatInput.jsx                     — 📷 OCR、textarea、请求答案、发送、禁用态
  OcrConfirmModal.jsx               — OCR 识别确认/修改弹窗
  SessionSummary.jsx                — 收尾总结卡片 + 再来一题
  HistorySidebar.jsx                — 历史会话常驻左栏(桌面,DeepSeek 式)/移动端汉堡拉出 overlay(方案 A 演进,替代原抽屉)
hooks/useTutoringSession.js         — 会话状态机 / SSE 消费 / localStorage 持久化 / 对账
api/modules/tutoring.js             — API + SSE 客户端(决策 2)
```

路由/常量:
- `routes.jsx`:student children 增加 `{ path: 'ai-qa', element: <AiQa /> }`
- `pageMeta.js`:STUDENT_AI_QA `status: 'active'`,features 去掉"语音问答"
- `routes.jsx` studentMenu:AI答疑 status → `'active'`

## Risks / Trade-offs

- [localStorage 仅本设备,换设备/清缓存丢本地快照] → COS transcript 为权威完整记录,服务端 Redis/MySQL 为权威状态;本地只是"入口 + 即时渲染",丢失影响为需重新发起会话
- [SSE 中途断连导致消息丢失] → 气泡级"重试"(重发最近 user 消息);后端 decide/generate 已内置 1 次重试
- [类型徽标与后端语义不一致导致误导] → 徽标纯展示、不可点击,仅作阅读辅助
- [answerRequestCount 流式中途短暂未到/兜底值] → 以 `meta.answerRequestCount` 为准,兜底仅用于弹窗时机判断,不影响护栏
- [B4:无关/非数学内容实测走 ARCHIVED 而非 TERMINATED(Python decide 判定)] → 前端对 ARCHIVED/TERMINATED 一视同仁视为结束,不阻塞;属 Python 侧问题,后续修复
- [katex 公式渲染长线程性能] → 答疑消息短、公式量小,可接受;如超长可 lazy render
- [chips 数据依赖后端 master 信号,Python 未上线时不可见] → 设计上即条件渲染,不报错;属预期行为

## Migration Plan

- 纯前端增量:新增页面/组件/API 模块 + 改路由/常量,不动既有页面与 `AIChatPanel`/`llm.js`
- 后端 `ai-tutoring` 已实现接口为前置依赖;若后端未就绪,页面按错误码友好降级(50005 网络波动提示),不影响其他学生端功能
- 回滚:移除路由与菜单即可,无数据迁移

## Open Questions

- 总结卡片是否暴露 COS `transcript_url`(对话回放链接)——暂不做,留后续
- 学生端是否也需要知识图谱页叠加掌握度——超出本 change 范围,接口已留
- **后端契约确认已闭环(2026-08-06)**:① 错误码以 **50004** 为准(后端已修正 tasks 7.9);② 结束判定 = `ARCHIVED` **或** `TERMINATED` 均算会话结束(安全→TERMINATED+reply,无关/非数学→ARCHIVED 收尾,B4 属 Python 侧问题,前端兼容);③ 终止后**无 done**,前端按 reply 渲染不等待;④ `answerRequestCount` 在 SSE meta 中返回,第 2 次确认直接用服务端值
- **待定**:`GET /api/tutoring/sessions/active`——后端可低成本补(缓存层已有 `findActiveByStudentId`),但前端 MVP 用 localStorage 绕开,**本期不依赖**;跨设备断点恢复需要时再启用
- 对外字段 camelCase 已确认(`masterySignals/kpLabel/endReason/denied/reply/answerRequestCount`)
