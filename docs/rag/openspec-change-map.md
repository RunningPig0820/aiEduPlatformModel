# OpenSpec 变更 → 功能模块 映射（全量，含归档）

> 3 仓库 OpenSpec 全量盘点：后端 `aiEduPlatform` / 前端 `aiEduPlatformFront` / Python `aiEduPlatformModel`
> **51 个变更**（活跃 31 + 归档 20），对应 5 个功能模块 + 基础底座
> 重要度：⭐⭐⭐ 必讲核心 ｜ ⭐⭐ 重点故事 ｜ ⭐ 支撑
> 2026-08-24

## 总览

| 功能模块 | 活跃 | 归档 | 合计 |
|---------|------|------|------|
| **AI答疑** | 14 | 1 | 15 |
| **知识图谱** | 4 | 9 | 13 |
| **组织中心** | 4 | 5 | 9 |
| **题型知识点** | 7 | 0 | 7 |
| **RAG问答系统** | 2 | 0 | 2 |
| **基础底座**（LLM网关/前端框架） | 0 | 5 | 5 |

---

## 一、AI答疑（15 个）

### 后端（Java 平台：认证/护栏/编排/数据）
| 变更 | 状态 | 一句话 |
|------|------|--------|
| ⭐⭐⭐ `ai-tutoring` | 活跃 | **核心**：能力受限 agent + 工具护栏，Java 网关编排 decide→guard→generate 类型先行流式；掌握度按 TextbookKP URI 落库 + 图谱点亮 |
| ⭐⭐ `tutoring-subject-gate` | 活跃 | **学科门**：decide 前学科无关分类，非数学题不建/不续会话、不落库、不耗轮次 |
| `tutoring-agent-events` | 活跃 | agent 阶段事件推 SSE，把 40s+ 等待黑盒变可见进展 |
| `tutoring-agent-workflow-backend` | 活跃 | 工作流六阶段移入回答气泡内 + SENDING 期 |
| `add-tutoring-session-history-backend` | 活跃 | 会话历史从 localStorage 迁后端，可删可跨设备 |

### 前端
| 变更 | 状态 | 一句话 |
|------|------|--------|
| ⭐⭐ `add-ai-tutoring-frontend` | 活跃 | **核心 UI**：拍照传题→OCR 确认→引导式解答流式展示 |
| `tutoring-subject-gate-frontend` | 活跃 | 学科门边界提示 |
| `add-tutoring-agent-events-frontend` | 活跃 | 事件可见化展示 |
| `show-tutoring-agent-workflow` | 活跃 | 工作流气泡内管线 + 思考子工作流 |
| `add-tutoring-session-mysql-history` | 活跃 | 历史会话列表 |

### Python（纯智能：LLM 推断）
| 变更 | 状态 | 一句话 |
|------|------|--------|
| ⭐⭐⭐ `ai-tutoring` | 活跃 | **核心**：decide（非流式动作元数据）+ generate（流式正文），动作 type 闭集 |
| ⭐⭐ `tutoring-subject-gate-python` | 活跃 | 学科无关分类器，K12 十值闭集，降级 math 放行 |
| ⭐⭐ `ai-tutoring-question-understand` | 活跃 | 图片题目识别题型（视觉模型，关思考+超时+关重试） |
| ⭐⭐ `ai-tutoring-decide-guide-not-end` | 活跃 | **答对判定修复**：不确定语气判对 / 学生断言复核 / end 一致性护栏 |
| ⭐⭐ `2026-08-12-tutoring-agent-protocol` | 归档 | **agent 协议**：decide 响应 JSON→SSE 流（感知→意图→规划→决策→生成→记忆），等待黑盒变可见——后续 `tutoring-agent-events` 的前身 |

---

## 二、知识图谱（13 个）

### 后端
| 变更 | 状态 | 一句话 |
|------|------|--------|
| ⭐⭐ `kp-matching-lightup` | 活跃 | 题型→教材知识点解析（label→URI）+ 掌握度点亮图谱 |
| `2026-06-03-knowledge-graph-datasource` | 归档 | Neo4j/MySQL 独立库 `ai_edu_kg`，与业务库物理隔离 |
| `2026-06-03-knowledge-graph-ui` | 归档 | 知识图谱数据建模 + 导航 API（Neo4j→MySQL） |

### 前端
| 变更 | 状态 | 一句话 |
|------|------|--------|
| `kp-matching-lightup-frontend` | 活跃 | 知识点匹配 + 图谱点亮展示 |
| `2026-06-09-knowledge-graph-ui-front` | 归档 | 图谱可视化：树形导航教材知识点 + 关系图谱 |

### Python
| 变更 | 状态 | 一句话 |
|------|------|--------|
| ⭐⭐⭐ `2026-04-15-kg-math-complete-graph` | 归档 | **里程碑**：知识图谱数据整合层——教材/章节/知识点生成 + 匹配 + Neo4j 导入，6,757 节点/20,887 关系/97.1% 匹配率 |
| ⭐⭐ `kg-math-prerequisite-inference` | 活跃 | **前置关系推断**（EduKG 只有 RELATED_TO，无 PREREQUISITE）：教材顺序+定义依赖+LLM 多证据融合 |
| `kp-match-review-system` | 活跃 | 未匹配知识点（308 个）人工审核工具化 |
| `2026-03-28-integrate-edukg-knowledge-graph` | 归档 | 接入 EduKG：从 TTL 构建学科知识点体系 |
| `2026-04-08-kg-infrastructure-init` | 归档 | 课标模块基础设施 |
| `2026-04-10-knowledge-graph-data-research` | 归档 | 答疑业务需要图谱数据的前期研究 |
| `2026-04-10-textbook-concept-linking` | 归档 | 教材章节↔知识点关联（1275 Concept/2810 Statement 缺教材锚点） |
| `2026-04-10-textbook-crawler` | 归档 | 小学/初中教材爬虫（EduKG 只有高中 main.ttl） |

---

## 三、组织中心（9 个）

### 后端
| 变更 | 状态 | 一句话 |
|------|------|--------|
| ⭐⭐ `organization-edu-management` | 活跃 | 行政班（学段→年级→班级）复用 `t_department` 树形能力 |
| `add-admin-class-student` | 活跃 | 跨域操作：创建/查询学生（身份证加密）+ 绑定家长，加入行政班 |
| ⭐⭐ `2026-06-03-organization-management` | 归档 | **基础**：学校组织作为权限管控基础单元（后续所有功能的隔离根） |
| `2026-06-09-add-org-teacher` | 归档 | 教职工与行政部门关联（人事管理） |

### 前端
| 变更 | 状态 | 一句话 |
|------|------|--------|
| `organization-edu-management` | 活跃 | 组织中心行政班管理 UI |
| `add-admin-class-student-frontend` | 活跃 | 行政班添加学生（Mock → 真 API） |
| `2026-06-03-organization-management-ui` | 归档 | 组织管理 UI（学校组织） |
| `2026-06-04-department-management-ui` | 归档 | 部门管理 UI（教师组织架构可视化） |
| `2026-06-09-add-org-teacher-frontend` | 归档 | 教职工管理 UI |

---

## 四、题型知识点（7 个）

### 后端
| 变更 | 状态 | 一句话 |
|------|------|--------|
| ⭐⭐⭐ `question-type-mastery-backend` | 活跃 | **掌握度=题型**：题目全入口采集→向量 COS→定时聚类 canonical→累计掌握程度 |
| `kp-question-analysis-backend` | 活跃 | 题型分析页「贴题→识别题型→关联知识点」独立入口 |

### 前端
| 变更 | 状态 | 一句话 |
|------|------|--------|
| `question-type-mastery` | 活跃 | 掌握度页列表展示：题型/来源/掌握程度/题目列表 |
| `kp-question-analysis` | 活跃 | 智能练习·题型分析页（贴题→识别+知识点参考） |

### Python
| 变更 | 状态 | 一句话 |
|------|------|--------|
| ⭐⭐ `question-type-mastery-python` | 活跃 | 题型动态聚集：散题型名向量归并 canonical |
| ⭐⭐ `ai-tutoring-topic-mastery-signal` | 活跃 | **掌握度主体翻转**：知识点→题型，知识点掌握度由题型×映射推导 |
| `add-question-kps` | 活跃 | Agent 工作流面板展示知识点（题目→知识点匹配） |

---

## 五、RAG问答系统（2 个）

| 变更 | 状态 | 一句话 |
|------|------|--------|
| ⭐⭐⭐ `project-intro-rag` | 活跃 | **本项目**：证明 RAG 能力 + 给面试官讲清每个页面；双池+两道门+完善文档语料 |
| ⭐⭐ `rag-eval-agent` | 活跃 | 可观测评测：hit@k + 质量分 + 版本对比 |

---

## 六、基础底座（5 个，全归档）

| 变更 | 端 | 一句话 |
|------|-----|--------|
| ⭐⭐ `2026-03-26-llm-gateway-multi-provider` | Python | **LLM 底座**：智谱/DeepSeek/百炼多 provider + 场景路由（后续所有 AI 能力的地基） |
| `2026-06-03-llm-gateway-integration` | 后端 | Java 对接 Python LLM 网关（9527）：页面助手/批改/FAQ/图片分析/内容生成 |
| `2026-06-09-ai-assistant-integration` | 前端 | AI 对话面板（对接网关，流式响应） |
| `2026-03-19-frontend-base-framework` | 前端 | 前端基础框架 |
| `2026-06-09-ui-modernization` | 前端 | UI 现代化（面试展示精致度） |

---

## 关键洞察

1. **AI答疑 三端协作最深**（15 变更）——Java 定护栏/状态，Python 纯智能，前端可视化。面试讲"微服务分工"靠它。
2. **"掌握度=题型"是跨 3 仓库的语义翻转**：`kp-matching-lightup` 翻转 → `question-type-mastery-*` 采集 → `ai-tutoring-topic-mastery-signal` 信号，一条完整演进线。
3. **知识图谱的真实工程量在归档**：6 个 Python 归档变更（EDU数据→教材爬虫→概念关联→完整图谱）才是"6,757 节点/97.1%"的来路，`kg-math-complete-graph` 是数据里程碑。
4. **组织中心是"学校为权限根"的演进**：归档 `organization-management`（学校基础）→ 部门 → 教职工 → 活跃 `organization-edu-management`（行政班）。
5. **归档 ≠ 不重要**：`tutoring-agent-protocol`（SSE演进）、`llm-gateway-multi-provider`（LLM底座）、`kg-math-complete-graph`（图谱里程碑）恰恰是面试"从哪来到哪去"的叙事素材。
