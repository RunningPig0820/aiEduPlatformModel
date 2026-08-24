"""
RAG 源文件静态服务测试 - 前端按 file_path 访问源文件内容

覆盖:
- /api/rag/source/{file_path} 返回源文件内容(200)
- 不存在的文件 → 404
- 语料目录缺失时跳过挂载(不崩启动)
"""
import sys
import os

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
)

import pytest
from fastapi import FastAPI


def _make_app_with_mount(corpus_dir):
    """构造挂载了静态服务的 app(隔离测试, 不依赖 main 全局)"""
    from fastapi.staticfiles import StaticFiles
    app = FastAPI()
    if os.path.isdir(corpus_dir):
        app.mount("/api/rag/source", StaticFiles(directory=corpus_dir), name="rag_source")
    return app


class TestRagSource:
    """静态源文件服务"""

    def test_source_served(self, tmp_path):
        # 造一个假语料目录 + 文件
        doc = tmp_path / "4.完善文档"
        doc.mkdir()
        (doc / "04-安全与防作弊.md").write_text("# 04 安全\n内容", encoding="utf-8")

        from fastapi.testclient import TestClient
        app = _make_app_with_mount(str(tmp_path))
        c = TestClient(app)
        r = c.get("/api/rag/source/4.完善文档/04-安全与防作弊.md")
        assert r.status_code == 200
        assert "# 04 安全" in r.text

    def test_source_missing_404(self, tmp_path):
        doc = tmp_path / "4.完善文档"
        doc.mkdir()
        (doc / "04.md").write_text("x", encoding="utf-8")

        from fastapi.testclient import TestClient
        c = TestClient(_make_app_with_mount(str(tmp_path)))
        assert c.get("/api/rag/source/4.完善文档/nope.md").status_code == 404

    def test_missing_corpus_dir_skips_mount(self, tmp_path):
        # 语料目录不存在 → 不挂载, 请求 404(不崩启动)
        from fastapi.testclient import TestClient
        app = _make_app_with_mount(str(tmp_path / "nonexistent"))
        c = TestClient(app)
        assert c.get("/api/rag/source/x.md").status_code == 404


class TestMainMount:
    """main.py 真实挂载(语料目录存在)"""

    def test_main_mounts_source(self):
        import main as main_mod
        assert any(getattr(r, "path", "") == "/api/rag/source" for r in main_mod.app.routes) or \
               any(getattr(r, "path", "").startswith("/api/rag/source") for r in main_mod.app.routes)
