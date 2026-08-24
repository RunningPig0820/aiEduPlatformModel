"""
2.3 评测集加载器 - 加载 + 格式校验

评测集格式(2A 定稿, 对齐 rag-eval-agent spec):
  {module, question, question_type, expected_references[], expected_points[]}
  - module: "ai-tutoring"(本期唯一)
  - question_type: 问题表分类(项目介绍/操作/数据关联/难点/最危险)
  - expected_references: 预期命中页/节 key 前缀(供 hit@k 判定"检索是否捞得对")
  - expected_points: 答案应覆盖要点(供 LLM 判分 answer_quality)

校验规则:
  - 每模块 ≥5 条; 字段齐全非空; question_type 在闭集内
  - expected_references 非空且为字符串列表; expected_points 非空
  失败抛 ValueError(评测集 curation 错误必须当场暴露, 不静默)

用法: python scripts/rag/eval_dataset.py   # 加载并打印校验摘要
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "eval")

# 闭集: 问题表分类(与 1.5A「8节↔问题表」映射一致)
VALID_TYPES = {"项目介绍", "操作", "数据关联", "难点", "最危险"}
MIN_PER_MODULE = 5


def load_dataset(module: str = "ai-tutoring") -> list:
    """加载并校验单个模块评测集 → list[dict]。校验失败抛 ValueError。"""
    path = os.path.join(DATA, f"{module}.jsonl")
    if not os.path.exists(path):
        raise ValueError(f"评测集不存在: {path}")
    items = []
    with open(path, encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as e:
                raise ValueError(f"{path}:{lineno} JSON 解析失败: {e}")
            _validate(item, path, lineno)
            items.append(item)
    if len(items) < MIN_PER_MODULE:
        raise ValueError(f"{module} 评测集 {len(items)} 条 < 最少 {MIN_PER_MODULE} 条")
    return items


def _validate(item: dict, path: str, lineno: int) -> None:
    err = lambda msg: ValueError(f"{path}:{lineno} 格式错误: {msg}")

    if not isinstance(item.get("question"), str) or not item["question"].strip():
        raise err("question 必填非空字符串")
    if not isinstance(item.get("question_type"), str) or item["question_type"] not in VALID_TYPES:
        raise err(f"question_type 必填且 ∈ {sorted(VALID_TYPES)}, 实际 {item.get('question_type')!r}")
    if not isinstance(item.get("expected_references"), list) or not item["expected_references"]:
        raise err("expected_references 必填非空列表")
    if not all(isinstance(r, str) and r for r in item["expected_references"]):
        raise err("expected_references 元素必须是非空字符串")
    if not isinstance(item.get("expected_points"), list) or not item["expected_points"]:
        raise err("expected_points 必填非空列表")
    if not all(isinstance(p, str) and p for p in item["expected_points"]):
        raise err("expected_points 元素必须是非空字符串")
    if item.get("module") != "ai-tutoring":
        raise err(f"module 应为 ai-tutoring, 实际 {item.get('module')!r}")


def main():
    items = load_dataset()
    types = {}
    for i in items:
        types[i["question_type"]] = types.get(i["question_type"], 0) + 1
    print(f"评测集加载: {len(items)} 条")
    print("按类型:", types)
    for i in items:
        print(f"  [{i['question_type']}] {i['question']}")
        print(f"      refs: {i['expected_references']}")
        print(f"      pts:  {i['expected_points']}")


if __name__ == "__main__":
    main()
