# 页面化-datasource-api（语雀原稿）

> 来源：https://www.yuque.com/zhangmin-jrrer/iu9s4m/api
> 字数：200 ｜ 下载：2026-08-24

# 知识图谱数据源配置 - API 影响说明

> 本文档说明双数据源改造对 API 的影响
> 更新日期: 2026-04-15

---

## API 无变更

本次变更为**基础设施层改造**，所有 API 接口（路径、参数、响应格式）**完全不变**。

- 知识图谱 API（`/api/kg/**`）的接口定义与 `knowledge-graph-ui` change 中的 `api.md` 一致
- 现有业务 API（`/api/user/**`, `/api/org/**`, `/api/question/**` 等）完全不受影响
- `ApiResponse<T>` 统一响应格式不变

## 数据源映射

| API 路径前缀 | 数据源 | 数据库 |
|-------------|--------|--------|
| `/api/kg/**` | `kg` | `ai_edu_kg` |
| `/api/user/**` | `user`（默认） | `ai_edu_user` |
| `/api/org/**` | `user`（默认） | `ai_edu_user` |
| `/api/question/**` | `user`（默认） | `ai_edu_user` |
| `/api/homework/**` | `user`（默认） | `ai_edu_user` |
| `/api/learning/**` | `user`（默认） | `ai_edu_user` |

前端无需修改任何调用方式。

---

*文档生成时间: 2026-04-15*