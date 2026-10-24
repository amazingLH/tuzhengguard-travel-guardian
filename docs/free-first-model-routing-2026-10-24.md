# 免费优先与付费备用模型 · 2026-10-24

## 模型选择

| 模型 Code | 能力与用途 | 本项目策略 |
| --- | --- | --- |
| `deepseek-v4.1-flash-1017` | 文本问答、视觉理解、JSON 输出 | 问答与截图解析的优先模型 |
| `qwen-image-2.1-pro` | 图片生成与编辑 | 不用于行程识别或问答 |
| `qwen-image-2.1-turbo` | 图片生成与编辑 | 不用于行程识别或问答 |
| `qwen3.7-flash` | 文本问答、视觉理解、JSON 输出 | 免费额度耗尽后的付费备用模型 |

能力依据：[模型发布记录](https://help.aliyun.com/zh/model-studio/newly-released-models)、[DeepSeek 接口](https://help.aliyun.com/zh/model-studio/deepseek-api)、[图像生成](https://help.aliyun.com/zh/model-studio/text-to-image)。

## 调用策略

在百炼为 DeepSeek **开启**“免费额度用完即停”，为备用 Qwen **关闭**该开关。上游先抵扣 DeepSeek 免费额度；额度耗尽后拒绝主模型请求，应用收到明确的免费额度错误后，将原始会话或图片请求完整发送给备用 Qwen。程序没有覆盖百炼账户开关的能力；若 DeepSeek 关闭开关，上游可能直接对其按量计费，应用就收不到用于切换的免费额度拒绝信号。额度规则见[官方说明](https://help.aliyun.com/zh/model-studio/new-free-quota)。

```text
DASHSCOPE_TEXT_MODEL=deepseek-v4.1-flash-1017
DASHSCOPE_VISION_MODEL=deepseek-v4.1-flash-1017
DASHSCOPE_FALLBACK_MODEL=qwen3.7-flash
```

主模型成功时不调用备用模型。只对明确的免费额度拒绝切换一次，不因普通权限、欠费、网络、限流或服务错误追加付费调用。图片 JSON 首次未通过校验时，沿用已经切换成功的模型进行原有的单次结构修复，不重新循环模型。解析摘要记录实际成功的模型及请求次数；内部元数据记录切换原因，不包含密钥。应用每日额度按用户操作计一次，保留原有 100 次策略。

若主、备都被免费模式限制，页面提示维护者检查备用模型开关；若账户欠费则使用余额不足提示。上述错误不缓存。问答继续携带当前会话、原方案、Plan B 及对话历史，输出最多 300 字。账户可用性、网络或上游服务故障仍可能导致请求失败，备用策略不能替代账户余额与服务授权。

## 验证

- DeepSeek 真实问答成功；三张公开脱敏车票一次请求完整返回三段行程及逐张覆盖记录。
- 维护者确认关闭 Qwen 仅免费限制后，Qwen 文本与视觉实际调用均恢复。
- 人工仅注入主模型“免费额度耗尽”错误，后续请求转发至真实 Qwen：问答和图片解析均成功。没有为了测试实际耗尽账户额度。记录见[验证摘要](evidence/free-first-routing-2026-10-24.json)。
- 自动回归覆盖主模型成功不调用备用、带全部会话切换、全量图片切换、结构修复沿用备用、重复拒绝时有界终止、非额度错误不触发付费、显式指定模型时不切换与 300 字上限。
