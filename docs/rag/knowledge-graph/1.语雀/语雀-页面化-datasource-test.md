# 页面化-datasource-test（语雀原稿）

> 来源：https://www.yuque.com/zhangmin-jrrer/iu9s4m/test
> 字数：985 ｜ 下载：2026-08-24

# 知识图谱数据源配置 测试用例设计

## 1. 测试概述

### 1.1 测试目标
验证双数据源配置的正确性，确保知识图谱 Mapper 路由到 `ai_edu_kg`，业务 Mapper 路由到 `ai_edu_user`，事务按数据源正确隔离。

### 1.2 测试方式
- **集成测试**: 使用 `@SpringBootTest` + 真实数据源
- **测试环境**: 使用 H2 内存库（单库模拟），验证路由逻辑
- **数据源验证**: 通过检查 SQL 执行的数据库连接确认路由正确

### 1.3 测试环境配置
- Profile: `test`
- 数据库：使用 H2 内存库（单库简化，仅验证路由逻辑）
- 生产环境需切换到真实的 `ai_edu_user` + `ai_edu_kg`

---

## 2. 测试数据

| 参数 | 值 | 说明 |
|-----|-----|-----|
| TEXTBOOK_URI | "http://edukg.org/knowledge/3.1/textbook/一年级上册" | 教材 URI |
| TEXTBOOK_LABEL | "一年级上册" | 教材名称 |
| TEXTBOOK_GRADE | "一年级" | 年级 |
| TEXTBOOK_PHASE | "primary" | 学段 |
| TEXTBOOK_SUBJECT | "math" | 学科 |

---

## 3. 测试用例清单

### 3.1 双数据源启动 (KG-DS-001 ~ KG-DS-003)

| 用例编号 | 场景描述 | 前置条件 | 输入 | 预期结果 |
|---------|---------|---------|------|---------|
| KG-DS-001 | 启动成功-双数据源初始化 | application.yml 配置正确 | 无 | 应用启动成功，user 和 kg 两个 HikariCP 池均初始化 |
| KG-DS-002 | 启动失败-缺少 kg 数据源配置 | application.yml 中无 kg 配置 | 无 | 应用启动失败，日志提示 "datasource 'kg' not found" |
| KG-DS-003 | 启动失败-非法数据源名称 | Mapper 使用 `@DS("unknown")` | 无 | 应用启动失败，Strict 模式抛异常 |

### 3.2 Mapper 路由验证 (KG-DS-004 ~ KG-DS-008)

| 用例编号 | 场景描述 | 前置条件 | 输入 | 预期结果 |
|---------|---------|---------|------|---------|
| KG-DS-004 | UserMapper 走 user 库 | 双数据源已启动 | userMapper.insert(user) | 数据写入 `ai_edu_user` 库 |
| KG-DS-005 | KgTextbookMapper 走 kg 库 | 双数据源已启动 | kgTextbookMapper.insert(textbook) | 数据写入 `ai_edu_kg` 库 |
| KG-DS-006 | KgChapterMapper 走 kg 库 | 双数据源已启动 | kgChapterMapper.insert(chapter) | 数据写入 `ai_edu_kg` 库 |
| KG-DS-007 | 无 @DS Mapper 默认走 user 库 | Mapper 无注解 | anyMapper.insert(data) | 数据写入 `ai_edu_user` 库 |
| KG-DS-008 | 现有业务接口不受影响 | 用户已登录 | GET /api/user/profile | 正常返回用户数据，路由到 user 库 |

### 3.3 事务隔离 (KG-DS-009 ~ KG-DS-012)

| 用例编号 | 场景描述 | 前置条件 | 输入 | 预期结果 |
|---------|---------|---------|------|---------|
| KG-DS-009 | `@Transactional("kg")` 绑定 kg 库 | kg 库可写 | syncFull() 方法执行 | 所有写入在 `ai_edu_kg` 事务中 |
| KG-DS-010 | `@Transactional` 默认绑定 user 库 | user 库可写 | saveUser() 方法执行 | 所有写入在 `ai_edu_user` 事务中 |
| KG-DS-011 | kg 事务失败回滚 | kg 库中途抛异常 | syncFull() 中途失败 | `ai_edu_kg` 全部回滚，无半写入状态 |
| KG-DS-012 | 跨库操作无分布式事务 | 需同时写两个库 | 应用层分别操作 | 两个事务独立，应用层保证一致性 |

### 3.4 Flyway 迁移 (KG-DS-013 ~ KG-DS-015)

| 用例编号 | 场景描述 | 前置条件 | 输入 | 预期结果 |
|---------|---------|---------|------|---------|
| KG-DS-013 | user 库迁移脚本定位 | Flyway 配置正确 | 扫描 user 路径 | 读取 `db/migration/user/` 下的脚本 |
| KG-DS-014 | kg 库迁移脚本定位 | Flyway-kg 配置正确 | 扫描 kg 路径 | 读取 `db/migration/kg/` 下的脚本 |
| KG-DS-015 | 初始知识图谱表创建 | `V1__Init_Knowledge_Graph.sql` | 执行 Flyway-kg | 7 张表在 `ai_edu_kg` 中创建成功 |

---

## 4. 错误码对照表

| 错误码 | 常量名 | 说明 |
|-------|-------|------|
| 00000 | SUCCESS | 成功 |
| 10001 | PARAM_ERROR | 参数错误 |
| 10004 | UNAUTHORIZED | 未登录 |
| 70008 | KG_DATASOURCE_ERROR | 知识图谱数据源异常 |

---

## 5. 测试用例统计

| 模块 | 用例数量 |
|-----|---------|
| 双数据源启动 | 3 |
| Mapper 路由验证 | 5 |
| 事务隔离 | 4 |
| Flyway 迁移 | 3 |
| **总计** | **15** |

---

## 6. 测试执行顺序

```
KG-DS-001 ~ KG-DS-003 : 双数据源启动测试
KG-DS-004 ~ KG-DS-008 : Mapper 路由验证
KG-DS-009 ~ KG-DS-012 : 事务隔离测试
KG-DS-013 ~ KG-DS-015 : Flyway 迁移测试
```

---

## 7. 辅助方法

### 7.1 验证数据源路由
```java
private void verifyDatasourceRouting(String expectedDatasource) {
    String currentDs = DataSourceContextHolder.peek();
    assertThat(currentDs).isEqualTo(expectedDatasource);
}
```

### 7.2 创建测试教材数据
```java
private KgTextbook createTestTextbook() {
    KgTextbook textbook = new KgTextbook();
    textbook.setUri(TEXTBOOK_URI);
    textbook.setLabel(TEXTBOOK_LABEL);
    textbook.setGrade(TEXTBOOK_GRADE);
    textbook.setPhase(TEXTBOOK_PHASE);
    textbook.setSubject(TEXTBOOK_SUBJECT);
    return kgTextbookRepository.save(textbook);
}
```

---

## 8. 运行测试

```bash
# 运行数据源相关测试
cd ai-edu-backend && mvn test -Dtest=KgDatasourceTest

# 运行事务隔离测试
mvn test -Dtest=KgTransactionTest

# 运行全部知识图谱相关测试
mvn test -Dtest=Kg*Test
```