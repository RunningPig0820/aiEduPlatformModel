# 13.11 脚本执行流程
> summary: 主流程 run_math_pipeline 七步：解析TTL→教材匹配→定义依赖→关系提取→LLM推理→证据融合→Neo4j导入，每步幂等+进程锁。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-04-10-knowledge-graph-data-research-脚本执行流程.md
> 类别：操作流程

> 检索摘要：主流程 run_math_pipeline 七步：解析TTL→教材匹配→定义依赖→关系提取→LLM推理→证据融合→Neo4j导入，每步幂等+进程锁。

def run_math_pipeline():
    subject = "math"
    version = generate_version()
    config = load_config()

    # 进程锁
    with ProcessLock(f"data/state/{subject}.lock"):
        state_db = StateDB(f"data/versions/{version}/state.db")

        # Step 1: 数据解析（幂等）
        if state_db.get_step_status("parse_ttl") != "completed":
            kps = parse_ttl(f"data/ttl/{subject}.ttl")
            save_kps(kps, version)
            state_db.mark_step_completed("parse_ttl")

        # Step 2: 教材匹配（幂等）
        if state_db.get_step_status("textbook_match") != "completed":
            kps = load_kps(version)
            enriched_kps = match_textbook(kps)
            save_kps(enriched_kps, version)
            state_db.mark_step_completed("textbook_match")

        # Step 3: 定义依赖抽取（幂等）
        if state_db.get_step_status("definition_deps") != "completed":
            def_deps = extract_definition_dependencies(load_kps(version))
            save_def_deps(def_deps, version)
            state_db.mark_step_completed("definition_deps")

        # Step 4: 关系数据提取（幂等）
        if state_db.get_step_status("extract_relations") != "completed":
            relations = extract_relations(subject)
            save_relations(relations, version)
            state_db.mark_step_completed("extract_relations")

        # Step 5: LLM 推理（断点续传 + 成本控制）
        candidates = generate_candidates(load_kps(version), load_def_deps(version))
        process_llm_batches_with_cache(candidates, state_db, config)

        # Step 6: 证据融合（幂等）
        if state_db.get_step_status("fuse") != "completed":
            prerequisites = fuse(load_def_deps(version), load_llm_results(version))
            save_prerequisites(prerequisites, version)
            state_db.mark_step_completed("fuse")

        # Step 7: Neo4j 导入（幂等 MERGE）
        import_to_neo4j(version)

        # 生成 manifest
        generate_manifest(version, state_db)

        logging.info(f"Pipeline 完成: {version}")

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-10-knowledge-graph-data-research.md`（§13.11 脚本执行流程）
