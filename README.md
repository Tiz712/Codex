# -

# AI Nexus Lab · 千机工坊 MyriadForge

面向幻想装备的结构化创作平台。首期验证星穹千机伞的四形态、配方解锁与游戏资产接口。

## 当前交付

这是环境重建后的 GitHub 起步包，不是完整 MVP。

- 已实现：四形态约束、游戏材料扣除、会话内幂等、模型网关协议、离线回归测试。
- 已配置：GitHub Actions、Issue 模板、PR 模板、环境变量示例。
- 待实现：OpenAI 实际适配器、结构化生成、API、数据库、网页、3D、游戏导入与部署。
- 预设案例为人工示例，不冒充 AI 结果；尚无可打印性声明。

## 本地验证

Python 3.12+：

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
python -m compileall -q myriadforge tests
```

回归测试不调用模型，不需要密钥，也不会产生费用。

## 架构方向

业务 → ModelGateway → OpenAI（下一开发项）；以后可增加千问或本地模型适配器。
模型生成候选，确定性规则判断状态与材料。Blender 参数化模型生成 GLB 与同源三视图，后续接 Godot。

环境变量见 `.env.example`。目前仅定义配置契约，尚未读取或调用 API。
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
