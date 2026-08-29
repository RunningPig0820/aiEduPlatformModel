> summary: 本文档为数学知识图谱前置关系推断设计：区分教学顺序TEACHES_BEFORE与学习依赖PREREQUISITE，基于教材章节顺序、定义文本依赖、LLM双模型投票等多证据融合生成前置关系。核心决策覆盖双模型投票模块dual_model_voter、提示词文件化、教学知识点推断textbook_kp_inferer、llmTaskLock断点续传、输出文件结构与config配置，权威度0.7设计素材。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-source/knowledge-graph/OpenSpec设计决策/design-python-kg-math-prerequisite-inference.md
> 类别：数据关联

# Python 数学知识图谱前置关系推断设计（kg-math-prerequisite-inference）

## 文档说明
> 本文件为原始spec文档的RAG结构化重构版本。
> 重要提示：本文属于**设计阶段素材**，同时包含已落地、构想未实现、待决策内容；业务真实实现请以权威度0.8的canonical真相源文档为准。本文件独立完整，内容不拆分到外部canonical文档。

### Context：前置关系推断背景与约束
> 状态：
> 检索摘要：前置关系推断是知识图谱项目核心设计成本：需区分教学顺序TEACHES_BEFORE与学习依赖PREREQUISITE，多证据融合生成高质量前置关系，设计约束含多模型投票与断点续传。

前置关系推断是知识图谱项目的**核心设计成本**部分。需要区分教学顺序（TEACHES_BEFORE）和学习依赖（PREREQUISITE），通过多证据融合生成高质量的前置关系数据。

当前状态：
- **知识点**: 已导入 EduKG 数据（Class 39, Concept 1,295, Statement 2,932）
- **原生关系**: 已导入 RELATED_TO 10,183, SUB_CLASS_OF 38, PART_OF 298, BELONGS_TO 619
- **LLM Gateway**: 支持 GLM-4-flash（免费）和 DeepSeek-V3（低成本）
- **教材数据**: 已生成 TextbookKP 299 个（小学47 + 初中252）

设计约束：
- 区分教学顺序 vs 学习依赖
- 使用多模型投票提高准确率
- 保留低置信度关系作为候选
- **所有 LLM 任务必须支持断点续传**
- **核心代码放入 `edukg/core/llm_inference/`，scripts 只做命令行入口**

### Goals / Non-Goals
> 状态：
> 检索摘要：目标：按教材章节顺序推断TEACHES_BEFORE、LLM多模型投票推断PREREQUISITE、定义依赖抽取、推断教学知识点并融合多证据输出JSON；非目标：不处理其他学科、不做人工审核、不处理高中数据。

**Goals:**
- 基于教材章节顺序推断 TEACHES_BEFORE
- 从定义文本抽取定义依赖
- LLM 多模型投票推断 PREREQUISITE
- 从教材章节推断教学知识点（补全缺失数据）
- 融合多证据来源
- 输出 JSON 文件（手动验证后导入）
- 支持 LLM 任务断点续传

**Non-Goals:**
- 不处理其他学科（物理/化学等）
- 不做人工审核（Demo 阶段自动化）
- 不处理高中数据（知识点数据源缺失）

### D1：目录结构设计
> 状态：
> 检索摘要：目录结构设计：核心代码放edukg/core/llm_inference/，含dual_model_voter、prerequisite_inferer、textbook_kp_inferer与prompts，scripts仅做命令行入口。

**核心代码放入 `edukg/core/llm_inference/`**：

```
edukg/core/llm_inference/
├── __init__.py              # 模块导出
├── config.py                # 配置（模型、阈值等）
├── prompt_templates.py      # Prompt 加载和格式化
├── dual_model_voter.py      # 双模型投票核心逻辑
├── prerequisite_inferer.py  # 前置关系推断
├── textbook_kp_inferer.py   # 教学知识点推断（新增）
├── README.md                # 模块文档
└── prompts/                 # 提示词文件目录（新增）
    ├── prerequisite.txt     # 前置关系推断提示词
    ├── kp_match.txt         # 知识点匹配提示词
    ├── definition_deps.txt  # 定义依赖抽取提示词
    └── textbook_kg.txt      # 教学知识点推断提示词
```

**scripts 只做命令行入口**：

```
edukg/scripts/kg_inference/
├── infer_prerequisites.py   # 前置关系推断入口
├── infer_textbook_kp.py     # 教学知识点推断入口（新增）
└── validate_dag.py          # DAG 验证入口
```

### D2：双模型投票模块 (dual_model_voter.py)
> 状态：
> 检索摘要：双模型投票模块：主模型glm-4-flash+副模型deepseek-chat，返回consensus/result/confidence；一致且置信度≥0.8为PREREQUISITE，<0.8为CANDIDATE，不一致不采纳。

```python
class DualModelVoter:
    """双模型投票器"""

    def __init__(
        self,
        primary_model: str = "glm-4-flash",
        secondary_model: str = "deepseek-chat",
        llm_gateway: Any = None  # 支持依赖注入
    ):
        self.primary_model = primary_model
        self.secondary_model = secondary_model
        self._llm_gateway = llm_gateway

    async def vote(self, prompt: str) -> Dict:
        """
        两模型投票

        Returns:
            {
                'consensus': bool,       # 是否达成一致
                'result': Any,           # 投票结果
                'confidence': float,     # 置信度
                'primary_response': ..., # 主模型响应
                'secondary_response': ... # 副模型响应
            }
        """
```

**投票规则**：

| 两模型结果 | 置信度 | 状态 |
|------------|--------|------|
| 一致 | ≥ 0.8 | PREREQUISITE |
| 一致 | < 0.8 | PREREQUISITE_CANDIDATE |
| 不一致 | - | 不采纳 |

### D3：提示词文件化设计
> 状态：
> 检索摘要：提示词文件化设计：从代码内联改为独立prompts/*.txt文件，PromptLoader支持文件加载与MySQL加载扩展，便于修改维护。

**决策**: 提示词从代码内联改为独立文件，便于修改和后续扩展从 MySQL 加载。

```
edukg/core/llm_inference/prompts/
├── prerequisite.txt     # 前置关系推断
├── kp_match.txt         # 知识点匹配
├── definition_deps.txt  # 定义依赖抽取
└── textbook_kg.txt      # 教学知识点推断
```

**PromptLoader 类**：

```python
class PromptLoader:
    def load(self, name: str, use_cache: bool = True) -> str:
        """从文件加载提示词"""

    def _load_from_file(self, name: str) -> str:
        """从 prompts/{name}.txt 加载"""

    def _load_from_db(self, name: str) -> str:
        """从 MySQL 加载（TODO: 后续扩展）"""

    def format(self, template: str, **kwargs) -> str:
        """格式化提示词"""
```

### D4：教学知识点推断模块 (textbook_kp_inferer.py)
> 状态：
> 检索摘要：教学知识点推断模块：TextbookKPInferer用双模型投票推断小学3-6年级与高中缺失的knowledge_points，支持infer_batch断点续传。

**背景**: 教材数据中小学3-6年级、高中知识点的 `knowledge_points` 字段为空，需要 LLM 推断补全。

```python
class TextbookKPInferer:
    """教学知识点推断器"""

    def __init__(self, voter: DualModelVoter):
        self.voter = voter

    async def infer_section(
        self,
        stage: str,          # 学段
        grade: str,          # 年级
        semester: str,       # 册次
        chapter_name: str,   # 章节名称
        section_name: str,   # 小节名称
        existing_kps: List[str] = None  # 已有知识点
    ) -> Dict:
        """
        推断单个小节的教学知识点

        Returns:
            {
                'knowledge_points': [...],
                'confidence': 0.0-1.0,
                'notes': '推断依据'
            }
        """

    async def infer_batch(
        self,
        sections: List[Dict],
        resume: bool = True  # 断点续传
    ) -> List[Dict]:
        """批量推断"""
```

**提示词 (textbook_kg.txt)**：

```
输入：
- 学段、年级、册次
- 章节名称、小节名称
- 已有知识点（如为空则需推断）

输出：
{
    "knowledge_points": ["知识点1", "知识点2", ...],
    "confidence": 0.85,
    "notes": "依据人教版七年级上册1.1节标准教学内容"
}
```

### D5：断点续传设计（集成 llmTaskLock）
> 状态：
> 检索摘要：断点续传设计：所有LLM推断任务集成llmTaskLock（TaskState/CachedLLM/ProcessLock），前置关系推断用infer_prerequisites.py --resume，教材顺序推断与DAG验证无需续传。

**决策**: 所有 LLM 推断任务必须支持断点续传，使用 `llmTaskLock` 模块。

**需要断点续传的任务**：

- **前置关系推断**
  - 核心模块：`edukg/core/llm_inference/prerequisite_inferer.py`
  - 命令行入口：`infer_prerequisites.py --resume`
  - 进度文件：`progress/prerequisite_state.json`
  - 锁文件：`progress/prerequisite.lock`

**不需要断点续传的任务**：
- 教材顺序推断 (`infer_from_textbook_order`) - 基于章节顺序，无 LLM 调用
- 定义依赖抽取 (`extract_from_definition`) - 文本解析，瞬时完成
- DAG 验证 (`validate_dag.py`) - 图算法，无 LLM 调用

**注意**: 教学知识点推断 (`TextbookKPInferer`) 在 `kg-math-complete-graph` 中实现，本模块复用其输出结果。

**集成示例 (PrerequisiteInferer)**：

```python
from edukg.core.llmTaskLock import TaskState, CachedLLM, ProcessLock

class PrerequisiteInferer:
    def __init__(self, ...):
        self.task_state = TaskState("prerequisite_inference")
        self.cached_llm = CachedLLM("prerequisite_cache")
        self.process_lock = ProcessLock("prerequisite.lock")

    async def infer_batch(self, kp_pairs, resume=True):
        # 加载进度
        if resume:
            completed = self.task_state.load()

        # 进程锁保护
        with self.process_lock:
            for pair in kp_pairs:
                # 跳过已完成的
                pair_id = self._make_pair_id(pair)
                if pair_id in completed:
                    continue

                # 检查缓存
                cached = self.cached_llm.get(pair)
                if cached:
                    results.append(cached)
                    continue

                # 执行推断
                result = await self._infer_one(pair)

                # 缓存结果
                self.cached_llm.set(pair, result)

                # 记录完成
                self.task_state.mark_done(pair_id)

                # 每 N 个保存进度
                if len(results) % 10 == 0:
                    self.task_state.save()

            # 最终保存
            self.task_state.save()
```

**llmTaskLock 组件**：

| 组件 | 功能 |
|------|------|
| `TaskState` | 任务状态管理（已处理的知识点对 ID） |
| `CachedLLM` | LLM 调用缓存（相同输入复用结果） |
| `ProcessLock` | 进程锁保护（防止多进程冲突） |

### D6：输出文件结构
> 状态：
> 检索摘要：输出文件结构：edukg/data/edukg/math/6_推理结果/output/下输出teaches_before、definition_deps、llm_prereq等JSON、validation_report与进度文件。

```
edukg/data/edukg/math/6_推理结果/output/
├── teaches_before.json       # TEACHES_BEFORE 关系
├── definition_deps.json      # 定义依赖
├── llm_prereq.json           # LLM 推断的前置关系
├── textbook_kps_inferred.json # 推断的教学知识点（新增）
├── final_prereq.json         # 融合后的最终前置关系
├── validation_report.json    # DAG 验证报告
└── progress/                 # 进度文件目录（新增）
    ├── prerequisite_state.json
    ├── textbook_kp_state.json
    └── *.lock
```

### D7：配置 (config.py)
> 状态：
> 检索摘要：配置config.py：主模型glm-4-flash与副模型deepseek-chat，投票阈值0.8/0.6，批量BATCH_SIZE=10与断点续传保存间隔10。

```python
# 模型配置
PRIMARY_MODEL = "glm-4-flash"      # 免费
SECONDARY_MODEL = "deepseek-chat"  # DeepSeek-V3

# 投票阈值
CONFIDENCE_THRESHOLD_HIGH = 0.8
CONFIDENCE_THRESHOLD_LOW = 0.6

# 批量处理
BATCH_SIZE = 10
RATE_LIMIT_DELAY = 1.0

# 断点续传
CHECKPOINT_INTERVAL = 10  # 每 N 个保存进度
PROGRESS_DIR = "edukg/data/edukg/math/6_推理结果/output/progress/"
```

### Risk 1：LLM 推断准确率不足
> 状态：
> 检索摘要：风险：LLM可能错误推断前置关系或教学知识点，缓解用多模型投票+置信度阈值+候选关系保留+人工验证。

**风险**: LLM 可能错误推断前置关系或教学知识点
**缓解**: 多模型投票 + 置信度阈值 + 候选关系保留 + 人工验证

### Risk 2：成本超预期
> 状态：
> 检索摘要：风险：LLM调用次数超预期导致成本超支，缓解以免费模型为主+缓存复用+监控调用次数。

**风险**: 实际调用次数超过预期
**缓解**: 使用免费模型为主 + 缓存复用 + 监控调用次数

### Risk 3：DAG 出现环
> 状态：
> 检索摘要：风险：前置关系可能形成循环依赖环，缓解输出后DAG验证+发现环时报警。

**风险**: 前置关系可能形成循环依赖
**缓解**: 输出后验证 + 发现环时报警

### Risk 4：断点续传文件损坏
> 状态：
> 检索摘要：风险：断点续传进度文件可能损坏或丢失，缓解定期备份+JSON格式易恢复。

**风险**: 进度文件可能损坏或丢失
**缓解**: 定期备份 + JSON 格式易恢复

### Migration Plan 迁移计划
> 状态：
> 检索摘要：迁移计划：完善核心模块、更新提示词、开发命令行入口，先运行知识点推断再运行前置推断，最后DAG验证与人工导入。

**执行步骤**:

1. **完善核心模块**:
   - 创建 `textbook_kp_inferer.py`
   - 集成 `llmTaskLock` 到推断器

2. **更新提示词**:
   - 创建 `prompts/` 目录
   - 迁移提示词到独立文件

3. **开发命令行入口**:
   - 更新 `infer_prerequisites.py` 支持 `--resume`
   - 创建 `infer_textbook_kp.py`

4. **运行推理**:
   - 先运行教学知识点推断（补全数据）
   - 再运行前置关系推断

5. **验证和导入**:
   - DAG 验证
   - 人工验证后导入 Neo4j

### Open Questions 开放问题
> 状态：
> 检索摘要：开放问题已确定：无遗留待决策项，设计已拍板。

无（设计已确定）
