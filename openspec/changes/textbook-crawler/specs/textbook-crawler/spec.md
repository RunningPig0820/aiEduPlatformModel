## ADDED Requirements

### Requirement: 爬取 sitemap.xml 解析教材页面 URL

系统 SHALL 能够从教师之家 sitemap.xml 中解析出数学教材页面的 URL 列表。

#### Scenario: 解析 sitemap 成功
- **WHEN** 访问 https://www.renjiaoshe.com/sitemap.xml
- **THEN** 系统返回所有数学教材页面的 URL 列表
- **AND** URL 按小学/初中分组

#### Scenario: 筛选人教版数学 URL
- **WHEN** 解析 sitemap.xml
- **THEN** 系统筛选出匹配 `/shuxue/renjiaoban/` 的 URL
- **AND** 排除非数学学科和非人教版的 URL

---

### Requirement: 爬取教材目录页面

系统 SHALL 能够爬取教材目录页面，提取章节结构和知识点列表。

#### Scenario: 爬取小学数学目录
- **WHEN** 爬取小学数学教材页面
- **THEN** 系统提取年级、学期、章节名称、小节名称、知识点列表

#### Scenario: 爬取初中数学目录
- **WHEN** 爬取初中数学教材页面
- **THEN** 系统提取年级、学期、章节名称、小节名称、知识点列表

#### Scenario: 处理解析失败
- **WHEN** 页面结构无法识别
- **THEN** 系统记录失败 URL 和错误信息
- **AND** 继续处理其他页面

---

### Requirement: 输出 JSON 格式数据

系统 SHALL 能够将爬取的数据输出为 JSON 格式文件。

#### Scenario: 生成小学数学 JSON
- **WHEN** 完成小学数学目录爬取
- **THEN** 系统生成 `primary_math_textbook.json` 文件
- **AND** 文件包含 1-6 年级共 12 册教材目录

#### Scenario: 生成初中数学 JSON
- **WHEN** 完成初中数学目录爬取
- **THEN** 系统生成 `middle_math_textbook.json` 文件
- **AND** 文件包含 7-9 年级共 6 册教材目录

---

### Requirement: 输出 TTL 格式数据

系统 SHALL 能够将爬取的数据输出为与 main.ttl 兼容的 TTL 格式。

#### Scenario: 生成 TTL 文件
- **WHEN** 完成教材目录爬取
- **THEN** 系统生成 `k12_textbook.ttl` 文件
- **AND** 文件格式与 EDUKG main.ttl 兼容
- **AND** 包含 temp 字段记录教材章节信息

#### Scenario: TTL 数据可导入 Neo4j
- **WHEN** 使用 n10s 导入 TTL 文件
- **THEN** 知识点节点正确创建
- **AND** temp 属性正确存储教材信息

---

### Requirement: 支持断点续爬

系统 SHALL 支持断点续爬，避免重复爬取已完成页面。

#### Scenario: 记录爬取进度
- **WHEN** 爬虫运行过程中
- **THEN** 系统实时记录已爬取的 URL 到进度文件

#### Scenario: 恢复爬取
- **WHEN** 爬虫中断后重新启动
- **THEN** 系统读取进度文件
- **AND** 跳过已爬取的 URL