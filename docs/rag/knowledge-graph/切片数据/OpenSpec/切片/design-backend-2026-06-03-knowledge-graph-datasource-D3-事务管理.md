# 事务管理

> summary: 事务按数据源隔离：@Transactional 默认绑定 user 库，知识图谱 Service 用 @Transactional("kg") 显式指定。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-backend-2026-06-03-knowledge-graph-datasource-D3-事务管理.md
> 类别：架构设计

---

### D3：事务管理

> 检索摘要：事务按数据源隔离：@Transactional 默认绑定 user 库，知识图谱 Service 用 @Transactional("kg") 显式指定。

**决策**: `@Transactional` 默认绑定到 `user` 数据源。知识图谱的 Service 方法使用 `@Transactional("kg")` 指定数据源。跨库操作不使用分布式事务，通过应用层保证一致性。

```java
@Service
public class KgSyncAppService {
    @Resource
    private KgTextbookMapper kgTextbookMapper;

    @Transactional("kg")  // 绑定到 kg 数据源
    public void syncFull() { ... }
}
```

> 证据：详见 `2.OpenSpec design 决策/design-backend-2026-06-03-knowledge-graph-datasource.md`（§D3）
