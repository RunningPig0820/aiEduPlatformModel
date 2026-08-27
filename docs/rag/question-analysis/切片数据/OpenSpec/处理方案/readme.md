# 切片数据 / OpenSpec / 处理方案

> 本来源（2.OpenSpec design 决策）从源文档到切片数据的完整处理路径。

## 一、源头

- 源文档：`2.OpenSpec design 决策/design-*.md`（6 份 RAG 版，权威 0.7，素材溯源库）
- 原始草稿归档：`2.OpenSpec design 决策/原来的文件/`（证据源，不进库）
- 生成提示词：`2.OpenSpec design 决策/处理方案/提示词/spec文件整理` + `spec信息补充提示词`（双轨：spec 自身成文进池 + 收敛事实折入语雀 canonical）

## 二、切片

- 按 `###` 切，一个决策/小节一块；100% 保留 Migration/Risks/OpenQuestions
- 块元数据 `authority=0.7 + source=OpenSpec`（同切片池，不物理隔离第三索引——靠元数据识别）

## 三、导出视图

- `export_slices_md.py` 从 jsonl 导出到本目录（QT⑥）

## 四、检索侧规则

- design_spec 只做**补充溯源**：优先 0.8/1.0 真相源，主库无答案才允许引用 0.7 素材库；引用必须提示「该信息来源于历史设计文档，请核对代码确认实际落地情况」，禁止把 ⚠️/❓ 当已上线功能。