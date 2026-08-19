# 后端答疑链路「网络波动」排查记录（2026-08-19）

> 转后端结论:Python 服务**本机自测健康**,根因是 Java 后端 `gateway.base-url` 写死 `localhost:9527`,
> 后端运行环境(非本机/容器)连不到 Python 服务。改动在后端 `application.yml` 一行配置,Python 侧零改动。

## 一、现象（后端联调反馈）

| # | 现象 | 链路 |
|---|------|------|
| ① | 答疑 agent 全部返回「网络波动,请重试」(非偶发) | decide / generate |
| ② | `/api/kp/resolve` 知识点解析全部 PENDING | resolve → LLM 消歧 |
| ③ | analyze-question 题型识别降级 PENDING | analyze → question-understand |

## 二、Python 侧自测（全部通过）

| 检查项 | 结果 |
|--------|------|
| `GET http://localhost:9527/health` | 200,监听 `0.0.0.0:9527`(非仅 127.0.0.1) |
| `POST /api/tutoring/decide`(最小 SSE) | 200 + 完整事件流:agent(perceive→analyze→plan→decide)→ meta → done,真实 doubao,<15s |
| `POST /api/tutoring/generate` | 200 + meta → agent → thinking 推理流,正常 |
| token 比对 | 后端 `internal-token: my-secret-token-123` == Python `.env` `INTERNAL_TOKEN` |
| 端口比对 | 后端 `base-url: http://localhost:9527` == Python 实际监听 9527 |

decide/generate 共用路由注册 + `verify_internal_token` + SSE + doubao 链路,全通 ⇒ 路由、鉴权、网关层无问题。
resolve / question-understand / vector 复用同一套基础设施。

## 三、根因

`ai-edu-backend/ai-edu-interface/src/main/resources/application.yml:104`:

```yaml
gateway:
  base-url: http://localhost:9527   # ← 问题在这
  internal-token: my-secret-token-123  # 无需改
```

`localhost` 只在后端与 Python 同机时成立。全链路失败 + 非偶发,而 Python 本机自测全通 ⇒
**后端运行环境 ≠ Python 所在机器**,其 `localhost:9527` 指向后端自己。

## 四、后端改动（一行配置）

| 后端部署形态 | base-url 改成 |
|--------------|---------------|
| 同机不同 Docker 容器 | `http://host.docker.internal:9527` |
| k8s / 同内网 | `http://<python-svc>:9527` 或内网 IP |
| 跨机器 / 远程 | `http://<Python服务公网或内网IP>:9527` |

> 改 `src/main/resources/application.yml` 源文件;`target/classes/application.yml` 是编译产物,
> 改后需**重新构建/重启**才生效。

## 五、后端验证方法

```bash
# 1. 网络通路
curl http://<python地址>:9527/health    # 期望 200 {"status":"healthy"}

# 2. 最小 decide SSE
curl -N -X POST http://<python地址>:9527/api/tutoring/decide \
  -H "Content-Type: application/json" \
  -H "x-internal-token: my-secret-token-123" \
  -d '{"history":[{"role":"user","content":"鸡兔同笼,共35头94脚,鸡兔各几只?"}],"round_count":0,"answer_request_count":0,"subject_hint":"math"}'
# 期望: event: agent ... event: meta ... event: done
```

## 六、验收

- [ ] decide 返回 200 且事件流完整(thinking → agent → meta → done)
- [ ] resolve 传「鸡兔同笼」能解析出知识点 URI(不再 PENDING)
- [ ] 答疑 agent 不再回「网络波动,请重试」

> 若后端确认与 Python 同机仍失败:大概率走了不同网络命名空间(容器),或防火墙拦 9527;
> 少数情况是 `internal-token` 被注入为空(检查配置是否被覆盖)。

## 附:2026-08-19 同日已修(图片分析慢,另 commit)

`question-understand` 32s+ 根因 = 未关思考(extra_body thinking disabled)+ 无内部超时,
已修复并提交 `afaeb2d`(见 docs/ai-tutoring-question-understand 相关改动)。
