[EN](#en) | [CN](#cn)
-------------------

# [How to contribute](#en)

We welcome everyone to contribute to the project. If you would like to contribute to the project, please read the
following.

## Community Contact

- Ask any issues directly on Github.
- Join our Telegram group: https://t.me/Openai_LLM

## Branch description

- Our `main` branch is the default release branch, please do not submit code directly to this branch.
- Our `dev` branch is the development branch, if you want to contribute to the project, please submit code to this
  branch, we will merge the `dev` branch into the `main` branch regularly.
- Our documentation is published at https://github.com/LlmKira/Docs and any form of contribution is accepted.
- Our framework packages are published on pypi, changes to the sdk will only trigger Release CI when a new OpenAPI is
  released.

## CI/CD

Our CI/CD service is run by `GitHub Actions`, and every commit of `dev` triggers the CI/CD process or manually triggered
by the Release Manager. `main` branch consists of
Release
Manager or Manager triggered manually.

## Content specifications

- Do not submit personal information.
- Please use the PEP8 specification for naming.
- The formatting operation is completed by Reviewer, so there is no need to worry about formatting issues.
- Make sure all commits are atomic (one feature at a time).
- We use pydantic>2.0.0 for data validation, you can submit code for version 1.0.0 (very not recommended), but we will
  upgrade
  it to 2.0.0 when releasing.

## Compatibility instructions

Our code needs to be compatible with Python 3.8+, please do not use new features such as `str | None` `:=` `list[dict]`
and so on.
Of course, if you want to use new features, we also welcome your contributions. Release Manager will do compatibility
checks when releasing new versions.

## Add plugins to the registry

If you want to add your plugin to the registry, please submit the `assert/plugin.py` file update, we will automatically
synchronize to the registry and test through CI.

---------------

# [如何贡献](#cn)

我们欢迎每一个人为项目做出贡献。如果你想要为项目做出贡献，请阅读以下内容。

## 社区联系

- 直接在Github上提出任何问题。
- 加入我们的Telegram群组：https://t.me/Openai_LLM

## 分支说明

- 我们的 `main` 分支为默认发布分支，请勿向此分支直接提交代码。
- 我们的 `dev` 分支是开发分支，如果你想要为项目做出贡献，请向此分支提交代码，我们会定期将 `dev` 分支合并到 `main` 分支。
- 我们的文档发布在 https://github.com/LlmKira/Docs ，接受任意形式的贡献。
- 我们的框架包发布于 pypi，对 sdk 的更改只会在发布新的 OpenAPI 时才会触发 Release CI。

## CI/CD

我们的 CI/CD 服务由 `GitHub Actions` 运行，`dev` 的每一次提交都会触发 CI/CD 流程或 Release Manager 手动触发。`main` 分支由
Release
Manager 或 Manager 手动触发。

## 内容规范

- 不要提交个人信息。
- 命名请使用 PEP8 规范。
- 格式化操作由 Reviewer 完成，不需要担心格式化问题。
- 确保所有提交都是原子的（每次提交一个功能）。
- 我们使用 pydantic>2.0.0 来进行数据校验，你可以提交 1.0.0 版本的代码（非常不建议这样做），但是我们会在发布时将其升级到
  2.0.0。

## 兼容说明

我们的代码需要兼容 Python 3.8+，请不要使用 `str | None` `:=` `list[dict]` 等新特性。
当然如果你想要使用新特性，我们也欢迎你的贡献，Release Manager 会在发布新版本时做兼容性检查。

## 添加插件到注册表

如果你想要将你的插件添加到注册表，请提交 `assert/plugin.py` 文件更新，我们会自动通过 CI 同步到注册表并测试。
