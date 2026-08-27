# 13.5 成本控制与监控
> summary: 成本控制：日预算50元/总预算200元/70%告警，调用前检查成本限制，超预算停止调用。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-04-10-knowledge-graph-data-research-成本控制与监控.md
> 类别：业务视角

> 检索摘要：成本控制：日预算50元/总预算200元/70%告警，调用前检查成本限制，超预算停止调用。

实时成本累积：
# 配置文件 config/pipeline.yaml
cost_limits:
  daily_limit_cents: 5000   # 日预算 50 元
  total_limit_cents: 20000  # 总预算 200 元
  warning_threshold: 0.7    # 70% 时告警

alert:
  enabled: true
  method: "console"         # 个人项目：控制台告警
  # method: "email"         # 可扩展邮件通知

成本检查函数：
def check_cost_limit(state_db, subject: str) -> bool:
    """检查是否超出成本限制"""
    current_cost = state_db.get_total_cost(subject)
    config = load_config()

    if current_cost >= config['cost_limits']['total_limit_cents']:
        logging.error(f"已超出总预算 {current_cost} 分")
        return False

    if current_cost >= config['cost_limits']['daily_limit_cents']:
        logging.warning(f"已超出日预算 {current_cost} 分")

    if current_cost >= config['cost_limits']['total_limit_cents'] * config['alert']['warning_threshold']:
        logging.warning(f"成本已达 {current_cost} 分，接近预算上限")

    return True

def call_llm_with_cost_check(batch, state_db):
    """带成本检查的 LLM 调用"""
    if not check_cost_limit(state_db, batch['subject']):
        raise RuntimeError("超出成本限制，停止调用")
    return call_llm(batch)

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-10-knowledge-graph-data-research.md`（§13.5 成本控制与监控）
