# 本地 API 与持久化

```bash
python -m pip install -e '.[api,test]'
python -m uvicorn myriadforge.api:app --host 127.0.0.1 --port 8000
```

浏览器打开 `http://127.0.0.1:8000/docs` 操作接口。
通过 `NEXUS_DB_PATH` 配置 SQLite 文件，默认 `nexus.sqlite3`。
当前不含身份验证、配额与生产部署配置，仅限本地研发。

| 方法 | 路径（前缀 `/api/v1/myriadforge`） | 用途 |
| --- | --- | --- |
| GET | `/reference` | 人工案例、形态、配方与未实现状态 |
| POST | `/concepts` | 真实调用模型，校验并保存概念 |
| GET | `/concepts/{id}` | 读取概念及生成来源 |
| POST | `/sessions` | 创建固定案例模拟会话与示例背包 |
| GET | `/sessions/{id}` | 读取当前状态与版本 |
| POST | `/sessions/{id}/transitions` | 检查版本与形态条件后切换 |
| POST | `/sessions/{id}/crafts` | 事务内扣料、解锁并保存幂等记录 |

`GET /health` 只表示进程存活，不证明模型或数据库可用。

生成请求：`{"brief":"星空机关风的非功能性展示道具"}`。
切换请求：`{"target_form":"umbrella","expected_version":0}`。
合成请求：`{"recipe_id":"guardian","request_id":"unique-request-id","expected_version":1}`。
成功变更后版本加一；旧版本返回 `409 VERSION_CONFLICT`。
同一会话同一幂等键和配方重试不会再次扣料，返回当前会话快照；同键换配方返回冲突。
事务保证规则失败时不写入部分状态。重新启动进程后会话和概念仍可读取。

模型概念与模拟案例目前独立：生成的概念不会自动获得受验证的配方或3D模型。
模拟会话背包明确标为 `demo_fixture`，不是 AI 生成或真实游戏采集所得。
SQLite 调用为小规模同步本地实现；高并发部署前需要数据库迁移与任务队列。
概念生成当前是有超时的同步请求流程（异步等待网络），尚无后台任务或全局预算限制。
