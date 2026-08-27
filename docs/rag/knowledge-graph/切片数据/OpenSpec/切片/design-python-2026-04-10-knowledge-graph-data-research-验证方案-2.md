# 验证方案（续）
> summary: 验证方案务实策略：自动验证(循环依赖/年级倒置惩罚)+抽样测试(≥70%准确率即可)，Demo 不做人工教师审核。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-04-10-knowledge-graph-data-research-验证方案-2.md
> 类别：开发难点

---

### 九、验证方案（Demo 阶段务实策略）（续）

> 检索摘要：验证方案务实策略：自动验证(循环依赖/年级倒置惩罚)+抽样测试(≥70%准确率即可)，Demo 不做人工教师审核。

### 9.4 验证增强（新增）
> 检索摘要：验证增强四件套：循环依赖检测、孤立知识点检测、分层抽样评估、置信度校准，保障 PREREQUISITE 图质量。

#### 9.4.1 循环依赖检测
> 检索摘要：循环依赖检测用 DFS 找有向环，resolve_cycles 移除环中置信度最低的边，保证前置关系符合 DAG 要求。

问题：如果 A→B 且 B→A 同时存在，形成有向环，违背 DAG 要求。
def detect_cycles(prerequisites: list) -> list:
    """
    检测循环依赖
    返回: 环路列表
    """
    from collections import defaultdict, deque

    # 构建邻接表
    graph = defaultdict(list)
    for rel in prerequisites:
        graph[rel['from']].append(rel['to'])

    # 检测环（DFS）
    cycles = []
    visited = set()
    rec_stack = set()

    def dfs(node, path):
        visited.add(node)
        rec_stack.add(node)
        for neighbor in graph[node]:
            if neighbor not in visited:
                dfs(neighbor, path + [node])
            elif neighbor in rec_stack:
                # 发现环
                cycle_start = path.index(neighbor)
                cycles.append(path[cycle_start:] + [node, neighbor])

        rec_stack.remove(node)

    for node in graph:
        if node not in visited:
            dfs(node, [])

    return cycles

def resolve_cycles(prerequisites: list, cycles: list) -> list:
    """
    解决循环依赖：移除置信度最低的边
    """
    to_remove = set()
    for cycle in cycles:
        # 找到环中置信度最低的边
        cycle_edges = []
        for i in range(len(cycle) - 1):
            from_uri, to_uri = cycle[i], cycle[i+1]
            for rel in prerequisites:
                if rel['from'] == from_uri and rel['to'] == to_uri:
                    cycle_edges.append((rel['confidence'], from_uri, to_uri))
                    break
        if cycle_edges:
            # 移除置信度最低的边
            min_edge = min(cycle_edges)
            to_remove.add((min_edge[1], min_edge[2]))

    return [rel for rel in prerequisites if (rel['from'], rel['to']) not in to_remove]

#### 9.4.2 孤立知识点检测
> 检索摘要：孤立知识点检测按入度/出度区分真正孤立（定义/定理型）与 potential_missing（数据可能缺失型），辅助定位数据问题。

问题：没有任何 PREREQUISITE 关系，也没有被任何知识点依赖的知识点，可能是原子知识点或数据缺失。
def detect_isolated_kps(knowledge_points: list, prerequisites: list) -> dict:
    """
    检测孤立知识点
    返回: {'isolated': [...], 'potential_missing': [...]}
    """
    # 构建入度和出度
    in_degree = {kp.uri: 0 for kp in knowledge_points}
    out_degree = {kp.uri: 0 for kp in knowledge_points}

    for rel in prerequisites:
        out_degree[rel['from']] += 1
        in_degree[rel['to']] += 1

    isolated = []
    for kp in knowledge_points:
        if in_degree[kp.uri] == 0 and out_degree[kp.uri] == 0:
            isolated.append(kp)

    # 区分类型
    result = {
        'isolated': [kp for kp in isolated if kp.type in ['定义', '定理']],  # 真正孤立
        'potential_missing': [kp for kp in isolated if kp.type not in ['定义', '定理']]  # 可能缺失
    }
    return result

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-10-knowledge-graph-data-research.md`（§九、验证方案（Demo 阶段务实策略）（续））
