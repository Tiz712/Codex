# OpenAI 接入与更换模型

## 配置

通过系统环境或服务器秘密配置设置 `OPENAI_API_KEY`、`OPENAI_MODEL`。
默认 `AI_PROVIDER=openai`。`.env.example` 不会自动加载，不提交真实密钥。
选择账号可用、支持 Responses API 严格 JSON Schema 输出的模型。
本工程不硬编码未经账号验证的模型名称，也不承诺所有模型都兼容。

将文字需求写入 UTF-8 文件，例如 `brief.txt`，然后运行：

```bash
python -m myriadforge --brief-file brief.txt --output generated/concept.json
```

先创建 `generated/` 目录。命令会进行一次真实付费请求；离线测试不会。
模型有权拒绝或返回不完整输出，程序不会用示例代替成功。
输出目录已被 Git 忽略，但不要将密钥写入需求文件。

## 输出与边界

保存结构化概念、供应商、模型、提示词版本、输入 SHA-256 和返回用量。
本地检查字段类型、文本长度与四个互不重复的受支持形态。
`validation_scope=concept_schema_only`：只验证概念结构，不验证机械可行性、游戏配方或打印。
调用不启用模型工具，不授予模型执行 shell、改文件或直接扣料的权限。

## 错误

配置缺失、模型拒绝、输出不完整、字段错误、认证失败、限流、超时和网络失败均返回稳定错误码。
不向用户输出上游错误正文或 API Key。不自动重试，以免重复产生费用。
`store=false` 是请求配置，不等价于供应商的零数据保留协议。
没有总预算自动控制；在供应商后台设置预算和用量提醒，后续增加应用侧配额。

## 更换供应商

实现 `ModelGateway.generate_concept`，返回 `GenerationResult`，并在 `configured_gateway` 注册。
不同供应商分别映射结构化输出、错误与用量；不能只替换 URL 就假定能力相同。
供应商输出仍须经过相同的本地概念校验。

## 验证状态

目前使用模拟响应完成离线测试；尚未配置密钥进行真实模型实测。
