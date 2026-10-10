#!/usr/bin/env python3
"""lhg-tech-blog 硬门：发布相关命令执行前跑稿件审计，有 blocker 则拦截。

触发：PreToolUse / Bash。先判断本次 Bash 命令是否与"发布"相关
（publish / 发布 / 同步到掘金知乎 / deploy），不是则 0 开销直接放行；
是则对稿件目录运行插件自带的 tb_audit.py，有 blocker 时拒绝执行。

逃生方式（按推荐度排序）：
  1. 跑 `/lhg-tech-blog:audit` 修掉 blocker 后重新执行（推荐）。
  2. 紧急情况：LHG_TB_HOOKS_OFF=1 <原命令>（单次豁免本次 hook）。
  3. /plugin disable lhg-tech-blog（整个插件停用，hooks 不再触发）。

设计原则：脚本内部出错（找不到审计脚本、超时、稿件目录不存在等）时
fail-open 直接放行，不因插件自身故障骚扰用户。
零第三方依赖。
"""

import json
import os
import re
import subprocess
import sys

AUDIT_TIMEOUT = 60
PUBLISH_RE = re.compile(
    r"publish|发布|同步到|deploy|上线|juejin|zhihu|wechat.*article", re.I)


def main() -> int:
    # 逃生开关
    if os.environ.get("LHG_TB_HOOKS_OFF") == "1":
        return 0

    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        return 0  # 输入解析失败：fail-open

    tool_input = payload.get("tool_input", {}) or {}
    command = tool_input.get("command", "") or ""

    # 非发布相关命令：快速放行
    if not PUBLISH_RE.search(command):
        return 0

    plugin_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    script = os.path.join(plugin_root, "scripts", "audit", "tb_audit.py")
    if not os.path.isfile(script):
        return 0  # 审计脚本缺失：fail-open，不拦截用户

    drafts = os.environ.get("LHG_TB_DRAFTS", "")
    if not drafts:
        project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "") or os.getcwd()
        cand = os.path.join(project_dir, "drafts")
        drafts = cand if os.path.isdir(cand) else ""
    if not drafts:
        return 0  # 没有稿件目录：fail-open

    try:
        r = subprocess.run(
            [sys.executable, script, "--target", drafts, "--format", "json"],
            capture_output=True, text=True, timeout=AUDIT_TIMEOUT)
        data = json.loads(r.stdout)
    except Exception:
        return 0  # 审计跑不起来：fail-open

    blockers = [f for f in data.get("findings", [])
                if f.get("severity") == "blocker"]
    if not blockers:
        return 0

    lines = ["%s（%s:%s）" % (b["rule_id"], os.path.basename(b["file"]),
                              b["line"]) for b in blockers[:8]]
    reason = ("检测到 %d 个 blocker，发布已拦截。先跑 /lhg-tech-blog:audit 修掉：\n"
              % len(blockers) + "\n".join("· " + l for l in lines))
    if len(blockers) > 8:
        reason += "\n· …等共 %d 个" % len(blockers)
    reason += ("\n逃生：LHG_TB_HOOKS_OFF=1 <原命令>（单次豁免）。"
               "为清零而改规则算作弊，不许。")
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
