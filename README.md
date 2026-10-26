<!-- About 简介（推送后填写到仓库 About 栏）：
技术博客专家，技术主题一句话成文，代码示例自动校验 ｜ 一键安装：/plugin marketplace add lhg-plugs/lhg-tech-blog
-->
<!-- topics（推送后打）：claude-code, claude-plugin, agent-skills, tech-blog, writing -->

# lhg-tech-blog：技术主题一句话 → 能传播的技术文章

> **一句话介绍**：给 AI 助手装上"技术博客专家"——技术主题一句话输入，大纲、初稿、代码示例自动校验、多平台排版、发布前自查一条龙，帮程序员把"会做的东西"写成"能传播的文章"。
>
> **一键安装**：在 Claude Code 里运行
> ```
> /plugin marketplace add lhg-plugs/lhg-tech-blog
> /plugin install lhg-tech-blog@lhg-plugs
> ```

## 它是什么

`lhg-tech-blog` 是一个 Claude Code 插件（plugin 为主、skill 为辅）：

- **5 个命令**（小白入口）：`tech-blog` 一句话成文主流程，`outline` 先出大纲，`codecheck` 示例可运行性校验，`reformat` 掘金/知乎/公众号三版排版，`audit` 发布前自查
- **5 个平台中立 skill**（方法论，可移植到豆包/Workbuddy 等 agent 平台）：选题大纲、初稿写作、示例代码规范与校验、多平台排版、发布前自查
- **3 个专家 agent**：写手、代码校验员、独立审稿人
- **2 个 hooks**：发布前 blocker 硬拦截、写稿后轻提示（均可一键豁免，不骚扰）
- **40 条确定性审计规则**：纯 Python、零第三方依赖，覆盖代码块/标题/结构/引用/卫生五维

定位：开发者个人品牌向——把"你会做的东西"变成"别人愿意读、读完能动手"的文章。

## 5 个命令用法

| 命令 | 作用 | 示例 |
|---|---|---|
| `/lhg-tech-blog:tech-blog` | 一句话 → 完整文章（澄清→大纲→初稿→代码校验→排版→自查） | `/lhg-tech-blog:tech-blog "Python 重试装饰器"` |
| `/lhg-tech-blog:outline` | 只出大纲（读者定位+五段式+标题三备选），确认后再写 | `/lhg-tech-blog:outline "讲透 Redis 缓存击穿"` |
| `/lhg-tech-blog:codecheck` | 示例校验：语法检查 + Python 真实运行冒烟 | `/lhg-tech-blog:codecheck drafts/` |
| `/lhg-tech-blog:reformat` | 一份初稿 → 掘金/知乎/公众号三版排版 | `/lhg-tech-blog:reformat draft-retry.md` |
| `/lhg-tech-blog:audit` | 发布前自查（40 条审计 + 人工终审六项） | `/lhg-tech-blog:audit drafts/` |

## 质量分档

- **默认 = 极速档**：流程完整但评审轮次少，确定性审计必跑。适合日常输出、快速成稿。
- **`--quality` = 品质档**：增加独立审稿人复查、多轮打磨、朗读测试。**诚实说明**：品质档 token 消耗约为极速档的数倍，请确认接受再使用。

## 自查说明

自查 = 确定性脚本（机器）+ 人工终审清单（人）：

1. 先跑 `scripts/audit/tb_audit.py`（40 条规则），零第三方依赖；
2. 发现分三级：**blocker**（必须修，发布前 hook 会拦截）、**warning**（修或写豁免理由）、**nit**（顺手修）；
3. 再按 `lhg-tb-review` 的人工终审六项过一遍脚本抓不到的（标题兑现、数字出处、坑是否真实）。

blocker 清零才算写完；为清零改规则算作弊，不许。

## 目录结构

```
lhg-tech-blog/
├── .claude-plugin/          # plugin.json（插件清单）+ marketplace.json（本仓即市场）
├── commands/                # 5 个命令：tech-blog / outline / codecheck / reformat / audit
├── skills/                  # 5 个平台中立 skill（outline/draft/code/format/review）
├── agents/                  # 3 个专家 agent（writer / code-verifier / reviewer）
├── hooks/                   # 2 个门：发布前 blocker 拦截 / 写稿后轻提示 + 豁免说明
├── scripts/audit/           # 40 条确定性审计规则（零第三方依赖）
├── fixtures/                # 冒烟测试用例（坏/好对照，坏例命中全部 40 条）
├── smoke_test.py            # 一键冒烟测试
├── ATTRIBUTION.md           # 灵感来源与许可声明
└── LICENSE                  # MIT
```

## 什么时候用 / 什么时候不用（FAQ）

**什么时候用：**

- 你会做一个东西，但不知道怎么把它写成别人愿意读的文章时 → 用 `/lhg-tech-blog:tech-blog`
- 你有选题但大纲总写散、"坑"章节憋不出来时 → 用 `/lhg-tech-blog:outline` 先出施工图
- 你文章里的代码示例自己都没跑过，心里没底时 → 跑 `/lhg-tech-blog:codecheck`，能跑的必须跑通
- 你要一稿多发掘金/知乎/公众号，怕各平台排版翻车时 → 用 `/lhg-tech-blog:reformat`
- 你要发之前做一次"署名级"检查时 → 跑 `/lhg-tech-blog:audit`，结论只许"通过/不通过"
- 你想给团队立一套"技术文章发布前必须过"的纪律时 → 它的 hooks 硬门开箱即用

**什么时候不用：**

- 你要的是英文技术博客 → 规则（错别字表、中英空格、平台生态）全部按中文技术社区编写
- 你希望 AI 直接替你点"发布" → 本插件永远不自动发布，发布必须由你亲手完成（这是设计，不是缺功能）
- 你的文章没有代码示例（如纯观点评论）→ 代码校验部分用不上，但大纲/写作/自查 skill 依然可用
- 你希望 AI 自由发挥、不接受任何硬门 → 它的发布拦截会让你烦（可关，但那就别装它）

## 风险提示（诚实说明）

1. **示例运行环境**：`codecheck` 在本机真实运行 Python 示例，结论只对"当前机器+当前环境"负责。换机器、换版本请重跑；依赖外部服务（真实 API、数据库）的示例只能标"示意"，跑不了就是跑不了。
2. **AI 味**：脚本的反 AI 味规则是启发式（连接词计数、句长等），能抓明显的，抓不到"读着像 AI 但词表没覆盖"的。最终质检是"朗读测试"——大声读一遍，拗口就重写。
3. **平台规则时效**：掘金/知乎/公众号的排版与推荐规则会变（如知乎外链策略），`lhg-tb-format` 的对照表是 2026-10 快照，发现过时请按 skill 里的反馈渠道提 issue。
4. **不替你署名**：插件保证流程与底线，但文章的观点、案例真实性由你负责。"坑"章节编造亲身经历，被读者发现一次，信任归零。

## lhg-plugs 插件矩阵

| 插件 | 一句话 | 安装 |
|---|---|---|
| [lhg-tech-blog](https://github.com/lhg-plugs/lhg-tech-blog) | 技术博客专家：技术主题一句话成文，代码示例自动校验 | `/plugin install lhg-tech-blog@lhg-plugs` |
| *完整矩阵见* | [lhg-plugs/lhg-fullstack 模板仓 README](https://github.com/lhg-plugs/lhg-fullstack) | |

## 自检与反馈

本插件自带质检：每次使用后可跑 `python3 smoke_test.py` 一键验证（JSON 合法、skill/command/agent 完整性、40 条规则、fixtures 命中、hooks 行为）。

发现 bug 或有改进建议，以 `[QC] <一句话问题>` 为标题提交到 https://github.com/lhg-plugs/lhg-tech-blog/issues，正文写清"复现步骤 → 实际表现 → 期望表现"。

## 出品：刘洪光

本插件由真人出镜 IP「刘洪光」（安徽合肥）出品，归属 [lhg-skills](https://github.com/lhg-skills)。

- GitHub 主页：https://github.com/lhg-skills —— 全部 skill 开源在此，欢迎 star
- 抖音：搜「刘老师讲AI实战」
- 微信：lhgsmsw
