# 灵感来源与致谢（Attribution）

本插件的**方法论灵感**来自以下优秀的开源项目，**所有实现代码、检测规则与文案均为原创**，未复制任何第三方的原文案。

| 项目 | 作者 / 组织 | 许可 | 链接 | 借鉴了什么思路 |
|---|---|---|---|---|
| professional-skills | Kaos599 | MIT | https://github.com/kaos599/professional-skills | `technical-content-writer` 的"锚定→校准→成型→初稿→打磨→门禁→发布"流水线思想；`anti-slop-writing` 的"AI 味按模式簇计数、只做减法不够还要把人放回去"的问题意识。本插件的命令流水线与反 AI 味规则受其启发，**实现与文案全部原创** |
| Sentry skills | Sentry 团队（getsentry） | Apache-2.0 | https://github.com/nano-chmod-x/skills | `blog-writing-guide` 的"按自家博客标准做审稿清单"模式；`doc-coauthoring` 的结构化协作流程思想。本插件 `lhg-tb-review` 的人工终审清单模式受其启发 |
| agent-skills（docs-writing） | mblode（经 marchelero/open 转引） | 许可未单独核实 | https://github.com/marchelero/open/blob/HEAD/.agents/skills/docs-writing/SKILL.md | 文档类型先分类再定规则（教程/指南/解释/参考四象限）、"示例代码必须可运行"、内容卫生检查的思想。本插件审计规则的分类框架与代码可运行性校验受其启发 |
| lhg-wechat-article | 刘洪光（lhg-plugs） | MIT | https://github.com/lhg-plugs/lhg-wechat-article | 同组织写作类插件的工程结构：规则注册表 + JSON/text 双输出 + fixtures 坏/好对照 + hooks 硬门。本插件直接复用该工程模式（**代码为本插件独立实现**） |

## 声明

1. **借鉴思路，实现与文案均为原创**：以上项目的具体文案、规则原文、代码实现均未被复制。本插件的 skill 方法论文案、40 条审计规则、命令流程均为独立撰写。
2. **许可合规**：思路借鉴不涉及代码复制；本文件即为保留声明的一部分。mblode agent-skills 的许可未单独核实，本插件未复制其任何原文，仅借鉴"分类→规则"的通用方法论思想。
3. **商标与归属**：各项目名称与作者署名归其各自所有者所有。

## 本插件自身的许可

本插件原创部分采用 MIT 许可（见 `LICENSE` 文件），版权所有：刘洪光（https://github.com/lhg-skills）。
