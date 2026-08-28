# 页面锚定与检索范围

> summary: 页面锚定与检索范围（design-python-project-intro-rag）：前端传page、页面模式锁页/全局模式跨页、UI引导问题变体写法强制检索真实发生、锁页/跨页触发条件
> 权威度: 0.7
> 模块: rag-system
> COS路径: rag-slices/rag-system/OpenSpec/design-python-intro-rag-04-页面锚定与检索范围.md
> 类别：架构设计

---

### D3. 页面锚定 + 引导问题变体文案

> 检索摘要：页面锚定怎么让RAG检索可解释？前端传page，页面模式检索限定该页，全局模式不限；UI引导问题用索引规范问题的变体写法，强制检索真实发生

- 前端主动传 `page`;页面模式下检索限定该页(`page` 过滤),全局模式不限。
- UI 引导问题 = 索引层规范问题的**变体写法**(例:UI"你们为什么拆成三段" vs 索引"为什么拆 decide/generate/question-understand"),强制检索真实发生,避免"点按钮=预定答案"。
- **为什么**:页面锚定提升检索确定性、可解释;变体文案让 RAG 检索被真实执行、可演示。

### Requirement: 页面锚定 Scenario 明细（补锁页/跨页触发条件）

> 检索摘要：页面锚定的两个场景？页面模式锁页只在该页qa/source chunk内检索不返回他页；全局模式跨页检索并可按来源页区分命中结果

#### Scenario: 页面模式锁页
- **WHEN** 前端传入 `page=知识图谱` 且问题为该页相关
- **THEN** 检索 SHALL 只在该页面的 `qa`/`source` chunk 内进行,不返回其他页面结果

#### Scenario: 全局模式跨页
- **WHEN** 问题跨页(如"知识图谱怎么支撑AI答疑")或未传 page
- **THEN** 系统 SHALL 跨页检索,并可按来源页区分命中结果

> 证据：详见 `2.OpenSpec design 决策/原来的文件/design-python-project-intro-rag.md`（§D3/§补充 retrieval-页面锚定Scenario明细）
