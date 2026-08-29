# 数据加工流水线

> summary: 教材与课标双模块处理、三阶段迁移流水线
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-textbook-concept-linking-04-数据加工流水线.md
> 类别：操作流程

处理服务按业务划分为两个独立模块，放在 `edukg/core/` 目录，职责单一、便于测试，可独立运行也可整合运行：
- textbook 教材模块：parser.py 解析教材 JSON；matcher.py 匹配知识点；main.py 主脚本。
- curriculum 课标模块：pdf_ocr.py 百度 OCR；kp_extraction.py LLM 提取；relation_builder.py 关系构建（Neo4j 格式）；kp_comparison.py 对比分析；main.py 主脚本。

输出文件结构：
- `edukg/data/eduBureau/math/`：ocr_result.json（OCR 结果）、classes.json、concepts.json、statements.json、relations.json（均为 Neo4j 导入格式）。
- `edukg/data/output/`：curriculum_kps.json（课标知识点中间文件）、kp_comparison_report.json（对比报告）、textbook_chapters.json（章节结构）、matching_report.json（匹配报告）。

三阶段迁移流水线：
- 阶段一 课标 OCR + 提取（先补全知识点）：百度 OCR 识别课标 PDF → LLM 提取知识点结构 → 与 Neo4j Concept 对比 → 输出 kp_comparison_report.json → 人工确认后导入。
- 阶段二 教材解析 + 匹配：解析教材 JSON → 查询 Neo4j Concept（只读）→ 精确匹配 + LLM 模糊匹配 → 输出 matching_report.json → 人工确认。
- 阶段三 TTL 生成（可选）：整合教材 + 课标知识点 → 生成 TTL 格式文件 → 人工确认后手动导入 Neo4j。

知识点关系构建流水线（Neo4j 格式输出）：先做 Class 类型推断（LLM 推断 HAS_TYPE，示例 凑十法→数学方法、20 以内加法→数学运算；现有 Class 不匹配则建议新增），再做 Statement 定义提取（为每个知识点生成定义并建立 Statement→Concept 的 RELATED_TO），再做知识点关系提取（PART_OF：20 以内加法→加法；BELONGS_TO：凑十法→进位加法），最后输出 classes/concepts/statements/relations 四个独立文件。
