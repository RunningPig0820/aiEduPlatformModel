# 初高中知识点处理问题与解决思路

> 基于 kg-math-complete-graph 项目实践总结
>
> 更新日期: 2026-04-13

---

## 一、数据缺失问题

### 问题描述

原始教材 JSON 数据中，部分年级的知识点字段为空：

| 学段 | 知识点数 | 问题 |
|------|---------|------|
| 小学1-2年级 | 47 | 部分有知识点 |
| 小学3-6年级 | **0** | knowledge_points 全空 |
| 初中7-9年级 | 252 | 较完整 |
| 高中必修 | **0** | 仅有综合测试标记 |

### 解决思路

**方案**: LLM 推断补全

1. 使用双模型投票机制（GLM-4-flash + DeepSeek-chat）
2. 根据章节信息（学段、年级、章节名、小节名）推断知识点
3. 支持断点续传，避免重复调用

**实现**:
```python
inferer = TextbookKPInferer()
result = await inferer.infer_section(
    stage="小学",
    grade="三年级",
    chapter_name="时、分、秒",
    section_name="秒的认识"
)
# 输出: {"knowledge_points": ["秒的概念", "秒与分的关系"], "confidence": 0.93}
```

**结果**:
- 缺失章节: 295 个
- 推断知识点: 1052 个
- 平均置信度: 0.93

---

## 二、知识点匹配效率问题

### 问题描述

原方案遍历所有图谱知识点进行 LLM 匹配：

```
教材知识点 1350 × 图谱知识点 5000 = 675万次 LLM 调用 → 不可行
```

### 解决思路

**方案**: 两阶段匹配（粗筛 + LLM投票）

```
教材知识点 → 粗筛(top-20候选) → LLM双模型投票 → 匹配结果
```

**粗筛方式对比**:

| 方案 | 优点 | 缺点 | 采用 |
|------|------|------|------|
| difflib（原方案） | 无依赖 | 语义理解弱 | ❌ |
| **向量检索** | 自动理解同义词 | 需安装依赖 | ✅ |

**向量检索实现**:
```python
class LocalVectorRetriever:
    def __init__(self, kg_concepts):
        self.model = SentenceTransformer("BAAI/bge-small-zh-v1.5")
        self.vectors = self.model.encode(texts)  # 预计算向量

    def retrieve(self, query, top_k=20):
        # 余弦相似度计算
        return top-k 候选
```

**效果**:
- LLM调用次数: 500万 → 2.7万（下降 99%）
- 匹配准确率: 预计提升 10-20%

---

## 三、语义匹配问题

### 问题描述

difflib 只能匹配字符相似度，无法理解语义：

| 教材知识点 | 图谱知识点 | difflib | 向量检索 |
|-----------|-----------|---------|---------|
| "勾股定理" | "毕达哥拉斯定理" | ❌ 不匹配 | ✅ 匹配 |
| "百分数" | "百分比" | ❌ 不匹配 | ✅ 匹配 |

### 解决思路

**方案**: 向量检索 + 同义词映射

**同义词映射**（精确匹配增强）:
```python
SYNONYM_MAP = {
    "加法": ["加", "加法运算", "相加", "求和"],
    "百分数": ["百分比", "百分率"],
    "长方形": ["矩形", "长方形图形"],
}
```

**标准化处理**:
```python
def _normalize_name(name):
    # 转小写、去空格、统一括号
    name = name.lower().replace(' ', '')
    name = name.replace('（', '(').replace('）', ')')
    return name
```

---

## 四、同义词过度匹配问题

### 问题描述

原方案使用 `key in name` 进行同义词扩展，导致过度匹配：

| 知识点名称 | 原方案 | 问题 |
|-----------|--------|------|
| "加法" | 扩展为 ["加法", "加", "加法运算", ...] | 正确 ✓ |
| "加法交换律" | 扩展为 ["加法交换律", "加", "加法运算", ...] | **错误** ❌ |

"加法交换律"不应等同于"加法"。

### 解决思路

**方案**: 完整词匹配

```python
def _expand_with_synonyms(name):
    # 完整匹配（不是部分包含）
    for key, synonyms in SYNONYM_MAP.items():
        if normalized_name == normalized_key:  # 完全相等
            names.extend(synonyms)
    # 去重
    return list(set(names))
```

**效果**:
| 知识点名称 | 新方案 |
|-----------|--------|
| "加法" | ["加法", "加", "加法运算", "相加", "求和"] ✓ |
| "加法交换律" | ["加法交换律"] ✓ |

---

## 五、Topic继承偏差问题

### 问题描述

知识点 `topic` 字段直接继承章节 `topic`，导致语义矛盾：

| 知识点 | 所属章节 | 章节 topic | 知识点 topic（原） | 问题 |
|--------|---------|-----------|-------------------|------|
| "加法" | "位置"章 | 图形与几何 | 图形与几何 | **错误** ❌ |

"加法"应属于"数与代数"，不应继承"图形与几何"。

### 解决思路

**方案**: 基于匹配的 EduKG Concept 的 Class 类型修正

**规则映射**:
```python
TOPIC_CLASS_MAP = {
    "数学概念": "数与代数",
    "数学运算": "数与代数",
    "几何图形": "图形与几何",
    "几何性质": "图形与几何",
    "统计概念": "统计与概率",
}
```

**流程**:
1. 匹配 TextbookKP → EduKG Concept
2. 查询 Concept 的 Class 类型
3. 根据规则映射修正 topic

**状态**: 待实现（Task 16.6）

---

## 六、断点续传问题

### 问题描述

LLM 任务耗时较长，中断后需要重新执行：

| 任务 | 预估耗时 | 中断影响 |
|------|---------|---------|
| 教学知识点推断 | 2-3小时 | 从头开始 |
| 知识图谱匹配 | 1-2小时 | 从头开始 |

### 解决思路

**方案**: 集成 llmTaskLock 模块

**核心组件**:
- `TaskState`: 记录任务进度
- `CachedLLM`: LLM 结果缓存
- `ProcessLock`: 进程锁保护

**实现**:
```python
class TextbookKPInferer:
    def __init__(self):
        self.task_state = TaskState("infer_kp")
        self.process_lock = ProcessLock("infer_kp.lock")

    async def infer_batch(self, sections, resume=True):
        # 加载已完成的章节
        if resume:
            completed = self.task_state.get_state()['checkpoints']

        # 只处理未完成的
        pending = [s for s in sections if s not in completed]
```

**效果**:
- 中断后可继续执行
- 相同 Prompt 不重复调用 LLM

---

## 七、进度显示问题

### 问题描述

原方案使用循环索引作为进度，断点续传时显示不准确：

| 场景 | 显示 | 实际 |
|------|------|------|
| 已恢复500个，处理第1个 | 1/1000 = 0.1% ❌ | 501/1000 = 50.1% |

### 解决思路

**方案**: 使用实际已完成数量

```python
# 原方案
progress_callback(processed_count, total, kp_name)  # processed_count 是循环索引

# 新方案
completed_total = len(results) + 1  # 包含已恢复的断点
progress_callback(completed_total, total, kp_name)
```

---

## 八、异常处理问题

### 问题描述

LLM 调用失败时中断整个知识点处理：

```python
for concept in kg_concepts:
    vote_result = await vote_with_retry(prompt)  # 失败会中断循环
```

### 解决思路

**方案**: try-catch 继续下一个候选

```python
for concept in kg_concepts:
    try:
        vote_result = await vote_with_retry(prompt)
        if vote_result['consensus']:
            results.append(...)
    except Exception as e:
        logger.warning(f"LLM调用失败: {e}")
        continue  # 继续下一个候选
```

---

## 九、未匹配记录问题

### 问题描述

原方案只输出匹配成功的知识点，无法分析未匹配原因：

| 输出 | 内容 |
|------|------|
| matches_kg_relations.json | 仅含匹配成功的 |

### 解决思路

**方案**: 输出所有知识点，增加 `matched` 字段

```python
result = {
    'textbook_kp_uri': kp_uri,
    'textbook_kp_name': kp_name,
    'kg_uri': match['kg_uri'] if match else None,
    'kg_name': match['kg_name'] if match else None,
    'confidence': match['confidence'] if match else 0.0,
    'matched': True if match else False,
    'reason': '...' if not match else None
}
```

**效果**:
- 可分析未匹配原因
- 统计匹配率

---

## 十、向量索引构建问题

### 问题描述

每次匹配都重新加载模型和计算向量索引：

| 步骤 | 耗时 |
|------|------|
| 加载模型 | ~30秒 |
| 计算向量 | ~30秒 |
| 总计 | **~60秒** |

### 解决思路

**方案**: 预构建索引脚本

**计划**:
```bash
# 预构建索引（一次）
python build_vector_index.py

# 使用预构建索引（多次）
python match_textbook_kp.py --use-prebuilt-index
```

**索引文件**:
```
output/vector_index/
├── kg_vectors.npy       # 向量矩阵
├── kg_texts.json        # 知识点文本
├── kg_concepts.json     # 知识点元数据
└── index_meta.json      # 元数据（含checksum）
```

**状态**: 待实现（vector-index-script change）

---

## 总结：问题与解决对照表

| 问题 | 解决方案 | 状态 |
|------|---------|------|
| 数据缺失 | LLM推断补全 | ✅ 已完成 |
| 匹配效率低 | 向量检索粗筛 | ✅ 已完成 |
| 语义匹配弱 | 向量检索 + 同义词 | ✅ 已完成 |
| 同义词过度匹配 | 完整词匹配 | ✅ 已完成 |
| Topic继承偏差 | 基于Class类型修正 | ✅ 已完成（修正144个） |
| 断点续传 | llmTaskLock集成 | ✅ 已完成 |
| 进度显示不准确 | 使用实际已完成数 | ✅ 已完成 |
| 异常中断 | try-catch继续 | ✅ 已完成 |
| 未匹配无记录 | 输出所有+matched字段 | ✅ 已完成 |
| 索引重复构建 | 预构建脚本 | 📋 待实现 |

---

## 关键文件

| 文件 | 说明 |
|------|------|
| `kp_matcher.py` | 知识点匹配器（向量检索 + 双模型投票） |
| `textbook_kp_inferer.py` | 教学知识点推断器 |
| `kp_attribute_inferer.py` | 知识点属性推断器 |
| `dual_model_voter.py` | 双模型投票机制 |
| `llmTaskLock.py` | 断点续传模块 |

---

## 经验总结

### 1. 性能优化优先级

```
LLM调用次数 > 字符比较次数 > 内存占用
```

减少 LLM 调用是核心，其他优化是次要。

### 2. 语义匹配策略

```
向量检索 > 同义词映射 > difflib
```

向量检索是最强大的语义匹配方式。

### 3. 健壮性设计

```
try-catch > 断点续传 > 进度显示
```

确保任务可恢复、可中断。

### 4. 数据完整性

```
输出全部 > 仅输出成功
```

输出所有结果便于分析和改进。

---

## 十一、属性覆盖率低问题（新发现）

### 问题描述

```
textbook_kps.json:       1350 个知识点
textbook_kps_enhanced.json: 299 个知识点（仅 22% 有属性）
```

### 根因分析

**执行顺序问题**：

```
时间线：
12:10 → 属性增强 (enhance_kp_attributes.py) - 仅处理原有 299 个知识点
13:47 → LLM 推断 (infer_textbook_kp.py) - 新增 1052 个知识点
14:45 → 合并知识点 (merge_inferred_kps.py) - 合并后共 1350 个

问题：属性增强在 LLM 推断之前执行，导致推断的知识点缺少属性
```

### 解决方案

**重新运行属性增强**：

```bash
# 对所有 1350 知识点重新推断属性
python edukg/scripts/kg_data/enhance_kp_attributes.py --enhance --force
python edukg/scripts/kg_data/enhance_kp_attributes.py --merge
```

### 影响范围

- 仅影响属性覆盖率，不影响属性质量
- 规则匹配推断（无 LLM），可快速重新执行

---

## 十二、知识点匹配率低问题（新发现）

### 问题描述

```
匹配统计：
- 精确匹配：202 个 (15%)
- LLM 匹配：27 个 (2%)
- 未匹配：1121 个 (83%)

匹配率仅 17%，LLM 匹配率仅 2%
```

### 根因分析

**结构错位问题**：

```
教材知识点分布：
- 小学：940 个 (69.6%)
- 初中：252 个 (18.7%)
- 高中：158 个 (11.7%)

EduKG 知识点分布：
- 1,295 个抽象数学概念
- 几乎无小学具体知识点（如 "1-5的认识"、"连加连减"）
- 以高中抽象概念为主（如 "函数"、"方程"、"几何"）

问题：69.6% 的教材知识点（小学）无法匹配 EduKG 抽象概念
```

**示例对比**：

| 教材知识点 | EduKG 知识点 | 语义差距 |
|-----------|-------------|---------|
| "1-5的认识" | 自然数 | 教材名称贴近教学场景 |
| "连加连减" | 加法、减法 | EduKG 概念更抽象 |
| "秒的认识" | 秒、时间单位 | 命名风格差异 |
| "平行四边形的性质" | 平行四边形 | 可匹配，但需语义转换 |

### 解决方案

**知识点标准化预处理**：

采用两阶段匹配策略：

```
Phase 1: LLM 标准化预处理
  教材知识点 → LLM 推断标准名称 → 抽象概念列表

Phase 2: 向量检索 + LLM 投票
  抽象概念 → 向量检索 top-20 → LLM 双模型投票 → 匹配结果
```

**实现模块**：`kp_normalizer.py`

```python
from edukg.core.textbook import KPNormalizer

normalizer = KPNormalizer()
result = await normalizer.normalize("1-5的认识", "小学", "一年级")
# 返回: {"concepts": ["数的认识", "自然数", "数字"], "confidence": 0.9}
```

**效果验证**：

| 教材知识点 | LLM 推断概念 | EduKG 匹配结果 |
|-----------|-------------|---------------|
| "1-5的认识" | 自然数的基本概念 | 自然数 (0.711) ✓ |
| "连加连减" | 加法, 减法 | 减法 (0.655) ✓ |
| "秒的认识" | 时间单位, 秒的概念 | 秒 (0.830) ✓ |
| "平行四边形的性质" | 平行四边形定理 | 平行四边形 (0.853) ✓ |

---

## 十三、LLM 调用效率低问题（穿尽遍历）

### 问题描述

```
原始逻辑：
- 遍历全部 20 个候选
- 每个候选调用 2 次 LLM（GLM + DeepSeek）
- 最坏情况：40 次 API 调用/知识点
- 实测：3.5 小时仅完成 290 个知识点（21.5%）
```

### 根因分析

**穷尽遍历问题**：

```python
# 原始逻辑（低效）
for candidate in top_20_candidates:
    result = llm_vote(candidate)  # 每个都调用 2 次 LLM
    if result.matched:
        return result
# 即使第一个候选匹配成功，也要遍历全部 20 个
```

### 解决方案

**三重优化策略**：

```python
# 优化参数
LLM_CANDIDATE_LIMIT = 3      # 只对前 N 个候选做 LLM 投票
SIMILARITY_THRESHOLD = 0.5   # 相似度阈值，低于此值跳过
```

**优化后流程**：

```
for candidate in top-20:
    ① 相似度阈值检查
       if candidate.similarity < 0.5:
           continue  # 直接跳过，不调用 LLM

    ② LLM 调用上限检查
       if llm_calls >= 3:
           break  # 停止遍历，记录最佳候选待审核

    ③ LLM 双模型投票
       result = llm_vote(candidate)
       if result.matched:
           break  # 早停：匹配成功立即退出

    ④ 记录最佳未匹配候选
       best_unmatched = candidate  # 供人工审核
```

**效果对比**：

| 场景 | 原始逻辑 | 优化后 | 提升 |
|------|----------|--------|------|
| 第1个候选匹配成功 | 40 次 API | 2 次 API | **20x** |
| 前3个候选都不匹配 | 40 次 API | 6 次 API | **6.7x** |
| 所有候选相似度都低 | 40 次 API | 0 次 API | **∞** |

**实测效果**：
- 原始：3.5 小时 → 290 知识点（0.14 知识点/分钟）
- 优化：~7 知识点/分钟（新知识点）
- **整体提速约 50x**

---

## 十四、缓存机制不明确问题

### 问题描述

用户提问："缓存文件有效复用是什么意思？"

### 根因分析

**缓存机制未文档化**：

```
llm_cache/
├── 252441f392cbcc34.json
├── ...
└── 8255 个缓存文件

用户不理解缓存的作用和价值
```

### 解决方案

**缓存机制说明**：

1. **缓存内容**：
```json
{
  "result": {
    "decision": false,
    "confidence": 0.7,
    "primary_reason": "概念不同...",
    "secondary_reason": "概念不同..."
  },
  "primary_response": {"model": "glm-4-flash", ...},
  "secondary_response": {"model": "deepseek-chat", ...}
}
```

2. **缓存作用**：
- 存储 GLM + DeepSeek 双模型投票结果
- 相同知识点对（教材KP + 图谱KP）重复匹配时直接读取
- **跳过 2 次 API 调用**

3. **缓存键**：
```
cache_key = hashlib.md5(f"{textbook_kp}_{kg_kp}".encode()).hexdigest()
```

4. **复用效果**：
```
首次匹配：调用 GLM + DeepSeek（2 次 API）
再次匹配：读取缓存文件（0 次 API）

8255 个缓存 → 可节省 8255 × 2 = 16,510 次 API 调用
```

---

## 总结：问题与解决对照表（更新）

| 问题 | 解决方案 | 状态 |
|------|---------|------|
| 数据缺失 | LLM推断补全 | ✅ 已完成 |
| 匹配效率低 | 向量检索粗筛 | ✅ 已完成 |
| 语义匹配弱 | 向量检索 + 同义词 | ✅ 已完成 |
| 同义词过度匹配 | 完整词匹配 | ✅ 已完成 |
| Topic继承偏差 | 基于Class类型修正 | ✅ 已完成（修正144个） |
| 断点续传 | llmTaskLock集成 | ✅ 已完成 |
| 进度显示不准确 | 使用实际已完成数 | ✅ 已完成 |
| 异常中断 | try-catch继续 | ✅ 已完成 |
| 未匹配无记录 | 输出所有+matched字段 | ✅ 已完成 |
| 索引重复构建 | 预构建脚本 | ✅ 已完成 |
| **属性覆盖率低** | 重运行属性增强 | 📋 待执行 |
| **匹配率低(结构错位)** | LLM标准化预处理 | ✅ 已实现 |
| **LLM效率低(穿尽遍历)** | 早停+阈值+限制 | ✅ 已完成 |
| **缓存机制不明确** | 文档说明 | ✅ 已完成 |
| **未匹配知识点处理** | 人工审核系统设计 | 📋 待实现 |
| **知识图谱导入** | Cypher批量导入 | 📋 待执行 |

---

## 十五、未匹配知识点处理问题（新解决）

### 问题描述

知识点匹配完成后，308 个知识点未匹配，需要工程化手段处理：

```
未匹配分类：
- 颗粒度差异: 297 条（教材更细粒度，如"分数除法意义"）
- 图谱缺失: 11 条（如"田忌赛马故事背景"、"莫比乌斯带定义"）
```

### 解决方案

**方案**: 人工审核系统（MySQL + LLM推荐 + Web审核）

**数据流程**:
```
match_textbook_kp.py 匹配完成
    ↓ 自动保存
unmatched_kps.json (308条未匹配 + 候选列表)
    ↓ import_to_mysql.py
MySQL textbook_kp_match_review 表
    ↓ 审核页面
人工审核（确认/拒绝/创建新KP）
    ↓ export + import
Neo4j MATCHES_KG 关系
```

**状态**: 已创建 `kp-match-review-system` change，数据导出完成，MySQL导入待执行

---

## 十六、知识点匹配结果（最终统计）

### 匹配统计

| 类型 | 数量 | 占比 |
|------|------|------|
| 总知识点 | 1350 | 100% |
| 精确匹配 | 1025 | 75.9% |
| LLM 匹配 | 17 | 1.3% |
| 未匹配 | 308 | 22.8% |

### Topic修正结果

基于匹配的 EduKG Concept Class 类型修正：

```
修正前：
  数与代数: 855 (63.3%)
  图形与几何: 359 (26.6%)

修正后：
  数与代数: 891 (+36, 66.0%)
  图形与几何: 315 (-44, 23.3%)
```

修正示例：
- "作轴对称图形": 图形与几何 → 数与代数 (Class: 代数概念)
- "三角形定义": 数与代数 → 图形与几何 (Class: 面)

---

## 新增关键文件

| 文件 | 说明 |
|------|------|
| `kp_normalizer.py` | 知识点标准化预处理（新） |
| `prompts/kp_normalizer.txt` | 标准化提示词模板（新） |
| `output/normalizer_cache/` | 标准化结果缓存（新） |
| `output/llm_cache/` | 匹配投票结果缓存 |