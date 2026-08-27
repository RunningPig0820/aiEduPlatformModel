# 13.10 重试与错误恢复
> summary: 重试策略分错误类型：LLM超时重试2次指数退避、格式错误1次、网络故障3次、成本超限/解析错误0次；失败批次结构化存储。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-04-10-knowledge-graph-data-research-重试与错误恢复.md
> 类别：开发难点

> 检索摘要：重试策略分错误类型：LLM超时重试2次指数退避、格式错误1次、网络故障3次、成本超限/解析错误0次；失败批次结构化存储。

错误类型	重试次数	退避策略	处理方式
LLM 调用超时	2	指数退避（1s, 2s）	状态标记 pending，下次继续
LLM 返回格式错误	1	立即重试	解析失败记录日志
网络临时故障	3	固定间隔 2s	自动重试
成本超限	0	停止调用	抛出异常，记录状态
数据解析错误	0	记录跳过	写入 failed_batches

错误日志结构化（智谱建议）
问题：原方案将失败批次写入日志文件，难以批量重试。
改进：将失败批次信息写入 SQLite 表，便于开发一键重试脚本。
-- 失败批次表（新增）
CREATE TABLE failed_batches (
    id INTEGER PRIMARY KEY,
    subject TEXT NOT NULL,
    version TEXT NOT NULL,
    batch_id TEXT NOT NULL,
    batch_uris TEXT NOT NULL,        -- JSON 数组
    error_type TEXT NOT NULL,        -- 错误类型分类
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_retry_at TIMESTAMP,
    status TEXT DEFAULT 'pending'    -- pending/retrying/resolved/abandoned
);

-- 一键重试脚本
def retry_failed_batches(state_db, max_retries=3):
    """重试所有待处理或重试中的失败批次"""
    failed = state_db.query("""
        SELECT * FROM failed_batches
        WHERE status IN ('pending', 'retrying')
        AND retry_count < ?
    """, (max_retries,))

    for batch in failed:
        try:
            state_db.update_failed_batch(batch['id'], status='retrying')
            result = call_llm(json.loads(batch['batch_uris']))
            # 成功：标记为 resolved
            state_db.update_failed_batch(
                batch['id'],
                status='resolved',
                result_file=save_result(result)
            )
        except Exception as e:
            state_db.update_failed_batch(
                batch['id'],
                retry_count=batch['retry_count'] + 1,
                error_message=str(e)
            )

错误类型分类：
错误类型	说明	处理建议
json_parse_error	LLM 返回格式损坏	检查 Prompt，增加格式修复
token_limit_exceeded	输入超 Token 限制	减小批次大小
timeout	网络或 LLM 超时	增加超时时间，重试
rate_limit	API 调用频率限制	增加等待时间
network_error	网络临时故障	重试
unknown	其他错误	检查日志，人工介入

#### 13.10.1 动态批大小调整（新增）
> 检索摘要：动态批大小用 tiktoken 预估 token 数，按 Prompt 基础token+知识点token 动态分组，避免固定批次 Token 超限。

问题：不同章节知识点数量差异大，固定批大小可能导致 Token 超限。
import tiktoken

def estimate_tokens(text: str, model: str = "gpt-4") -> int:
    """预估文本 Token 数"""
    enc = tiktoken.encoding_for_model(model)
    return len(enc.encode(text))

def build_dynamic_batch(knowledge_points: list, max_tokens: int = 4000) -> list:
    """
    动态构建批次，确保不超过 Token 限制
    """
    batches = []
    current_batch = []
    current_tokens = 0

    # Prompt 模板基础 Token 数
    base_prompt = get_prompt_template()
    base_tokens = estimate_tokens(base_prompt)

    for kp in knowledge_points:
        kp_text = f"| {kp.name} | {kp.type} | {kp.definition} |"
        kp_tokens = estimate_tokens(kp_text)

        if current_tokens + kp_tokens + base_tokens > max_tokens:
            # 当前批次已满，开始新批次
            if current_batch:
                batches.append(current_batch)
            current_batch = [kp]
            current_tokens = kp_tokens
        else:
            current_batch.append(kp)
            current_tokens += kp_tokens

    if current_batch:
        batches.append(current_batch)

    return batches

#### 13.10.2 关系去重与合并（新增）
> 检索摘要：多来源重复关系合并去重：按(from,to,类型)取最高置信度并合并证据来源，避免图谱冗余。

问题：多个来源可能生成相同关系，需要合并去重。
def merge_duplicate_relations(relations: list) -> list:
    """
    合并重复关系，取最高置信度 + 合并证据
    """
    merged = {}
    for rel in relations:
        key = (rel["from"], rel["to"], rel["relation_type"])
        if key not in merged:
            merged[key] = rel.copy()
        else:
            # 保留更高置信度
            if rel["confidence"] > merged[key]["confidence"]:
                merged[key]["confidence"] = rel["confidence"]
            # 合并证据/来源
            merged[key]["evidence_types"] = list(set(
                merged[key]["evidence_types"] + rel["evidence_types"]
            ))
            merged[key]["source"] = ",".join(set(
                merged[key]["source"].split(",") + rel["source"].split(",")
            ))

    return list(merged.values())

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-10-knowledge-graph-data-research.md`（§13.10 重试与错误恢复）
