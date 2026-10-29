# 地理历史问答助手 · 学习项目

以地名、时代、事件与地理环境为场景，逐步开发可供 Android 调用的 Agent。
区分模拟文本、未检索来源的模型生成与有资料支撑的回答。

## 环境与入口

Python 3.11.16；本次实测安装 openai 3.37.0、python-dotenv 1.2.4。
pyproject.toml 与 uv.lock 已由学习者更新。

```bash
cd /Users/leon/workspace/PythonProject/history-ai-agent
.venv/bin/python geo_history_cli.py
.venv/bin/python config.py
.venv/bin/python test/check_display.py
.venv/bin/python test/check_s2_03.py
.venv/bin/python test/check_s3_01.py
.venv/bin/python test/check_s3_02.py
.venv/bin/python test/check_s3_03.py
.venv/bin/python test/check_s3_04.py
.venv/bin/python test/check_s3_05.py
```

geo_history_cli.py 是离线模拟入口；model_demo.py 保留早期实现，当前真实问答入口为 model_demo_ask_turn.py（原 model_demo_pro.py 已改名），使用 Kimi / kimi-k3。后续课程使用 ask_turn 入口；早期文件名只作为历史记录保留。可复用单次问答与 CLI 展示已通过离线验收。
config.py 维护供应商配置，并在导入时使用 dotenv 加载 .env；默认供应商仍为 DeepSeek，但模型示例显式选择 kimi。
Kimi 的本项目变量名为 KIMI_API_KEY。只在本地配置，不打印或提交；已验证 .env 被忽略且未被 Git 跟踪。

## 当前验证状态

- S1-01、S1-02 历史验收已通过；当前配置已扩展为多供应商与 .env，不能据此认为所有供应商均已调用验证。
- 学习者已提交本节两次真实运行输出与 usage/finish_reason；实际输入附带判定说明，作为带验收提示的初次验证记录，不当作原始问题基线。
- S2-01 本地功能验收通过：正常解析、空回答提示、缺少 Key、空白问题、截断、鉴权失败、503 和超时路径通过；异常不回显敏感假值。
- 已约定请求预算：timeout=120 秒、max_retries=0、max_completion_tokens=4096、reasoning_effort="low"。
- 2026-10-27 最新复验：test/check_display.py 的 10/10 项通过，S2-02 离线功能验收完成；请求参数已恢复，旧 max_tokens 字段已移除。
- 本节两题导师初评均满足实际输入要求，stop 正常结束；原始 E01/E02 未附判定说明的表现仍待验证，未做来源核验。

## S2-03 已验收范围

2026-10-27 复验源文件 b0a3638c：test/check_s2_03.py 7/7 通过（含上一课 10 项回归）；提示词四项规则与未接入检索的声明人工审阅通过。编辑工程的说明已删除，原调用参数及展示保留。
EVAL_CASES.md 学员两题自评仍待补，不标记评估训练或整个阶段完成；当前短提示词的真实效果尚未验证。
不打印原始 APIError 消息、Key、请求头或完整响应对象；来源标签不代表历史事实已核实。

## S3-01：离线历史管理验收通过

学员已实现 conversation.py 中的 create_history、build_turn_messages、commit_turn。2026-10-27 导师复验源码 ca747593：test/check_s3_01.py 9/9，退出码 0，含旧功能回归；完整 assistant 保留、嵌套快照及会话隔离、输入校验通过。检查隔离 .env 和真实环境并阻断网络。
已区分准备与提交：只有成功问答进入已提交历史，失败请求不留下半轮问题；正常历史增长仍需另做裁剪。学员最初将目的理解为“上下文过长”，本轮已解释，理解待后续失败分支迁移检验。
进入 S3-02 前源码 c57e4a4a 再次复验 9/9；当时历史模块尚未接入 CLI/SDK，接线现已在 S3-02 离线验收。

## S3-02：多轮调用离线验收通过

2026-10-28 导师复验 model_demo_pro.py（864e6779）、conversation.py（c57e4a4a）：test/check_s3_02.py 12/12，退出码 0，含此前回归。学员已将 assistant_message 移到原三个 token 字段之后，旧五参数构造恢复兼容。成功提交、完整协议字段、CLI 多轮及失败不污染历史均离线通过。
E12/E13 真实追问结果尚未提供，是否已运行不推断；已有输出可直接补录，无需重复付费。离线检查不证明真实回答质量或事实已核实。

## S3-03：请求历史裁剪离线验收通过

2026-10-28 导师复验 conversation.py（f894dec2）和当前入口 model_demo_ask_turn.py（44382524）：完整轮次、边界、深拷贝、SDK/CLI 及失败历史一致性通过。原脚本跳过旧回归显示 11/11；导师恢复该项后 12/12、退出码 0，最新版本在新课基线中再次通过回归。
学员能解释旧信息超出 max_rounds 窗口后未随请求发送；本地完整历史仍保留。轮数不保证 token 上限，也不限制本地历史内存增长。未新增真实调用，不据此判断回答质量。

## S3-04：会话存储离线验收通过

2026-10-29 导师复验：session_store.py（98aa44a8）、conversation.py（2a66f1ee）、model_demo_ask_turn.py（44382524），test/check_s3_04.py 12/12、退出码 0。学员已移除 commit_turn 的固定写盘及两个导入，历史模块只处理内存；完整存储、错误处理、新进程恢复和旧回归通过。导师未修改业务代码或已有会话，未调用模型；解释已提供，不等同于学员已独立掌握。

## 当前 S3-05：CLI 接线通过，保存失败提示待收尾

2026-10-29 学员已实现 main(session_path=None)、脚本默认路径与 Git 忽略、启动恢复、成功保存和失败后继续。源码 model_demo_ask_turn.py（85f35d9e）原脚本 12/12；人工审阅发现 OSError 提示“本地内存保存失败”，实际内存已成功提交，失败的是文件写入/目录创建。
导师原检查只匹配“内存”二字，漏检状态含义；已在原两项中补强，保留 12 项总数，实际 **10/12、退出码 1**。两个失败来自同一条提示，非两个独立错误；其他接线与旧回归通过。唯一小任务：将提示改为明确的“文件保存失败（异常类别），本轮回答仍在内存中”。不需要修改保存流程。

```bash
.venv/bin/python test/check_s3_05.py
```

目标仍 12/12、退出码 0；检查使用临时文件与假响应，不读取真实 Key 或调用模型。导师仅在临时副本修正文案确认 12/12，未改工程业务代码或已有会话；不能据诊断控制标学员完成。本轮已解释：模型生成与内存提交已成功，文件保存失败不能靠重调模型解决；学员目前明确提到资源消耗，失败阶段的独立理解待巩固。S3-06 流式任务尚未布置。

教学约定保存在 AGENTS.md；每课验收后自动更新记录并布置一个小任务，业务实现由学员完成。

## 每日学习复盘

[DAILY_REPORT.md](/Users/leon/workspace/PythonProject/history-ai-agent/DAILY_REPORT.md) 按日期记录当天进展、验证证据、易错点、关键知识、相关面试题与参考答案及复习建议。已启用“AI 应用开发每日复盘”，每天北京时间 22:00 在当前辅导对话执行；同日更新、保留既往记录，不运行项目模型请求或自动推进课程。2026-10-28 已创建初始化快照，既往成果单独标为历史复习。

## 文件组织

- 根目录 `*.py`：当前业务模块与学习示例；`pyproject.toml`、`uv.lock`：依赖。
- `test/`：各课离线检查脚本，从工程根目录运行，例如 `.venv/bin/python test/check_s3_05.py`。
- `docs/prompts/`：提示词参考资料。
- 根目录 `AGENTS.md`、学习计划、进度、评估和日报：保留约定位置，供辅导和每日复盘读取。
- `data/`：本地会话数据，不提交；`.env`、虚拟环境和 IDE 缓存也不提交。

新环境先执行 `uv sync`，复制 `.env.example` 为 `.env` 后自行配置 Key；检查脚本不需要真实 Key。
