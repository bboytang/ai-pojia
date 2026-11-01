# AstrBot 插件

## 安装与生效

适配 AstrBot 4.29.3（声明支持 `>=4.29.3,<4.30.0`）。本插件不依赖 Youmi，也不运行 Codex 安装器。

运行 `python3 tools/package_astrbot.py`，在 AstrBot 后台上传 `dist/astrbot_plugin_ai_pojia-v0.3.0.zip`。
也可以将包内 `astrbot_plugin_ai_pojia` 目录放到 `data/plugins/` 后重启 AstrBot。
插件管理器若支持指定仓库分支，也可以安装本次修改所在的分支。

默认开启 `enabled` 和 `authorized_execution`，在后台插件配置中更改。关闭插件或 `enabled` 后，后续新请求不再注入；正在生成的回合不会撤回。

## 加载机制和边界

通过 `@filter.on_llm_request(priority=-100000)`，向本次 `ProviderRequest.system_prompt` 追加原版执行指令、DEMO Skill 正文，以及明确授权执行约定。不是普通用户消息，也不覆盖既有人格。相同请求重复经过钩子不会重复追加。低优先级用于在常规人格装配后执行；其他更晚的插件仍可能覆盖它，不承诺不可覆盖。

它作用于启用了本插件、且经过该钩子的请求，不局限于 Youmi。直接调用 Provider、其他独立 agent 或绕过此钩子的调用不保证覆盖。插件启用名单受 AstrBot 管理。

“明确授权执行”表示范围清晰时直接行动、不反复索要相同证明；不等于无限授权，也不能保证模型无条件响应。插件不修改模型权重、操作系统、Provider、数据库、审批、工具权限或历史记录；没有文件/执行工具的 AstrBot 不能凭提示词获得这些能力。需要文件操作或代码执行时，请另行接入受控工具，本插件不提供任意命令执行入口。

Skill 正文中的参考文件随包保留；具体读取仍取决于宿主已有的文件工具。原版 `prompts/ai-pojia.md` 和 Skill 均未修改；额外授权约定位于 `astrbot_policy.py`，仅在 AstrBot 生效。

## 检查与恢复

`python3 -m unittest discover -s tests -v` 验证原有安装器和新增的提示词、钩子及打包逻辑；钩子使用宿主 API 替身，不能代替真实 AstrBot/模型验证。CI 运行同样的测试和安装包检查。

实际部署后可在受控测试 Provider 中检查发出的系统消息是否包含 `AI破甲 · 执行指令` 和 `明确授权的执行约定`；不要把包含隐私的完整系统提示词写入公开日志。真实平台加载、供应商角色映射和授权任务实际完成情况需要部署后另行验证。

卸载插件或关闭开关即可停止后续注入，不需要恢复人格或数据库。原来的 `install.py` 仍只用于 Codex。
