"""
任务 5.1/5.2: core/tutoring/vector_store.py 单测(mock 外部边界)

5.1 覆盖(端点层已在 test_vector_api.py 覆盖, 这里测 core 层):
- put_vector 正常: put_vectors 收到 Bucket/Index/Vectors(key + 768 维 float32 + metadata 透传)
- key 覆盖: 同 key 重写 → 第二次 put_vectors, key 不变
- query_vector 返回透传: hits 按 distance 升序 / 无近邻空数组
- 失败冒泡: embedding 失败 → 抛异常 / COS 失败 → 抛异常(端点层转 500)

5.2 覆盖:
- _resolve_index 路由: topic → topic-index;question/rag 占位不参与路由 → ValueError

Mock 边界 = embed + CosVectorsClient(_get_cos_client), 不碰真实 COS/dashscope。
"""
import sys
import os

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
)

import pytest

from config.settings import settings


class FakeCosClient:
    def __init__(self):
        self.put_calls = []
        self.query_result = None  # 默认: 返回空(无近邻)
        self.query_raise = None

    def put_vectors(self, Bucket=None, Index=None, Vectors=None, **kw):
        self.put_calls.append({"Bucket": Bucket, "Index": Index, "Vectors": Vectors})
        return {}

    def query_vectors(self, Bucket=None, Index=None, QueryVector=None, TopK=None, **kw):
        self.query_calls.append({"Bucket": Bucket, "Index": Index, "TopK": TopK})
        if self.query_raise:
            raise self.query_raise
        return {}, {"vectors": self.query_result or []}


@pytest.fixture
def fake(monkeypatch):
    from core.tutoring import vector_store as vs

    monkeypatch.setattr(vs, "embed", lambda text: [float(len(text))] * 768)
    fc = FakeCosClient()
    fc.query_calls = []
    monkeypatch.setattr(vs, "_get_cos_client", lambda: fc)
    return fc


class TestResolveIndex:
    """5.2 索引路由: vector_type → 物理索引映射;占位不参与路由"""

    def test_topic_maps_to_topic_index(self):
        from core.tutoring.vector_store import _resolve_index
        assert _resolve_index("topic") == "topic-index"

    def test_question_placeholder_rejected(self):
        from core.tutoring.vector_store import _resolve_index
        with pytest.raises(ValueError):
            _resolve_index("question")

    def test_rag_placeholder_rejected(self):
        from core.tutoring.vector_store import _resolve_index
        with pytest.raises(ValueError):
            _resolve_index("rag")

    def test_unknown_and_empty_rejected(self):
        from core.tutoring.vector_store import _resolve_index
        for bad in ["nope", "Topic", ""]:
            with pytest.raises(ValueError):
                _resolve_index(bad)


class TestPutVector:
    """5.1 put_vector"""

    def test_put_ok_payload(self, fake):
        from core.tutoring.vector_store import put_vector

        put_vector(key="q_5001", text="鸡兔同笼", vector_type="topic",
                   metadata={"topic_label": "鸡兔同笼"})

        assert len(fake.put_calls) == 1
        call = fake.put_calls[0]
        assert call["Bucket"] == settings.COS_VECTORS_BUCKET
        assert call["Index"] == "topic-index"
        vec = call["Vectors"][0]
        assert vec["key"] == "q_5001"
        assert len(vec["data"]["float32"]) == 768  # 维度对齐
        assert vec["metadata"] == {"topic_label": "鸡兔同笼"}  # metadata 透传

    def test_put_same_key_upsert(self, fake):
        from core.tutoring.vector_store import put_vector

        put_vector("q_5001", "鸡兔同笼", "topic", {"v": 1})
        put_vector("q_5001", "鸡兔同笼(改)", "topic", {"v": 2})

        assert len(fake.put_calls) == 2  # 第二次同 key 再写 → COS put_vectors 天然 upsert
        assert fake.put_calls[0]["Vectors"][0]["key"] == "q_5001"
        assert fake.put_calls[1]["Vectors"][0]["key"] == "q_5001"
        assert fake.put_calls[1]["Vectors"][0]["metadata"] == {"v": 2}

    def test_put_metadata_optional(self, fake):
        from core.tutoring.vector_store import put_vector

        put_vector("q_5001", "鸡兔同笼", "topic")  # metadata 缺省
        assert fake.put_calls[0]["Vectors"][0]["metadata"] == {}

    def test_put_unknown_vector_type(self, fake):
        from core.tutoring.vector_store import put_vector

        with pytest.raises(ValueError):
            put_vector("k", "t", "nope")


class TestQueryVector:
    """5.1 query_vector"""

    def test_query_ok_hits_passthrough(self, fake):
        from core.tutoring.vector_store import query_vector

        fake.query_result = [
            {"key": "a", "metadata": {}, "distance": 0.05},
            {"key": "b", "metadata": {}, "distance": 0.12},
        ]
        hits = query_vector("鸡兔同笼", 3, "topic")

        assert fake.query_calls[-1]["TopK"] == 3
        assert len(hits) == 2
        assert hits[0]["key"] == "a"  # distance 升序(COS 已排序, 透传)
        assert hits[1]["distance"] == 0.12

    def test_query_no_neighbor_empty(self, fake):
        from core.tutoring.vector_store import query_vector

        fake.query_result = []  # 无近邻
        assert query_vector("鸡兔同笼", 3, "topic") == []

    def test_query_unknown_vector_type(self, fake):
        from core.tutoring.vector_store import query_vector

        with pytest.raises(ValueError):
            query_vector("t", 3, "nope")


class TestFailures:
    """5.1 失败冒泡: embedding / COS 失败抛异常(端点层转 500, 不吞)"""

    def test_embedding_failure_put(self, fake, monkeypatch):
        from core.tutoring import vector_store as vs

        def boom(text):
            raise RuntimeError("dashscope embedding failed")
        monkeypatch.setattr(vs, "embed", boom)

        with pytest.raises(RuntimeError, match="embedding"):
            vs.put_vector("k", "t", "topic")
        assert fake.put_calls == []  # 未触碰 COS

    def test_embedding_failure_query(self, fake, monkeypatch):
        from core.tutoring import vector_store as vs

        def boom(text):
            raise RuntimeError("dashscope embedding failed")
        monkeypatch.setattr(vs, "embed", boom)

        with pytest.raises(RuntimeError, match="embedding"):
            vs.query_vector("t", 3, "topic")

    def test_cos_put_failure(self, fake, monkeypatch):
        from core.tutoring.vector_store import put_vector

        def boom_put(*a, **k):
            raise RuntimeError("cos put failed")
        monkeypatch.setattr(fake, "put_vectors", boom_put)

        with pytest.raises(RuntimeError, match="cos put"):
            put_vector("k", "t", "topic")

    def test_cos_query_failure(self, fake, monkeypatch):
        from core.tutoring.vector_store import query_vector

        fake.query_raise = RuntimeError("cos query failed")
        with pytest.raises(RuntimeError, match="cos query"):
            query_vector("t", 3, "topic")

    def test_unconfigured_cos_client(self, monkeypatch):
        """懒加载边界: COS_* 未配齐 → RuntimeError(不崩)"""
        from core.tutoring import vector_store as vs

        vs._client = None
        monkeypatch.setattr(settings, "COS_VECTORS_SECRET_ID", "")
        monkeypatch.setattr(settings, "COS_VECTORS_SECRET_KEY", "")
        with pytest.raises(RuntimeError, match="未配置完整"):
            vs._get_cos_client()
