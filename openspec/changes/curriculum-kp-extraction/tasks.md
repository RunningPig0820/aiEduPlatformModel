## 开发流程说明

**重要：分阶段开发，每个阶段完成后需验证再继续下一阶段**

```
阶段1 → 运行测试 → 人工确认 → 阶段2 → 运行测试 → 人工确认 → ...
```

每个阶段完成后：
1. 运行该阶段的测试用例 `pytest tests/curriculum/test_xxx.py -v`
2. 确认测试通过后，通知人工启动下一阶段
3. 如有失败，修复问题后重新测试

---

## 1. 项目结构初始化（阶段1）

- [ ] 1.1 创建 `edukg/scripts/curriculum/` 目录结构
- [ ] 1.2 配置百度 OCR API Key 环境变量 (BAIDU_OCR_API_KEY, BAIDU_OCR_SECRET_KEY)
- [ ] 1.3 配置智谱 API Key 环境变量

**阶段1完成验证**:
```bash
# 确认目录结构存在
ls -la edukg/scripts/curriculum/

# 确认环境变量配置正确
python -c "import os; print('BAIDU_OCR_API_KEY:', os.environ.get('BAIDU_OCR_API_KEY', 'NOT SET'))"
```

---

## 2. PDF OCR 服务（阶段2）

- [ ] 2.1 实现 `BaiduOCRService` 类，初始化百度 OCR API 客户端
- [ ] 2.2 实现 `extract_text()` 调用百度 OCR API 提取文字
- [ ] 2.3 实现 PDF 转图片 + OCR 识别流程
- [ ] 2.4 实现 `save_ocr_result()` 保存 OCR 结果到 JSON
- [ ] 2.5 实现进度指示器，显示处理进度
- [ ] 2.6 处理 API 调用限制（QPS、错误重试）

**阶段2完成验证**:
```bash
# 运行 OCR 测试用例
pytest tests/curriculum/test_pdf_ocr.py -v

# 手动验证：处理小 PDF 文件
python -m curriculum.pdf_ocr --pdf-path test.pdf --debug
# 确认生成 ocr_result.json
```

---

## 3. 知识点提取服务（阶段3）

- [ ] 3.1 实现 `LLMExtractor` 类，配置 ChatZhipuAI (glm-4-flash)
- [ ] 3.2 设计结构化 prompt，要求 JSON 输出
- [ ] 3.3 实现 `extract_knowledge_points()` 提取学段、领域、知识点
- [ ] 3.4 实现文本分块处理（超长文本切分）
- [ ] 3.5 实现 JSON schema 验证
- [ ] 3.6 保存提取结果到 `curriculum_kps.json`

**阶段3完成验证**:
```bash
# 运行 LLM 提取测试用例
pytest tests/curriculum/test_kp_extraction.py -v

# 手动验证：使用阶段2的 OCR 结果
python -m curriculum.kp_extraction --ocr-result ocr_result.json --debug
# 确认生成 curriculum_kps.json
```

---

## 4. 知识点对比服务（阶段4）

- [ ] 4.1 实现 `ConceptComparator` 类，连接 Neo4j
- [ ] 4.2 实现 `query_existing_concepts()` 查询所有 Concept label
- [ ] 4.3 实现 `compare_knowledge_points()` 对比匹配状态
- [ ] 4.4 实现 `generate_comparison_report()` 生成对比报告
- [ ] 4.5 保存报告到 `kp_comparison_report.json`

**阶段4完成验证**:
```bash
# 运行对比测试用例
pytest tests/curriculum/test_kp_comparison.py -v

# 手动验证：使用阶段3的提取结果
python -m curriculum.kp_comparison --kps curriculum_kps.json --debug
# 确认生成 kp_comparison_report.json
```

---

## 5. TTL 生成服务（阶段5）

- [ ] 5.1 实现 `TTLGenerator` 类
- [ ] 5.2 定义 namespace 和 prefix
- [ ] 5.3 实现 `generate_ttl()` 创建 TTL triples
- [ ] 5.4 保存 TTL 到 `curriculum_kps.ttl`

**阶段5完成验证**:
```bash
# 运行 TTL 测试用例
pytest tests/curriculum/test_ttl_generator.py -v

# 手动验证：生成 TTL
python -m curriculum.ttl_generator --kps curriculum_kps.json --debug
# 确认生成 curriculum_kps.ttl
```

---

## 6. 主脚本整合（阶段6）

- [ ] 6.1 创建 `main.py` 整合所有服务
- [ ] 6.2 实现命令行参数（--skip-ocr, --skip-ttl, --debug）
- [ ] 6.3 实现错误处理和日志记录
- [ ] 6.4 验证完整流程

**阶段6完成验证**:
```bash
# 运行主脚本测试
pytest tests/curriculum/test_main.py -v

# 运行完整流程
python main.py --debug

# 确认所有输出文件生成
ls -la ../../data/eduBureau/math/
# ocr_result.json, curriculum_kps.json, kp_comparison_report.json, curriculum_kps.ttl
```

---

## 7. 测试（阶段7）

- [ ] 7.1 编写 `test_pdf_ocr.py` OCR 单元测试
- [ ] 7.2 编写 `test_kp_extraction.py` LLM 提取单元测试（Mock LLM）
- [ ] 7.3 编写 `test_kp_comparison.py` 对比单元测试
- [ ] 7.4 编写 `test_ttl_generator.py` TTL 单元测试
- [ ] 7.5 编写 `test_main.py` 集成测试（完整流程）

**阶段7完成验证**:
```bash
# 运行所有测试
pytest tests/curriculum/ -v

# 测试覆盖率
pytest --cov=curriculum --cov-report=term-missing
```

---

## 8. 文档（阶段8）

- [ ] 8.1 编写 README.md 记录使用方法
- [ ] 8.2 记录输出文件格式说明