## Context

当前组织域已完成行政组织树（Department）的开发，支持树形结构的部门管理。现在需要在组织域添加教职工管理功能，教职工本质上是"用户与部门的关联关系"。

**领域边界划分**：
- **用户域**：负责用户基本信息管理（姓名、手机号），数据存储在 `ai_edu_user` 数据库
- **组织域**：负责用户与部门的关联关系管理，数据存储在 `ai_edu_org` 数据库

教职工添加时需要与用户域联动：通过手机号查询/创建用户，再创建组织关联关系。查询时需要聚合用户域基本信息，返回完整教职工信息。

## Goals / Non-Goals

**Goals:**
- 实现教职工关联关系的 CRUD 功能
- 教职工与行政部门的多对一关联
- 与用户域联动：查询/创建用户 + 创建关联关系
- 聚合查询：整合用户域基本信息，返回完整教职工信息

**Non-Goals:**
- 教职工与年级组、学科组的关联（属于"任职任课"模块，不在本范围）
- 用户基本信息修改（在用户中心处理）
- 手机号修改功能（用户域负责）

## Decisions

### D1: 教职工实体设计

**选择**: 在组织域创建 OrgTeacher 实体，**只存储关联关系**，不存储用户基本信息。

**字段设计**:
| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 主键 |
| school_id | Long | 所属学校 |
| user_id | Long | 关联用户域用户ID（必填） |
| department_id | Long | 所属行政部门（必填） |
| created_at/updated_at | DateTime | 时间戳 |
| created_by/modified_by | Long | 操作人（登录用户ID） |
| is_deleted | Boolean | 逻辑删除 |

**不存储字段**: name, phone - 这些基本信息存储在用户域，通过聚合查询获取

**备选方案**: 在组织域冗余存储用户基本信息（姓名、手机号）。
**选择理由**: 
1. 避免数据冗余和同步问题
2. 符合领域边界清晰原则：用户域负责用户信息，组织域负责关联关系
3. 通过聚合查询（DDD核心价值）整合信息，前端调用简单

### D2: 用户域关联机制

**选择**: 定义 UserQueryService 接口（组织域），由用户域实现并提供 RPC/Feign 接口。

**接口约定**:
```java
public interface UserQueryService {
    // 手机号查询用户
    Optional<UserInfo> findByPhone(String phone);
    
    // 创建用户（返回userId）
    Long createUser(String name, String phone);
    
    // 批量查询用户基本信息
    List<UserInfo> findByIds(List<Long> userIds);
}
```

**添加教职工流程**:
1. 组织域调用 `findByPhone(phone)` 查询用户
2. 如果用户不存在，调用 `createUser(name, phone)` 创建用户
3. 组织域创建 OrgTeacher(userId, departmentId, schoolId)

**备选方案**: 直接调用用户域 REST API。
**选择理由**: 防腐层设计避免组织域直接依赖用户域实现，便于测试和解耦。

### D3: 聚合查询设计

**选择**: 组织域应用层提供聚合查询接口，内部调用用户域批量查询接口。

**实现方式**:
```java
public List<OrgTeacherDTO> listTeachers(Long schoolId) {
    // 1. 查询组织域关联关系
    List<OrgTeacher> relations = repository.findBySchoolId(schoolId);
    List<Long> userIds = relations.stream().map(OrgTeacher::getUserId).toList();
    
    // 2. 批量查询用户域基本信息
    List<UserInfo> users = userQueryService.findByIds(userIds);
    
    // 3. 聚合合并返回完整信息
    return merge(relations, users);
}
```

**备选方案**: 前端分离查询（先查组织域，再查用户域）。
**选择理由**: 聚合查询是DDD的核心价值，简化前端调用，提供完整业务视图。

### D4: 数据库表设计

**选择**: 创建 `t_org_teacher` 表，使用 MyBatis-Plus 动态数据源 `@DS("org")`。

**表结构**:
```sql
CREATE TABLE t_org_teacher (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    school_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,       -- 关联用户域用户
    department_id BIGINT NOT NULL, -- 所属行政部门
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by BIGINT NOT NULL DEFAULT 0,  -- 创建人（登录用户ID）
    modified_by BIGINT NOT NULL DEFAULT 0, -- 最后修改人（登录用户ID）
    is_deleted TINYINT(1) NOT NULL DEFAULT 0,
    UNIQUE INDEX idx_school_user (school_id, user_id), -- 一个用户在一个学校只能有一条记录
    INDEX idx_department (department_id)
);
```

**说明**: 
- 不存储用户基本信息（name, phone）
- school_user 唯一索引保证一个用户在一个学校只能有一条教职工记录

### D5: 修改与删除逻辑

**修改教职工**:
- 组织域只支持修改所属部门（departmentId）
- 用户基本信息修改在用户中心处理，不在组织域接口提供

**删除教职工**:
- 只删除组织域的关联关系（逻辑删除 OrgTeacher）
- 用户域的用户数据保留不受影响

## Risks / Trade-offs

### R1: 用户域接口依赖
- **风险**: 用户域接口尚未就绪，教职工添加功能可能阻塞
- **缓解**: 当前先定义接口契约，组织域实现防腐层；用户域就绪后对接

### R2: 跨域查询性能
- **风险**: 聚合查询需要调用用户域批量查询接口，可能影响性能
- **缓解**: 
  1. 使用批量查询而非逐个查询
  2. 用户域接口提供缓存机制
  3. 组织域可以考虑缓存聚合结果（后续优化）

### R3: 数据一致性
- **风险**: 用户域用户删除后，组织域的 userId 失效
- **缓解**: 
  1. 查询时不强制要求 userId 有效，返回"用户已删除"提示
  2. 后续可以通过事件机制同步状态，或提供清理无效关联的管理接口

### R4: 部门删除影响
- **风险**: 行政部门删除后，关联的教职工失去归属
- **缓解**: 
  1. 部门删除时检查是否有教职工关联
  2. 或者限制删除有教职工的部门