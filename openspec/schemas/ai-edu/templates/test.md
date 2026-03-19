# {模块名称} 测试用例设计

## 1. 测试概述

### 1.1 测试目标
验证 `{ModuleName}` 的所有业务场景，确保功能的正确性和健壮性。

### 1.2 测试方式
- **集成测试**：使用 TestClient 调用真实 API 端点
- **数据库回滚**：使用 pytest fixture 配合事务回滚
- **无 Mock**：真实数据库操作，验证完整业务流程

### 1.3 测试环境配置
- pytest 配置：`pytest.ini`
- 数据库：使用测试数据库，事务自动回滚
- 环境：使用 `.env.test` 配置

---

## 2. 测试数据

| 参数 | 值 | 说明 |
|-----|-----|-----|
| TEST_ID | 1 | 测试ID |
| TEST_NAME | test001 | 测试名称 |
| TEST_PHONE | 13800138001 | 测试手机号 |
| TEST_PASSWORD | password123 | 测试密码 |

---

## 3. 测试用例清单

### 3.1 {模块名称}

| 用例编号 | 场景描述 | 前置条件 | 输入 | 预期结果 |
|---------|---------|---------|------|---------|
| {MODULE}-001 | 正常场景 | 数据存在 | 正确参数 | 返回成功 |
| {MODULE}-002 | 异常场景-参数错误 | 无 | 错误参数 | 抛出 INVALID_PARAMS 异常 |
| {MODULE}-003 | 异常场景-数据不存在 | 数据不存在 | 有效参数 | 抛出 NOT_FOUND 异常 |
| {MODULE}-004 | 异常场景-未授权 | 未登录 | 需要登录的接口 | 抛出 UNAUTHORIZED 异常 |
| {MODULE}-005 | 边界场景-空值 | 无 | 空参数 | 抛出 INVALID_PARAMS 异常 |

---

## 4. 错误码对照表

| 错误码 | 常量名 | 说明 |
|-------|-------|------|
| 00000 | SUCCESS | 成功 |
| 10001 | INVALID_PARAMS | 参数无效 |
| 10002 | NOT_FOUND | 实体不存在 |
| 10003 | INVALID_PARAMS | 参数校验失败 |
| 10004 | UNAUTHORIZED | 未授权 |

---

## 5. 测试用例统计

| 模块 | 用例数量 |
|-----|---------|
| {模块1} | {数量} |
| {模块2} | {数量} |
| **总计** | **{总数}** |

---

## 6. 测试执行顺序

测试按文件名和方法名顺序执行：

```
test_module1.py    : {模块1}测试
test_module2.py    : {模块2}测试
test_module3.py    : {模块3}测试
```

使用 `pytest-ordering` 或方法命名控制执行顺序。

---

## 7. 辅助方法

### 7.1 创建测试数据
```python
def create_test_entity(name: str) -> Entity:
    """创建测试实体"""
    entity = Entity(name=name)
    db.add(entity)
    db.commit()
    db.refresh(entity)
    return entity
```

### 7.2 创建认证头
```python
def create_auth_headers(user_id: int) -> dict:
    """创建 JWT 认证头"""
    token = create_access_token({"sub": user_id})
    return {"Authorization": f"Bearer {token}"}
```

---

## 8. 运行测试

```bash
# 运行单个测试文件
pytest tests/test_{module}.py -v

# 运行单个测试方法
pytest tests/test_{module}.py::test_{method_name} -v

# 运行所有测试
pytest

# 运行并显示覆盖率
pytest --cov=ai_edu_ai_service --cov-report=term-missing
```