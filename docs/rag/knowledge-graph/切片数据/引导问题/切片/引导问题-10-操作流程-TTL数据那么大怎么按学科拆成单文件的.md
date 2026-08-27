# TTL 数据那么大，怎么按学科拆成单文件的？

> summary: 操作流程引导问题回答：main.ttl 按 URI 学科前缀 instance/{subject}# 正则拆（8 学科+unknown），material.ttl 按 C3 类型+P4 名称关键词+BFS 沿 P13/P2/P3 传播拆（9 学科+unknown）；三元组数量校验兜底
> 权威度: 1.0（合成问答答案切片，非原始证据）
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/引导问题/引导问题-10-操作流程-TTL数据那么大怎么按学科拆成单文件的.md
> 类别：操作流程

**核心结论**：main.ttl 按 URI 学科前缀 `instance/{subject}#` 正则拆（8 学科+unknown），material.ttl 按 C3 类型 + P4 名称关键词 + BFS 沿 P13/P2/P3 关系传播拆（9 学科+unknown）；产物 main-math.ttl 14019 triples、material-math.ttl 6024 triples。

## 分层展开
- **main.ttl 拆分**：`split_main_ttl.py` 用 `SUBJECT_URI_PATTERN = instance/([^/#]+)[#/]` 从 URI 提取学科代码，未匹配归 `unknown`；默认 8 学科（math/physics/chemistry/biology/...），`--auto-discover` 可从图遍历自动发现；输出 `main-{subject}.ttl` + `main-unknown.ttl`（依据：分析-02 关键机制）
- **material.ttl 拆分**：实体 URI 不体现学科，改用 RDF 类型 **C3（Textbook）** 识别教材实体 + P4 名称关键词（SUBJECT_KEYWORDS 10 词→9 学科）识别学科，再 BFS 沿真实包含关系 P13(hasLesson)/P2(hasUnit)/P3(hasSection) 把学科传播到所有子实体；**P5 hasImage 已移除**（注释明确"不是包含关系"）（依据：分析-02 关键机制）
- **完整性校验**：拆完比对 `Original=总三元组数` vs `Written=写入数`，相等才打 ✓，否则打 ✗（不中断、照常返回 stats）（依据：分析-02 关键机制 / 边界与降级）
- **拆错兜底**：剩余无归属实体全部标 `unknown`；`--skip-unknown` 时直接丢弃不写文件（依据：分析-02 边界与降级）
- **产物规模**：main-math.ttl 14019 triples、material-math.ttl 6024 triples（依据：完善文档 02 落地真相表 / 分析-02）

## 追问防御
- **可能追问：拆错学科怎么办？** → unknown 兜底 + 三元组数量校验 + 人工确认；main 用 URI 前缀较稳，material 靠名称子串匹配顺序敏感（`生物` 在 `生物学` 前），名含多学科词以 dict 顺序先者为准（依据：分析-02 隐性坑 / 引导问题.md 操作流程）
- **可能追问：`--skip-validation` 是什么？** → 是死参数——split_main_ttl 里定义了 argparse 参数但 main 未传、函数无此签名，传了不生效，验证始终执行（依据：分析-02 隐性坑）

> 证据：详见 `4.完善文档/02-知识图谱数据入库主流程.md` ｜ `3.代码/分析-02-TTL数据拆分与Neo4jSchema.md`
