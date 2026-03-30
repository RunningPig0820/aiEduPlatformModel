## 1. 环境准备

- [ ] 1.1 创建爬虫脚本目录 `edukg/scripts/crawler/`
- [ ] 1.2 创建数据输出目录 `edukg/data/edukg/textbook/`
- [ ] 1.3 安装依赖 requests, beautifulsoup4, lxml
- [ ] 1.4 创建 `__init__.py` 文件

## 2. 爬虫脚本开发

- [ ] 2.1 创建 `renjiaoshe_crawler.py` 主爬虫脚本
- [ ] 2.2 实现请求函数（带 User-Agent、超时、重试）
- [ ] 2.3 实现页面下载函数（GBK 编码处理）
- [ ] 2.4 实现章节目录解析（`<li class="cut nourl">` 章节名）
- [ ] 2.5 实现小节解析（`<li><a>小节名</a></li>`）

## 3. 数据模型实现

- [ ] 3.1 定义教材数据结构（subject, stage, grade, semester）
- [ ] 3.2 定义章节数据结构（chapter_order, chapter_name, sections）
- [ ] 3.3 定义小节数据结构（section_order, section_name, knowledge_points）
- [ ] 3.4 实现教材 ID 到年级学期的映射（19-30 小学, 31-36 初中）

## 4. 数据输出

- [ ] 4.1 实现 JSON 格式输出（单册文件 `grade{N}_{shang|xia}.json`）
- [ ] 4.2 实现 JSON 合并输出（`primary_math_textbook.json`, `middle_math_textbook.json`）
- [ ] 4.3 实现 TTL 格式输出（`k12_math_textbook.ttl`，与 main.ttl 兼容）
- [ ] 4.4 添加元数据（source_url, crawled_at）

## 5. 容错与日志

- [ ] 5.1 实现请求失败重试机制（最多 3 次）
- [ ] 5.2 实现断点续爬功能（记录已爬取 ID 到 `progress.json`）
- [ ] 5.3 添加爬取进度日志（显示当前 ID、成功/失败数）
- [ ] 5.4 记录解析失败的页面和错误信息

## 6. 测试与验证

- [ ] 6.1 测试单个页面爬取（ID=19 一年级上册）
- [ ] 6.2 验证 JSON 数据格式正确性
- [ ] 6.3 完整爬取小学数学教材（ID=19-30）
- [ ] 6.4 完整爬取初中数学教材（ID=31-36）
- [ ] 6.5 验证 TTL 文件格式（可导入 Neo4j）
- [ ] 6.6 更新 README.md 记录数据来源和结构