# 课标链路与小学补全

> summary: 百度 OCR 识别课标 PDF，LLM 提取知识点，对比报告补全小学
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-textbook-concept-linking-09-课标链路与小学补全.md
> 类别：数据关联

链路目标：从义务教育数学课程标准（2022 年版）扫描版 PDF（189 页）中，OCR 识别并 LLM 提取教学知识点，与 EduKG Concept 对比，补全 EduKG 缺失的小学知识点。

OCR 技术选型：使用百度 OCR API（收费服务）。理由：用户已有百度 OCR 账号；中文识别效果好；API 调用简单、无需本地部署；支持 QPS 限制和重试。费用说明：按次计费，建议控制调用次数、优先处理关键页面，可用免费额度或购买套餐。替代方案：PaddleOCR 需本地部署 GPU，维护成本高；PyMuPDF 仅提取已有文字，无法识别扫描版。

课标模块实现（edukg/core/curriculum/）：pdf_ocr.py（百度 OCR）、kp_extraction.py（LLM 提取知识点）、relation_builder.py（关系构建，Neo4j 格式）、kp_comparison.py（对比分析，输出 kp_comparison_report.json）、main.py 主脚本。

处理步骤：百度 OCR 识别课标 PDF → LLM 提取知识点结构 → 与 Neo4j Concept 对比 → 输出对比报告 → 人工确认后导入 Neo4j。中间文件 curriculum_kps.json 存放课标知识点。

风险与缓解：
- OCR 识别准确率受扫描质量影响。缓解：人工校验 OCR 结果；提取后人工整理知识点列表；不直接导入，先确认再入库。
- API 成本（OCR 收费 + LLM 调用费用）。缓解：OCR 控制次数、用免费额度或套餐；LLM 用 glm-4-flash 免费；分批处理，记录进度。
