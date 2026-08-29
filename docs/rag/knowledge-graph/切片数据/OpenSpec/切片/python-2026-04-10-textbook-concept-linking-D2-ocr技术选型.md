# D2 OCR 技术选型
> summary: 课标 PDF OCR 选百度 OCR API（收费），用户已有账号且中文效果好、调用简单，控制调用次数；备选 PaddleOCR 需 GPU、PyMuPDF 无法识别扫描版。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/python-2026-04-10-textbook-concept-linking-D2-ocr技术选型.md
> 类别：架构设计

> 检索摘要：课标 PDF OCR 选百度 OCR API（收费），用户已有账号且中文效果好、调用简单，控制调用次数；备选 PaddleOCR 需 GPU、PyMuPDF 无法识别扫描版。

**决策**: 使用百度 OCR API（收费服务）

**理由**:
- 用户已有百度 OCR 账号
- 中文识别效果好
- API 调用简单，无需本地部署
- 支持 QPS 限制和重试

**费用说明**:
- 百度 OCR 是收费服务，按次计费
- 建议控制调用次数，优先处理关键页面
- 可使用免费额度或购买套餐

**替代方案**:
- PaddleOCR：需要本地部署 GPU，维护成本高
- PyMuPDF：仅提取已有文字，无法识别扫描版

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-10-textbook-concept-linking.md`（§D2 OCR 技术选型）
