# 坑档案-J-KG11-全量同步任务拆分

> summary: 全量同步任务拆分
> 来源: 坑档案 ｜ 锚点: J-KG11 ｜ 节: 5.难点/坑档案.md
> COS路径: rag-slices/knowledge-graph/坑档案/坑档案-J-KG11-全量同步任务拆分.md
> 类别：开发难点
> target: 开发对账

---

**1. 问题现象**：知识图谱从 MySQL 同步到 Neo4j 的全量同步是一个超长任务，一旦某年级失败整个同步挂掉；崩溃后状态记录卡在 running，**后续同步被阻塞**；多人同时点"同步"还会并发写冲突。

**2. 触发流程**：前端 SyncManager 触发全量同步（`aiEduPlatformFront/ai-edu-front/src/components/kg/SyncManager.jsx`）→ Java `KgSyncAppService.syncFull` 把该 edition+subject 下所有年级一次性跑 → 任一年级抛错/进程被杀 → 同步记录停在 running。

**3. 根因分析**：修前同步是**单一大任务**：没有按 grade 切分（一个失败全挂）、没有锁（并发触发互相覆盖）、崩溃后 running 记录无超时判定（后续同步永远认为"有任务在跑"）。`KgSyncAppService.java:40` 注释："每个 grade 子任务拥有独立的锁、独立的同步记录、独立的对账"。

**4. 排查过程**：一次同步中途进程被杀，重跑提示"已有任务在跑"；查同步记录表发现上次任务状态是 running 且 startedAt 很久以前——**僵尸任务卡死**。

**5. 解决方案 & 改动点**（`ai-edu-backend/ai-edu-application/src/main/java/com/ai/edu/application/service/kg/KgSyncAppService.java`）：① **按 grade 拆分**——`syncOneGrade(edition, subject, stage, grade)` 每个年级独立锁/记录/对账（`:253-310`）；② **Redis 分布式锁**——`redisService.tryLock(lockKey, lockValue, 600s)` 防并发，锁粒度 `edition:subject:stage:grade`（`:79,166-223,256-330,363-368`）；③ **卡死检测**——启动前 `detectAndMarkStale`，超过 10 分钟（`KG_SYNC_STALE_THRESHOLD_MINUTES=10`，`:80`）的 running 记录标记 failed（"Task exceeded time limit, considered crashed"，`:338-346`），解除阻塞；④ **对账**——同步后 `reconcile(gradeRequest)` 比对 MySQL 与 Neo4j 计数，mismatch 记入 `reconciliationStatus`（`:288,136-153`）。提交：`e7865a8 [知识图谱]-[同步任务拆分]`、`fd2a102 [知识图谱]-[同步任务优化]`。

**6. 面试口述要点**：长任务工程化三件套：**拆粒度**（一个大任务拆成可独立成功/失败/重试的子任务）、**加锁**（分布式锁防并发，锁粒度越小并发度越高）、**状态自愈**（running 要有超时判定，崩溃不留僵尸）。对账（MySQL vs Neo4j 计数比对）是同步类任务的可观测性兜底——不能只"跑完就算完"，要能证明两库一致。
