"""
任务 2.3 评测集加载器测试

覆盖(2.3 加载器格式校验 + 评测集 curation 一致性):
- 正常加载: 5 条, 5 类各 1, 字段齐全
- 校验失败: 缺字段/类型错/question_type 非闭集/refs 空/points 空 → ValueError
- 条数下限: <5 条 → ValueError
- expected_references 与完善文档文件一致(引用节真实存在, 不指向不存在的节)

Mock 边界: 无(纯本地文件操作, 不碰 COS/LLM)。
"""
import sys
import os
import json

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
)

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "rag"))
import eval_dataset

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "rag", "data", "eval")
# tests/rag/ → ai-edu-ai-service → 项目根 → docs/rag/ai-tutoring/4.完善文档
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DOC_DIR = os.path.join(PROJECT_ROOT, "docs", "rag", "ai-tutoring", "4.完善文档")


@pytest.fixture
def tmp_dataset(tmp_path):
    """临时评测集文件"""
    return tmp_path / "ai-tutoring.jsonl"


def write(tmp_dataset, lines):
    tmp_dataset.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _valid_line():
    return json.dumps({
        "module": "ai-tutoring", "question": "怎么防学生套答案？",
        "question_type": "难点",
        "expected_references": ["ai-tutoring/04-安全与防作弊（护栏）"],
        "expected_points": ["reveal 两次出口", "count 计数"],
    }, ensure_ascii=False)


class TestLoadDataset:
    """2.3 加载器正常加载"""

    def test_load_6_items_all_types(self):
        """6 条 6 类(含 D1 边界拒答, 其 expected_references 允许空)"""
        items = eval_dataset.load_dataset()
        assert len(items) == 6
        types = [i["question_type"] for i in items]
        # 6 类各 1 条(集合相等, 顺序无关)
        assert set(types) == {"操作", "数据关联", "最危险", "项目介绍", "难点", "边界拒答"}
        assert len(set(types)) == 6
        for i in items:
            assert i["expected_points"]
            if i["question_type"] != "边界拒答":
                assert i["expected_references"]  # 非边界拒答类 refs 必填

    def test_validate_ok(self, tmp_dataset, monkeypatch):
        """单条通过格式校验(条数下限另测; 这里直接用 _validate)"""
        monkeypatch.setattr(eval_dataset, "DATA", str(tmp_dataset.parent))
        eval_dataset._validate(json.loads(_valid_line()), "inline", 1)  # 不抛即过

    def test_full_dataset_has_five(self):
        """真实评测集 5 条全过(加载器验证)"""
        assert len(eval_dataset.load_dataset()) >= eval_dataset.MIN_PER_MODULE


class TestValidation:
    """2.3 格式校验失败场景"""

    def _load(self, line, tmp_dataset, monkeypatch):
        monkeypatch.setattr(eval_dataset, "DATA", str(tmp_dataset.parent))
        write(tmp_dataset, [line])
        return eval_dataset.load_dataset()

    @pytest.fixture
    def setup(self, tmp_dataset, monkeypatch):
        return lambda line: self._load(line, tmp_dataset, monkeypatch)

    def test_missing_question(self, setup):
        bad = json.dumps({"module": "ai-tutoring", "question_type": "难点",
                          "expected_references": ["x"], "expected_points": ["y"]}, ensure_ascii=False)
        with pytest.raises(ValueError, match="question"):
            setup(bad)

    def test_invalid_type(self, setup):
        bad = json.dumps({"module": "ai-tutoring", "question": "q", "question_type": "闲聊",
                          "expected_references": ["x"], "expected_points": ["y"]}, ensure_ascii=False)
        with pytest.raises(ValueError, match="question_type"):
            setup(bad)

    def test_empty_references(self, setup):
        bad = json.dumps({"module": "ai-tutoring", "question": "q", "question_type": "难点",
                          "expected_references": [], "expected_points": ["y"]}, ensure_ascii=False)
        with pytest.raises(ValueError, match="expected_references"):
            setup(bad)

    def test_empty_points(self, setup):
        bad = json.dumps({"module": "ai-tutoring", "question": "q", "question_type": "难点",
                          "expected_references": ["x"], "expected_points": []}, ensure_ascii=False)
        with pytest.raises(ValueError, match="expected_points"):
            setup(bad)

    def test_wrong_module(self, setup):
        bad = json.dumps({"module": "kg", "question": "q", "question_type": "难点",
                          "expected_references": ["x"], "expected_points": ["y"]}, ensure_ascii=False)
        with pytest.raises(ValueError, match="module"):
            setup(bad)

    def test_boundary_type_allows_empty_refs(self):
        """D1: 边界拒答类型允许 expected_references 为空(预期不命中任何节)"""
        line = json.dumps({"module": "ai-tutoring", "question": "帮我写辞职信。",
                           "question_type": "边界拒答",
                           "expected_references": [], "expected_points": ["应拒答"]},
                          ensure_ascii=False)
        eval_dataset._validate(json.loads(line), "inline", 1)  # 不抛即过

    def test_boundary_type_invalid_type_rejected(self, setup):
        """D1: 非边界拒答类型 refs 空仍拒绝"""
        bad = json.dumps({"module": "ai-tutoring", "question": "q", "question_type": "难点",
                          "expected_references": [], "expected_points": ["y"]}, ensure_ascii=False)
        with pytest.raises(ValueError, match="expected_references"):
            setup(bad)

    def test_boundary_type_refs_must_be_str(self, setup):
        """D1: 边界拒答提供 refs 时元素仍须字符串"""
        bad = json.dumps({"module": "ai-tutoring", "question": "q", "question_type": "边界拒答",
                          "expected_references": [123], "expected_points": ["y"]},
                         ensure_ascii=False)
        with pytest.raises(ValueError, match="expected_references"):
            setup(bad)

    def test_bad_json_line(self, setup):
        with pytest.raises(ValueError, match="JSON 解析失败"):
            setup("{not valid json")

    def test_too_few_items(self, tmp_dataset, monkeypatch):
        monkeypatch.setattr(eval_dataset, "DATA", str(tmp_dataset.parent))
        write(tmp_dataset, [_valid_line()])
        # 单条 < MIN_PER_MODULE=5 → 失败
        with pytest.raises(ValueError, match="最少"):
            eval_dataset.load_dataset()


class TestReferenceConsistency:
    """2.3 curation 一致性: expected_references 指向的节必须真实存在(完善文档)"""

    def test_all_references_point_to_real_docs(self):
        """每个 expected_references 前缀(ai-tutoring/0X-...) 对应完善文档真实文件"""
        items = eval_dataset.load_dataset()
        doc_names = {f.split("-")[0] for f in os.listdir(DOC_DIR) if f.endswith(".md")} if os.path.isdir(DOC_DIR) else set()
        if not doc_names:
            pytest.skip("完善文档目录不存在")
        for i in items:
            for ref in i["expected_references"]:
                # ref 形如 ai-tutoring/01-模块定位 → 节号 01
                prefix = ref.split("/")[1] if "/" in ref else ref
                section = prefix.split("-")[0]
                assert section in doc_names, f"{ref} 指向不存在的节 {section}"
