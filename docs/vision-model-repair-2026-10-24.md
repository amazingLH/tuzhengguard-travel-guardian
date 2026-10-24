# 图片解析模型修复 · 2026-10-24

## 原因

上传图片解析使用的 `qwen3.7-flash` 被上游返回 HTTP 403、`insufficient_quota`，消息明确为免费额度耗尽且启用了仅免费用量模式。此前文本问答已切换至可用模型，但视觉解析仍使用受限模型。

## 修改

图片解析默认值、本地配置与魔搭空间普通变量统一改为 `qwen3-vl-plus`，文本问答继续使用 `qwen-plus`。两者均在当前凭据的模型列表中，且通过实际请求验证。未修改账户计费保护开关，不自动尝试其他收费模型。

图片解析错误现在区分免费额度限制、账户欠费、权限、模型不存在与其他服务错误。页面不会暴露上游错误正文或凭据。按日调用限制及本地示例行为保持原有策略。

## 验证

单张车票真实请求成功；随后绕过本地示例缓存，将三张公开脱敏车票一起发送给 `qwen3-vl-plus`，一次请求完整返回三张覆盖记录及三段行程。第三张被遮挡的车次列入低置信字段，供人工确认。结构化摘要见 [真实解析记录](evidence/vision-model-2026-10-24.json)。

自动回归新增免费额度/权限/模型不存在错误的安全提示检查；完整测试 200 项通过，离线评估与 Ruff 检查通过。

## 控制台位置

在[华北2（北京）免费额度页面](https://bailian.console.aliyun.com/cn-beijing/costing-balance/free-quota)按 Code 搜索 `qwen-plus` 和 `qwen3-vl-plus`；也可从[模型广场](https://bailian.console.aliyun.com/model/market)进入详情选择对应 Code/版本。免费额度显示受地域、有效期和模型本身是否提供额度影响，具体规则见[百炼官方说明](https://help.aliyun.com/zh/model-studio/new-free-quota)。
