#!/usr/bin/env python3
"""lhg-tech-blog 轻提示：写完/改完稿件 .md 文件后，做一次快速自检。

触发：PostToolUse / Write|Edit。只对 .md 文件生效；发现"代码块缺语言标记、
TODO 残留、围栏未闭合"这类低级问题时，用 additionalContext 给一句提示，
不拦截、不打断。

逃生：LHG_TB_HOOKS_OFF=1（与发布硬门共用一个开关）。
设计原则：只读被写的文件，不扫描全目录；内部出错 fail-open 静默。
零第三方依赖。
"""

import json
import os
import re
import sys


def quick_check(text):
    hints = []
    lines = text.split("\n")
    in_fence = False
    for i, ln in enumerate(lines, start=1):
        m = re.match(r"^\s*```\s*([A-Za-z0-9+#_.-]*)\s*$", ln)
        if m:
            if not in_fence and not m.group(1):
                hints.append("第 %d 行代码块缺语言标记" % i)
            in_fence = not in_fence
    if in_fence:
        hints.append("围栏 ``` 疑似未闭合")
    for i, ln in enumerate(lines, start=1):
        if re.search(r"\b(TODO|FIXME|XXX)\b", ln):
            hints.append("第 %d 行残留 TODO 标记" % i)
            break
    return hints


def main() -> int:
    if os.environ.get("LHG_TB_HOOKS_OFF") == "1":
        return 0
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        return 0
    tool_input = payload.get("tool_input", {}) or {}
    path = tool_input.get("file_path", "") or ""
    if not path.endswith(".md"):
        return 0
    if not os.path.isfile(path):
        return 0
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except Exception:
        return 0
    hints = quick_check(text)
    if not hints:
        return 0
    ctx = ("lhg-tech-blog 写稿提示（%s）：%s。跑 /lhg-tech-blog:audit 做完整 40 条自查。"
           % (os.path.basename(path), "；".join(hints[:5])))
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": ctx,
        }
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
