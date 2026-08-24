# tests（语雀原稿）

> 来源：https://www.yuque.com/zhangmin-jrrer/iu9s4m/org-mgmt-tests
> 字数：1355 ｜ 下载：2026-08-24

# 组织管理域 测试用例设计

## 1. 测试概述

### 1.1 测试目标

验证 `SchoolController` 和 `OrganizationApplicationService` 的所有业务场景，确保学校组织创建、更新、查询、权限管控功能的正确性和健壮性。

### 1.2 测试方式

+ **集成测试**：直接注入 Controller，调用真实方法
+ **数据库回滚**：使用 `@Transactional` 注解，测试完成后自动回滚
+ **无 Mock**：真实数据库操作，验证完整业务流程

### 1.3 测试环境配置

+ Profile: `test`
+ 数据库：使用开发数据库，事务自动回滚
+ Session：使用 `MockHttpSession` 模拟

---

## 2. 测试数据

| 参数 | 值 | 说明 |
| --- | --- | --- |
| TEST_SCHOOL_NAME | 测试学校001 | 测试学校名称 |
| TEST_SCHOOL_ICON | [https://test.com/icon.png](https://test.com/icon.png) | 测试学校图标 |
| TEST_SCHOOL_TYPE | PUBLIC | 公立学校 |
| TEST_SCHOOL_STAGES | [PRIMARY, JUNIOR_HIGH] | 测试学段 |
| TEST_USER_ID | 1001 | 测试用户ID |
| TEST_USER_ROLE | TEACHER | 测试用户角色 |
| TEST_ADMIN_ROLE | ADMIN | 管理员角色 |

---

## 3. 测试用例清单

### 3.1 创建学校 (ORG-SCHOOL)

| 用例编号 | 场景描述 | 前置条件 | 输入 | 预期结果 |
| --- | --- | --- | --- | --- |
| ORG-SCHOOL-001 | 正常创建学校 | 已登录管理员 | 完整参数(name,type,stages) | 返回成功，包含学校ID |
| ORG-SCHOOL-002 | 创建学校-名称为空 | 已登录 | name为空字符串 | 抛出 INVALID_PARAMS 异常 |
| ORG-SCHOOL-003 | 创建学校-类型非法 | 已登录 | type为非法枚举值 | 抛出 INVALID_PARAMS 异常 |
| ORG-SCHOOL-004 | 创建学校-学段为空数组 | 已登录 | stages为空数组 | 抛出 INVALID_PARAMS 异常 |
| ORG-SCHOOL-005 | 创建学校-名称重复 | 同名学校已存在 | 与已有学校同名 | 抛出 20001 冲突错误 |
| ORG-SCHOOL-006 | 创建学校-未登录 | 未登录 | 正确参数 | 抛出 UNAUTHORIZED 异常 |
| ORG-SCHOOL-007 | 创建学校-可选字段为空 | 已登录 | iconUrl为null | 返回成功，iconUrl为null |

### 3.2 更新学校 (ORG-UPDATE)

| 用例编号 | 场景描述 | 前置条件 | 输入 | 预期结果 |
| --- | --- | --- | --- | --- |
| ORG-UPDATE-001 | 正常更新学校 | 学校存在，已登录 | 完整更新参数 | 返回更新后的学校数据 |
| ORG-UPDATE-002 | 更新不存在的学校 | 已登录 | id为不存在的值 | 抛出 NOT_FOUND 异常 |
| ORG-UPDATE-003 | 更新名称导致重复 | 另一同名学校存在 | 更新为已有名称 | 抛出 20001 冲突错误 |
| ORG-UPDATE-004 | 更新学段为空 | 学校存在 | stages为空数组 | 抛出 INVALID_PARAMS 异常 |

### 3.3 获取学校详情 (ORG-DETAIL)

| 用例编号 | 场景描述 | 前置条件 | 输入 | 预期结果 |
| --- | --- | --- | --- | --- |
| ORG-DETAIL-001 | 正常获取学校详情 | 学校存在，已登录 | 有效学校ID | 返回完整学校信息 |
| ORG-DETAIL-002 | 获取不存在的学校 | 已登录 | 不存在的ID | 抛出 NOT_FOUND 异常 |
| ORG-DETAIL-003 | 获取详情-未登录 | 未登录 | 有效学校ID | 抛出 UNAUTHORIZED 异常 |

### 3.4 获取学校列表 (ORG-LIST)

| 用例编号 | 场景描述 | 前置条件 | 输入 | 预期结果 |
| --- | --- | --- | --- | --- |
| ORG-LIST-001 | 正常分页查询 | 有学校数据，已登录 | page=1, size=20 | 返回分页数据 |
| ORG-LIST-002 | 按类型筛选 | 有不同类型学校 | type=PUBLIC | 仅返回公立学校 |
| ORG-LIST-003 | 查询空列表 | 无匹配数据 | type=TRAINING_INSTITUTE | 返回空列表，total=0 |
| ORG-LIST-004 | 边界-页码为0 | 已登录 | page=0 | 返回默认第一页 |

### 3.5 关联用户与学校 (ORG-ASSOCIATE)

| 用例编号 | 场景描述 | 前置条件 | 输入 | 预期结果 |
| --- | --- | --- | --- | --- |
| ORG-ASSOCIATE-001 | 正常关联 | 学校和用户存在 | userId, role=TEACHER | 返回关联记录 |
| ORG-ASSOCIATE-002 | 关联不存在的学校 | 用户存在 | 不存在的schoolId | 抛出 NOT_FOUND 异常 |
| ORG-ASSOCIATE-003 | 关联不存在的用户 | 学校存在 | 不存在的userId | 抛出 NOT_FOUND 异常 |
| ORG-ASSOCIATE-004 | 重复关联 | 已关联该用户 | 相同userId和schoolId | 抛出 20002 冲突错误 |
| ORG-ASSOCIATE-005 | 关联-角色非法 | 学校和用户存在 | role为非法值 | 抛出 INVALID_PARAMS 异常 |

### 3.6 获取用户的学校列表 (ORG-USER-SCHOOLS)

| 用例编号 | 场景描述 | 前置条件 | 输入 | 预期结果 |
| --- | --- | --- | --- | --- |
| ORG-USER-SCHOOLS-001 | 正常获取 | 用户已关联学校 | 有效userId | 返回学校列表和角色 |
| ORG-USER-SCHOOLS-002 | 用户无关联学校 | 用户存在但未关联 | 有效userId | 返回空数组 |
| ORG-USER-SCHOOLS-003 | 用户不存在 | 无 | 不存在的userId | 抛出 NOT_FOUND 异常 |

---

## 4. 错误码对照表

| 错误码 | 常量名 | 说明 |
| --- | --- | --- |
| 00000 | SUCCESS | 成功 |
| 10001 | INVALID_PARAMS | 参数无效 |
| 10002 | NOT_FOUND | 实体不存在 |
| 10003 | INVALID_PARAMS | 参数校验失败 |
| 10004 | UNAUTHORIZED | 未授权 |
| 20001 | SCHOOL_NAME_CONFLICT | 学校名称已存在 |
| 20002 | USER_ALREADY_ASSOCIATED | 用户已关联该学校 |
| 20003 | NO_SCHOOL_ACCESS | 无学校访问权限 |

---

## 5. 测试用例统计

| 模块 | 用例数量 |
| --- | --- |
| 创建学校 | 7 |
| 更新学校 | 4 |
| 获取学校详情 | 3 |
| 获取学校列表 | 4 |
| 关联用户与学校 | 5 |
| 获取用户的学校列表 | 3 |
| **总计** | **26** |

---

## 6. 测试执行顺序

测试按 `@Order` 注解指定的顺序执行：

```plain
100-106 : 创建学校测试
200-203 : 更新学校测试
300-302 : 获取学校详情测试
400-403 : 获取学校列表测试
500-504 : 关联用户与学校测试
600-602 : 获取用户的学校列表测试
```

---

## 7. 辅助方法

### 7.1 创建测试学校

```java
private SchoolAggregate createTestSchool(String name, SchoolType type, List<SchoolStage> stages) {
    CreateSchoolCommand command = new CreateSchoolCommand(name, null, type, stages);
    return schoolApplicationService.createSchool(command);
}
```

### 7.2 创建登录会话

```java
private HttpSession createLoginSession(Long userId, String role) {
    MockHttpSession session = new MockHttpSession();
    session.setAttribute("userId", userId);
    session.setAttribute("role", role);
    return session;
}
```

### 7.3 关联用户与学校

```java
private void associateUser(Long schoolId, Long userId, SchoolUserRole role) {
    AssociateUserWithSchoolCommand command = new AssociateUserWithSchoolCommand(userId, role);
    organizationApplicationService.associateUserWithSchool(schoolId, command);
}
```

---

## 8. 运行测试

```bash
# 运行组织管理测试类
cd ai-edu-backend && mvn test -pl ai-edu-interface -Dtest=OrganizationManagementTest

# 运行单个测试方法
mvn test -pl ai-edu-interface -Dtest=OrganizationManagementTest#createSchool_normal
```
