# 初高中知识点处理问题与解决思路

> 基于 kg-math-complete-graph 项目实践总结
>
> 更新日期: 2026-04-12

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
| Topic继承偏差 | 基于Class类型修正 | 📋 待实现 |
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