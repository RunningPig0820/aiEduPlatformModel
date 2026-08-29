"""
RAG API - 前端/后端调:
  - `POST /api/tutoring/rag/query`   RAG 问答(1.6C 契约)
  - `GET  /api/rag/source/{key}`     "查看原文"(U4: 按 COS key 从普通桶读文件)
  - `POST /api/rag/eval/run`         触发评测(6.1, 离线工具, 同步执行 ~30s)
  - `GET  /api/rag/eval/report`      查询最新报告 + 版本对比(6.2)

对齐: docs/rag/ai-tutoring/每模块流水线-tasks.md 1.6C + 6 + 1.13
鉴权: x-internal-token(同 api/vector.py / api/chat.py)
健壮性(1.6C 降级语义, 按序):
  1. COS 向量挂了   → 降级纯 BM25(references 仍返回)
  2. doubao 挂了    → 降级返回召回块清单(references 当答案, 不空答)
  3. 置信度过低     → 拒答"语料未覆盖", 不编造
  4. 所有降级路径 response 结构不变(前端只按同一结构渲染)
"""
import logging
import os

from fastapi import APIRouter, Header, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import Response

from api.chat import verify_internal_token
from config.settings import settings
from core.rag import query as rag_core
from core.tutoring.vector_store import get_normal_cos_client
from models.rag import (
    RAGQueryRequest,
    RAGQueryResponse,
    RAGReference,
    RAGIntent,
    RAGEvalRunResponse,
    RAGEvalReportResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tutoring/rag", tags=["Tutoring"])
SOURCE_ROUTER = APIRouter(prefix="/api/rag", tags=["RAG Source"])
EVAL_ROUTER = APIRouter(prefix="/api/rag/eval", tags=["RAG Eval"])

# run_eval 在 scripts/rag/(评测执行), API 侧按需延迟导入(避免 import 链过早初始化)
EVAL_RUN_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                             "scripts", "rag", "run_eval.py")


# ============ U4: "查看原文" 读 COS 普通桶 ============


def _read_cos_file(file_path: str) -> bytes:
    """同步读 COS 普通桶文件(线程池包裹, 不阻塞事件循环)。"""
    client = get_normal_cos_client()
    obj = client.get_object(Bucket=settings.COS_OBJ_BUCKET, Key=file_path)
    return obj["Body"].get_raw_stream().read()


@SOURCE_ROUTER.get("/source/{file_path:path}")
async def rag_source(file_path: str, x_internal_token: str = Header(None)):
    """查看原文(U4): 按 COS key 从普通桶 ai-edu-1318177119 读文件, 替代本地 StaticFiles。

    file_path = 引用块里的 COS key(`rag-source|rag-slices/<模块>/...`, 见向量桶入桶清单 7.2)。
    安全: 只允许 rag-source/rag-slices 前缀(防任意 COS key 读取); 读取失败 → 404。
    """
    verify_internal_token(x_internal_token)
    if not file_path.startswith(("rag-source/", "rag-slices/")):
        raise HTTPException(404, "文件不存在")
    try:
        body = await run_in_threadpool(_read_cos_file, file_path)
    except Exception as e:
        logger.warning("RAG source 读取失败: %s: %s", file_path, e)
        raise HTTPException(404, "文件不存在")
    return Response(content=body, media_type="text/markdown; charset=utf-8")


@router.post("/query", response_model=RAGQueryResponse)
async def rag_query(
    request: RAGQueryRequest,
    x_internal_token: str = Header(None),
):
    """RAG 问答: 意图 → 双路召回 → 编排 → doubao 生成。降级语义见模块 docstring。"""
    verify_internal_token(x_internal_token)

    # --- 1.6C 降级语义: COS 向量挂了 → 降级纯 BM25(需绕开 rag_query 的整链路) ---
    try:
        blocks = rag_core._load_all_blocks()
        it = rag_core.intent(request.question, current_project=request.current_project,
                             history=request.history)  # 多模块: 判模块+9类, 倾向当前模块; 带 history 供指代
        corpus = it["anchor"] if it["anchor"] in rag_core.MODULE_ANCHORS else None

        # 追问改写(方案 A, 2026-08-26): 结合 history 补全指代/省略
        #   "能说的详细一点吗" + history(上一轮"流程图") → "ai-tutoring 流程图详细内容"
        # 追问不基于旧答案扩写(_GEN_SYSTEM 硬性约束 6): 重读全部召回语料重新生成, 生成只用改写后问题+新检索块
        rewritten = rag_core.rewrite_query(request.question, anchor=it["anchor"],
                                           history=request.history)

        # 双池向量路失败冒泡 → 捕获降级纯 BM25(构造空向量结果)
        try:
            dual = rag_core.retrieve_dual(rewritten, corpus=corpus,
                                          locked_categories=it["locked_categories"])
        except Exception as e:
            logger.warning("RAG 向量路失败, 降级纯 BM25: %s", e)
            bm_pool = rag_core.select_corpus(blocks, corpus) if corpus else blocks
            dual = {"full": {"hits": [], "confidence": 0.0},
                    "slice": {"hits": [], "confidence": 0.0},
                    "slice_q": {"hits": [], "confidence": 0.0},   # 双向量: summary/问题路
                    "bm25": rag_core.retrieve_bm25(rewritten, bm_pool)}

        hits = rag_core.orchestrate(rewritten, blocks, dual["full"], dual["bm25"],
                                    it, top_k=request.top_k, vec2_result=dual["slice"],
                                    vec3_result=dual["slice_q"], corpus=corpus)

        references = [
            RAGReference(**{k: h[k] for k in ("file", "file_path", "anchor", "authority", "summary")})
            for h in hits
        ]
        intent = RAGIntent(locked_sections=it["locked_sections"], strategy="retrieve",
                           anchor=it["anchor"], categories=it["locked_categories"])

        # --- 降级语义 3: 无命中 或 离题 → 拒答不编造 ---
        # 离题判定(2026-08-30 用户口径): intent category=其他 且 非澄清(ambiguous=false)
        #   且 无 history(非追问省略) → 问题语义无法归属项目主题, 直接边界拒答, 不勉强生成
        off_topic = (it.get("category") == "其他" and not it.get("ambiguous")
                     and not request.history)
        if not hits or off_topic:
            answer = "该问题语料未覆盖，建议问项目相关话题"
            if off_topic and hits:
                answer = "这个问题和项目主题关系不大，可以聊聊项目介绍、架构、技术实现、评测相关的问题"
            return RAGQueryResponse(
                answer=answer,
                references=[],
                intent=intent,
                version=rag_core._current_version(blocks),
            )

        # --- 降级语义 2: doubao 挂了 → references 当答案, 不空答 ---
        try:
            answer = rag_core.generate(hits, rewritten)
        except Exception as e:
            logger.error("RAG 生成失败(doubao), 降级返回召回块清单: %s", e)
            answer = "生成服务不可用，以下为检索到的语料：\n" + "\n".join(
                f"- [{h['file']}/{h['anchor']}] {h['summary']}" for h in hits
            )

        return RAGQueryResponse(
            answer=answer,
            references=references,
            intent=intent,
            version=rag_core._current_version(blocks),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("RAG query 端点异常: %s", e)
        raise HTTPException(status_code=500, detail="rag query failed")


# ============ 6 评测 API(离线工具上线, 6.1/6.2/6.3) ============


@EVAL_ROUTER.post("/run", response_model=RAGEvalRunResponse)
async def eval_run(x_internal_token: str = Header(None)):
    """触发评测(6.1): 跑评测集 → 聚合报告 → 落盘。离线工具, 同步执行(~30s)。"""
    verify_internal_token(x_internal_token)
    try:
        from scripts.rag import run_eval  # 延迟导入(run_eval 自处理 sys.path)
        out = await run_in_threadpool(run_eval.run_evaluation)  # 不阻塞事件循环
        return RAGEvalRunResponse(
            ok=True,
            version=out["version"],
            aggregate=out["aggregate"],
            report_path=out["report_path"],
        )
    except Exception as e:
        logger.error("RAG eval run 端点异常: %s", e)
        raise HTTPException(status_code=500, detail="rag eval run failed")


@EVAL_ROUTER.get("/report", response_model=RAGEvalReportResponse)
async def eval_report(x_internal_token: str = Header(None)):
    """查询评测报告(6.2): 最新聚合 + 历史版本列表(供版本对比)。"""
    verify_internal_token(x_internal_token)
    try:
        from scripts.rag import run_eval
        reports = run_eval._list_reports()
        if not reports:
            return RAGEvalReportResponse(ok=True, has_report=False, reports=[])
        latest = reports[-1]
        import json
        with open(os.path.join(run_eval.REPORT_DIR, latest), encoding="utf-8") as f:
            data = json.load(f)
        return RAGEvalReportResponse(
            ok=True,
            version=data.get("version", latest.replace(".json", "")),
            aggregate=data.get("aggregate", {}),
            reports=reports,
            has_report=True,
        )
    except Exception as e:
        logger.error("RAG eval report 端点异常: %s", e)
        raise HTTPException(status_code=500, detail="rag eval report failed")
