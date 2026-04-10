## 1. 环境准备

- [x] 1.1 创建爬虫脚本目录 `edukg/scripts/textbook_data/`
- [x] 1.2 创建数据输出目录 `edukg/data/textbook/math/renjiao/primary/`、`middle/`、`high/`
- [x] 1.3 安装依赖 requests, beautifulsoup4, lxml
- [x] 1.4 创建 `__init__.py` 文件

## 2. 入口页面解析

- [x] 2.1 访问入口页面 `https://www.renjiaoshe.com/renjiaoshuxue/`
- [x] 2.2 解析页面编码（GB18030）
- [x] 2.3 提取小学、初中、高中三个学段的区块结构
- [x] 2.4 提取各学段下的教材链接（册数 URL）

## 3. 教材页面爬取

- [x] 3.1 实现请求函数（带 User-Agent、超时、重试）
- [x] 3.2 实现页面下载函数（GB18030 编码处理）
- [x] 3.3 实现章节目录解析（章节名、小节名、知识点）
- [x] 3.4 实现三级结构解析（小学两级、初中三级）

## 4. 数据模型实现

- [x] 4.1 定义教材数据结构（subject, textbook, stage, grade）
- [x] 4.2 定义章节数据结构（chapter_order, chapter_name, sections）
- [x] 4.3 定义小节数据结构（section_order, section_name, knowledge_points）

## 5. 数据输出（按层级目录）

- [x] 5.1 创建年级目录（grade1-grade6, grade7-grade9, bixiu1-3）
- [x] 5.2 实现 JSON 格式输出（单册文件）
- [x] 5.3 实现学段合并输出（primary_textbook.json, middle_textbook.json, high_textbook.json）
- [x] 5.4 实现 TTL 格式输出（`k12_math_textbook.ttl`，与 main.ttl 兼容）
- [x] 5.5 添加元数据（source_url, crawled_at, publisher, edition）
- [x] 5.6 创建 README.md 数据说明文档

## 6. 容错与日志

- [x] 6.1 实现请求失败重试机制（最多 3 次）
- [x] 6.2 实现断点续爬功能（记录已爬取 URL 到 `progress.json`）
- [x] 6.3 添加爬取进度日志（显示当前 URL、成功/失败数）
- [x] 6.4 记录解析失败的页面和错误信息

## 7. 测试与验证

- [x] 7.1 测试入口页面解析（提取学段和教材链接）
- [x] 7.2 测试单个教材页面爬取
- [x] 7.3 验证 JSON 数据格式正确性
- [x] 7.4 完整爬取小学数学教材（12册）
- [x] 7.5 完整爬取初中数学教材（6册）
- [x] 7.6 完整爬取高中数学教材（6册，人教A版）
- [x] 7.7 验证 TTL 文件格式（179KB，包含知识点）
- [x] 7.8 验证目录层级结构（学科-教材-学段-年级）

## 完成统计

| 学段 | 教材数 | 章节数 | TTL知识点数 |
|-----|--------|--------|-------------|
| 小学数学 | 12册 | 102章 | ~200+ |
| 初中数学 | 6册 | 29章 | ~300+ |
| 高中数学 | 6册 | 21章 | ~100+ |

## 关键修复

1. **编码问题**：教师之家使用 GB18030 编码，需使用 `apparent_encoding` 检测
2. **章节识别**：
   - 支持 `1.准备课` 格式（数字+点）
   - 支持 `1　数据收集整理` 格式（数字+全角空格）
   - 支持 `第一章 有理数` 格式（中文数字章节）
3. **三级结构**：初中教材包含 章节→小节→知识点 三级结构
4. **高中年级**：解析 `必修第一册`、`选择性必修第一册` 等格式