# 掌握度信号题型化 测试用例设计

## 1. 测试概述

### 1.1 测试目标
验证 `mastery_signals` 从知识点粒度翻转为题型粒度：字段名 `topic_label`、输出题型语义、题型名稳定、不接地 snapshot、纠错提示词字段名同步，且不影响 decide 主流程（type/eval/question_kps/signal）。

### 1.2 测试方式
- **unit**: 纯函数/prompt 断言 + Pydantic 模型字段断言 + 结构化纠错提示词断言
- **real**: 真实模型对鸡兔同笼题输出题型名（有 key 才跑）

---

## 2. 测试数据

| 参数 | 值 | 说明 |
|-----|-----|------|
| TOPIC_LABEL | 鸡兔同笼 | 题型名（topic_label 应输出） |
| KP_LABEL | 二元一次方程组 | 知识点名（不应作为 topic_label 输出） |
| QUESTION | 鸡兔同笼，共35头94脚，各几只？ | 当前题目 |

---

## 3. 测试用例清单

### 3.1 模型字段（unit, test_models.py）

| 用例编号 | 场景 | 输入 | 预期 |
|---------|------|------|------|
| MODEL-001 | MasterySignalItem 字段名为 topic_label | topic_label + signal | Pydantic 校验通过 |
| MODEL-002 | 旧字段名 kp_label 拒绝 | kp_label + signal | Pydantic 校验失败（字段已改名） |

### 3.2 结构化纠错提示词（unit, test_structured.py）

| 用例编号 | 场景 | 输入 | 预期 |
|---------|------|------|------|
| STR-001 | _schema_instructions 字段名同步 | 调用 _schema_instructions() | 输出含 "topic_label"，不含 "kp_label" |

### 3.3 prompt 断言（unit, test_prompts.py）

| 用例编号 | 场景 | 输入 | 预期 |
|---------|------|------|------|
| PROMPT-001 | 输出题型语义 | build_decide_prompt | prompt 含「题型」约束、不含「输出知识点」 |
| PROMPT-002 | 题型名稳定规范 | build_decide_prompt | prompt 含「同一题型一致命名/别换说法」约束 |
| PROMPT-003 | 不接地 snapshot | build_decide_prompt(snapshot_labels) | mastery_signals 段不含「优先复用快照候选」 |
| PROMPT-004 | JSON 示例字段名 | build_decide_prompt | 含 "topic_label"，不含 "kp_label" |
| PROMPT-005 | question_kps 仍知识点 | build_decide_prompt | question_kps 段仍为「知识点」 |

### 3.4 回归（unit, 既有用例）

| 用例编号 | 场景 | 输入 | 预期 |
|---------|------|------|------|
| REG-001 | type 判定不受影响 | 既有 test_first_message_defaults_to_hint 等 | 保持通过 |
| REG-002 | signal 枚举不变 | 既有 mastered/practicing/struggling 断言 | 保持通过 |

### 3.5 real（真实模型，skip 无 key）

| 用例编号 | 场景 | 输入 | 预期 |
|---------|------|------|------|
| REAL-001 | 鸡兔同笼题输出题型 | 鸡兔同笼题目 | topic_label 为「鸡兔同笼」而非「二元一次方程组」 |

---

## 4. 运行测试

```bash
pytest ai-edu-ai-service/tests/tutoring/unit/ -v
pytest ai-edu-ai-service/tests/tutoring/real/ -v   # 有 key 才跑
```
