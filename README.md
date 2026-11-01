# -

# AI Nexus Lab · 千机工坊 MyriadForge

面向幻想装备的结构化创作平台。首期验证星穹千机伞的四形态、配方解锁与游戏资产接口。

## 当前交付

这是环境重建后的 GitHub 起步包，不是完整 MVP。

- 已实现：四形态约束、游戏材料扣除、会话内幂等、可替换模型网关、OpenAI 结构化概念适配器与命令行、FastAPI、SQLite 持久化与离线回归测试。
- 已配置：GitHub Actions、Issue 模板、PR 模板、环境变量示例。
- 待实现：真实模型实测、中文工作台、3D、游戏导入与生产部署。
- 预设案例为人工示例，不冒充 AI 结果；尚无可打印性声明。

## 本地验证

Python 3.12+：

```bash
python -m pip install -e '.[api,test]'
python -m unittest discover -s tests -v
python -m compileall -q myriadforge tests
```

回归测试不调用模型，不需要密钥，也不会产生费用。

## 架构方向

业务 → ModelGateway → OpenAI Responses；以后可增加千问或本地模型适配器。
模型生成候选，确定性规则判断状态与材料。Blender 参数化模型生成 GLB 与同源三视图，后续接 Godot。

环境变量见 `.env.example`。现已支持读取环境变量并通过命令行调用 API，配置方法见 [OpenAI 接入说明](docs/openai.md)。尚未配置密钥进行真实调用验证。
不要提交真实密钥、模型权重、学生数据或大型生成文件。

## GitHub 仓库

目标仓库：https://github.com/Tiz712/Codex 。当前仓库为公开可见。

```bash
git clone https://github.com/Tiz712/Codex.git
cd Codex
```

在工程初始化 PR 合并前，需切换到 `codex/myriadforge-starter` 分支。
GitHub 认证通过官方 CLI、SSH 或凭据管理器完成，不将令牌写入远程 URL。
CI 使用离线测试，不需要模型密钥；实际结果以 GitHub Actions 为准。

参见 [开发规范](CONTRIBUTING.md)、[安全说明](SECURITY.md)、[开发任务](docs/backlog.md)。
尚未选定开源许可证；公开可见不构成开源授权。

## 本地接口

```bash
python -m uvicorn myriadforge.api:app --host 127.0.0.1 --port 8000
```

打开 `http://127.0.0.1:8000/docs` 查看接口。详见 [API 与持久化](docs/api.md)。
仅限本地研发；目前没有登录、配额和公开部署能力。生成概念与固定模拟案例仍相互独立。
