# 坑档案 K9 引导问题 summary 用 LLM 翻译版 → 语义错位召回不到

> summary: 引导问题 summary 被 LLM 翻成答案式描述致检索错位：summary 改回问题标题，BM25/向量路全部命中
> 权威度: 0.8 ｜ 来源: 坑档案 ｜ 锚点: K9. 引导问题 summary 用 LLM 翻译版 → 语义错位召回不到
> 模块: rag-system ｜ 节: 坑档案
> COS路径: rag-slices/rag-system/坑档案/坑档案-K9-summary翻译错位.md
> 类别：开发难点
> target: 开发对账

---

**1. 问题现象**：引导题（"AI答疑如何使用？"）点击后检索不到自己的答案块，BM25 排第 7、向量路不进 top——引导题作为"索引层入口"失灵。

**2. 触发流程**：引导题点击 → 检索 → 切片池 `-q` 问题路 embedding/BM25。切片池里引导题块 summary 是 LLM 翻译版（"AI答疑如何使用？"被翻成"学生端拍题/打字/粘贴...使用闭环"），embedding/BM25 用 summary+text 与 query 语义错位。

**3. 根因分析**：引导问题块 summary 用 LLM 翻译（把问题标题译成"答案式描述"）→ 索引向量/BM25 检索特征（summary+text）与用户 query（原问题标题）语义错位（实测 sim 0.65）→ 向量路不命中、BM25 靠后。本质：引导题这类"问题即内容"的块，summary 应等于"用户会问的问题"，翻成答案式描述反而错位。

**4. 排查过程**：实测"AI答疑如何使用？"命中情况：BM25 第 7、向量 slice 不进 top、orchestrate 不进 top6——检索全偏；对照切片数据发现引导题 summary 是翻译版。

**5. 解决方案 & 改动点**：`b4cec79`（用户方案）——引导问题 summary 直接用问题标题（anchor），不做 LLM 翻译：`md_to_jsonl.py:111-117` 对引导问题 source，summary=`meta["anchor"]`（标题）、不读翻译头（防御 md 头再被翻译，jsonl 仍用标题）；90 个引导问题切片头 summary 改为标题；重新生成 `rag_slices.jsonl` + 重入切片池。实测：BM25 第 7→第 1、向量 slice 不进 top→第 1（sim 0.8513）、orchestrate 不进 top6→#1 命中目标块。

**6. 面试口述要点**：讲"索引块 summary 的语义对齐"——向量/BM25 检索的特征是"块摘要+正文"，预写 QA/引导题这类"问题即内容"的块，summary 取问题标题比 LLM 改写可靠。踩坑收获：离线切片的"元数据语义"和"线上 query 语义"必须对齐，翻译/改写会引入不可控错位。

- **证据**：`b4cec79`（引导问题 summary=标题）+ `md_to_jsonl.py:111-117`
