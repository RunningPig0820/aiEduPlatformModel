"""
任务 4: api/vector.py 端点测试(mock 外部边界, 走真实 put/query 业务逻辑)

覆盖:
- 鉴权: 缺 token → 403 / 错 token → 403 / 对 token → 正常
- 路由: 未知 vector_type → 400(真实 _resolve_index 逻辑) / 缺 vector_type → 422
- 端点: put 正常结构 / query 正常结构(vectors 字段) / 底层异常 → 500
- 失败冒泡: embedding / COS 失败 → 500(不吞异常, 与 question-understand 相反)

Mock 边界 = embed + CosVectorsClient(_get_cos_client);put_vector/query_vector 走真实实现,
确保未知 vector_type 抛 ValueError → 400 与 COS 失败 → 500 是真实路径验证。
"""
import sys
import os

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
)

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.vector import router as vector_router

app = FastAPI()
app.include_router(vector_router)
client = TestClient(app)

from config.settings import settings

TOKEN = settings.INTERNAL_TOKEN
AUTH = {"x-internal-token": TOKEN}


class FakeCosClient:
    """假 CosVectorsClient: 记录调用, 默认成功。"""

    def __init__(self):
        self.put_calls = []
        self.query_calls = []

    def put_vectors(self, Bucket=None, Index=None, Vectors=None, **kw):
        self.put_calls.append({"Bucket": Bucket, "Index": Index, "Vectors": Vectors})
        return {}

    def query_vectors(self, Bucket=None, Index=None, QueryVector=None, TopK=None, **kw):
        self.query_calls.append({"Bucket": Bucket, "Index": Index, "TopK": TopK})
        return {}, {"vectors": [
            {"key": "q_5001", "metadata": {"topic_label": "鸡兔同笼"}, "distance": 0.12},
        ]}


@pytest.fixture
def fake_cos(monkeypatch):
    """只 mock 外部边界: embed + CosVectorsClient;put/query 走真实逻辑。"""
    from core.tutoring import vector_store as vs

    monkeypatch.setattr(vs, "embed", lambda text: [0.0] * 768)
    fake = FakeCosClient()
    monkeypatch.setattr(vs, "_get_cos_client", lambda: fake)
    return fake


class TestAuth:
    def test_put_missing_token_403(self):
        r = client.post("/api/tutoring/vector/put",
                        json={"key": "k", "text": "t", "vector_type": "topic"})
        assert r.status_code == 403

    def test_put_wrong_token_403(self):
        r = client.post("/api/tutoring/vector/put",
                        json={"key": "k", "text": "t", "vector_type": "topic"},
                        headers={"x-internal-token": "wrong"})
        assert r.status_code == 403

    def test_query_missing_token_403(self):
        r = client.post("/api/tutoring/vector/query",
                        json={"text": "t", "top_k": 3, "vector_type": "topic"})
        assert r.status_code == 403


class TestPut:
    def test_put_ok(self, fake_cos):
        r = client.post("/api/tutoring/vector/put",
                        json={"key": "q_5001", "text": "鸡兔同笼", "vector_type": "topic",
                              "metadata": {"topic_label": "鸡兔同笼"}},
                        headers=AUTH)
        assert r.status_code == 200
        assert r.json() == {"ok": True, "key": "q_5001"}
        # 真实 put_vector 应把 vector_type 路由到 topic-index 并透传 metadata
        call = fake_cos.put_calls[-1]
        assert call["Index"] == "topic-index"
        assert call["Vectors"][0]["key"] == "q_5001"
        assert call["Vectors"][0]["metadata"] == {"topic_label": "鸡兔同笼"}

    def test_put_unknown_vector_type_400(self, fake_cos):
        # 真实 _resolve_index 抛 ValueError → 端点转 400
        r = client.post("/api/tutoring/vector/put",
                        json={"key": "k", "text": "t", "vector_type": "nope"},
                        headers=AUTH)
        assert r.status_code == 400
        assert "unknown vector_type" in r.json()["detail"]

    def test_put_missing_vector_type_422(self):
        r = client.post("/api/tutoring/vector/put",
                        json={"key": "k", "text": "t"},
                        headers=AUTH)
        assert r.status_code == 422

    def test_put_cos_failure_500(self, fake_cos, monkeypatch):
        from core.tutoring import vector_store as vs

        def boom(*a, **k):
            raise RuntimeError("cos put failed")
        monkeypatch.setattr(fake_cos, "put_vectors", boom)
        r = client.post("/api/tutoring/vector/put",
                        json={"key": "k", "text": "t", "vector_type": "topic"},
                        headers=AUTH)
        assert r.status_code == 500

    def test_put_embedding_failure_500(self, fake_cos, monkeypatch):
        from core.tutoring import vector_store as vs

        def boom_embed(text):
            raise RuntimeError("dashscope embedding failed")
        monkeypatch.setattr(vs, "embed", boom_embed)
        r = client.post("/api/tutoring/vector/put",
                        json={"key": "k", "text": "t", "vector_type": "topic"},
                        headers=AUTH)
        assert r.status_code == 500


class TestQuery:
    def test_query_ok_vectors_field(self, fake_cos):
        r = client.post("/api/tutoring/vector/query",
                        json={"text": "鸡兔同笼问题", "top_k": 3, "vector_type": "topic"},
                        headers=AUTH)
        assert r.status_code == 200
        body = r.json()
        assert "vectors" in body  # 对齐 COS 返回字段(非 hits)
        assert body["vectors"][0]["key"] == "q_5001"
        assert body["vectors"][0]["distance"] == 0.12
        assert fake_cos.query_calls[-1]["TopK"] == 3

    def test_query_unknown_vector_type_400(self, fake_cos):
        r = client.post("/api/tutoring/vector/query",
                        json={"text": "t", "top_k": 3, "vector_type": "nope"},
                        headers=AUTH)
        assert r.status_code == 400
        assert "unknown vector_type" in r.json()["detail"]

    def test_query_missing_vector_type_422(self):
        r = client.post("/api/tutoring/vector/query",
                        json={"text": "t", "top_k": 3},
                        headers=AUTH)
        assert r.status_code == 422

    def test_query_backend_failure_500(self, fake_cos, monkeypatch):
        def boom(*a, **k):
            raise RuntimeError("cos query failed")
        monkeypatch.setattr(fake_cos, "query_vectors", boom)
        r = client.post("/api/tutoring/vector/query",
                        json={"text": "t", "top_k": 3, "vector_type": "topic"},
                        headers=AUTH)
        assert r.status_code == 500
