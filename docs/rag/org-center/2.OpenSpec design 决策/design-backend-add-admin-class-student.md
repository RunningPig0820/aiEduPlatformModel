## Context

当前组织域已通过 `t_department` + `t_department_edu` 实现行政班树（学段→年级→班级），参考 `add-org-teacher` 完成的跨域集成模式（Gateway ACL），本期实现行政班添加学生功能。

**领域边界**：
- **用户域**：负责学生/家长用户的创建与管理、身份证加密存储、家长-学生关联关系
- **组织域**：负责学生与行政班班级节点的关联关系（复用 `StudentClass` 实体，`classId` 指向 `Department.id`）
- **通用层**：提供 AES 加密工具，供基础设施层调用

**核心差异（vs OrgTeacher）**：
- OrgTeacher 只需创建 1 个教师用户；AdminClassStudent 需创建 1 个学生 + N 个家长用户
- 学生有身份证敏感数据需要 AES 加密存储
- 家长通过 `t_parent_profile` 表与学生建立关联

## Goals / Non-Goals

**Goals:**
- 支持将学生添加到行政班班级节点（Department with DeptEduType=CLASS）
- 学生用户自动创建（手机号查重，角色=STUDENT），身份证 AES 加密存储
- 多家长绑定：每个家长通过手机号查重/创建（角色=PARENT），记录关联关系到 `t_parent_profile`
- 复用 `StudentClass` 实体存储组织域关联（classId 指向行政班 Department 节点）
- 加密逻辑封装在基础设施层（`UserDataProvider`），领域层和应用层不感知加密细节
- 跨域调用使用 Gateway ACL 模式，与 OrgTeacher 保持一致

**Non-Goals:**
- 不修改现有 `ClassAppService.addStudent()` 的行为（教学班添加学生走不同路径）
- 不支持家长角色变更（如家长也是学生 → 先拒绝，后续迭代）
- 不支持学生身份证的修改接口（本期只做添加时写入）
- 不做分布式事务补偿（Step 4 失败不回滚 Step 2/3 的用户创建，最终一致性）
- 不实现学生查询/修改/删除（本期只做添加）

## Decisions

### D1: 身份证加密分层

**选择**: 加密/解密发生在基础设施层 `UserDataProvider`，加密后的密文直接存入 `User.idCard` 字段。

```
请求 → Controller(明文) → AppService(明文) → Gateway(明文)
                                                  ↓
                                          UserDataProvider
                                          ├── create: EncryptUtil.encrypt(idCard) → 密文存 User.idCard
                                          └── query:  EncryptUtil.decrypt(user.idCard) → EncryptUtil.mask() → 脱敏
                                                  ↓
                                          StudentInfo { idCard: "110101****1234" }
```

**理由**:
1. 加密是技术关注点，不是业务逻辑，放在基础设施层最合适（符合 DDD 分层）
2. 领域层 `User` 实体不关心存储格式，只持有加密后的字符串
3. 应用层透传明文，不处理加解密
4. ACL 模型 `StudentInfo` 返回脱敏后的 idCard

**备选方案**: 在 User 实体内加密 → 违反 DDD 原则，实体不应依赖加密工具。

### D2: 用户角色冲突策略

**选择**: 创建学生/家长时，如果手机号已存在但角色不匹配，**拒绝并提示**。

| 场景 | 行为 |
|------|------|
| 学生手机号 → 查到 STUDENT | ✅ 复用已有用户 |
| 学生手机号 → 查到 TEACHER/PARENT/ADMIN | ❌ 拒绝: "该手机号已被其他角色使用" |
| 家长手机号 → 查到 PARENT | ✅ 复用已有用户 |
| 家长手机号 → 查到 STUDENT/TEACHER/ADMIN | ❌ 拒绝: "该手机号已被其他角色使用" |

**理由**: 当前阶段不处理跨角色身份（如学生同时也是家长），先拒绝保持数据干净。后续迭代可放开。

**备选方案**: 允许同一手机号多角色 → 需要改造 User 表结构（角色字段改为列表），成本大且不符合当前业务假设。

### D3: `StudentClass.classId` 指向行政班 Department 节点

**选择**: `StudentClass.classId` 存储 `Department.id`（行政班树的 CLASS 节点），底层表 `t_class` 已融合到 `t_department_edu`。

**理由**:
1. 用户确认 `t_class` 已融合到 `t_department_edu`，`ClassId` 实际指向 Department
2. 复用现有 `StudentClass` 实体和全套持久化层，无需新建实体
3. 业务语义清晰：`classId` 指向的就是班级（不论教学班还是行政班）

**备选方案**: 新建 `AdminClassStudent` 实体 → 造成大量重复代码，且 StudentClass 现有字段完全满足需求。

### D4: `t_parent_profile` 表设计

**选择**: 新建 `t_parent_profile` 表存储家长-学生关联，放在用户域。

```sql
CREATE TABLE t_parent_profile (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    student_user_id BIGINT NOT NULL COMMENT '学生用户ID',
    parent_user_id BIGINT NOT NULL COMMENT '家长用户ID',
    relationship VARCHAR(32) NOT NULL DEFAULT '' COMMENT '关系类型(父亲/母亲/监护人等)',
    is_primary TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否主要联系人',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE INDEX idx_student_parent (student_user_id, parent_user_id),
    INDEX idx_student (student_user_id),
    INDEX idx_parent (parent_user_id)
) COMMENT '家长信息扩展表';
```

**理由**:
1. 用户明确要求此表在用户域
2. 支持一个学生多个家长（唯一索引按 student+parent 组合）
3. `relationship` 字段记录关系类型（父亲/母亲/监护人）
4. 可灵活添加/删除字段

**备选方案**: 将关联关系放在组织域 → 与用户域边界不清晰，且家长-学生本质是用户间关系。

### D5: Gateway 接口扩展设计

**选择**: 在现有 `OrgUserGateway` 新增 3 个方法，而非新建独立 Gateway。

```java
// 查询或创建学生用户（带身份证加密）
StudentInfo findOrCreateStudent(String name, String phone, String idCard);

// 查询或创建家长用户
ParentInfo findOrCreateParent(String name, String phone);

// 绑定学生与家长的关联关系
void bindStudentParents(Long studentUserId, List<ParentBinding> bindings);
```

**理由**:
1. OrgUserGateway 的职责是"用户域与组织域的桥接"，学生/家长均属此范畴
2. 避免 Gateway 接口膨胀（多个小 Gateway vs 一个聚合 Gateway）

**备选方案**: 新建 `StudentGateway` 独立接口 → 职责碎片化，且底层依赖相同的 `UserDataProvider`。

### D6: 事务边界与最终一致性

**选择**: 不加分布式事务，接受最终一致性。步骤 2/3（用户域写）和步骤 4（组织域写）各自独立事务。

```
Step 2: createStudent  → @DS("user") 独立事务，失败则整体终止
Step 3: createParents  → @DS("user") 独立事务，失败则整体终止
Step 4: createStudentClass → @DS("org") @Transactional，失败时不回滚 Step 2/3
Step 5: bindParents    → @DS("user") 独立事务
```

**理由**:
1. 跨库操作无法用单一本地事务
2. 当前规模下不需要分布式事务（Saga/TC）
3. 如果 Step 4 失败，Step 2/3 创建的孤儿用户可通过「用户已存在」逻辑在重试时自动复用
4. 与 OrgTeacher 保持一致的处理方式

### D7: `UserService.createUser` 扩展

**选择**: 扩展 `UserService.createUser` 方法签名，支持角色参数和身份证。

```java
// 通用创建（支持角色参数 + 可选 idCard）
Long createUser(String name, String phone, String role, String idCard);
```

**理由**:
1. 当前 `createUser` 硬编码角色为 `"TEACHER"`，需要参数化
2. idCard 为学生专用，非必填（家长传 null）
3. `UserServiceImpl` 负责生成默认用户名和密码
4. 手机号唯一性校验保留在 `UserRepository` 层

**备选方案**: 新建 `createStudent()` / `createParent()` 独立方法 → 方法膨胀，逻辑相同仅参数不同。

## Risks / Trade-offs

### R1: 加密密钥管理
- **风险**: AES 密钥泄露导致身份证数据暴露
- **缓解**: 密钥通过环境变量/配置中心注入，不硬编码；后续可接入 KMS

### R2: 孤儿用户
- **风险**: Step 4 失败导致 Step 2/3 创建的用户成为孤儿数据
- **缓解**: 重试时手机号查重自动复用；后续可加定时清理脚本

### R3: 性能 — 多家长批量创建
- **风险**: 家长列表较长时，逐个创建用户可能慢
- **缓解**: 当前场景下家长数量 ≤ 4，逐个创建可接受；后续可优化为批量创建

### R4: StudentClass 实体 classId 语义
- **风险**: `StudentClass.classId` 指向 `Department` 而非 `Class` 实体，可能引起混淆
- **缓解**: 代码注释明确说明 classId 在行政班场景下指向 Department 节点；后续可考虑重命名为 `groupId` 或加文档

## Migration Plan

1. Flyway `V7__alter_t_user_add_id_card.sql`: `ALTER TABLE t_user ADD COLUMN id_card VARCHAR(512)`
2. Flyway `V8__create_t_parent_profile.sql`: `CREATE TABLE t_parent_profile`
3. 部署顺序：先执行数据库迁移，再部署应用代码
4. 回滚：删除 `t_parent_profile` 表 + 删除 `t_user.id_card` 列
