# 地理历史 Agent 学习路线

每次一个主要目标、一个 30～60 分钟小任务；学习者实现，导师按代码和运行证据验收。
S1-01、S1-02 已通过；S2-01～S2-03 程序验收及当前提示词人工审阅通过。已有两次带提示的真实结果；学员自评、短提示词真实效果仍待验证，不标记整个阶段完成。S3-01 离线历史管理 9/9；S3-02 多轮调用离线 12/12 验收通过，真实追问结果待提供；S3-03 请求历史裁剪离线 12/12 通过；S3-04 存储及旧回归 12/12 通过；S3-05 CLI 保存恢复及状态提示离线 12/12 通过；S3-06 导师示范程序及学员当前概念小问通过；S3-07A SDK 流式调用离线 12/12 通过；S3-07B最新保存版本离线12/12通过；S3-08中断与提交边界离线12/12通过；S3-09由导师按请求完成示范报告并离线3/3通过；当前S4-01在阶段4新入口定义离线契约，基线1/8。

## 每课验收后同步 GitHub（2026-10-30补充）

- 用户持续授权：每次课程任务经导师检查确认无误后，同一轮自动提交并推送到本工程已配置的GitHub仓库和当前对应分支，无须学员逐次提醒或重复确认；本工程当前为zhoulei9910-gif/history-ai-agent的main。
- 先更新验收记录、布置下一课并生成其检查脚本，再提交课程相关代码、检查与学习记录。下一课未完成的状态必须写清，不把新检查的预期失败算成本课验收失败或新课完成。
- 只纳入相关文件；不提交.env、真实Key、会话缓存、虚拟环境或个人IDE配置，保留无关工作区及暂存内容。普通提交和推送，不擅自覆盖远端历史或把无关暂存文件带入提交。
- 推送并核对远端分支后才报告“已上传”；失败时区分已本地提交与尚未推送，说明实际原因，不编造上传成功。本约定不授权自动执行付费模型调用。

## 每个大阶段使用独立 Python 入口（2026-10-31补充）

- 按学员要求，每个大阶段新建一个学习入口；同阶段的小课持续迭代该入口。阶段3保留model_demo_ask_turn.py，阶段4从stage4_structured.py开始，后续阶段不再往旧入口叠加功能。
- 需要继承旧课能力时，可将ask_turn及必要依赖复制到新阶段入口，说明复制来源和当前改动；保留旧课及其检查。只有学员明确要求修复旧课时才修改旧入口，不因新阶段需要顺手重构旧代码。
- 复制到新阶段时检查配置、入口保护和会话路径；会话存储使用各阶段独立路径，避免练习覆盖旧会话。本课仅离线构造数据，无需复制模型调用或创建会话目录。
- 只创建当前阶段、当前任务所需文件；新课由学员实现，脚手架和检查可由导师提供，不预建全部阶段代码。

## 每课自检约定

- 学员最初完整教学要求和每课自检补充均已写入工程 AGENTS.md，作为后续每次辅导先读取的持久约定。
- 每课验收通过的同一轮，自动更新本地 MD、布置下一课并提供其检查脚本，不等待学员再次提醒；只布置当前一个小任务，业务代码仍由学员实现。
- 每节课、每章节布置任务时同步提供工程内检查脚本，覆盖该任务的正常、异常和边界行为；阶段结束提供汇总检查入口，复用已完成章节的检查。
- 提供一条运行命令、明确的通过标准和逐项失败说明；全部通过退出码 0，存在失败为非 0。导师先实际运行脚本，再记录观察结果。
- 默认离线模拟，不读取真实 Key、不自动发起付费请求；需真实验证时单独说明用途与预计调用规模。回答质量、事实来源等人工评估项单列，不能用离线通过替代。
- 只创建当前任务需要的脚本，不预建后续阶段目录或实现。当前入口为 test/check_display.py；后续按课次命名，如 test/check_s2_03.py，阶段汇总如 test/check_stage_2.py。

| 阶段 | 项目产物 | 阶段验收标准 |
| --- | --- | --- |
| 1. Python 与工程基础 | CLI 与必要工程能力 | 解释器、输入输出分离、空白/退出、配置和异常可运行；其他知识按需补充。 |
| 2. 最小模型应用 | 单次问答及少量评估 | 配置、消息、响应解析、超时与调用失败可处理，记录用量并区分模型生成与来源支持。 |
| 3. 多轮对话 | 可恢复的会话 | 追问、流式、保存加载和历史裁剪可运行，能解释上下文限制。 |
| 4. 结构化输出与工具 | 地名或年代工具 | 输出先校验；区分模型请求与实际执行，处理参数和执行失败。 |
| 5. 基于资料的问答 | 有引用的回答 | 简单检索先建基线，按效果再引入切分/向量检索；引用可追溯、地名明确时代，缺资料时说明。 |
| 6. Agent | 有边界的自主循环 | 工具选择、终止条件、步数与成本限制可验证，并与固定流程比较。 |
| 7. 服务与 Android | HTTP 接口及客户端 | 配置、日志、访问控制、成功/失败展示可验证，Key 留在服务端。 |

## 后续小课总览（规划，不代表完成）

2026-10-29 按学员请求展开完整后续路线。现已验收到 S3-05，当前布置 S3-06；本节用于查看路径，不一次性布置全部任务。每课默认 30～60 分钟，一个主要目标，实际可按进度拆分或合并。

### 阶段 3：完成可靠的多轮 CLI

| 课次 | 单一目标 | 产物与验收重点 |
| --- | --- | --- |
| S3-05 | CLI 保存与恢复会话（离线已验收） | 重启后能继续对话，加载/保存失败有明确处理。 |
| S3-06 | 离线拼接流式事件（示范程序及概念小问通过） | 分块正文还原为完整回答，区分正文、结束状态和用量。 |
| S3-07A | 接入 SDK 流式调用（离线验收通过） | 独立函数发送流式请求，复用消费器、转交回调并关闭资源。 |
| S3-07B | 将流式输出接入 CLI（离线已验收） | 边接收边展示，最终保留完整 assistant 与元数据。 |
| S3-08 | 处理流式中断与提交边界（离线已验收） | 中断、截断不提交或保存半轮；成功结果只提交一次。 |
| S3-09 | 多轮会话阶段评估（导师示范报告及离线汇总通过） | 汇总检查覆盖追问、裁剪、恢复、流式及错误；真实效果和用量单列。 |

### 阶段 4：结构化输出与工具调用

| 课次 | 单一目标 | 产物与验收重点 |
| --- | --- | --- |
| S4-01 | 定义结构化回答契约（当前） | 确定答案、不确定性、来源状态等字段及合法示例。 |
| S4-02 | 解析并校验结构化结果 | 缺字段、错误类型和非法 JSON 能被明确拒绝。 |
| S4-03 | 接入模型结构化输出 | 按供应商届时支持的能力调用，结果通过程序校验。 |
| S4-04 | 实现一个确定性工具 | 本地地名条目查询可独立运行，练习资料明确标注来源或模拟状态。 |
| S4-05 | 读取模型提出的工具请求 | 识别工具名称与参数，理解它尚未被程序执行。 |
| S4-06 | 执行工具并回填结果 | 程序完成一次受控调用，模型根据工具结果继续回答。 |
| S4-07 | 处理工具参数与执行失败 | 未知工具、无效参数、无结果或异常得到明确处理。 |
| S4-08 | 固定流程与阶段评估 | 对比直接回答与工具辅助流程，记录正确性、调用次数和用量。 |

### 阶段 5：基于资料的问答与 RAG

| 课次 | 单一目标 | 产物与验收重点 |
| --- | --- | --- |
| S5-01 | 整理小型可追溯资料集 | 保存标题、出处、片段及相关时代背景，避免混淆事实与练习数据。 |
| S5-02 | 建立关键词检索基线 | 给定问题能返回相关片段及来源，无命中时明确返回空结果。 |
| S5-03 | 评估检索效果 | 用固定问题检查命中、误检和漏检，形成改进依据。 |
| S5-04 | 实现文档切分 | 片段保留来源与位置，比较切分前后的检索效果。 |
| S5-05 | 搭建最小 RAG 流程 | 检索资料进入上下文，模型据资料作答，外部文本与程序指令分开。 |
| S5-06 | 展示引用并处理资料不足 | 引用能追溯到实际片段；人工核对结论支持程度，资料不足时明确说明。 |
| S5-07 | 理解嵌入与相似度（按需） | 先用可解释示例理解向量表示与相似度，不把演示当作真实语义质量。 |
| S5-08 | 接入最小向量检索（按需） | 对同一资料和问题与关键词基线比较，确认改进是否值得复杂度。 |
| S5-09 | RAG 阶段对照评估 | 检查检索、引用、拒答、回答质量和成本，选定当前方案。 |

### 阶段 6：受控 Agent

| 课次 | 单一目标 | 产物与验收重点 |
| --- | --- | --- |
| S6-01 | 划清固定流程与 Agent 的边界 | 选出需要自主决策的任务，保留更适合固定流程的场景。 |
| S6-02 | 实现单步工具选择 | 模型选择回答或调用工具，动作交由程序校验。 |
| S6-03 | 实现执行循环与动作记录 | 可完成多步任务，记录动作、结果和错误，便于定位失败步骤。 |
| S6-04 | 加入步数、超时与用量限制 | 预算或次数耗尽时明确停止，避免无限执行。 |
| S6-05 | 识别无进展循环 | 重复工具调用或反复失败时能停止或按约定降级。 |
| S6-06 | 限制工具权限与不可信指令 | 预设诱导用例不能越过程序的工具白名单与参数约束。 |
| S6-07 | 对照评估 Agent | 与固定流程比较成功率、步骤、时延及成本，再决定适用范围。 |

### 阶段 7：HTTP 服务与 Android 接入

| 课次 | 单一目标 | 产物与验收重点 |
| --- | --- | --- |
| S7-01 | 提取可复用的应用服务 | CLI 与后续接口复用问答能力，业务逻辑不依赖终端。 |
| S7-02 | 提供非流式 HTTP 接口 | 明确请求/响应契约，正常请求和非法输入可验证。 |
| S7-03 | 实现服务端会话隔离 | 两个客户端的历史与持久化记录不串联。 |
| S7-04 | 处理并发下的会话一致性 | 按实际需要学习 Python 异步，保证同一会话的请求顺序和状态。 |
| S7-05 | 统一日志与错误协议 | 通过请求标识定位失败，日志不泄露 Key 或原始敏感内容。 |
| S7-06 | 加入基本访问控制 | 服务接口限制访问，模型 Key 留在服务端。 |
| S7-07 | 提供流式 HTTP 接口 | 客户端能接收分块、结束和错误，并处理取消。 |
| S7-08 | Android 非流式接入 | Kotlin 客户端完成提问、会话、加载、错误和来源展示。 |
| S7-09 | Android 流式接入 | 逐步展示回答，处理取消与页面生命周期。 |
| S7-10 | 端到端验收 | 覆盖连续追问、恢复、失败、会话隔离及来源状态。 |
| S7-11 | 项目交付与独立排障 | 按 README 在新环境运行，用评估集和日志复现并定位问题。 |

### 执行方式与持续评估

- 初次展开共 40 个小任务（含当时的 S3-05）；S5-07/S5-08 按关键词基线效果决定，其他分支如混合检索、重排或复杂部署仅在出现明确问题时另行规划。
- 每次只展开当前一课，最多三个新概念；布置时生成该课检查脚本，阶段结束提供汇总入口，不提前创建未来代码目录或全部检查脚本。
- 每课补充正常、异常和边界样例；涉及真实模型输出的质量、事实来源、时延与实际用量单独评估。旧输出不证明新版本效果，模拟用量不作为费用。
- 模型、SDK、结构化输出及流式协议在对应课开始时核对当前官方文档，不在路线中锁定未知接口或版本。需要真实付费调用时，先说明用途和规模。
- 框架在解决明确问题时引入，同类框架只选一个；不安排模型训练或复杂基础设施。Python 知识继续按需穿插，用 Java/Kotlin 类比并说明差异。
- 路线展开本身不新增验收结论；当前实际任务及验证结果见文末 S4-01。



## S2-01：本地功能验收通过

学习者确认 Kimi / kimi-k3 真实运行成功。导师本地验证参数、输入/配置失败、响应展示及安全错误提示。
最新 7 组输出场景全部通过：空回答仍保留统计、结束原因及截断提示，缺少 usage 不崩溃，统计只显示一次。
请求配置已验证：重试 0、120 秒超时、reasoning_effort="low"、max_completion_tokens=4096；鉴权/503/超时只尝试一次。
S2-01 当时未提供真实明细；S2-03 已提交两次带判定说明的运行输出，见评估记录；本地假响应不能替代模型质量评估。

## S2-02：提取可复用的单次调用（离线验收通过）

目标：让模型调用可被 CLI、后续会话与服务复用。学习者将实现放在 model_demo_pro.py，继续在该文件修正，不增加依赖或目录。

- 标准库 dataclass ModelAnswer：content、finish_reason，以及可为 None 的 prompt_tokens、completion_tokens、total_tokens。
- ask_once(question: str) -> ModelAnswer：先校验空白问题，再读取配置、调用一次并解析；无 input/print，异常交给 main 处理，空回答仍返回元数据。
- main 保留交互、ValueError/APIError 提示与已有展示行为；参数沿用当前配置。
- 验收：可导入与构造结果对象，离线假响应验证返回值、缺失统计、零请求输入校验及原错误行为；不以付费重跑替代离线检查。
- Python 新知识限 dataclass、可空类型及调用层职责/异常传播；用 Kotlin data class、Int? 与 try/catch 类比。

2026-10-27 最新复验：test/check_display.py 全部 10/10 通过，包括独立 display 函数、空白正文、缺失/零用量、截断提示及既定调用参数；max_completion_tokens=4096、reasoning_effort="low" 已恢复。
S2-02 离线功能验收通过；没有新增真实调用，不据此判定回答质量或整个阶段完成。

## S2-03：回答规则与最小评估（程序及提示词审阅通过）

目标：为当前问答定义可检查的行为要求，用两条固定问题建立评估记录，预计 30～60 分钟。

- 学员修改 model_demo_pro.py：新增非空字符串 SYSTEM_PROMPT，以及 build_messages(question: str) -> list[dict[str, str]]。先 strip，空白抛 ValueError；无输入输出或模型/配置调用；返回 system=SYSTEM_PROMPT、user=问题两条消息。
- 提示词由学员编写：中文、简洁、地理历史领域；说明不确定性，不编造虚构前提下的真实年份和来源，不声称已检索。系统消息是指令，不保证模型一定遵守。
- ask_once 使用 build_messages 的结果，不改变已验收的模型、预算与展示行为。新知识限消息角色、list/dict 的消息表示、评估样例及人工判定。
- 2026-10-27 源码 b0a3638c 复验 7/7 通过（含上一课 10 项回归）；编辑说明及未填模板已移除，当前四项行为规则和未检索声明人工审阅通过。
- 手动各运行 E01/E02 一次，在 EVAL_CASES.md 填回答摘要、通过/未通过及理由、usage、finish_reason。允许回答未达标，关键是有证据判定；不能把两条样例当作全面可靠性证明。

本节两次真实输出由学员提交，实际输入包含判定说明；导师初评满足实际输入要求，不当作原始问题基线。题目和评分标准已拆分；学员自评仍待补，保留待完成状态。短提示词尚未真实验证，不为补记录追加调用。

## S3-01：离线管理对话历史（功能验收通过）

目标：用程序维护完整的成功问答历史，构造带前文的第二轮请求。先离线练习状态管理，验收后再接真实调用。

只由学员新增 conversation.py，不导入配置、不读取输入、不打印或调用 SDK。实现以下三个函数：

| 函数 | 契约 |
| --- | --- |
| create_history(system_prompt: str) -> list[dict] | 提示词为空白抛 ValueError；返回只含一条 system 消息的新列表，content 保留传入原文；不同会话独立。 |
| build_turn_messages(history: list[dict], question: str) -> list[dict] | 问题先 strip，空白抛 ValueError；返回历史的独立快照加一条 user，不修改 history；嵌套 dict/list 也隔离。 |
| commit_turn(history: list[dict], question: str, assistant_message: dict) -> None | 先校验：strip 后问题非空、role 为 assistant、content 是非空白字符串；无效抛 ValueError 且历史不变。有效时原地追加清理后的 user 和完整 assistant 的独立副本，返回 None；assistant 正文原文及所有额外字段原样保留。 |

本课仅处理普通文本完整回答，不处理工具消息；调用失败时不执行 commit_turn。准备请求不等于提交历史，未来调用层确认成功后再提交。本课不接 CLI、SDK、会话文件、流式或裁剪。
Python 按需知识：无状态 API 与显式上下文、可变容器引用及 copy.deepcopy、准备/提交两个步骤。list(history) 与 Kotlin toMutableList() 一样只复制外层，内部可变对象仍可能共享。

2026-10-27 导师复验 conversation.py（ca747593）：test/check_s3_01.py 9/9，退出码 0，覆盖初始化、首轮、空白边界、完整提交、追问、嵌套隔离、失败不污染、会话隔离与回归。完整字段保留及先校验后追加经人工代码审阅确认。离线演示只验证历史数据，不证明真实模型理解了追问。
学员将准备/提交分离的目的解释为“上下文过长”；本轮澄清主要目的为失败时的状态一致性、避免半轮记录和重试重复。成功轮次仍增长，长度限制需另做裁剪；待下一课失败分支验证理解，不因讲解标掌握。

官方已复核：[Kimi 多轮与无状态](https://platform.kimi.com/docs/guide/engage-in-multi-turn-conversations-using-kimi-api)、[K3 完整 assistant 回传](https://platform.kimi.com/docs/guide/kimi-k3-quickstart)。K3 不能只用回答正文重建历史，须保留如 reasoning_content 等协议字段。本课用假字典检验保留能力；不实现 SDK 转换或调用，不切换模型。

## S3-02：接入多轮调用（离线验收通过）

一个目标：将已验证的历史管理用于真实 CLI 调用，成功提交、失败不污染上下文。学员只改 model_demo_pro.py，复用 conversation.py，不加依赖。ModelAnswer 新字段为 `assistant_message: dict | None = None`。

| 修改点 | 契约 |
| --- | --- |
| ModelAnswer | 新增上述可空字段，默认 None，放在原三个 token 字段之后；保留旧五参数构造及所有字段。 |
| ask_messages(messages: list[dict]) -> ModelAnswer | 移入既有客户端创建、请求及解析，发送传入消息，不打印/读取输入或修改调用方消息；保留模型/超时/预算。用 choice.message.to_dict() 保存完整 assistant，正文和元数据继续单独供 display 使用，异常传播。 |
| ask_once(question: str) -> ModelAnswer | 保留单轮接口；先清理/校验，再 build_messages，最后复用 ask_messages；空白在读配置/建客户端前抛 ValueError。 |
| ask_turn(history: list[dict], question: str) -> ModelAnswer | build_turn_messages 准备请求，调用 ask_messages。只有 finish_reason == stop 且正文非空白时，commit_turn 提交完整 assistant；其余结果原样返回供展示，历史不变；配置/SDK 异常传播，不提交或重试。 |
| main | 循环外 create_history(SYSTEM_PROMPT) 一次，循环内用 ask_turn(history, question)；保留空白/退出、错误类别、来源标签、用量及截断展示。 |

三个按需知识：共用请求函数与业务包装；SDK 对象 to_dict() 保留协议数据；会话状态跨循环复用及成功条件。SDK 最小示例只有 assistant_message = choice.message.to_dict()；不提供整段实现。
2026-10-28 源码 18071ef4 原检查 12/12，但人工发现新增字段插入中间会使旧位置参数错绑；原要求保留旧构造，脚本此前漏检这一条件。已在现有兼容项补断言，仍 12 项，实测 11/12。其他项通过：真实 SDK 序列化、两轮上下文、空白/缺配置零请求、401/503/超时不提交且不重试、空回答/截断返回统计、CLI 继续处理和旧回归。
2026-10-28 最终复验源码 864e6779：学员已将 assistant_message 移到原三个 token 字段之后；test/check_s3_02.py 12/12、退出码 0，旧五参数兼容与全部回归通过。S3-02 离线功能验收完成；真实 E12/E13 结果尚未提供，已运行则补现有输出。
原检查脚本仅适配新流程：假消息改为实际 SDK 消息类型，展示假调用入口随 main 使用 ask_turn，原断言保留；CLI 多轮接线由新脚本验证。后续不为凑通过弱化检查。
原真实验证计划：由学员在同一进程运行 E12/E13，各一次、最多 2 次真实请求，目的为核对前文记忆；已有结果只补录，无需重跑；回答摘要、人工判断/理由、usage、finish_reason 记入 EVAL_CASES.md。失败如实记录，不为通过追加调用；无 Key 则真实项待验证，导师不执行付费请求。离线通过与真实效果分别记录，验收通过后自动布置下一课。

2026-10-27 已核对 [Kimi K3](https://platform.kimi.com/docs/guide/kimi-k3-quickstart) 和 [OpenAI Docs：SDK 字典转换](https://developers.openai.com/api/reference/python)，本地 3.37.0 假消息验证 to_dict() 保留 reasoning_content。只保留完整字段用于回传，display 不输出原始对象或该协议字段。

## S3-03：按完整问答轮次裁剪请求（离线验收通过）

目标：让每次请求只携带最近 N 轮，同时保留完整已提交历史，预计 30～60 分钟；本课真实调用 0 次，不增加依赖。

学员只改两处：

1. conversation.py：扩展为 `build_turn_messages(history: list[dict], question: str, max_rounds: int | None = None) -> list[dict]`，保留旧两参数调用。
2. model_demo_ask_turn.py（学员从 model_demo_pro.py 改名）：定义 `MAX_HISTORY_ROUNDS = 2`，在 ask_turn 组装请求时显式传入 `max_rounds=MAX_HISTORY_ROUNDS`，其余调用/提交/展示行为保持。

| 输入/行为 | 验收契约 |
| --- | --- |
| None（默认） | 保留全部已提交历史，与原行为兼容。 |
| 0 | 只发送 system＋当前 user；不能用负零切片误保留全部历史。 |
| 正整数 N | 仅选最近 N 轮已完成 user/assistant，保持时间顺序；不足 N 轮保留现有轮次。当前新问题不计入 N。 |
| 负整数 | 抛 ValueError，历史不变。本课参数类型约定为 int 或 None，不另考查非整数输入。 |
| 消息完整性 | system 原文只出现一次；保留完整 assistant 及协议字段，不只拼正文。问题 strip，空白仍抛 ValueError。 |
| 数据隔离 | 返回嵌套数据独立的快照；准备请求不改变已提交历史。成功仍只向完整历史追加当前问答；失败/空答/截断不提交。 |

本课历史由 create_history/commit_turn 产生，格式固定为一条 system＋完整文本问答对；暂不新增损坏历史修复或工具消息逻辑。四轮已完成历史限两轮，发送顺序：system → user3 → assistant3 → user4 → assistant4 → 当前 user。
默认两轮窗口下，连续五次成功请求的消息条数为 2、4、6、6、6；第五次成功后的完整历史共 11 条。只限制请求窗口，不限制本地内存增长；单条消息很长时仍可能超 token 限制。旧信息未发送时，模型也无法凭本地完整历史自动获知。

按需新知识限三个：完整轮次窗口、Python 切片、轮数与 token 预算的区别。最小语法示例：`items = [10, 20, 30, 40]`，`items[-2:]` 得到 `[30, 40]`；`items[:1]` 得到 `[10]`。切片是新外层列表，嵌套隔离仍需沿用 deepcopy。类似 Kotlin takeLast，但 Python 的 `items[-0:]` 返回全部，不能代表保留零项。

检查：`.venv/bin/python test/check_s3_03.py`，目标 12/12、退出码 0。覆盖 None/0/不足/超限/负数/空白、深拷贝、完整协议字段、ask_turn 参数接线、五轮 SDK 序列化、失败状态、CLI 及 S3-02 回归。2026-10-28 布置时实跑 2/12，退出码 1：新接口尚未实现；旧行为及旧回归通过。检查使用假响应且隔离真实配置/网络；不是模型质量评估。
提交本课检查输出，并用一句话解释为什么本地有旧信息、裁剪后模型却可能答不出旧信息。通过后同轮安排下一课；后续小任务为会话保存/恢复，再学习流式输出，不在本课预建代码。

2026-10-28 验收：当前入口已改名为 model_demo_ask_turn.py，SYSTEM_PROMPT 移至 conversation.py。导师恢复被注释的旧回归后，test/check_s3_03.py 实际 12/12、退出码 0；当前源码 44382524/f894dec2，最新版本在 S3-04 基线中再次通过回归。学员正确解释超窗信息未发送，基础概念提问通过，不据此标全面掌握。

2026-10-28 官方复核：[Python 3.11 序列切片](https://docs.python.org/3.11/library/stdtypes.html#common-sequence-operations)、[Kimi 无状态多轮](https://platform.kimi.com/docs/guide/engage-in-multi-turn-conversations-using-kimi-api)、[K3 完整消息回传](https://platform.kimi.com/docs/guide/kimi-k3-quickstart)。本课沿用 kimi-k3 和已有 SDK/预算。

## S3-04：独立保存与加载完整会话（离线验收通过）

2026-10-29 最新源码 session_store.py 98aa44a8、conversation.py 2a66f1ee：test/check_s3_04.py 12/12、退出码 0，含全部旧回归。保存前校验、完整 JSON/中文/协议字段、缺文件及坏数据、独立进程恢复已验证。此前 11/12 的唯一问题是 commit_turn 混入固定路径写盘，学员已移除并清理导入；历史修正过程见 PROGRESS.md 和 EVAL_CASES.md。
存储函数保持独立，不读取配置或调用模型。完整存档与请求窗口的解释由导师提供，理解仍需后续迁移检验；先校验/序列化不等于任意 I/O 失败时文件都完整，不要求本阶段增加原子写入。

## S3-05：CLI 保存与恢复会话（离线验收通过，保留修正过程）

一个目标：让真实 CLI 在重启后继续同一会话，预计 30～60 分钟。学员只修改 model_demo_ask_turn.py、.gitignore；不改 conversation.py 或 session_store.py，不引入依赖。本课所有验收离线，真实请求 0 次。

1. 从 pathlib 导入 Path，从 session_store 导入 load_history、save_history。定义 `SESSION_PATH = Path(__file__).resolve().parent / "data" / "session.json"`，不依赖进程启动目录。
2. 扩展为 `main(session_path: Path | None = None) -> None`：None 时完全保留旧无持久化行为，供旧调用复用；在脚本入口改用 `main(SESSION_PATH)`。新增会话路径 `/data/session.json` 加入 .gitignore，不操作已有暂存文件或旧缓存。
3. 按下表接线；路径、加载、保存和错误提示均由 main 安排，ask_turn/commit_turn 保持原职责与请求预算。

| 时机/结果 | 行为 |
| --- | --- |
| 启动且路径非 None | 在第一次 input 前加载一次；保留文件中原 system，不在循环内反复加载。 |
| FileNotFoundError | 仅新建内存历史，不提前建目录或写文件。 |
| 坏 JSON/结构的 ValueError，或其他 OSError | 提示“加载失败＋异常类别”，返回；不进入交互、不覆盖文件，不把它们当作缺文件。 |
| 成功返回 stop 且正文非空白 | 保留 display；父目录 mkdir(parents=True, exist_ok=True)，保存完整已提交历史。 |
| 空白/退出、API 错误、空答、截断及其他未提交状态 | 不保存、不自动重试模型；已有错误与结果展示保持。 |
| 创建父目录/保存发生 OSError | 已生成回答仍展示，提示“保存失败＋异常类别＋本轮回答仍在内存”，继续交互；不回滚已成功的内存问答，不重新调用模型。后续成功保存完整历史，包含前次未落盘问答。 |

错误提示不输出原始异常全文、Key、完整会话或协议字段。FileNotFoundError 属于 OSError，先处理缺文件分支；JSONDecodeError 属于 ValueError。mkdir 与 save 放进保存错误处理范围。暂不增加 EOF/键盘中断、会话管理命令或磁盘原子写入；不要声称任意保存失败都保留旧文件。

三个按需概念：入口与路径注入（类似给 Android 对象传入文件位置，main(None) 保留旧行为）；异常分类与捕获顺序（类似先捕具体异常再捕基类）；内存成功与落盘成功分开（生成回答已成功，保存失败不能重发模型请求）。最小路径示例就是上面的 SESSION_PATH；业务接线由学员实现。

验收：`.venv/bin/python test/check_s3_05.py`，目标 12/12、退出码 0。检查缺文件/坏文件/读取权限、成功保存与新目录、四轮恢复后请求 6 条并保存 11 条、失败不保存、保存/目录错误后继续、实际脚本入口和 S3-04 全回归；文件都在临时目录，入口检查只模拟加载并 quit。
2026-10-29 布置时实跑 2/12、退出码 1，旧行为及旧回归通过，新接线待实现；不得标完成。提交输出，并解释为什么保存失败后不应再调用一次模型。通过后同轮安排流式输出任务，不预建后续代码。

2026-10-29 本轮审阅：入口源码 85f35d9e，原检查 12/12；实际接线与失败后内存保留正确。唯一问题为保存 OSError 提示“本地内存保存失败”，与代码已提交内存的状态相反。导师原检查只找“内存”二字，现补强现有保存/建目录错误两项，实际 10/12、退出码 1，总数仍 12，其余及旧回归通过。
当前只改该提示，明确失败的是文件操作、回答仍在内存；推荐“文件保存失败（异常类别），本轮回答仍在内存中”。仅临时副本改文案后 12/12；导师未修改学员实现，不标整课验收完成。已核对后续流式官方资料、只读现有示例，未执行示例或布置新课；修复通过后再进入 S3-06。

官方复核：[Python Path 与 mkdir](https://docs.python.org/3.11/library/pathlib.html#pathlib.Path.mkdir)、[异常继承](https://docs.python.org/3.11/library/exceptions.html#FileNotFoundError)。本课沿用现有模型和 SDK，不更改接口。

## 验收与费用边界

导师所有自动检查默认离线。S3-01 真实请求数为 0；S3-02 独立计划最多 2 次学员手动请求，结果尚未提供，不推断是否已运行、不复用旧额度；S3-03～S3-05 全离线，不安排新增真实请求。每次继续 max_completion_tokens=4096、reasoning_effort=low、max_retries=0、timeout=120。S2-03 旧额度已用，不重跑。费用按实际供应商价格及 usage，不虚构金额。
实际 token 已记录，货币费用未提供，不用 token 数量占比推算费用占比。变更后的提示词、原始问题基线仍需后续另行计划真实验证，不能复用旧结果标通过。
dotenv 会在导入时加载 .env，离线验收隔离该加载，不读取或传输真实 Key；仅 unset 一个变量不足以保证“配置缺失”。

官方依据：[Kimi K3：推理与生成上限](https://platform.kimi.com/docs/guide/kimi-k3-quickstart)、[模型参数差异](https://platform.kimi.com/docs/api/models-overview)、[Kimi 计费说明](https://platform.kimi.com/docs/pricing/chat)、[SDK 重试与异常](https://developers.openai.com/api/reference/python)。

2026-10-29 最终复验：学员已将提示改为“保存失败，本轮回答仍在内存＋异常类别”；入口源码 079924f0，`test/check_s3_05.py` **12/12、退出码 0**，含此前回归。S3-05 离线验收完成；未新增真实调用，不将提示修正或导师讲解标为全面掌握。

## S3-06：离线拼接流式事件（示范程序及当前概念小问通过）

一个目标：将单个回答的 SDK 增量分片折叠为 ModelAnswer，并在正文到达时通知调用者，预计 30～60 分钟。只由学员在 model_demo_ask_turn.py 新增函数；不增加依赖，不修改既有非流式入口。模型、请求预算保持不变，本课真实调用 0 次。

建议类型签名（只提供接口，由学员实现函数体）：

```python
from collections.abc import Callable, Iterable
from openai.types.chat import ChatCompletionChunk

def consume_stream(
    chunks: Iterable[ChatCompletionChunk],
    on_text: Callable[[str], None] | None = None,
) -> ModelAnswer:
    ...
```

| 输入/行为 | 本课验收契约 |
| --- | --- |
| chunks | SDK ChatCompletionChunk 的可迭代对象，可能只能遍历一次；本课 n=1，只处理 choices[0] 对应的文本回答。不得改写输入分片。 |
| 正文 | 将 delta.content 中非 None、非空字符串按顺序追加，原样保留空格/换行/中文；不能 strip 每个片段。片段不保证恰好一个字或一个 token。 |
| on_text | 默认为 None；提供时，每收到一个非空正文片段立即调用一次 on_text(原片段)，再读下一片。空白片段仍是正文。回调可为 list.append；消费函数不直接 print/input。不能先 list(chunks) 再通知。 |
| 空内容 | role-only、content=None/"" 不回调。choices=[] 时不能取下标，但仍先处理该分片顶层 usage。 |
| 结束原因 | 保留最后非 None 的 choice.finish_reason；没有则 ""。收到 stop/length 等也继续消费直到迭代器结束，不能提前 break 或 return，后面可能还有用量。 |
| 用量 | 采用最后非 None 的 chunk.usage；三个 token 字段缺失时为 None，提供 0 保留 0。只要求官方推荐的最终顶层用量路径；本课不要求 choice 内兼容字段或自行计算 token。 |
| 协议消息 | assistant_message 至少为 {"role": "assistant", "content": 完整正文}。如果分片含 reasoning_content，将其单独按序追加到该字段；不拼入 content，也不通过 on_text 输出。用 getattr(delta, "reasoning_content", None) 安全读取 SDK 未声明的扩展字段。本课只支持文本及这一扩展，不声称还原工具/音频等所有协议字段。 |
| 空流/无结束标记 | 返回空正文、空结束原因、None 用量及 content="" 的 assistant 字典；有正文但无结束标记仍保留正文，finish_reason=""，不能擅自当作 stop。 |
| 失败 | 迭代器或回调抛异常时原样传播，不重试、不返回成功的部分答案。已通知部分正文也不等于整轮成功。 |
| 职责 | 只消费传入分片、构造结果及调用回调；不创建客户端、不读配置、不调用模型、不提交历史、不读写会话文件。真实 SDK 流资源管理、CLI 接入和中断提交策略留 S3-07/S3-08。 |

最多三个新概念：①可迭代对象/单次消费，类似 Kotlin Iterator/Sequence，普通 for 即可，不需要异步；②回调，Callable[[str], None] 类似 Kotlin (String) -> Unit，Python 函数可作为参数，None 表示未提供；③增量正文与最终元数据分开，边展示不等于整轮已成功。最小语法示例：`pieces = []; notify = pieces.append; notify("南"); notify("京"); "".join(pieces)` 得到“南京”，不提供消费函数完整实现。

检查：`.venv/bin/python test/check_s3_06.py`，目标 **12/12、退出码 0**。覆盖原文、单次迭代与即时回调、空分片、结束后的用量、None/0、结束标记、reasoning_content、异常及 S3-05 全回归。2026-10-29 布置实跑 **1/12、退出码 1**，只有旧回归通过，新函数尚未实现。检查器临时正向控制 12/12；预置提前 break 仅 8/12，先 list 消费仅 9/12，说明这两个边界能检出；控制副本不是学员成果。

提交本课检查输出，并用一句话解释“为什么读到 finish_reason 后还要继续读取分片”。通过后同轮布置 S3-07，接 SDK 流式输出与 CLI。本课没有真实流式效果或费用结论；消费器的 finish_reason 也不是对真实传输完整性的证明，SSE 结束标记/中断需在真实传输层另行处理。

2026-10-29 已复核 [OpenAI ChatCompletionChunk 字段](https://developers.openai.com/api/reference/resources/chat/subresources/completions/streaming-events)及 [Kimi 流式输出](https://platform.kimi.com/docs/guide/utilize-the-streaming-output-feature-of-kimi-api)。Kimi 文档示例的模型不用于自动替换本工程 kimi-k3；现有 kimi_stream_demo.py 仅作只读参考，含顶层真实请求，本课不导入或执行。

2026-10-29 S3-06 草稿复验（d8481a60）：实际 0/12、退出码 1，多项被同一直接输出断言拦截；独立内存诊断确认回调未执行、缺失 usage/空流属性访问失败、无结束标记返回 None。正常分片下正文和 reasoning_content 分开拼接正确；ask_messages 提前切换流式使旧回归失败，display 的 ModelAnswer 参数也不符合正文回调 str 契约。仅给修正提示，不改业务实现、不弱化检查、不推进课程；当前目标仍 12/12，先恢复本课约定的非流式接线。

### 2026-10-30：按学员请求示范实现，当前只做理解巩固

- 学员明确表示仍困惑并请求导师实现；导师保留已有正文／协议字段收集思路，补齐即时回调、空结束原因及显式 None 用量处理，移除工具占位／打印，恢复 ask_messages 的非流式接线。源码 0dc4db43，test/check_s3_06.py **12/12、退出码 0**，含此前回归；程序已验证，不标学员独立掌握。
- 同一脚本新增 `--demo`，只展示既有消费函数的离线行为，不修改原 12 项断言。实际输出顺序：调用前 → 回调“第一片” → 回调“第二片” → 拿到完整 ModelAnswer → 正文“第一片第二片”；用量是假值。真实请求 0 次。
- 当前一个 5 分钟修改实验：先运行 --demo，把 `if on_text is not None:` 暂改为 `if False:`，再运行观察回调消失、完整正文仍返回；恢复条件后完整检查应回到 12/12。提交两次演示差异及“为什么 append 不能代替通知”的解释。仍用本课检查脚本，不预建下一课代码。
- 函数体的两个出口含义：on_text(fragment) 在循环中多次通知，return ModelAnswer(...) 在循环结束后一次返回；类似 Kotlin 的回调参数与普通返回值。理解迁移验收后，在同一轮自动布置 S3-07 及其检查，不要求再次提醒。
- 本次已核对 OpenAI 官方流式字段；模型及预算保持原约定，不执行有真实顶层请求的示例或读取 Key。真实流式、SSE 完整性与 CLI 接入不在本次示范验证范围。


2026-10-30 理解练习复验：学员说明“禁用回调后，完整正文仍组装在结果对象中”，当前概念小问通过。入口另有流式展示试验（629ca7a5），本课原样复验 11/12；消费函数 11 项均通过，旧回归失败。导师按先前代写授权保存试验备份并恢复非流式入口，0dc4db43 重新 12/12。程序来源仍为导师示范，不标学员独立编写或全面掌握。试验临时备份：/var/folders/q_/vbq0l8216zn7rqr9ql0nxh540000gn/T/geo-history-s307-mwz0y31j/stream-experiment-backup.py。

## S3-07A：独立接入 SDK 流式调用（离线验收通过）

一个目标：把已验证的消费函数接到 SDK 返回的 Stream，预计 30～60 分钟。鉴于上课接线与回调混淆，将原 S3-07 拆为 A（SDK）、B（CLI），只布置 A；原总览 40 课为历史规划，本次拆分后约 41 个小任务，仍可按实际进度调整。不预建 B 或后续代码。

只由学员在 model_demo_ask_turn.py 新增以下函数，不改既有非流式调用、CLI、历史和存储；不新增依赖：

```python
def ask_stream_messages(
    messages: list[dict],
    on_text: Callable[[str], None] | None = None,
) -> ModelAnswer:
    ...
```

| 范围 | 本课验收契约 |
| --- | --- |
| 客户端 | 复用 get_api_key("kimi")、get_base_url("kimi")；timeout=120、max_retries=0。缺配置传播 ValueError，创建客户端前停止。 |
| 请求 | 原样发送 messages，不修改输入。model="kimi-k3"，stream=True，stream_options={"include_usage": True}，max_completion_tokens=4096，reasoning_effort="low"，请求有效 timeout=120 秒。一次调用仅请求一次，不带旧 max_tokens。 |
| 消费与结果 | 调用 consume_stream(stream, on_text) 一次，传入实际 SDK Stream 和原回调，不先 list、不自行重写拼接逻辑；直接返回它产生的同一 ModelAnswer。on_text=None 也可正常返回。 |
| 职责 | 无 input/print/display；不提交历史、不读写会话、不调用其他模型接口。回调来自调用者，不在函数内写死展示方式。 |
| 生命周期 | 在函数返回或消费／回调异常传播之前，关闭流响应及客户端；推荐外层 with OpenAI(...) as client、内层 with client.chat.completions.create(...) as stream。也可用等效的 finally 清理，不要求重写 SDK 资源类型。 |
| 失败 | 原配置／SDK／消费／回调异常向上传播，不吞错、自动重试或伪造成功；只验证基础错误路径，真实断流的提交／落盘策略留 S3-08。 |
| 保留行为 | ask_messages、ask_turn、main 仍走旧非流式行为，consume_stream 与旧检查保持；本课不接 CLI 或新增会话模式参数。 |

三个按需概念：①SDK Stream 与一次性完整响应不同，create 返回可迭代流，再交给消费器；②回调透传，调用层转交调用者的函数，不把片段回调与最终 display 混用；③with 管理资源，类似 Kotlin use／Java try-with-resources，块内 return 或抛异常也会执行退出清理。Python 需对象实现上下文管理协议，不是任意对象都能放入 with。

最小语法示例：`with open("README.md", encoding="utf-8") as file:` 后缩进读取；离开块后文件关闭，读取到的字符串仍可使用。SDK 的客户端／流同样支持 with；无需自行编写 __enter__/__exit__。业务函数仍由学员实现。

检查：`.venv/bin/python test/check_s3_07a.py`，目标 **12/12、退出码 0**。2026-10-30 布置时实际 **1/12、退出码 1**：新函数未实现，S3-06 及此前回归通过。测试用真实已安装 SDK 解析内存 SSE 假响应，隔离真实环境和 dotenv、阻断网络；模型真实请求数 0。临时正向控制 12/12，丢弃回调及遗漏资源清理各为 8/12；这些是检查器验证，不是学员完成证明。

提交本课检查输出，并解释“为什么回调应该由调用方传入，而不是在 ask_stream_messages 里写死 print”。通过后同轮布置 S3-07B CLI 接入并提供对应检查。SSE 真正传输完成、真实回答效果／费用并未由本课证明，不执行带顶层请求的参考示例。

2026-10-30 已实际获取并复核：[OpenAI stream/include_usage 参数](https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create)、[Kimi 流式输出](https://platform.kimi.com/docs/guide/utilize-the-streaming-output-feature-of-kimi-api)、[Python with 语义](https://docs.python.org/3.11/reference/compound_stmts.html#the-with-statement)。随后核对本地 SDK Stream／客户端的上下文管理与 close 实现；沿用当前模型、SDK 和预算，不迁移模型。


2026-10-30 S3-07A 验收：学员实现 ask_stream_messages，入口 816aaa3f；test/check_s3_07a.py **12/12、退出码 0**，含此前回归。独立源码审阅未发现新增实质问题；第 102 行的第二个 return 不可达，是非阻断清理。学员回答体现职责分离，但“展示不应在 ask 中运行”需澄清为：展示方式由调用者提供，回调仍在消费时同步执行，不是等 ask 返回或自动切线程。该执行时机由导师补充，不据讲解标掌握。

## S3-07B：将流式输出接入 CLI（最终离线12/12）

一个目标：终端边收到边显示正文，并在最后展示一份完整元数据，预计 30～60 分钟。只由学员修改 model_demo_ask_turn.py；复用已验收的 SDK 流式函数、消费器、历史与存储，不增加依赖。

建议扩展接口，保留旧调用与默认值：

```python
def ask_turn(history: list[dict], question: str, *, stream: bool = False,
             on_text: Callable[[str], None] | None = None) -> ModelAnswer:
    ...

def display(answer: ModelAnswer, *, streamed: bool = False) -> None:
    ...

def main(session_path: Path | None = None, *, stream: bool = False) -> None:
    ...
```

| 修改点 | 本课验收契约 |
| --- | --- |
| ask_turn | 沿用清理问题／两轮窗口；stream=False 走原 ask_messages，且不调用 on_text；True 走 ask_stream_messages，将回调透传。两种方式均仅在 stop 且正文非空白时提交一次完整 assistant，其他返回或异常不提交；不展示、不存储。 |
| main 默认 | main()／main(path) 保留原非流式行为；只在传 stream=True 时启用新展示。启动加载、空白／退出及原异常处理保持；加载失败、空白与退出不打印模型来源标签或请求。 |
| 流式正文 | 每次有效问题请求前打印一次“模型生成｜未检索来源”；CLI 提供正文回调，等效于 print(fragment, end="", flush=True)。原片段立即显示，不加前缀、换行或 strip；不显示 reasoning_content。 |
| 换行与最终展示 | 流式调用结束时补一个换行，异常时也执行，推荐 try/finally；随后 display(answer, streamed=True)。回调仍在 ask 尚未返回时同步执行。 |
| display | 默认完全保留旧展示；streamed=True 不打印来源标签或完整正文，只输出原元数据、空答提示和 length 截断提示。统计和结束原因只显示一次，None/0 区分不变。 |
| 历史／持久化 | 沿用已提交才保存；恢复四轮仍请求 6 条、成功后完整保存 11 条。空答／截断／消费错误不提交或保存半轮；保存失败仍显示回答并保留内存，下次保存补齐，不重调上一轮模型。 |
| 入口 | 脚本入口改为 main(SESSION_PATH, stream=True)，既有默认 main() 兼容逻辑不改。ask_stream_messages、consume_stream、conversation.py、session_store.py 保持已验收功能；可顺手删除不可达 return。 |

最多三个按需概念：①默认值与命名模式参数，Python 的 * 后参数需按名称传递，便于保留旧默认；②print 的 end="" 和 flush=True，避免每片换行及输出缓冲造成延迟；③try/finally 将补换行安排到正常／异常都执行的路径，类似 Kotlin try/finally，不应在 finally 返回而吞掉异常。最小展示示例只有 print("一片正文", end="", flush=True)，实际接线由学员完成。

检查：`.venv/bin/python test/check_s3_07b.py`，目标 **12/12、退出码 0**。布置基线 **1/12、退出码 1**，当前新接口未实现，S3-07A 及此前回归通过。使用真实 SDK 解析内存 SSE、临时会话和网络阻断；不加载 .env／真实 Key、不发送模型网络请求。临时正确接线控制 12/12，去掉 flush 或重复打印全文各 11/12，仅用于验证检查器，不计为学员完成。

提交检查输出，并解释“为什么片段已经显示，最后仍需保留完整 ModelAnswer”。通过后同轮进入 S3-08，讨论更完整的流式中断／提交边界。本课仅保持已有基本成功条件，不证明真实 SSE 结束标记、真实质量或费用；本课真实调用 0 次。

官方复核：[Python print/end/flush](https://docs.python.org/3.11/library/functions.html#print)、[try/finally](https://docs.python.org/3.11/reference/compound_stmts.html#finally-clause)、[SDK 流式字段](https://developers.openai.com/api/reference/resources/chat/subresources/completions/streaming-events)。不改变模型、SDK 或既定调用预算。


2026-10-30 S3-07B 本轮审阅：入口7ff22bd1，原检查12/12；人工复现正文在缺少usage时粘连“未提供用量统计”，空回答没有来源标签。两点均属于原契约：标签须在有效流式请求前、流式调用结束须补换行。原检查只在首片回调后看标签且只用有统计的正文检验换行，导师承认漏检，已在现有两项补强，仍12项；实际 **10/12、退出码1**，其余接线、历史与存储回归通过。

当次布置的10～20分钟修正任务：将标签从首片回调移到有效流式请求前；回调只原样打印片段；在调用外用try/finally统一补换行，并移除display的用量字符串前导换行。这样空回答／缺统计也得到一致收尾。不要求改SDK、窗口或持久化；原目标仍12/12。临时副本只修这两处后12/12，是诊断控制，不标学员工程修复；本轮没有修改学员业务文件或推进S3-08。

学员解释完整ModelAnswer用于用量和结束原因，这部分正确；导师补充完整assistant_message用于成功后的历史提交／文件保存，不能以已显示的片段代替完整结果。补充内容仍待学员迁移检验，不据讲解标掌握。当前自检命令不变，修正通过后再自动进入S3-08。


2026-10-30 最终复验：本轮初读版本053e5b36的换行已正确，来源仍绑首片；准备修改期间文件又保存为030f874e，标签也已移至请求前。导师未覆盖这次保存，也未向业务文件写入实现。以当前保存版本实际运行 test/check_s3_07b.py **12/12、退出码0**，含此前回归，S3-07B离线功能验收通过。来源声明不依赖正文、统一换行不依赖usage；无法仅凭这次文件保存判定学员是否独立完成或掌握，不作此归因。没有新增真实调用。

## S3-08：中断时不提交半轮历史（离线已验收）

主要目标：片段已经展示时，仍根据完整调用结果决定是否提交历史，预计30～60分钟。只由学员修改 model_demo_ask_turn.py，不新增依赖；保持 consume_stream、ask_stream_messages、conversation.py、session_store.py及旧默认行为。

为什么现在学：CLI已能实时显示正文，但“看见一些文字”不能证明这一轮能进入后续上下文。现有代码已让API异常向外传播、不提交；本课补齐缺结束原因的明确反馈和请求／消费时的用户取消。

最多三个按需概念：

1. 项目自定义异常：IncompleteStreamError继承Exception，表示应用完成条件未满足；类似Kotlin自定义Exception，Python没有Java那样的受检异常声明要求。
2. KeyboardInterrupt：Ctrl-C通常触发它；它继承BaseException，except Exception捕获不到。在CLI边界显式捕获并退出，不用裸except吞掉所有错误。
3. 提交边界：回调展示属于暂态；调用结束、校验满足条件后，才提交完整问答，再由CLI保存。可类比Android先展示临时UI，成功后再更新持久状态；本项目并没有数据库事务或任意中断点的原子保证。

动手契约：

| 修改点 | 要求 |
| --- | --- |
| 自定义异常 | 新增IncompleteStreamError(Exception)，区分流式结果不完整与配置／API错误。 |
| ask_turn | 仅stream=True且返回结果finish_reason==""时，在提交之前抛上述异常。即使正文非空也不能正常返回；不要把usage缺失当中断。其余原状态／提交条件保持；不打印、不保存。 |
| main未完成分支 | 捕获IncompleteStreamError，输出固定“流式回答未完成，本轮未加入历史”，继续下一次input；沿用finally补换行，不显示成功元数据，不保存半轮。 |
| main取消分支 | 请求创建／分片消费期间KeyboardInterrupt，输出固定“已取消，退出程序”，随后return；资源仍由既有with关闭，finally仍补换行，不重试或继续提问。 |
| 原行为 | stop且正文非空白、调用未抛错时只提交一次完整assistant；缺usage仍允许按此策略接受，0保留。length／其他非空原因／空白正文沿用不提交；API错误及回调错误继续传播到适当边界，不伪造成功。 |

提示：低层consume_stream仍如实返回finish_reason=""，是否接受结果放在ask_turn；这样消费、业务判断、CLI反馈各有职责。先增加异常类型，再在流式结果返回后、commit_turn前检查；最后为main补两个明确的except分支。不要在finally里return，否则可能吞掉异常。可参照已有APIError捕获结构，先自行实现。

运行：`.venv/bin/python test/check_s3_08.py`，目标 **12/12、退出码0**。2026-10-30布置时导师实际基线 **8/12、退出码1**（入口030f874e）：新异常、无结束原因拒绝、CLI未完成反馈和Ctrl-C退出四项待实现，旧B及此前回归通过。检查只用假分片、真实SDK的内存HTTP与临时会话，禁用dotenv、清空环境并阻断网络；所有usage为假值，不要求真实调用。

检查器在临时控制实现中12/12；移除缺失结束原因校验的控制实现10/12，用于证明检查能发现该缺口，不计为学员成果。补强请求创建时取消后，正向仍12/12；只在consumer处理取消的错误控制11/12，检出请求阶段漏捕获。只新增本课检查，不将控制业务实现复制进工程。

边界：本课拒绝缺finish_reason的结果，但SDK对外迭代的分片没有暴露原始[DONE]；stop＋非空正文＋正常消费只是当前应用可观察的接受策略，不能据此证明传输完整，也不用usage充当完成标记。本课取消保证限请求／消费期间的可控用例，不涵盖等待输入、提交或文件保存任意指令位置的原子安全，不新增SSE解析器或存储基础设施。

完成后提交本课检查输出，并回答：“第一片正文已经显示，随后网络报错，为什么这一轮仍不能加入历史？”通过后同轮安排S3-09阶段评估并提供对应检查；当前尚未布置或实现该课。

2026-10-30官方核对：[Python异常与KeyboardInterrupt](https://docs.python.org/3.11/library/exceptions.html#KeyboardInterrupt)、[try/finally](https://docs.python.org/3.11/reference/compound_stmts.html#finally-clause)、[Kimi流式输出与原始DONE](https://platform.kimi.com/docs/guide/utilize-the-streaming-output-feature-of-kimi-api)、[include_usage边界](https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create)。本课不切换模型、SDK或请求预算。


2026-10-30：学员提交入口bd824623，新增IncompleteStreamError.py并在流式分支拒绝缺失结束原因；CLI分别处理未完成后继续和Ctrl-C退出。导师实际运行test/check_s3_08.py **12/12、退出码0**，包含此前整链回归。独立异常模块已补入临时回归副本的复制清单，相关原断言保持；本轮导师未代写业务代码。离线功能验收通过，不据此标学员全面掌握或真实流式／模型质量已验证。无新增真实模型请求或费用。

## S3-09：阶段评估（导师示范及离线汇总通过）

目标：把已通过的程序检查与尚未验证的真实模型效果分开，形成可回顾的阶段结论，预计30～45分钟。本课不增加业务功能、依赖或真实模型调用。

三个按需概念：①评估证据链：场景→预期→实际观察→证据；②离线与真实评估：假响应验证程序行为，不能替代模型语义质量；③版本指纹：类似Android记录构建版本，输入代码或依赖变化后旧结论不能直接套用。指纹只覆盖脚本声明的业务／配置／依赖文件，不证明远端模型版本或完整运行环境相同。

动手只新增STAGE3_REVIEW.md，用下列四个二级标题组织：

- `## 自动检查`：记录实际命令`.venv/bin/python test/check_stage_3.py`、`版本指纹：<本次输出>`、`程序检查：12/12，退出码0`。这里的12/12是底层S3-08程序检查，不是模型质量分数。
- `## 验证范围`：四列表格“场景｜离线证据｜能确认｜不能确认”，写四行“多轮追问、窗口裁剪、保存恢复、流式中断”。证据分别引用test/check_s3_02.py、check_s3_03.py、check_s3_04.py或check_s3_05.py、check_s3_08.py，路径都带test/。每行用自己的话写具体结论与局限；可以读取相应测试，不必重写测试或业务代码。
- `## 真实验证`：按本课实际范围分别记录`本课新增真实调用：0`、`真实模型效果：待验证`、`实际费用：未知`；引用EVAL_CASES.md的E12/E13，说明当前版本缺少哪类证据。不用假usage估算实际费用，不用旧版本日志替代当前版本验证；已有结果以后可单独补录，本课不要求重跑。
- `## 我的理解`：至少一小段，回答“离线程序检查全通过，为什么仍不能宣布真实多轮回答质量通过？”解释由导师人工审阅，脚本不自动判断理解正确。

只提供一个最小表头，不代填四行结论：

```markdown
| 场景 | 离线证据 | 能确认 | 不能确认 |
| --- | --- | --- | --- |
```

运行`.venv/bin/python test/check_stage_3.py`，目标 **3/3、退出码0**。三项为：复用S3-08及此前整链程序回归、报告版本／结果记录、报告证据与验证范围结构。报告格式通过后仍需导师审阅解释，不能自动标掌握或模型质量通过。运行加`--program-only`时只检查程序，1/1不等于本课验收完成。

2026-10-30布置实跑基线 **1/3、退出码1**：程序回归通过，报告未创建；`--program-only`实跑1/1、退出码0。当前业务与依赖指纹109fb6d6。临时控制报告3/3、过期指纹2/3，只验证检查器，未把控制报告写入工程。默认只用内存SSE和临时文件，不读.env／真实Key、不请求模型。

完成后保存报告并提交检查输出；导师阅读报告和代码后再验收S3-09。通过后同轮安排S4-01结构化回答契约、生成其检查、更新记录并按新约定提交推送GitHub；当前不创建S4代码或执行付费调用。


2026-10-31：学员明确要求导师代完成S3-09。导师补齐四场景证据与局限，将误填的Git提交号改成本次检查输出的指纹109fb6d6；程序底层12/12、汇总3/3、退出码0。报告注明导师示范，不标学员独立完成或掌握；真实模型效果、E12/E13当前版本结果及实际费用仍待验证。本轮不请求模型，不改阶段3业务代码或旧检查断言。

## 当前 S4-01：离线结构化回答契约（阶段4独立入口）

本次一个30～45分钟目标：将回答和来源状态放入固定数据结构，输出机器可解析的JSON。先固定契约，后续S4-02再处理外部JSON的解析与校验，S4-03再按供应商官方能力接入模型；本课不调用模型、不引入框架。

新入口stage4_structured.py已创建，只含json、函数占位和main示例；阶段3入口与旧检查保持原样。本次无需复制ask_turn，因为只构造离线数据；需要模型或多轮能力时再复制到阶段4程序。

最多三个按需概念：①数据契约，像Kotlin DTO或约定字段的Map，键名与类型稳定；②Python dict是内存对象，json.dumps把它序列化为JSON字符串，类似Kotlin对象与序列化后的String不同；③模拟模式与来源状态分别描述“数据怎么产生”和“有没有检索证据”，正文看起来可信不能代替来源。

最小语法示例：`json.dumps({"label": "练习"}, ensure_ascii=False)`得到可读中文JSON字符串；不要用手工拼接处理引号和换行。实际目标对象由学员构造。

只实现新入口的`make_mock_answer(answer: str, uncertainty: str) -> dict`：

| 字段 | 类型与本课要求 |
| --- | --- |
| mode | str，固定为mock，明确尚未调用模型 |
| answer | str，使用清理首尾空白后的传入正文，内部换行、引号与反斜线保留 |
| uncertainty | str，使用清理首尾空白后的传入说明，保持内部原文 |
| source_status | str，固定为not_retrieved，表示没有检索 |
| sources | list，每次新建空列表，不捏造来源 |

输入规则沿用已学的异常：先检查**两个参数都是str**，任一类型错误均抛TypeError；再strip，任一为空白抛ValueError。必须先完成类型检查再检查空白，例如("", None)应是TypeError。Python注解不会替你执行校验。

输出恰好上述五个字段；每次返回新的dict和sources列表，不能共享可变结果。构造函数只返回数据，不打印、不读输入、不访问文件或网络。main已复用构造函数并用`json.dumps(..., ensure_ascii=False, indent=2)`打印一份JSON；正常stdout不混入额外说明，mode字段本身说明是模拟。

运行`.venv/bin/python test/check_s4_01.py`，目标 **8/8、退出码0**；完成后运行`.venv/bin/python stage4_structured.py`，输出含五字段的一份合法JSON。当前基线 **1/8、退出码1**：函数占位尚未实现，S3-09及此前回归已通过；直接运行当前占位入口会抛NotImplementedError，不记为新课完成。

检查覆盖契约、文本与JSON往返、空白、错误类型、来源状态、对象隔离、CLI及阶段3回归。临时正向控制8/8，伪造已检索来源5/8、共享sources列表7/8；仅用于验证检查器，不是学员成果。检查不加载.env／真实Key、模型网络被阻断，只用内存数据与临时回归副本；本课只需json标准库，无新依赖或费用。

完成后提交检查输出、离线JSON示例，并解释“为什么构造函数返回dict，而main输出JSON字符串”。通过后同轮安排S4-02、更新记录并同步GitHub；当前不代写此函数或创建后续功能。

已核对[Python 3.11 json官方说明](https://docs.python.org/3.11/library/json.html#json.dumps)：dumps返回str，ensure_ascii=False保留可读中文。合法JSON只表示格式可解析，不证明模型能力或地理历史事实正确。
