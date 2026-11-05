# 地理历史 Agent 学习路线

每次一个主要目标、一个 30～60 分钟小任务；学习者实现，导师按代码和运行证据验收。
截至2026-11-05：阶段1／2既有程序、阶段3离线能力及阶段4整链已有验收记录；S3-09为导师示范，S4-08学员报告4/4及人工审阅通过。S5-01学员加载器10/10、实际CLI42条及42个来源页面简介支持核对通过；不代表独立史实多源核实或全面掌握。当前S5-02关键词检索待实现，基线2/12。真实模型质量与费用继续单列，历史证据见下文及PROGRESS.md。

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
| S4-01 | 定义结构化回答契约（离线已验收） | 确定答案、不确定性、来源状态等字段及合法示例。 |
| S4-02 | 解析并校验结构化结果（离线已验收） | 缺字段、错误类型和非法 JSON 能被明确拒绝。 |
| S4-03 | 接入模型结构化输出（程序已验收） | D离线10/10；学员报告真实已运行，输出和质量判定待补。 |
| S4-04 | 实现一个确定性工具（离线已验收） | 本地地名条目查询可独立运行，练习资料明确标注来源或模拟状态。 |
| S4-05 | 读取模型提出的工具请求（离线程序已验收） | 识别工具名称与参数，理解它尚未被程序执行。 |
| S4-06A | 执行工具并构造回传消息（离线已验收） | 单次受控执行，role=tool关联调用ID，完整序列化结果。 |
| S4-06B | 回填工具结果并让模型续答（离线13/13已验收） | 从已有调用消息出发，保留完整assistant并追加tool，只请求一次续答。 |
| S4-06C | 接通首轮调用请求与续答（离线13/13已验收） | 加入模型首轮生成tool_calls，形成有限两次请求的固定流程。 |
| S4-07 | 处理工具参数与执行失败（离线12/12已验收） | 未知工具、无效参数、无结果或异常得到明确处理。 |
| S4-08 | 固定流程与阶段评估（离线报告及人工审阅通过） | 对比直接回答与工具辅助流程，记录正确性、调用次数和用量。 |

### 阶段 5：基于资料的问答与 RAG

| 课次 | 单一目标 | 产物与验收重点 |
| --- | --- | --- |
| S5-01 | 整理并加载小型可追溯资料集（10/10及来源支持核对通过） | 保存标题、出处、片段及相关时代背景，避免混淆事实与练习数据。 |
| S5-02 | 建立关键词检索基线（当前） | 给定问题能返回相关片段及来源，无命中时明确返回空结果。 |
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
- 路线展开本身不新增验收结论；当前实际任务及验证结果见文末S4-04。



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

## S4-01：离线结构化回答契约（离线已验收）

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


2026-11-02：学员已实现make_mock_answer，入口833265d1实际通过test/check_s4_01.py **8/8、退出码0**，含阶段3及此前回归。两个参数先检查类型再清理空白，固定字段、原文保留、来源状态和独立列表均符合契约。dict与JSON字符串的解释方向正确；学员误称dict可append，导师已纠正append属于list，dict用键赋值或update修改。此处仍待后续迁移巩固，不据一次通过标全面掌握。未读取Key、未请求模型，无新增真实用量或费用。

## S4-02：解析并校验JSON回答（保留布置基线，现已离线验收）

一个30～60分钟目标：将外部JSON文本转换成符合已有契约的数据。只在阶段4入口stage4_structured.py实现parse_answer_json(raw: str) -> dict；不改make_mock_answer、main、阶段3入口或旧检查，无新依赖／模型调用。函数占位和本课检查已提供。

最多三个概念：①json.loads反序列化，类似Kotlin JSON解析，但返回的是运行时Python类型，数组、null等也能是合法JSON；②语法正确与业务结构正确分开；③错误分层，原参数类型错误TypeError、JSON语法错误JSONDecodeError、解析后的结构或字段不合法ValueError。JSONDecodeError本身也是ValueError子类，本课保留其具体类型。

最小示例：`json.loads('{"city": "示例"}')`得到dict；`json.loads('[]')`得到list。后者能解析，但本项目不接受它作回答。不要用eval或手工裁剪代码围栏替代JSON解析。

| 范围 | 本课契约 |
| --- | --- |
| raw参数 | 必须str，否则TypeError；不要str()强转、默认返回空对象 |
| JSON语法 | 使用json.loads；语法错误保留json.JSONDecodeError，不吞掉或替换成成功结果 |
| 顶层 | 必须dict；合法数组、null、数字、布尔、字符串仍抛ValueError |
| 字段集合 | 恰好mode、answer、uncertainty、source_status、sources；缺字段、多字段或拼错字段均ValueError |
| 正文与说明 | answer、uncertainty必须为str且strip后非空；错误统一ValueError。清理两端，内部中文、换行、引号等保持 |
| 模式与来源 | mode必须是mock，source_status必须是not_retrieved；sources必须list且为空。空字典、空字符串、null等不能因是假值就放行。任何伪造来源或其他状态均ValueError |
| 返回值 | 合法时返回独立dict和sources列表；先校验解析得到的全部原字段，再规范化。可复用make_mock_answer，但不能丢弃非法来源／模式后重新构造“合法”对象 |
| 职责 | 不打印、不读输入／文件或请求模型；无效结构不能泄漏KeyError或AttributeError，不改已有main的离线展示 |

建议顺序：检查raw类型 → json.loads → 检查顶层和字段集合 → 校验字段类型与值 → 复用已验收构造函数或自行返回新对象。先做正常路径，再补无效输入；具体实现由学员完成。本课沿用标准库默认解析行为，不扩展底层解析器或宣称覆盖所有JSON兼容边界。

运行`.venv/bin/python test/check_s4_02.py`，目标 **10/10、退出码0**。布置时占位基线 **1/10、退出码1**：S4-01的8项及此前回归通过，新解析函数待实现。实现后运行同一脚本加`--demo`，观察合法JSON返回dict，以及伪造sources被拒绝；演示同样不请求模型。旧main继续保持S4-01输出。

检查覆盖正常对象、原参数类型、JSON语法、合法非对象、字段集合、字段类型／空白、来源一致性、文本保留、对象隔离和旧回归。临时正向与故障控制仅验证检查器，不计学员成果；实际正向控制10/10、覆盖非法来源的错误控制9/10、只做json.loads的错误控制4/10，详情见EVAL_CASES.md。检查禁用dotenv／隔离真实环境／阻断网络，只使用假数据和临时回归副本。

完成后提交检查输出与--demo结果，并解释“为什么json.loads('[]')能成功，但parse_answer_json必须拒绝它”。通过后同轮安排S4-03，届时再查Kimi当前官方结构化输出能力、说明真实调用规模，不提前请求模型。

2026-11-02已核对[Python JSON反序列化及异常](https://docs.python.org/3.11/library/json.html#json.loads)、[Python容器方法](https://docs.python.org/3.11/tutorial/datastructures.html#dictionaries)。合法JSON不代表业务有效、有来源或史实正确。


2026-11-02：学员实现入口a4dabb6e实际通过test/check_s4_02.py **10/10、退出码0**，--demo成功，S4-02离线功能验收通过。拒绝合法数组的原因是业务要求dict，而非输入不是JSON字符串；导师已解释，理解待后续迁移检验。不据此标模型质量或史实通过。

## S4-03A：构造Kimi JSON Mode请求（保留布置基线，现已离线验收）

按实际理解情况将原S4-03拆为A请求构造、B调用与响应校验；后续B再衔接少量人工真实评估。本次只有一个30～45分钟目标：在stage4_structured.py实现纯函数build_structured_request(question: str) -> dict，形成可查看、可测试的请求参数，不发送请求。旧make_mock_answer、parse_answer_json和main保持当前实现，阶段3入口／旧检查／依赖不变。

三个按需概念：①JSON Mode通过response_format约束JSON格式，字段类型／来源与事实仍需程序和证据校验；②system描述固定回答规则，user只放本次问题，类似固定请求配置与用户入参分离，不保证模型必然遵守；③嵌套dict/list是待交给SDK的内存参数，类似Kotlin请求DTO，不能提前dumps成String。打印演示时才序列化。

先检查question是str，否则TypeError；再strip，空白抛ValueError。返回恰好六个字段：

| 字段 | 本课要求 |
| --- | --- |
| model | 字符串kimi-k3，沿用本工程模型，不跟随文档示例升级 |
| messages | 两条消息的新list，system在前、user在后；每条恰好role/content，content为str |
| response_format | 新dict，等于{"type": "json_object"} |
| stream | 布尔False，本课不处理流式 |
| max_completion_tokens | 整数4096，沿用既定上限，不用旧max_tokens |
| reasoning_effort | 字符串low，沿用既定推理强度 |

system提示词由学员编写，可定义字符串常量；不同问题不改变它。明确只输出一个JSON对象、没有代码围栏或额外解释、恰好五字段：mode固定model；answer、uncertainty为非空字符串；source_status固定not_retrieved；sources为空列表。回答中文地理历史问题，不确定或虚构前提要说明，不编造年份／来源或声称已检索。提示词自动检查JSON、字段名和枚举词，语义由导师人工审阅。

user.content仅是question.strip()，内部换行／引号保留，不把用户文字插入system，也不json.dumps问题。每次返回独立请求dict、messages及其中两个消息dict、response_format；调用方修改前次结果不影响后次请求。函数不打印、输入、读文件、加载配置、连接网络或调用解析器。

最小示例仅说明新参数形状：`response_format = {"type": "json_object"}`。其余六字段和消息组装由学员实现。SDK发送留到S4-03B；API Key不属于本函数的返回值。现parse_answer_json仍只接受mock，这个限制本课保留；未来接入真实响应时再显式扩展校验，不能让真实模型自称mock或覆盖错误状态。

已提供函数占位、test/check_s4_03a.py和--demo。运行`.venv/bin/python test/check_s4_03a.py`，占位基线 **1/10、退出码1**，仅S4-02及此前回归通过；目标10/10、退出码0。实现后加`--demo`查看带“未发送”声明的请求参数，不代表模型回答或真实用量。旧main仍只显示模拟回答。检查使用内存数据／临时回归副本，禁用dotenv、隔离真实环境并阻断网络，不读取真实会话。

完成后提交检查及--demo输出，并解释“messages为什么保留list[dict]，而不是先json.dumps成字符串？”导师同时人工审阅system提示词。通过后同轮布置S4-03B、更新记录并上传GitHub；不提前实现调用端或执行付费请求。本课真实调用计划0次，暂无新增费用；B中的真实验证另说明用途／规模。

2026-11-02核对官方：[Kimi JSON Mode](https://platform.kimi.com/docs/guide/use-json-mode-feature-of-kimi-api)、[Kimi K3参数](https://platform.kimi.com/docs/guide/kimi-k3-quickstart)。JSON Mode文档当前示例使用其他模型，本工程保留kimi-k3；输出预算按K3当前max_completion_tokens说明，不照搬通用页旧max_tokens示例。不引入严格JSON Schema或新SDK版本。


2026-11-02：学员实现build_structured_request，入口0cfd746f实际通过test/check_s4_03a.py **10/10、退出码0**；--demo成功。提示词人工审阅通过：JSON对象／五字段、中文、不确定性、虚构前提及未检索来源声明齐全。仅离线请求构造验收，不证明供应商实际返回、模型质量或史实。

## S4-03B：用注入客户端接通结构化问答（保留修正过程，已离线验收）

一个30～60分钟目标：把已验收的请求构造与回答解析串起来，用假客户端验证调用边界。本课不创建真实客户端、加载配置或发送付费请求；阶段4继续使用stage4_structured.py。仅修改解析器的模式参数并实现ask_structured，其余函数和main保持当前实现。

最多三个按需概念：①客户端注入，类似将Retrofit service传入业务层，Python本课按对象提供的方法调用，无须新建接口／继承层次；②`**request`将字典展开为命名实参，不是JSON序列化；③`*`后的参数只能按名称传递，用显式expected_mode避免由模型自报模式决定校验规则。

动手一：将签名扩展为`parse_answer_json(raw: str, *, expected_mode: str = "mock") -> dict`。先检查expected_mode为str，否则TypeError；仅允许mock/model，其他值ValueError。默认mock保留旧契约。原始data["mode"]必须精确等于调用方传入的expected_mode，交叉模式拒绝；返回mode保留已验证值，不能继续写死mock，也不能覆盖错误模式。原raw类型、JSON语法／字段／来源校验、清理和对象隔离全部保持。

动手二：实现占位`ask_structured(client, question: str) -> dict`，流程如下：

1. 调用build_structured_request(question)一次；问题校验失败时零SDK调用。
2. 用`client.chat.completions.create(**request)`调用一次，沿用六个请求参数，不加载配置或创建客户端。
3. 校验响应包络：choices必须是list且恰好一项；缺少choice/message、非stop结束、content非str或空白均抛普通ValueError。在这些失败分支不调用解析器。
4. 将原始content交给`parse_answer_json(content, expected_mode="model")`恰好一次，直接返回解析器得到的dict。不预先strip／dumps／截取或修补JSON，不从模型文本选expected_mode。

JSON语法错误仍为JSONDecodeError，字段错误为ValueError；SDK调用异常原样传播，不吞掉、不自动重试或返回模拟答案。函数不打印、输入、访问文件，不关闭调用方传入的客户端。finish_reason==stop仅是本课接收策略，仍须字段校验，不等于事实正确或来源存在。

最小语法示例：`print("甲", "乙", **{"sep": " | "})`等价于传sep命名参数；这里并未生成JSON字符串。完整问答流程由学员实现。可复用阶段2／3中已学的getattr和异常传播，不复制旧ask_turn或接入多轮、流式、存档。

已提供ask_structured占位及test/check_s4_03b.py，解析器扩展由学员完成。运行`.venv/bin/python test/check_s4_03b.py`，实际占位基线 **1/12、退出码1**，仅旧S4-03A及全链回归通过；目标12/12、退出码0。实现后加`--demo`看假响应→调用接线→dict的完整离线演示。演示中的mode=model只是被测响应协议，数据由假客户端提供，不能记为真实生成。

默认检查隔离真实环境、阻断网络，使用内存假客户端和临时旧课副本，不读.env／Key或真实会话。本课只返回回答dict，尚未保留usage；S4-03C在真实评估前补齐usage／finish_reason记录并另说明用途和调用规模。本课真实调用计划0次、无新增真实费用；不把假usage当费用，不提前执行C。

完成后提交检查及--demo输出，并解释“为什么expected_mode由调用方传入，而不能从模型输出的mode自动选择？”通过后同轮更新记录、上传GitHub并布置下一小课；未通过时只修本课。

2026-11-02核对[Kimi JSON Mode与content解析](https://platform.kimi.com/docs/guide/use-json-mode-feature-of-kimi-api)、[Kimi K3](https://platform.kimi.com/docs/guide/kimi-k3-quickstart)、[OpenAI Docs的Python兼容SDK调用形状](https://developers.openai.com/api/reference/python/resources/chat/subresources/completions/methods/create)。本地已安装openai 3.37.0的create签名包含本工程六字段；未升级依赖、不将OpenAI模型规则套用于Kimi，不承诺真实账户可用性。


2026-11-02：学员提交入口87aebdc0，原检查实跑12/12。人工审阅发现choices还接受单项tuple，而约定必须list；原脚本仅测空tuple，因长度不符而拒绝，漏检类型放宽。导师只在原包络项新增单项tuple，保留原断言和12项；补强后实际 **11/12、退出码1**，唯一失败为包络检查，其他接线、模式、异常及旧回归通过。本课尚未验收完成，不进入下一课或上传课程。

当前小任务只收窄ask_structured的choices类型判断，使单项tuple拒绝为ValueError，长度检查保留。raw与expected_mode都在json.loads前校验，本轮不另设双参数同时无效的错误优先级。修正后目标12/12、退出码0，再按约定进入下一课及上传。


2026-11-02：学员将choices类型收窄为list（保留长度检查），入口ec31245b实际通过补强后的test/check_s4_03b.py **12/12、退出码0**，--demo成功。单项tuple拒绝、显式模式、响应检查、异常传播及旧回归均离线通过，S4-03B功能验收完成。此前87aebdc0的11/12保留为修正过程，不当作当前得分；未请求真实模型，不证明模型质量或史实。

## S4-03C：失败回答也保留响应元数据（保留布置基线，已离线验收）

一个30～60分钟目标：回答校验失败时，仍保留已经返回的结束原因与用量。复用阶段3学过的回调，保持现有ask_structured返回回答dict；元数据不混入模型五字段答案。本课仅假客户端，不读Key、不请求模型；真实接线／人工评估单列后续S4-03D，届时再说明调用规模。

必要知识最多三个：①请求返回、答案通过业务校验、事实已核实是不同状态，失败答案也可能已消耗token；②None表示统计未取得，0是明确的零值，不能用or把0变成None；③可选回调负责把元数据交给调用方，类似Kotlin函数类型监听器，Python可传函数并用callable检查，不必引入接口类。

只修改stage4_structured.py两处，其他已验收函数和main保持：

1. 实现已提供占位`extract_response_metadata(response) -> dict`。每次返回新的扁平dict，恰好finish_reason、prompt_tokens、completion_tokens、total_tokens四键。usage缺失／None或个别计数属性缺失，对应值为None；已有0和计数原样保留，不强转、推算total或计算费用。仅在choices为恰好一项list时提取其finish_reason，缺失为None；原值保留，不strip或翻译。choices无效时结束原因None，仍可提取usage。只读SDK对象，不打印／读文件／判断回答成功；本课按SDK约定的int／None统计字段练习，不新增损坏usage字段的类型校验。
2. 扩展签名为`ask_structured(client, question: str, *, on_metadata=None) -> dict`。回调非None时在请求前验证callable，否则TypeError且零SDK调用；默认None时完全跳过提取器，保留旧行为。create返回后、原choices／正文／JSON及字段校验前，提取元数据并回调一次。回调返回值忽略，仍返回原解析结果；回调修改收到的独立dict不能改变SDK响应、正文或回答。

SDK异常时没有拿到响应，不调用提取器或回调；不能推断费用为0，也不重发请求补统计。回调自身抛错时原样传播，不重试、不继续解析。本课不实现遥测异常吞掉策略、费用计算或持久化；客户端仍由外层管理。

最小回调示例仅示意接收端：`def remember(meta): seen.append(meta)`，其中seen由调用方创建为列表。提取器和ask接线由学员实现；函数返回值继续给业务层，回调只接收四字段元数据。原始响应、Key及请求头不传给回调。

运行`.venv/bin/python test/check_s4_03c.py`，占位基线 **1/12、退出码1**，仅旧补强B及全链回归通过；目标12/12、退出码0。实现后加`--demo`查看正常假回答及JSON失败时仍收到假用量，演示明确未请求模型，假值不作为真实费用。检查隔离真实环境、阻断网络，仅内存假对象与临时旧课副本。

完成后提交检查与演示输出，解释“为什么JSON解析失败时仍要保留usage，而不能认定这一请求没有消耗？”通过后更新记录、上传GitHub，再布置真实接线的小任务；本课真实调用计划0次，不代写业务实现。

2026-11-02已核对[OpenAI Docs：ChatCompletion的可选usage与统计字段](https://developers.openai.com/api/reference/python/resources/chat/subresources/completions/methods/create)。只依据兼容SDK响应形状，不将OpenAI模型定价／能力用于Kimi；本课沿用kimi-k3及已安装依赖，不升级或引入框架。


2026-11-03：学员实现元数据提取与on_metadata接线，核心b302cbcc实际通过test/check_s4_03c.py **12/12、退出码0**，--demo成功。缺失／零统计、失败前通知、回调隔离、异常传播及旧回归通过；JSON失败演示仍收到假统计。S4-03C离线功能验收完成，没有新增真实模型请求或费用。

## S4-03D：单次真实客户端入口与小规模评估（程序通过，真实输出待补）

一个30～60分钟目标：把已验收的阶段4纯核心接到真实Kimi客户端，保留来源声明、失败统计与资源关闭。新建同阶段I/O入口stage4_live.py，不修改stage4_structured.py或阶段3入口；CLI预览和展示辅助由导师提供，学员只实现run_live(question: str) -> int。

最多三个按需概念：①副作用放在显式调用边界，Python import会执行模块顶层代码，与Java/Kotlin仅做名称解析的import不同，因此配置导入延后到run_live内；②with管理客户端，类似Kotlin use／Java try-with-resources，异常时也关闭；③离线SDK检查与真实模型评估分层，前者确认接线，后者观察实际结构、回答、结束原因及用量。

run_live按以下要求实现：

1. 先检查question是非空白str；不合法时给简短提示、返回1，不读取配置或创建客户端。
2. 在函数内部导入配置get_api_key/get_base_url，并显式指定kimi；不要沿用config默认DeepSeek，不打印Key。使用已安装OpenAI兼容SDK，不更新依赖。
3. 创建OpenAI客户端，api_key/base_url取配置；timeout=120.0、max_retries=0。由本函数用with或等效finally关闭其创建的客户端，成功、JSON失败及API异常都关闭。
4. 准备独立容器（字典配update或列表配append）承接on_metadata，调用ask_structured恰好一次；请求六字段继续由核心构造。输出有效回答前打印一次SOURCE_LABEL；成功用json.dumps(answer, ensure_ascii=False, indent=2)展示已校验回答，返回0。
5. 捕获APIError及ValueError（含JSONDecodeError），给简短安全提示并返回1；不打印原异常对象／响应／请求头，不自动重试、回退成mock或修补回答。
6. 复用已提供show_metadata(metadata)，在成功／失败收尾都展示已捕获的四字段；推荐finally。缺统计保留None、0保留0；SDK异常无元数据时说明未知，不推断免费。输入校验提前结束时无需展示请求统计。

导师提供main(argv)：默认仅组装并显示请求，不导入配置或发送模型请求；只有显式--live才执行run_live。保留这一开关和入口保护；Ctrl-C由main处理为130。JSON打印、预览和参数解析已经提供，本课无需自行学习完整argparse用法，不接多轮／流式／存档／框架。

运行`.venv/bin/python test/check_s4_03d.py`，实际占位基线 **2/10、退出码1**：安全导入／默认预览与旧S4-03C回归通过，run_live待实现，目标10/10。实现后加--demo，使用真实SDK、假配置和内存MockTransport展示全链路，仍未读取Key、未连接模型、无真实费用。旧检查断言及核心代码保持。

预览：`.venv/bin/python stage4_live.py "为什么河流会影响城市的发展？"`，不调用模型。离线检查通过后，再由学员手动为E14/E15各加--live运行一次；导师不代执行。

付费用途与规模：验证Kimi真实返回能否满足五字段契约，并记录回答、不确定性、来源状态、usage和finish_reason；计划最多2次，每题一次，沿用每次4096 completion预算、120秒超时和零自动重试。实际用量／金额以响应和供应商账单为准，不用假值填表；失败也记录，不为刷通过追加调用。若暂不付费或无Key，可先完成离线部分并注明真实评估待验证。

E14问题为“为什么河流会影响城市的发展？”；E15为“我捏造了‘青岚朝’。请给出它真实存在时的建国年份。”。只发送问题，不把评分标准拼进prompt。人工判定见EVAL_CASES.md：格式、中文相关性、虚构前提识别和未检索声明分别检查；来源状态不证明史实已核实。

完成后提交离线检查和演示输出，以及两题真实输出或注明仅离线；在EVAL_CASES.md补摘要、判定理由、实际四字段元数据。说明“为什么不加--live时不应读取Key或发送请求？”程序检查与真实评估分开记录，真实失败允许如实记录，不强求回答刷过。

2026-11-03核对[OpenAI Docs：客户端timeout、max_retries、错误与资源管理](https://developers.openai.com/api/reference/python)、[Kimi K3参数](https://platform.kimi.com/docs/guide/kimi-k3-quickstart)、[Kimi JSON Mode](https://platform.kimi.com/docs/guide/use-json-mode-feature-of-kimi-api)。本地SDK仍3.37.0，现有客户端参数和httpx2.MockTransport可用；保留kimi-k3，不随文档示例升级模型，不承诺实际账号权限／余额。


2026-11-03：学员实现run_live，原入口64bdb3f9通过test/check_s4_03d.py **10/10、退出码0**及离线SDK演示；后续保存为962f0be9，再复验10/10，作为本轮验收版本。配置显式kimi、零重试／120秒、关闭客户端、失败统计及旧回归通过，S4-03D程序部分验收完成。学员采用captured.append承接回调，符合行为目标，无须统一改成字典update。

学员本轮报告E14/E15已真实运行，并在评估表补录：E14为stop、333/387/720，E15为stop、344/142/486，均自评通过。以上计数按学员记录保留；回答正文和具体判定理由仍待补，导师暂不将真实格式／质量标通过，实际费用未知。无需重复调用，导师本轮未发模型请求。

## S4-04：实现确定性地名工具（离线已验收）

一个30～45分钟目标：用程序查询固定目录并返回明确结果，为后续模型提出工具调用请求做准备。新增stage4_tools.py；两条目录与CLI由导师提供，只由学员实现lookup_place(name: str) -> dict，不修改旧问答、SDK入口或解析器。

目录为青岚城／别名青岚、赤川镇／别名赤川，全部是明确标注的虚构练习数据，不对应真实地理历史事实，不使用真实史料引用。学习重点是工具的输入、执行、输出及来源标记；有可追溯资料的检索留到阶段5。

必要知识最多三个：①确定性工具：固定输入和目录得到固定结果，由Python执行，本课不调用模型；②合法未命中与非法参数分开，类似Kotlin Repository返回null与参数检查抛异常的区别；③返回嵌套数据需隔离，deepcopy可复用，Kotlin复制外层Map/List也不会自动复制内部可变对象。

输入先检查str，其他类型（包括None、False、bytes）抛TypeError；保存strip结果，清理后空白抛ValueError。仅精确匹配目录的name或aliases中的完整字符串；不做子串／模糊匹配，不删除内部空白，也不调用模型补答案。使用已提供PLACE_FIXTURES，不硬编码两条示例的返回值。

返回恰好四字段：

| 字段 | 契约 |
| --- | --- |
| query | 清理后的原查询；用别名查询时保留别名，不替换成标准名 |
| found | bool，命中True，否则False |
| place | 命中时为目录完整条目的独立深拷贝（name/aliases/description）；未命中None |
| source_status | 固定fixture，表示人工构造练习目录，命中与未命中都保留 |

合法未知名称是正常结果，不抛异常；未收录不等于现实中不存在，也不能猜一个“最像”的条目。每次新建外层dict与命中的嵌套条目／aliases列表，调用方修改结果不影响原目录或后续查询。查询函数只返回或抛异常，不打印、不读输入／文件或访问网络。工具结果是独立协议，不交给旧parse_answer_json，也不把fixture改成已检索或已核实。

最小类比：`{"found": False, "place": None}`可表达查无记录，None序列化后为null；实际四字段由学员构造。deepcopy已导入，可以用于隔离命中的条目。main只负责参数与JSON展示，已提供，无须再写CLI。

运行`.venv/bin/python test/check_s4_04.py`，占位基线 **1/10、退出码1**，仅S4-03D及全链回归通过，目标10/10。实现后加--demo查看命中和未命中；或直接`.venv/bin/python stage4_tools.py "青岚"`与`... "未收录地点"`。正常命中／未命中均输出一份中文JSON、退出码0；空白参数由main提示并返回1。

检查覆盖标准名、别名、空白、未知、非法输入、fixture标记、嵌套隔离、替换／空目录、CLI及旧回归；不接模型、不加载配置／Key或真实会话。本课真实调用计划0次。模型如何提出调用请求、程序如何读取请求留到S4-05，不提前实现工具选择、回填或Agent循环。

完成后提交检查与--demo输出，并回答“为什么合法但未收录的地名应返回found=False，而空白参数要报错？”通过后同轮提供S4-05检查、更新记录并上传GitHub。E14/E15已有真实输出可随时补录，不重跑，不用工具假数据替代真实评估。

2026-11-03：学员实现lookup_place，工具源码42757a33由导师实际运行test/check_s4_04.py **10/10、退出码0**，--demo成功。标准名／别名、空白／未知／错误输入、fixture标记、嵌套隔离、替换目录与CLI及旧回归均通过，S4-04离线功能验收完成；未新增真实模型请求。

学员正确区分空白无效参数与合法未命中。补充澄清：found=False只表示当前目录未收录，是否继续查询由调用方决定，工具不会自动继续查，也不证明地名不存在。这是本次单次澄清，不据测试通过标全面掌握。学员在旧检查中新增一行未使用局部变量，原断言未删改，不影响本次验收。

## S4-05：读取一次工具请求（离线程序已验收）

一个30～60分钟目标：从完整的非流式assistant消息中提取并验证一次调用请求。仍在同阶段stage4_tools.py，只实现导师新加的parse_tool_request(assistant_message: dict) -> dict | None占位；保留lookup_place、目录和CLI，不改旧核心／模型入口，不执行工具，也不请求模型。

最多三个概念：①tool_calls是模型提出的结构化调用，正文提到函数名不算调用，执行仍由程序负责；②function.arguments是嵌套JSON字符串，需要json.loads后再做业务校验，类似Kotlin先从响应中取出一段JSON文本再反序列化，Python dict不会自动校验字段；③调用id用于后续工具结果关联，只检查为非空白str，原样保留，不像地名那样strip后返回。

下面是假消息的协议示例，不是真实模型调用，也不是工具查询结果：

```python
message = {
    "role": "assistant",
    "content": None,
    "tool_calls": [{
        "id": "call_lookup_1",
        "type": "function",
        "function": {
            "name": "lookup_place",
            "arguments": '{"name": " 青岚 "}',
        },
    }],
}
# parse_tool_request(message)期望：
# {"tool_call_id": "call_lookup_1", "tool_name": "lookup_place",
#  "arguments": {"name": "青岚"}}
```

输入与分支契约：

1. 顶层必须dict，否则TypeError；role必须恰好assistant，否则ValueError。允许content、reasoning_content等额外SDK字段，不丢弃或修改原消息。
2. tool_calls缺失、None或空list表示没有调用，返回None；其他值必须list且只有一项。其他类型、超过一项或项不是dict都ValueError；不能用if not calls把空dict／空字符串也当作无调用。本课只处理单次调用是练习范围，不是API能力限制。
3. 单项id必须非空白str，type恰好function，function必须dict，function.name恰好lookup_place；缺失、不合法或未知工具均ValueError。id校验可用strip，但返回原字符串；工具名不私自去空白或动态eval／执行。
4. function.arguments必须str，缺失或其他类型ValueError；用json.loads解析，JSON语法错误保留json.JSONDecodeError，不修补或剥离代码围栏。解码后必须dict且恰好一个name字段，name是非空白str；业务错误用普通ValueError。清理并保存name.strip()。
5. 返回新dict，恰好tool_call_id/tool_name/arguments三字段；arguments为新dict且恰好清理后的name。每次结果相互独立，不修改原消息／目录、不打印、不查地名。合法未知名称同样能解析成功，查询是否命中留给工具执行。

可按“顶层和无调用分支 → 单项协议 → 解码及参数 → 新结果”逐步实现，不需引入类、框架或新依赖。真实SDK消息后续可用response.choices[0].message.to_dict()作为输入；to_dict只把DTO转成dict，不把arguments字符串再解码。本课使用假消息和SDK DTO检查，不建立真实client。

运行`.venv/bin/python -B test/check_s4_05.py`，导师实际占位基线 **1/12、退出码1**，S4-04及此前回归通过，目标12/12；实现后加--demo，看到假消息变成三字段请求，以及无调用为null（Python None）。不在此处调用lookup_place，不回填role=tool，不接多轮／流式或Agent循环；真实模型请求计划0次。

检查器控制在临时工程实际验证：正向12/12、演示退出码0；误执行工具7/12、参数保持字符串7/12、擅自strip调用ID11/12，均检出。参考实现不写入学员工程，不计为学员完成。检查覆盖正常／异常／边界、原消息隔离、现有SDK DTO桥接及旧回归，不改变旧断言。

完成后交检查和--demo输出，并说明“成功解析tool_calls，为什么仍不能说工具已执行？”验收后同轮布置下一课并上传。E14/E15正文与具体判定理由仍待补，已有输出即可，不重复付费调用。

2026-11-03核对[Kimi工具调用协议](https://platform.kimi.com/docs/guide/use-kimi-api-to-complete-tool-calls)：模型提出工具名及JSON参数，应用执行，结果用tool_call_id关联；[Kimi K3指南](https://platform.kimi.com/docs/guide/kimi-k3-quickstart)要求后续保留完整assistant消息。现有本地SDK 3.37.0的chat_completion_message_function_tool_call.py与_models.py核对arguments:str和to_dict；本课未升级依赖。暂不处理流式工具分片或多调用，不声称已验证真实工具选择。

2026-11-03：学员提交parse_tool_request，工具源码1721087a由导师实际运行test/check_s4_05.py **12/12、退出码0**，--demo退出码0。单次协议／参数校验、None分支、错误分类、ID与原消息保留、结果隔离、SDK DTO桥接及旧回归通过；S4-05离线程序验收完成。没有新增真实模型请求。

概念小问待巩固：学员提到尚未给模型生成入参，回答未明确区分本课离线假消息与真实响应。导师补充：本课确实没有请求模型；真实tool_calls已经包含模型生成的工具名和JSON参数，解析后由程序执行lookup_place，再把工具结果回传给模型。此处仅记录一次表述待澄清，不判断为反复出错或已掌握。下一课用实际执行练习检验迁移。

## S4-06A：执行工具并构造回传消息（离线已验收）

一个30～45分钟目标：把经过校验的调用请求变成一次Python函数执行及一条可回传的tool消息。为巩固调用方向，将原S4-06拆成A（本地执行与消息）和B（下一课接模型续答），每次保留一个目标；本课不请求模型。

完整方向是：tools能力描述和用户问题 → 模型生成tool_calls → 程序解析参数 → 程序执行lookup_place → tool结果消息 → 模型生成后续回答。模型不会因为返回了工具名而自动运行本地函数；解析也不需要再请模型生成参数。本课的第一份调用消息仍由离线样例提供。

最多三个按需概念：①调用请求与函数执行：类似Android收到JSON事件后还要显式调用Repository方法，Python解析dict同样不会自动执行函数；②role=tool表示工具输出，用tool_call_id对应原调用id，name保留工具名；③工具输出dict通过json.dumps变成content字符串，外层消息仍是dict，不把整条消息也变成字符串。

只实现stage4_tools.py新占位execute_tool_request(assistant_message: dict) -> dict | None，不改已验收lookup_place、parse_tool_request、main或旧问答入口。

1. 恰好调用parse_tool_request(assistant_message)一次，保留完整输入；不要重写解析逻辑，也不需要重新向模型询问参数。
2. 解析返回None时直接返回None，执行工具0次，不伪造tool消息。
3. 有请求时取已解析的arguments中的name，显式调用lookup_place一次。当前解析器只允许这个工具，因此直接调用该函数即可，无需eval、globals、动态分发或注册框架。
4. 返回独立的新dict，恰好以下四字段；不修改原assistant消息、解析结果或目录，不打印。

| 字段 | 本课契约 |
| --- | --- |
| role | 固定tool |
| tool_call_id | 解析结果中的tool_call_id，原样保留 |
| name | 解析结果中的tool_name，当前lookup_place |
| content | 完整工具返回值的json.dumps(result, ensure_ascii=False)字符串 |

未知地名的found=False／place=None也是正常工具结果，照常序列化并保留source_status=fixture；不要改写成有真实来源或已核实，也不要用旧parse_answer_json处理工具结果。内层content是JSON文本，外层回传消息是Python dict。

最小执行示例：`result = lookup_place("青岚")`才会进入工具函数体。已有上一课解析结果中的name可以代替这个写死的示例值；消息字段由学员组装。本课不提供完整函数答案。

解析器拒绝的输入必须在执行工具前失败，原异常传播，工具0次；lookup_place抛异常也原样传播，只尝试一次，不重试、不转换为found=False，不调用模型。成功命中、未命中均只执行一次。每次结果独立，异常处理和安全展示由未来调用方负责。

运行`.venv/bin/python -B test/check_s4_06a.py`，实际占位基线 **1/10、退出码1**，S4-05及此前全链回归通过，目标10/10；实现后加--demo查看假消息 → 解析 → 本地工具实际执行一次 → tool消息，无调用时执行0次。脚本观察调用次数与顺序，覆盖正常／异常／边界、动态工具结果、序列化和隔离；不加载.env／Key、真实会话或请求模型。

检查器临时控制实际：正向10/10、--demo退出码0；跳过执行3/10、content直接放dict5/10、工具异常后重试9/10，均检出。控制实现只在临时工程，不写入学员代码，不计学员完成。

完成后提供检查和演示输出，并指出你代码中“哪一行真正执行了地名查询”。验收后同轮布置S4-06B及检查并上传；该下一课再追加完整assistant和tool消息并做有限模型续答，不在本课提前实现循环。E14/E15已有回答正文／理由仍可补录，无需为补证据重跑。

2026-11-03已查询[Kimi工具调用官方说明](https://platform.kimi.com/docs/guide/use-kimi-api-to-complete-tool-calls)：应用执行工具后用role、tool_call_id、name和序列化content回传。此处是自定义本地函数工具，模型输出请求与程序执行分别记录。本课未新增依赖、模型参数或真实API验证，真实请求计划0次。

2026-11-03：学员提交execute_tool_request，工具源码a4ca67f6由导师实际运行test/check_s4_06a.py **10/10、退出码0**，--demo退出码0。复用解析器、单次执行、四字段tool消息、完整序列化、无调用／非法输入零查询、异常传播与隔离及旧回归通过；S4-06A离线程序验收完成，新增真实模型请求0次。

学员指出第38行：该行确实是工具内部的目录匹配条件；导师补充第138行lookup_place(...)是从execute_tool_request发起工具执行的调用点。区分内部查找逻辑与调用入口，不据行号回答或测试通过标全面掌握；下一课检验完整消息关联。

## S4-06B：一次工具结果续答（离线已验收，保留修正过程）

2026-11-04最终13/13、退出码0；下文保留原布置与首次12/13的定位记录，最终复验见后记。

一个30～60分钟目标：收到已有的assistant工具调用消息后，执行本地工具，把完整协议回填给模型请求一次续答，复用五字段答案校验。新增当前所需编排模块stage4_tool_flow.py，不修改纯工具模块、旧核心、真实入口或阶段3代码。S4-06C再接首轮生成调用消息，本课不提前实现完整两次请求或Agent循环。

最多三个概念：①回填顺序是system → 原user → 完整assistant调用消息 → tool结果，完整assistant保留tool_calls／reasoning_content，不能只留content；②tools是能力描述，tool_choice=none约束本次只续答，应用仍检查结束原因，不继续执行新调用；③编排复用已验收模块，类似Kotlin UseCase依次调用Repository；Python list存对象引用，因此将外部assistant深拷贝后放入新请求，避免嵌套对象共享。

导师已提供三个辅助：build_followup_request(question)沿用旧六字段请求与问题校验，额外提供tools和tool_choice=none，并说明fixture是虚构教学数据；execute_tool_request来自S4-06A；parse_final_response(response)沿用旧包络和五字段解析，必须stop且无新调用。extract_response_metadata亦可直接复用，不需要改写这些辅助。默认CLI只预览基础参数，不创建client、不读配置或发请求。

只由学员实现ask_after_tool(client, question: str, assistant_message: dict, *, on_metadata=None) -> dict：

1. 调用build_followup_request(question)得到独立请求，非str／空白沿用TypeError／ValueError。on_metadata不为None时须callable，否则TypeError；两项输入校验都在工具执行和SDK请求之前。
2. 恰好复用execute_tool_request(assistant_message)一次。若返回None，说明本续答函数没有有效调用要回填，抛ValueError且零SDK请求；解析／工具异常原样传播，不请求模型、不重试或伪造结果。
3. 保留请求中已有system/user，在后面依次追加deepcopy(assistant_message)和执行器返回的tool消息。完整保留assistant原字段和调用ID，不把整条消息json.dumps；tool.content已经是JSON字符串。
4. 使用外部client.chat.completions.create(**request)恰好一次。保留八个请求字段，不重新创建／关闭client，不读取配置或添加自动重试。SDK异常原样传播，无响应就不通知元数据。
5. 收到响应后，若有on_metadata，先调用一次on_metadata(extract_response_metadata(response))，然后才做回答校验；None时跳过提取。缺失统计保留None、0保留；回调异常原样传播，不继续校验或重试。
6. 最后返回parse_final_response(response)得到的五字段dict。结束length、tool_calls、空正文或坏JSON等原样失败，不再查询、不发第二次请求，不返回工具结果冒充模型答案。函数不打印，也不修改输入消息、目录或SDK响应。

最小消息顺序示例（仅结构，不是完整实现）：

```python
# 原有基础请求中已经有system和user
# 应得到四条消息：
# [system消息, user消息, 完整assistant调用消息, tool结果消息]
```

最终回答沿用mode=model、source_status=not_retrieved、sources=[]；这里not_retrieved表示没有检索真实资料，工具内部fixture状态完整保留在tool.content。提示词要求说明虚构设定，但实际模型能否遵守仍须后续人工评估，不能由离线检查证明。本课假SDK正文与token数不当作真实结果。

运行`.venv/bin/python -B test/check_s4_06b.py`，实际占位 **2/12、退出码1**，安全预览与S4-06A及此前全链回归通过；目标12/12，实现后加--demo退出码0。演示显示四条消息、模拟五字段续答和模拟元数据；SDK方法调用1次来自假client，本地查询1次，真实模型请求0次，不需要Key。

检查器临时控制实测：正向12/12、演示退出码0；遗漏assistant消息10/12、解析后才通知统计10/12、重复执行工具4/12，均检出。参考实现不写入学员工程，不计为学员完成。检查覆盖输入与协议、请求预算、来源状态、元数据先后、失败不循环、client所有权和新旧结果隔离。

完成后交检查与--demo输出，回答“为什么不能只把tool结果发给模型，而省略前面的assistant调用消息？”验收后同轮布置S4-06C检查、更新记录并上传。真实模型请求计划0次，E14/E15正文和具体理由仍待补，已有输出即可，不为补记录重复调用。

2026-11-03查询[Kimi工具调用消息顺序](https://platform.kimi.com/docs/guide/use-kimi-api-to-complete-tool-calls)、[tool_choice约束](https://platform.kimi.com/docs/guide/use-tool-choice)及[Kimi K3完整assistant要求](https://platform.kimi.com/docs/guide/kimi-k3-quickstart)；本地SDK 3.37.0的ChatCompletionToolChoiceOptionParam确认支持none，ChatCompletion/ChatCompletionMessage DTO在离线检查使用。保留现有模型和预算，不升级依赖；本课不声称验证Kimi真实生成、传输或计费。

### 2026-11-04：S4-06B首次提交与入口定位（后续已修复）

2026-11-04：学员提交ask_after_tool，续答源码7969b3ad实际通过原test/check_s4_06b.py **12/12、退出码0**，--demo退出码0。完整assistant/tool顺序、工具单次执行、请求预算、收到响应后校验前通知元数据、失败传播、隔离及旧回归通过；这是原检查覆盖内的续答核心通过，尚未整体验收。

额外实际子进程复现：空白问题打印“问题必须是非空字符串”，但进程退出0，main约定返回1。文件末尾从raise SystemExit(main())改为只调用main()，丢失函数返回码。原检查仅调用main函数，遗漏真实入口；导师补入第13项“真实CLI进程：有效0／空白1”，保留原12项。当前补强检查 **12/13、退出码1**，只差入口码；未修改业务文件。临时副本仅恢复原入口后13/13，是定位控制，不计学员完成。

学员解释省略assistant会丢prompt，方向接近；导师补充这里丢的是模型工具调用记录及其与tool_call_id的关联，原system/user即使仍在也不够。此处为单次表述待巩固，不标全面掌握或反复出错。

当前只做一个5～10分钟修正：在stage4_tool_flow.py的__main__保护内将main()返回值传递给解释器退出状态。Python函数return 1不会自动结束整个进程；原被注释入口已提供方向。无需重写ask_after_tool，不改旧工具或SDK调用逻辑。

test/check_s4_06b.py已保留原12项并新增进程边界检查，目标改为13/13、退出码0；布置时2/12及旧参考实现12/12作为历史保留。修正后提交新检查结果，并解释“为什么main返回1，进程仍可能退出0？”本课整体通过后同轮再布置S4-06C、更新记录和上传，不提前代写下一课。

2026-11-04核对[Python官方sys.exit／SystemExit及退出状态](https://docs.python.org/3.11/library/sys.html#sys.exit)。本轮全程离线，新增真实模型请求0次；原12项与--demo的假统计不计真实用量。未完成整体验收，当前不执行课程提交／上传，也不改既往日报。

### 2026-11-04：S4-06B最终复验

2026-11-04最终复验：学员恢复raise SystemExit(main())，续答源码4bbeca8a实际通过test/check_s4_06b.py **13/13、退出码0**，包含真实离线CLI有效输入0／空白输入1及原12项。S4-06B离线程序整体验收完成。此前7969b3ad的12/13保留为入口回归及检查补强过程，临时13/13控制不计学员成果；最终成绩来自当前实际工程。

本轮文字包含“调用SystemExit，进程退出0”，可能有省略，不能据此标概念已掌握。导师给出精确对照：main()的返回值被丢弃时，脚本正常结束通常退出0；raise SystemExit(main())在main返回1时退出1。代码修复通过与概念复述分别记录，仍待后续迁移，不据含糊表述增加反复出错次数。导师本轮真实模型请求0次。

## S4-06C：首轮工具请求与一次续答（离线已验收）

一个30～60分钟目标：在已有续答能力前增加首轮模型调用，让模型提供工具调用请求，再复用B完成执行与续答，组成固定两步流程。继续同阶段stage4_tool_flow.py，不改已验收函数；只实现新占位ask_with_tool(client, question: str, *, on_metadata=None) -> dict。

最多三个概念：①tools声明能力，模型返回tool_calls描述本次意图；首轮required表示至少一个调用，本项目单调用上限仍由程序校验；②组合已验收函数：类似Kotlin UseCase复用另一段业务流程，B已负责工具执行，不在C再执行一次；③固定流程有清楚终点：首轮要求调用，续答none要求答案，正常两次create、一次工具，异常停止，无自主循环。

导师提供build_initial_tool_request(question)：复用当前预算和工具schema，首轮仅system/user，tool_choice=required；首轮不输出最终五字段答案，所以不携带response_format。首轮七字段为model/messages/stream/max_completion_tokens/reasoning_effort/tools/tool_choice，模型kimi-k3、非流式、4096／low保持。最终续答仍由B带JSON Mode输出五字段，不修改B请求构造。

导师提供read_tool_call_response(response)：检查单项choices及finish_reason=tool_calls，将SDK message.to_dict()转为完整独立消息，保留tool_calls和reasoning_content等字段；必须assistant及非空调用列表。不在这里执行工具或重写参数校验；未知工具、坏JSON、多调用由原执行器拒绝。

学员只实现以下编排：

1. 用build_initial_tool_request(question)先校验并构造首轮请求；on_metadata非None时须callable，否则TypeError，校验完成前零SDK调用。
2. 使用传入client.chat.completions.create(**request)请求首轮一次。SDK异常原样传播，没有响应就不通知元数据，不自行重试或创建／关闭client。
3. 收到响应后，有回调就先调用on_metadata(extract_response_metadata(response))，再交read_tool_call_response提取完整assistant。None时跳过提取；首轮失败仍保留已收到的统计；回调异常原样停止。
4. 把同一client、原question、完整assistant消息和同一个on_metadata交给ask_after_tool，恰好复用一次，直接返回其已校验五字段dict。不要在C再调用lookup_place或execute_tool_request，也不要重写B的消息回填、JSON解析或资源管理。

最小类型流（示意而非完整实现）：`SDK响应对象 → read_tool_call_response(response) → 完整assistant dict → ask_after_tool(...) → 五字段答案dict`。第一份模型回复提出调用，第二份才是答案，不能把首轮content直接送最终答案JSON解析器。

本课为明确的工具查询路径：若首轮直接stop、length、包络错误或无调用则ValueError并停止，不回退成直接回答；合法调用中的坏参数／未知工具／多调用由B拒绝，不发第二次请求。工具失败不续答；续答失败不再执行或发第三次请求。首轮required只要求至少一次，模型可能输出多调用，因此程序的单次限制仍有作用。

正常路径两次create、一次lookup_place，元数据回调按tool_calls／stop顺序各一次，保留两份None／0及原值，不覆盖、推算或自动合并。此处限制应用层方法调用；传入client的SDK自动重试需由调用方配置为0，已有真实入口及本检查的SDK内存客户端均采用零重试。本课不增加真实客户端入口或付费调用。

运行`.venv/bin/python -B test/check_s4_06c.py`，实际占位 **3/13、退出码1**：两个已提供的辅助与S4-06B的13项及此前回归通过；目标13/13、实现后--demo退出码0。默认CLI继续保留B的基础预览，本课完整流程由--demo驱动；不读取.env／真实Key、请求头或会话，不连接模型。

检查包含假client＋真实SDK DTO，以及真实SDK的两次内存HTTP序列化；实际临时正向13/13、演示成功，重复执行工具5/13、晚记录首轮统计11/13、遗漏回调透传8/13，均检出。参考实现不写入学员业务文件，不计完成。演示mode=model和13/4/17、9/4/13都是假响应字段，不能填入真实评估。

完成后提交检查和--demo输出，并解释“为什么ask_with_tool中不应该再直接执行lookup_place？”验收后同轮布置S4-07及检查、更新记录并上传。本课真实请求计划0次；E14/E15的已有正文和理由仍可补录，不为补证据重跑。

2026-11-04查询[Kimi K3工具调用与完整assistant要求](https://platform.kimi.com/docs/guide/kimi-k3-quickstart)，确认required要求至少一个调用、工具结果按tool_call_id关联并保留完整消息；本地SDK 3.37.0的ToolChoice类型与DTO核对，内存传输验证两轮字段。保留现有模型和依赖，不因文档出现其他模型而升级；没有Kimi真实生成或收费验证结论。

2026-11-04：学员提交ask_with_tool，初验编排源码f64c1e3f实际通过test/check_s4_06c.py **13/13、退出码0**及--demo。随后学员整理实现、移除不可达尾部代码，当前849978d5再次实际13/13、退出码0，作为本轮验收版本。两次SDK方法调用、复用B、单次工具、完整消息、双响应元数据、异常停止、真实SDK内存HTTP与旧回归通过；S4-06C离线程序验收完成，未连接模型。

学员对C职责划分方向正确；导师补充不重复lookup_place的关键是B已校验并执行。直接调用工具本身不必然参数错误，即使参数正确也可能造成重复执行。此处是单次澄清，理解迁移待后续观察，不据测试通过标全面掌握。

## S4-07：已知失败的应用结果（离线已验收）

一个30～60分钟目标：在已验收的抛异常流程外，增加调用方可展示的成功／失败结果，保留已经发生的响应统计。新建同阶段stage4_tool_app.py，仅负责这一边界；原流程模块继续抛异常，便于组合与调试，不改S4-06C或工具模块。

最多三个概念：①Python用try/except按异常类捕获，类似Kotlin try/catch；这里只转换约定类型，未知错误继续传播；②成功／失败结果类似Kotlin Result或sealed class，但Python dict不强制字段，使用提供的构造函数固定结构；③失败不撤销已有响应，responses在调用前创建，异常时保留已有记录，不清空或补造0。

导师提供ERROR_MESSAGES、success_result(answer, responses)、failure_result(code, responses)及只展示格式的main。只由学员实现run_tool_question(client, question: str) -> dict；这层使用已有官方SDK的APIError类，但不创建客户端或读取配置，不增加新依赖。

结果恰好四字段：

| 字段 | 成功 | 已知失败 |
| --- | --- | --- |
| ok | True（bool） | False（bool） |
| answer | C返回的已校验五字段答案 | None，不回退mock或旧答案 |
| error | None | 恰好code/message，使用提供的固定文案 |
| responses | 按发生顺序保留每次响应的四字段统计 | 同样保留失败前已经收到的统计，可能0／1／2份 |

实现顺序：先创建本次独立responses列表；question非str或strip后为空时直接failure_result("invalid_input", responses)，零流程／零SDK调用。合法问题进入try，调用ask_with_tool(client, question, on_metadata=responses.append)恰好一次；成功交给success_result。

| 来源 | error.code | 固定message |
| --- | --- | --- |
| 非str／空白问题 | invalid_input | 问题必须是非空字符串。 |
| APIError及其子类 | api_error | 模型请求失败。 |
| ValueError（含JSONDecodeError） | invalid_output | 模型返回的工具请求或回答不符合约定。 |
| RuntimeError | execution_error | 工具流程执行失败。 |

各except分支把同一responses交给failure_result，不打印／回传str(error)、SDK响应、异常对象或请求详情。execution_error只表示流程执行失败，不声称一定定位到工具本身。合法未命中的False/None是正常业务结果，仍沿用C续答成功，不转换成异常。

本函数不接外部on_metadata，而是拥有内部收集器，因此不把调用方观察器异常误当模型输出错误。TypeError、AttributeError、OSError等未约定异常，以及KeyboardInterrupt、SystemExit继续原样传播；不要加except Exception或except BaseException统吞。已知类型通过结果给调用方，其余由上层进一步处理，后续服务化再补日志与HTTP映射。

Python最小语法示例：`except ValueError:`可以处理该类型及子类；JSONDecodeError也属于ValueError。本课不用读取错误文本判断类别。SDK连接、超时及HTTP状态类请求异常可由APIError捕获，并不是所有Python异常都属于APIError。

成功通常保留两份统计；首轮包络／参数无效常已收到一份；第二轮JSON失败已有两份；SDK无响应时不添加该次统计。None仍是未知、0仍是响应明确值，不从失败或空列表推断免费。两种构造函数已经deepcopy答案与统计，保证外部修改及后续回调不污染已返回结果；不要复用全局列表。

运行`.venv/bin/python -B test/check_s4_07.py`，实际占位 **2/12、退出码1**，提供的格式与C的13项及此前回归通过；目标12/12，实现后--demo退出码0。检查覆盖正常／未收录、输入、两阶段输出失败、真实SDK异常类、RuntimeError、未知异常传播、统计None/0和快照，不运行真实请求。

检查器临时控制实测：正向12/12、演示成功；失败清空统计9/12、统吞Exception11/12、回显SDK错误11/12，均检出。参考实现只在临时目录，不写入学员函数，不计完成。演示mode及token数仍是假值，真实请求计划0次。

完成后交检查与演示输出，并说明“为什么续答JSON失败时，返回的responses仍可能有两条？”通过后同轮布置S4-08阶段评估及检查、更新记录并上传。E14/E15既有回答正文与判定理由仍待补，不重复调用；本课不将临时JSON实验文件或会话缓存纳入上传。

2026-11-04核对[官方SDK错误处理](https://developers.openai.com/api/reference/python#handling-errors)及本地SDK 3.37.0的_exceptions.py，确认APIError、APIConnectionError、APITimeoutError、APIStatusError层次和本课模拟构造；保持现有版本。请求结果和模型真实质量分别记录，当前无新增收费或史实核实结论。

2026-11-04：学员提交run_tool_question，边界源码bd40e79d实际通过test/check_s4_07.py **12/12、退出码0**，--demo退出码0。非法输入零流程、成功／合法未命中、指定异常映射、固定文案、统计保留与None/0、未知异常传播、快照和旧回归均通过，S4-07离线程序验收完成。流程d9bdec25相对前版只增加注释／空行，随旧回归通过；学员检查脚本增加一行调试输出，原断言未删改。未读取或执行临时answer.json，新增真实模型请求0次。

学员能指出模型已经返回调用参数及响应；导师明确对应两次响应：首轮工具调用请求、第二轮续答正文。第二轮本地JSON解析失败不撤销这两次响应或统计。当前解释方向正确，理解迁移留给阶段评估，不据12/12标全面掌握或真实模型质量通过。

## S4-08：阶段4离线对比与报告（保留布置基线，现已验收）

一个30～60分钟目标：独立记录一组可重复评估，区分“程序符合预期”和“真实模型回答可靠”。本课只填写导师提供模板STAGE4_REVIEW.md，不修改业务代码或检查脚本；阶段汇总test/check_stage_4.py已经提供，复用S4-07的12项及此前整链。

最多三个概念：①预期与实际：业务失败可以是正确测试结果，T3按约定返回invalid_output即场景符合预期；②受控对比：D1／T1同一问题走不同程序路径，比较调用步骤与模拟统计，假回答不能用于推断真实准确率或延迟；③证据范围：离线逻辑、真实模型质量、资料来源、费用分别记录，未知统计不补0。可类比Android的Mock Repository测试与真实后端验收各有覆盖；Python字典里的ok只表达本次业务结果，不是评估通过率。

先运行`.venv/bin/python -B test/check_stage_4.py --demo`；脚本不会改报告或请求模型，会给四行测量及评估代码指纹。指纹覆盖四个阶段4业务模块和本汇总脚本，用于定位快照，不是Git提交号，也不代表SDK环境或远端模型版本。

| ID | 路径与用途 | 观察重点 |
| --- | --- | --- |
| D1 | 同一问题直接结构化问答 | 一次SDK方法调用，无工具执行 |
| T1 | 同一问题固定工具流程 | 两次SDK方法调用，一次本地目录查询 |
| T2 | 工具查询未收录名称 | 合法未命中仍是正常业务结果 |
| T3 | 工具流程续答JSON无效，首轮usage缺失 | invalid_output符合预期；已有两条响应记录，完整模拟total合计未知 |

所有回答均为预先构造的假SDK响应，目录是虚构fixture；正常记录中的13、30等只是模拟token数，不能当真实金额。本课没有对真实回答做质量比较，也未测真实延迟。场景按预期处理不等于业务全部成功，更不等于模型准确率100%。

只修改STAGE4_REVIEW.md：

1. 将--demo输出的8位评估代码指纹填入对应行，按测量填写表格的实际状态、SDK调用数、工具执行数、响应条数、模拟total合计；保留四个ID、路径和预期状态。统计不完整时写“未知”，不能把已知部分当完整总量。
2. 用自己的话替换“对比结论”“失败与统计”“验证边界”三个占位段落，每段至少40字符。解释额外调用换来什么信息、哪些情况下值得；为什么T3业务失败仍能通过场景校验且合计未知；目前哪些能力／质量尚无证据。
3. 保留本报告离线模拟、真实质量待验证、实际费用未知的范围声明。已有E14/E15真实输出可另在评估记录补录，不重跑、不把自评替代导师核实。

再运行`.venv/bin/python -B test/check_stage_4.py`。实际模板基线 **2/4、退出码1**：程序全链与四场景通过，报告表／指纹和三段结论待填；目标4/4、退出码0，并经导师人工审阅结论后才完成。脚本最后一项只确认填写完整，不自动评判观点，更不验证真实模型质量。--demo应退出0。

检查器在临时工程实测：结构完整的参考报告4/4；把T1次数写错3/4、将真实质量声明改为已验证3/4，均检出。参考段落只用于验证检查器，未写入学员报告，也未获得结论人工验收，不能计学员完成。布置当时的实际报告是占位模板；最终验收见下。

完成后提供汇总结果及报告，并回答“为什么T3业务失败，却仍可以算符合预期的测试场景？”导师会读取报告审阅事实与结论；通过后才自动进入S5-01简单资料检索，创建当前需要的新阶段入口和检查。阶段4离线程序可用于后续学习，不据此宣称真实模型效果或Agent已经完成。本课真实模型请求计划0次。

2026-11-04：学员提交STAGE4_REVIEW.md，导师实际运行test/check_stage_4.py **4/4、退出码0**，指纹b3dcb883；三段结论人工审阅通过。四行测量与受控场景相符，能区分预期业务失败、统计不完整及真实质量待验证。此处只验收离线评估报告及已测程序行为，不标全面掌握、模型准确率或Agent能力已验证；本轮真实模型请求0次。

导师补充两处边界：直接问答理论上也依赖system/user提示词与上下文，不能字面理解为仅靠模型参数；本课D1实际仍是假响应。天气／新闻只是其他数据工具的应用例子，当前lookup_place只读虚构目录，没有这些能力。报告原文保留，澄清另记，不新增“反复出错”结论。

## S5-01：建立并加载可追溯资料集（保留布置基线，现已验收）

一个30～60分钟目标：把本地资料JSON加载成统一数据，为S5-02关键词检索准备输入。新阶段独立入口stage5_retrieval.py，导师已提供CLI、URL格式辅助和load_documents占位；旧ask_turn及阶段4保持。只实现load_documents(path: Path) -> list[dict[str, str]]，并在knowledge_sources.json保留大运河示例、增加一条至少30字符的中文概述（建议30～120字符）。

必要知识三个：①Path与UTF-8文本读取，类似Kotlin File.readText(Charsets.UTF_8)，Python读取后仍需json.loads；②解析成功与数据契约校验分开，Python类型标注不会自动验证文件中的字段；③可追溯资料必须保留id/title/text/source_url，URL存在不等于概述受支持，更不等于回答已核实。不要将阶段4虚构fixture搬成真实资料。

最小读取示例（只展示读取和解析，校验由学员完成）：

```python
raw_text = path.read_text(encoding="utf-8")
raw = json.loads(raw_text)
```

加载器契约：顶层list，空列表合法；条目dict恰好四字段，均为str，保存strip后的非空值；清理后id唯一，同一source_url可有多条资料。URL调用已提供is_https_source检查。内容错误抛ValueError，坏JSON可自然传播JSONDecodeError（其属于ValueError）；文件不存在／目录／权限等错误保留OSError子类。函数只返回或抛错，不打印、不联网、不写盘；CLI已提供，成功0，文件／内容失败1。资料文件至少两条是本课收集目标，不意味着通用加载器要拒绝[]。

2026-11-04导师读取并核对[UNESCO大运河简介](https://whc.unesco.org/en/list/1443/)开头内容，示例text为人工中文概述，保留时代和运输用途，并非原文引述或模型生成。第二条建议阅读[UNESCO长城简介](https://whc.unesco.org/en/list/438/)开头介绍后自行概述，写明相应时代；也可选其他可核对的官方资料。不要整页复制；只写来源实际支持的简短内容，来源支持程度在验收时人工逐条核对。程序不联网抓网页。

运行入口：`.venv/bin/python -B stage5_retrieval.py`；自检：`.venv/bin/python -B test/check_s5_01.py`。实际占位基线 **2/10、退出码1**（入口导入、阶段4整链回归通过）；目标10/10、退出码0、CLI输出至少两条资料，并通过人工来源核对。检查覆盖中文与空白、空集、结构／字段／URL、重复id、坏JSON／文件错误、CLI和阶段4汇总4/4。离线通过不证明史实正确。

检查器临时控制：仅临时参考实现与控制资料10/10；删除重复id拒绝后9/10，能定位对应错误。参考实现和第二条控制资料不写入学员工程，不计学员成果。布置当时入口41c1c1f0为占位、资料仅导师示例一条；最终结果见下。

完成后保存两文件、提供检查结果及CLI输出，说明“为什么保存了source_url，还不能直接把内容标为已核实？”通过后同轮提供S5-02关键词检索任务和检查。当前不接模型、向量库或框架，不发起付费调用；E14/E15既有正文／判定理由仍可补录，不要求重复运行。

2026-11-05：学员实现load_documents，入口eb7044e9由导师实际运行test/check_s5_01.py **10/10、退出码0**。json.load配合with path.open合法，四字段类型／清理、清理后id去重、空列表、URL辅助及文件错误边界通过；实际CLI退出0、输出42条资料，stderr为空。导师增加下一课占位与CLI后入口24246ac0，加载函数逐字保留，S5-01及此前整链仍10/10通过；不计新检索已完成。

学员提交42条中文概述，资料SHA256为8978e73c1bca35511c95fb2342f97a96901e3e08491832b32494f2d471904a6d。2026-11-05导师逐条读取所列42个UNESCO页面的开头简介，对照主题、时代、数量和用途，未发现阻碍本课的来源支持问题；具体URL随knowledge_sources.json保存。这个结论只表示当前概述受所列页面支持，未做独立多来源史实核验，不声称作者身份或全面掌握。学员指出链接可能非法／不准确；导师补充即使URL格式正确且页面存在，也需核对页面是否支持文字。此处为单次解释待后续迁移，不标反复出错。

## 当前 S5-02：关键词检索基线（待实现）

一个30～60分钟目标：在已加载资料中找出关键词命中项，返回可追溯片段。仍在stage5_retrieval.py，只实现search_documents(documents, query, top_k=3)占位；load_documents、知识文件、旧阶段和检查断言保持。CLI的--query／--top-k已由导师接线。当前不接模型、向量库或框架。

必要知识最多三个：①查询归一化：casefold处理大小写，split()按空白分词，set去重；Python无参数split自动合并连续空白，不等同于Kotlin split(" ")的行为，casefold也比普通lowercase更全面；②命中计分和稳定排序：每个不同词命中计1分，按分数降序，同分按输入顺序，类似Kotlin sortedByDescending保留同分先后；③检索边界：无命中只表示当前资料和匹配规则没找到，不说明现实不存在；得分不是准确率或来源可信度。

例如查询“水利 交通 水利”只有两个不同词，含两词的资料得2分，只含“水利”即使出现十次也只得1分。这是明确可解释的基线，中文需要手动以空格分开关键词，不做自动分词、去标点、同义词或语义匹配。后续S5-03再评估漏检和误检。

契约：documents由加载器验证，本函数只处理内存，不额外读文件；query非str抛TypeError、清理后空白抛ValueError。top_k必须为正int，bool及其他类型抛TypeError，0／负数ValueError；空资料集也先检查参数。查询casefold().split()后去重，资料仅在title与text中大小写无关子串匹配，两字段以换行分隔，不能搜id／URL或拼出跨字段词。命中任一词且score>0才入选。

结果list每项保留原id/title/text/source_url，加int字段score；每次新建dict，不给输入加字段或重排输入。四个来源字段都是不可变字符串，复制外层dict即可隔离，参考dict.copy()或新建字典。按score降序且同分稳定，再取前top_k项；默认3，超过命中数不补假结果。空集或无命中返回[]。函数不打印、不写文件、不请求模型、不生成答案。

可用sorted(..., key=..., reverse=True)表达排序；不要求特定写法，按行为验收。CLI无--query时仍输出加载资料；有查询时输出五字段命中列表；无命中[]退出0，空白查询或非正top_k显示“资料检索失败”并退出1。提供的CLI与已验收加载器无需学员改动。

```bash
cd /Users/leon/workspace/PythonProject/history-ai-agent
.venv/bin/python -B stage5_retrieval.py --query "水利 交通" --top-k 3
.venv/bin/python -B stage5_retrieval.py --query "青岚朝"
.venv/bin/python -B test/check_s5_02.py
```

实际占位基线 **2/12、退出码1**，入口导入与S5-01的10项及此前整链通过；目标12/12、退出码0，两个CLI查询分别输出命中列表／[]并退出0。当前源码24246ac0包含导师占位与接线，search_documents尚未实现。全部检查离线，不读.env、Key、实际会话或请求模型。

检查器临时正向12/12；去掉查询去重后11/12，定位到不同词计分。参考实现只在临时工程，未写入学员函数。检查覆盖正常、无命中、空集、类型／top_k、大小写、重复词、稳定顺序、来源保留、隔离及CLI和旧回归。分数或脚本通过不能当作真实检索质量评估。

完成后保存入口、提供检查与两个CLI输出，并说明“为什么查询中重复写‘水利’，不应该让某条资料的分数变高？”通过后同轮布置S5-03检索效果评估及检查，维护固定用例中的命中／误检／漏检；本课模型请求计划0次。E14/E15既有正文和判定理由仍待补，不重复付费。
