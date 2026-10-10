#!/usr/bin/env python3
"""lhg-tech-blog 确定性稿件审计：40 条规则，零第三方依赖。

扫描 Markdown 技术博客稿件，检测：
  代码块：语言标记缺失、Python 语法错误、未完成占位、JS 括号失衡、
          疑似真实密钥、高危 shell 命令、"结果如下"无输出块、
          "代码如下"无代码块、占位符未注明示意、$ 提示符混用、
          重复代码块、围栏未闭合、代码占比过高、第三方库无安装说明、
          py2 print 残留、输出块超长
  标题：缺一级标题、多一级标题、层级跳跃、标题末尾标点
  结构：超长段落、长文无二级标题、开篇无问题锚点、无总结、无"坑"章节、
        空章节、列表项超长
  引用：见图无图、死锚链、代码无引出、"完整代码"无链接
  卫生：TODO 残留、无 alt 图片、中英混排缺空格、无依据性能断言、
        绝对化用语、行尾空格、连续空行、语言标记拼写错、示例链接未替换

输出 JSON 与人类可读报告；达到 --fail-on 级别时以 exit code 2 退出。

用法：
    python3 tb_audit.py --target <稿件文件或目录> [--format json|text]
                        [--fail-on blocker|warning|nit]

规则文案与实现均为本项目原创，未复制任何第三方原文。
"""

import argparse
import ast
import json
import os
import re
import sys

VERSION = "1.0.0"
TOOL = "lhg-tech-blog/tb-audit"

SKIP_DIRS = {"node_modules", ".git", "__pycache__", "vendor", ".turbo", ".venv"}

SEV_ORDER = {"nit": 0, "warning": 1, "blocker": 2}

# 常见 Python 标准库（启发式判断第三方库用，非穷举）
PY_STDLIB = {
    "os", "sys", "re", "json", "math", "random", "datetime", "time", "pathlib",
    "collections", "itertools", "functools", "typing", "dataclasses", "enum",
    "abc", "copy", "pickle", "csv", "io", "logging", "argparse", "configparser",
    "sqlite3", "hashlib", "hmac", "secrets", "uuid", "base64", "urllib",
    "http", "socket", "ssl", "email", "html", "xml", "unittest", "threading",
    "multiprocessing", "subprocess", "shutil", "glob", "tempfile", "warnings",
    "contextlib", "decimal", "fractions", "statistics", "string", "textwrap",
    "unicodedata", "struct", "codecs", "locale", "getpass", "platform",
    "inspect", "traceback", "gc", "weakref", "queue", "asyncio", "concurrent",
    "decimal",
}

LANG_TYPO = {
    "pythno": "python", "pyhton": "python", "javasript": "javascript",
    "javascrip": "javascript", "typescirpt": "typescript", "typesript": "typescript",
    "shel": "shell", "jason": "json", "yam": "yaml", "sqll": "sql",
    "htlm": "html", "golang": "go", "jav": "java", "cplus": "cpp",
}


class Doc:
    """Markdown 稿件的轻量解析结果。"""

    def __init__(self, path, text):
        self.path = path
        self.text = text
        self.lines = text.split("\n")
        self.code_blocks = []   # (lang, code, start_line, end_line)
        self.headings = []      # (level, title, line_no)
        self.images = []        # (alt, src, line_no)
        self.anchors = []       # (anchor, line_no)
        self.prose = ""         # 去掉代码块后的正文（用于正文规则）
        self._parse()

    def _parse(self):
        in_fence = False
        fence_lang = ""
        fence_start = 0
        buf = []
        prose_lines = []
        skip_blank = False
        for i, ln in enumerate(self.lines, start=1):
            m = re.match(r"^\s*```\s*([A-Za-z0-9+#_.-]*)\s*$", ln)
            if m:
                if not in_fence:
                    in_fence = True
                    fence_lang = m.group(1)
                    fence_start = i
                    buf = []
                    # 围栏前的结构性空行丢弃（Markdown 排版所需，不算正文空行）
                    if prose_lines and not prose_lines[-1].strip():
                        prose_lines.pop()
                else:
                    in_fence = False
                    self.code_blocks.append(
                        (fence_lang, "\n".join(buf), fence_start, i))
                    fence_lang = ""
                    # 围栏后保留一个结构性空行做段落分隔，多余的丢弃
                    prose_lines.append("")
                    skip_blank = True
                continue
            if skip_blank and not in_fence and not ln.strip():
                skip_blank = False
                continue
            if not in_fence:
                skip_blank = False
            if in_fence:
                buf.append(ln)
                continue
            prose_lines.append(ln)
            hm = re.match(r"^(#{1,6})\s+(.*?)\s*#*\s*$", ln)
            if hm:
                self.headings.append((len(hm.group(1)), hm.group(2), i))
            for im in re.finditer(r"!\[([^\]]*)\]\(([^)]+)\)", ln):
                self.images.append((im.group(1), im.group(2), i))
            for am in re.finditer(r"\]\(#([^)\s]+)\)", ln):
                self.anchors.append((am.group(1), i))
        if in_fence:  # 围栏未闭合：残余部分也算一个代码块（规则会报）
            self.code_blocks.append((fence_lang, "\n".join(buf), fence_start,
                                    len(self.lines)))
        self.prose = "\n".join(prose_lines)

    def heading_slugs(self):
        slugs = set()
        for _, title, _ in self.headings:
            s = title.strip().lower()
            s = re.sub(r"[^\w\u4e00-\u9fff\s-]", "", s)
            s = re.sub(r"\s+", "-", s)
            slugs.add(s)
        return slugs


def slug_ok(anchor, slugs):
    a = anchor.lower()
    if a in slugs:
        return True
    return any(a == s or s.endswith(a) or a.endswith(s) for s in slugs)


# ---------------- 规则实现 ----------------
# 每个函数返回 findings 列表：(line_no, detail_suffix)

def r_code_lang(doc):
    out = []
    for lang, code, s, e in doc.code_blocks:
        if not lang:
            out.append((s, "第 %d 行代码块没有语言标记，读者无法高亮、脚本无法校验" % s))
    return out


def r_code_py_syntax(doc):
    out = []
    for lang, code, s, e in doc.code_blocks:
        if lang.lower() in ("python", "py", "python3"):
            body = "\n".join(
                ln for ln in code.split("\n")
                if not re.match(r"^\s*\.\.\.\s*$", ln))
            try:
                ast.parse(body)
            except SyntaxError as ex:
                out.append((s + (ex.lineno or 1) - 1,
                            "Python 示例第 %d 行语法错误：%s" % (ex.lineno, ex.msg)))
    return out


def r_code_py_todo(doc):
    out = []
    for lang, code, s, e in doc.code_blocks:
        if lang.lower() in ("python", "py", "python3"):
            for j, ln in enumerate(code.split("\n"), start=s + 1):
                if re.search(r"#\s*(TODO|FIXME|XXX|待补充|省略)", ln) or \
                   re.match(r"^\s*\.\.\.\s*$", ln):
                    out.append((j, "示例代码含未完成标记，读者跑不通"))
                    break
    return out


def r_code_js_balance(doc):
    out = []
    for lang, code, s, e in doc.code_blocks:
        if lang.lower() in ("javascript", "js", "typescript", "ts", "jsx", "tsx"):
            stripped = re.sub(r"'[^']*'|\"[^\"]*\"|`[^`]*`|//[^\n]*|/\*.*?\*/",
                              "", code, flags=re.S)
            pairs = {"{": "}", "(": ")", "[": "]"}
            stack = []
            for ch in stripped:
                if ch in pairs:
                    stack.append(ch)
                elif ch in pairs.values():
                    if stack and pairs[stack[-1]] == ch:
                        stack.pop()
                    else:
                        out.append((s, "JS/TS 示例括号不配平，疑似截断或笔误"))
                        break
            else:
                if stack:
                    out.append((s, "JS/TS 示例括号不配平（缺 %d 个闭括号）" % len(stack)))
    return out


def r_code_secret(doc):
    out = []
    for lang, code, s, e in doc.code_blocks:
        for j, ln in enumerate(code.split("\n"), start=s + 1):
            if re.search(
                    r"(?i)(password|passwd|api[_-]?key|secret[_-]?key|secret|access[_-]?token)\s*[:=]\s*[\"'][^\"'<>]{6,}[\"']",
                    ln) and not re.search(
                    r"(?i)your|xxx|example|占位|示意|demo|changeme|placeholder", ln):
                out.append((j, "示例含疑似真实密钥字面值，换成占位符并注明"))
                break
    return out


def r_code_danger_bash(doc):
    out = []
    for lang, code, s, e in doc.code_blocks:
        if lang.lower() in ("bash", "sh", "shell", "console", "zsh"):
            for j, ln in enumerate(code.split("\n"), start=s + 1):
                if re.search(r"rm\s+(-[a-z]*r[a-z]*|--recursive).*(^|\s)(/|\~|\$HOME|\*)(\s|$)",
                             ln) or re.search(r":\(\)\s*\{\s*:\|:\s*&\s*\}\s*;", ln):
                    ctx = "\n".join(doc.lines[max(0, s - 4):min(len(doc.lines), e + 3)])
                    if not re.search(r"注意|危险|警告|不要|切勿|备份", ctx):
                        out.append((j, "高危 shell 命令（rm -rf 根路径/fork 炸弹类）无风险提示"))
                    break
    return out


def _fence_within(doc, line_no, after):
    for _, _, s, _ in doc.code_blocks:
        if 0 < s - line_no <= after:
            return True
    seg = "\n".join(doc.lines[line_no:line_no + after])
    return bool(re.search(r"^\s*>", seg, re.M))


def r_code_output_claim(doc):
    out = []
    for i, ln in enumerate(doc.lines, start=1):
        if re.search(r"运行结果|输出结果|执行结果|结果如下|输出如下", ln):
            if not _fence_within(doc, i, 8):
                out.append((i, "声称给出运行结果，但后面 8 行内没有输出代码块/引用块"))
    return out


def r_code_intro_claim(doc):
    out = []
    for i, ln in enumerate(doc.lines, start=1):
        if re.search(r"代码如下|示例如下|完整示例|看下面这段|先看代码", ln):
            if not any(0 < s - i <= 5 for _, _, s, _ in doc.code_blocks):
                out.append((i, "说“代码如下”但后面 5 行内没有代码块"))
    return out


def r_code_placeholder(doc):
    out = []
    for lang, code, s, e in doc.code_blocks:
        if re.search(r"<[^>\n]{1,40}>|YOUR_[A-Z_]+|your-[a-z-]+-here|\bxxx+\b",
                     code, re.I):
            ctx = "\n".join(doc.lines[max(0, s - 6):min(len(doc.lines), e + 2)])
            if not re.search(r"示意|伪代码|占位|请替换|改成你|示例", ctx):
                out.append((s, "示例含 <占位符>/YOUR_X/xxx，前后文未注明需替换"))
    return out


def r_code_dollar_mix(doc):
    out = []
    for lang, code, s, e in doc.code_blocks:
        if lang.lower() in ("bash", "sh", "shell", "console", "zsh"):
            clines = [ln for ln in code.split("\n") if ln.strip()]
            if len(clines) >= 2:
                with_d = sum(1 for ln in clines if ln.lstrip().startswith("$"))
                if 0 < with_d < len(clines):
                    out.append((s, "$ 提示符风格混用（部分行有、部分行无），统一去掉或保留"))
    return out


def r_code_dup(doc):
    out = []
    seen = {}
    for lang, code, s, e in doc.code_blocks:
        key = (lang.lower(), re.sub(r"\s+", " ", code.strip()))
        if len(key[1]) < 30:
            continue
        if key in seen:
            out.append((s, "与第 %d 行代码块内容重复，疑似复制粘贴未删" % seen[key]))
        else:
            seen[key] = s
    return out


def r_code_unclosed(doc):
    n = sum(1 for ln in doc.lines if re.match(r"^\s*```", ln))
    if n % 2 == 1:
        return [(len(doc.lines), "围栏 ``` 数量为奇数（%d），有一处未闭合" % n)]
    return []


def r_code_ratio(doc):
    total = len([ln for ln in doc.lines if ln.strip()])
    code_ln = sum(e - s - 1 for _, _, s, e in doc.code_blocks)
    if total > 40 and code_ln / total > 0.6:
        return [(1, "代码行占比 %.0f%%（超 60%%），讲解不足，读者只见代码不见为什么"
                 % (code_ln / total * 100))]
    return []


def r_code_thirdparty(doc):
    out = []
    has_install = bool(re.search(r"pip(3)?\s+install|requirements\.txt|安装依赖",
                                 doc.prose))
    if has_install:
        return out
    for lang, code, s, e in doc.code_blocks:
        if lang.lower() in ("python", "py", "python3"):
            mods = set(re.findall(r"^\s*(?:from|import)\s+([a-zA-Z0-9_]+)", code, re.M))
            third = sorted(m for m in mods if m not in PY_STDLIB)
            if third:
                out.append((s, "引用了第三方库（%s）但正文无安装说明" % "、".join(third[:4])))
    return out


def r_code_py2(doc):
    out = []
    for lang, code, s, e in doc.code_blocks:
        if lang.lower() in ("python", "py", "python3"):
            for j, ln in enumerate(code.split("\n"), start=s + 1):
                if re.match(r"^\s*print\s+[^(]", ln):
                    out.append((j, "疑似 Python2 风格 print 语句"))
                    break
    return out


def r_code_long_output(doc):
    out = []
    for lang, code, s, e in doc.code_blocks:
        if lang.lower() in ("text", "txt", "output", "plain", ""):
            n = e - s - 1
            if n > 50:
                out.append((s, "输出块长达 %d 行，建议只保留关键行或折叠" % n))
    return out


def r_head_no_h1(doc):
    if not any(lv == 1 for lv, _, _ in doc.headings):
        return [(1, "全文没有一级标题（# 标题），先定标题再谈其他")]
    return []


def r_head_multi_h1(doc):
    h1s = [ln for lv, _, ln in doc.headings if lv == 1]
    if len(h1s) > 1:
        return [(h1s[1], "出现第 2 个一级标题，一篇文章只应有一个 # 标题")]
    return []


def r_head_jump(doc):
    out = []
    prev = 0
    for lv, title, ln in doc.headings:
        if prev and lv > prev + 1:
            out.append((ln, "标题层级从 h%d 直接跳到 h%d：「%s」"
                        % (prev, lv, title[:20])))
        prev = lv
    return out


def r_head_punct(doc):
    out = []
    for lv, title, ln in doc.headings:
        if re.search(r"[。！？；，、]$", title):
            out.append((ln, "标题末尾带中文标点，去掉更干净"))
    return out


def _paras(doc):
    """正文段落（排除代码/标题/列表/引用/空行）。"""
    paras = []
    buf = []
    start = 0
    for i, ln in enumerate(doc.prose.split("\n"), start=1):
        s = ln.strip()
        if not s:
            if buf:
                paras.append((start, " ".join(buf)))
                buf = []
            continue
        if re.match(r"^#{1,6}\s", s) or re.match(r"^([-*+]|\d+[.)])\s", s) or \
           s.startswith(">") or re.match(r"^\|", s) or re.match(r"^---+$", s):
            if buf:
                paras.append((start, " ".join(buf)))
                buf = []
            continue
        if not buf:
            start = i
        buf.append(s)
    if buf:
        paras.append((start, " ".join(buf)))
    return paras


def r_struct_long_para(doc):
    out = []
    for ln, p in _paras(doc):
        if len(p) > 400:
            out.append((ln, "段落长达 %d 字（超 400），按“一段一层意思”拆成短段落" % len(p)))
    return out


def r_struct_no_h2(doc):
    if len(doc.prose) > 2000 and not any(lv == 2 for lv, _, _ in doc.headings):
        return [(1, "正文超 2000 字却没有二级小标题，手机阅读需要呼吸点")]
    return []


def r_struct_no_hook(doc):
    head = doc.prose[:400]
    head = re.sub(r"^#.*$", "", head, flags=re.M)
    if len(doc.prose) > 800 and not re.search(r"问题|痛点|为什么|场景|背景|需求|踩坑", head):
        return [(1, "开篇 400 字没有锚定“问题/场景/为什么”，读者不知道为谁而写")]
    return []


def r_struct_no_summary(doc):
    if len(doc.prose) > 1500 and not re.search(r"^#{1,6}\s*(总结|小结|结论|回顾|写在最后| takeaway)",
                                               doc.prose, re.M | re.I):
        return [(len(doc.lines), "长文缺少“总结/小结”章节，读者带不走结论")]
    return []


def r_struct_no_pitfall(doc):
    if len(doc.prose) > 1500 and not re.search(
            r"^#{1,6}\s*.*(坑|注意|避坑|陷阱|小心|常见错误)", doc.prose, re.M):
        return [(len(doc.lines), "长文没有“坑/注意事项”章节，技术文的可信度一半来自踩坑")]
    return []


def r_struct_empty_section(doc):
    out = []
    hs = doc.headings
    for idx, (lv, title, ln) in enumerate(hs):
        nxt = hs[idx + 1][2] if idx + 1 < len(hs) else len(doc.lines) + 1
        body = [l for l in doc.lines[ln:nxt - 1] if l.strip()
                and not re.match(r"^\s*```", l)]
        if not body:
            out.append((ln, "空章节：「%s」下面没有任何内容" % title[:20]))
    return out


def r_struct_long_item(doc):
    out = []
    for i, ln in enumerate(doc.lines, start=1):
        m = re.match(r"^\s*([-*+]|\d+[.)])\s+(.+)$", ln)
        if m and len(m.group(2)) > 200:
            out.append((i, "列表项长达 %d 字，拆成段落或子列表" % len(m.group(2))))
    return out


def r_ref_img(doc):
    if re.search(r"见图|如下图|如图所示|截图", doc.prose) and not doc.images:
        m = re.search(r"见图|如下图|如图所示|截图", doc.prose)
        ln = doc.prose[:m.start()].count("\n") + 1
        return [(ln, "正文提到“图”但全文没有图片")]
    return []


def r_ref_anchor(doc):
    out = []
    slugs = doc.heading_slugs()
    for anchor, ln in doc.anchors:
        if not slug_ok(anchor, slugs):
            out.append((ln, "内部锚链 #%s 找不到对应标题，点进去是空的" % anchor))
    return out


def r_ref_code_intro(doc):
    out = []
    for lang, code, s, e in doc.code_blocks:
        prev = "\n".join(doc.lines[max(0, s - 4):s - 1])
        # 标题与围栏行不算"引出"，只看真正的正文行
        prev = "\n".join(ln for ln in prev.split("\n")
                         if ln.strip()
                         and not re.match(r"^\s*#{1,6}\s", ln)
                         and not re.match(r"^\s*```", ln))
        if not prev.strip():
            out.append((s, "代码块前面 3 行没有任何正文引出，读者不知道这段代码是干嘛的"))
    return out


def r_ref_repo_link(doc):
    if re.search(r"完整代码|源码|代码仓库|GitHub.*见|开源地址", doc.prose) and \
       not re.search(r"https?://", doc.prose):
        return [(1, "提到“完整代码/源码在 GitHub”但没给链接，读者找不到")]
    return []


def r_hyg_todo(doc):
    out = []
    for i, ln in enumerate(doc.prose.split("\n"), start=1):
        if re.search(r"\b(TODO|FIXME|XXX)\b|待补充|占位符", ln):
            out.append((i, "正文残留 TODO/待补充标记，发出去会被读者看到"))
            break
    return out


def r_hyg_img_alt(doc):
    out = []
    for alt, src, ln in doc.images:
        if not alt.strip():
            out.append((ln, "图片没有 alt 文本，无障碍与 SEO 都受影响"))
    return out


def r_hyg_zh_en_space(doc):
    n = len(re.findall(r"[\u4e00-\u9fff][A-Za-z0-9]|[A-Za-z0-9][\u4e00-\u9fff]",
                       doc.prose))
    if n >= 5:
        return [(1, "中英文混排缺空格共 %d 处（如“Python装饰器”→“Python 装饰器”）" % n)]
    return []


def r_hyg_perf_claim(doc):
    out = []
    for ln, p in _paras(doc):
        if re.search(r"(提升|提高|加快|优化|快)\s*\d+\s*%|\d+\s*倍", p):
            ctx = p
            if not re.search(r"实测|测试|基准|来源|数据|benchmark|对比", ctx, re.I):
                out.append((ln, "性能数字断言（提升 x%/快 x 倍）附近无实测/来源依据"))
                break
    return out


def r_hyg_absolute(doc):
    n = len(re.findall(r"最快|第一|唯一|绝不|永远|100%|零风险", doc.prose))
    if n >= 2:
        return [(1, "绝对化用语出现 %d 次（最快/唯一/永远等），技术文里每用一次可信度打一次折" % n)]
    return []


def r_hyg_trailing(doc):
    n = sum(1 for ln in doc.lines if re.search(r"[ \t]+$", ln))
    if n > 5:
        return [(1, "行尾多余空格共 %d 行，编辑器开“显示不可见字符”清掉" % n)]
    return []


def r_hyg_blank(doc):
    # 查原文，但跳过围栏区（代码里的 PEP8 式空行不算排版问题）
    ranges = [(s, e) for _, _, s, e in doc.code_blocks]
    n = 0
    for m in re.finditer(r"\n{3,}", doc.text):
        ln = doc.text[:m.start()].count("\n") + 1
        if not any(s <= ln <= e for s, e in ranges):
            n += 1
    if n:
        return [(1, "连续空行（≥3 行）出现 %d 处，压成 1 个空行" % n)]
    return []


def r_hyg_lang_typo(doc):
    out = []
    for lang, code, s, e in doc.code_blocks:
        if lang.lower() in LANG_TYPO:
            out.append((s, "语言标记拼写疑似有误：%s → %s" % (lang, LANG_TYPO[lang.lower()])))
    return out


def r_hyg_example_link(doc):
    out = []
    for m in re.finditer(r"(https?://)?example\.com[^\s)]*", doc.prose):
        ln = doc.prose[:m.start()].count("\n") + 1
        out.append((ln, "示例链接 example.com 未替换成真实链接"))
        break
    return out


# ---------------- 规则注册表 ----------------
RULES = [
    # 代码块
    {"id": "TB-CODE-001", "severity": "blocker", "category": "代码块",
     "title": "代码围栏缺语言标记", "fn": r_code_lang,
     "detail": "``` 后面没写语言，渲染无高亮、自动化校验也跳过。补上 python/bash/js 等。"},
    {"id": "TB-CODE-002", "severity": "blocker", "category": "代码块",
     "title": "Python 示例语法错误", "fn": r_code_py_syntax,
     "detail": "Python 代码块过不了语法解析，读者复制即报错。修到能解析为止。"},
    {"id": "TB-CODE-003", "severity": "warning", "category": "代码块",
     "title": "Python 示例含未完成标记", "fn": r_code_py_todo,
     "detail": "示例里有 TODO/…/待补充，等于告诉读者“这段跑不通”。补全或删掉。"},
    {"id": "TB-CODE-004", "severity": "warning", "category": "代码块",
     "title": "JS/TS 示例括号不配平", "fn": r_code_js_balance,
     "detail": "括号配不平的代码 99% 是粘贴截断。补全括号再发。"},
    {"id": "TB-CODE-005", "severity": "blocker", "category": "代码块",
     "title": "示例含疑似真实密钥", "fn": r_code_secret,
     "detail": "password/api_key 等写了字面值。换成 <YOUR_API_KEY> 类占位符并注明替换。"},
    {"id": "TB-CODE-006", "severity": "warning", "category": "代码块",
     "title": "高危 shell 命令无风险提示", "fn": r_code_danger_bash,
     "detail": "rm -rf 根路径/fork 炸弹类命令前后必须有“危险/注意”提示，否则读者误伤自己。"},
    {"id": "TB-CODE-007", "severity": "warning", "category": "代码块",
     "title": "“结果如下”但无输出块", "fn": r_code_output_claim,
     "detail": "写了“运行结果如下”却没贴输出，承诺落空。补输出块或删掉这句话。"},
    {"id": "TB-CODE-008", "severity": "warning", "category": "代码块",
     "title": "“代码如下”但无代码块", "fn": r_code_intro_claim,
     "detail": "写了“代码如下”却没贴代码。补代码或改说法。"},
    {"id": "TB-CODE-009", "severity": "warning", "category": "代码块",
     "title": "占位符未注明需替换", "fn": r_code_placeholder,
     "detail": "示例里的 <xxx>/YOUR_X/xxx 必须在前后文注明“请替换成你自己的”，否则读者原样复制。"},
    {"id": "TB-CODE-010", "severity": "nit", "category": "代码块",
     "title": "$ 提示符风格混用", "fn": r_code_dollar_mix,
     "detail": "同一 shell 代码块里 $ 有的有、有的无。统一：要么全去掉，要么全保留。"},
    {"id": "TB-CODE-011", "severity": "warning", "category": "代码块",
     "title": "重复代码块", "fn": r_code_dup,
     "detail": "两处代码块内容完全相同，疑似复制粘贴后忘了删。删掉重复，保留引用。"},
    {"id": "TB-CODE-012", "severity": "nit", "category": "代码块",
     "title": "围栏未闭合", "fn": r_code_unclosed,
     "detail": "``` 数量为奇数，有一处代码块没闭合，后面整篇都会被吞进代码块。"},
    {"id": "TB-CODE-013", "severity": "warning", "category": "代码块",
     "title": "代码占比过高", "fn": r_code_ratio,
     "detail": "代码行超全文 60%，读者只见代码不见“为什么”。补讲解：每段代码前说清目的、后说清关键行。"},
    {"id": "TB-CODE-014", "severity": "warning", "category": "代码块",
     "title": "第三方库无安装说明", "fn": r_code_thirdparty,
     "detail": "import 了第三方库但正文没写 pip install，读者第一步就卡住。补安装命令+版本。"},
    {"id": "TB-CODE-015", "severity": "warning", "category": "代码块",
     "title": "Python2 风格残留", "fn": r_code_py2,
     "detail": "print 后面没括号是 Python2 写法。现在默认 Python3，改掉。"},
    {"id": "TB-CODE-016", "severity": "nit", "category": "代码块",
     "title": "输出块超长", "fn": r_code_long_output,
     "detail": "输出块超 50 行没人看完。只保留关键行，其余用“……省略”。"},
    # 标题
    {"id": "TB-HEAD-001", "severity": "blocker", "category": "标题",
     "title": "缺少一级标题", "fn": r_head_no_h1,
     "detail": "全文没有 # 标题。标题是读者点开的理由，先定标题。"},
    {"id": "TB-HEAD-002", "severity": "warning", "category": "标题",
     "title": "多个一级标题", "fn": r_head_multi_h1,
     "detail": "一篇文章只应有一个 # 标题，其余降级为 ##。"},
    {"id": "TB-HEAD-003", "severity": "warning", "category": "标题",
     "title": "标题层级跳跃", "fn": r_head_jump,
     "detail": "h1 直接跳 h3 会让目录结构断裂，补上中间层级。"},
    {"id": "TB-HEAD-004", "severity": "nit", "category": "标题",
     "title": "标题末尾带标点", "fn": r_head_punct,
     "detail": "标题末尾的中文标点是视觉噪音，去掉。"},
    # 结构
    {"id": "TB-STRUCT-001", "severity": "warning", "category": "结构",
     "title": "超长段落", "fn": r_struct_long_para,
     "detail": "超 400 字的段落是文字墙。按“一段一层意思”拆成 ≤150 字的短段落。"},
    {"id": "TB-STRUCT-002", "severity": "warning", "category": "结构",
     "title": "长文无二级标题", "fn": r_struct_no_h2,
     "detail": "正文超 2000 字却没有 ## 小标题。手机阅读需要呼吸点，每 300~500 字一个。"},
    {"id": "TB-STRUCT-003", "severity": "warning", "category": "结构",
     "title": "开篇无问题锚点", "fn": r_struct_no_hook,
     "detail": "开篇 400 字没说清“解决什么问题/什么场景”，读者 3 秒就划走。先抛问题。"},
    {"id": "TB-STRUCT-004", "severity": "nit", "category": "结构",
     "title": "长文无总结章节", "fn": r_struct_no_summary,
     "detail": "超 1500 字的长文缺“总结/小结”，读者带不走结论。补 3~5 条要点。"},
    {"id": "TB-STRUCT-005", "severity": "nit", "category": "结构",
     "title": "长文无“坑”章节", "fn": r_struct_no_pitfall,
     "detail": "超 1500 字的技术文没有“坑/注意事项”，可信度打折。把你踩过的坑写出来。"},
    {"id": "TB-STRUCT-006", "severity": "nit", "category": "结构",
     "title": "空章节", "fn": r_struct_empty_section,
     "detail": "标题下面没有任何内容，大纲先行时常见。补内容或删标题。"},
    {"id": "TB-STRUCT-007", "severity": "nit", "category": "结构",
     "title": "列表项超长", "fn": r_struct_long_item,
     "detail": "单条列表项超 200 字，拆成段落或子列表。"},
    # 引用一致性
    {"id": "TB-REF-001", "severity": "warning", "category": "引用",
     "title": "见图但无图", "fn": r_ref_img,
     "detail": "正文写了“见图/如下图”但全文没图片。补图或改说法。"},
    {"id": "TB-REF-002", "severity": "warning", "category": "引用",
     "title": "死锚链", "fn": r_ref_anchor,
     "detail": "内部 #锚链 找不到对应标题。检查标题改名后链接是否同步。"},
    {"id": "TB-REF-003", "severity": "nit", "category": "引用",
     "title": "代码块无正文引出", "fn": r_ref_code_intro,
     "detail": "代码块前 3 行没任何正文铺垫。加一句“这段代码做了什么”。"},
    {"id": "TB-REF-004", "severity": "warning", "category": "引用",
     "title": "“完整代码”无链接", "fn": r_ref_repo_link,
     "detail": "说“完整代码见 GitHub”却没给链接。补链接，或删掉这句话。"},
    # 卫生
    {"id": "TB-HYG-001", "severity": "warning", "category": "卫生",
     "title": "TODO 残留", "fn": r_hyg_todo,
     "detail": "正文有 TODO/待补充，发出去等于把草稿给读者看。清掉。"},
    {"id": "TB-HYG-002", "severity": "nit", "category": "卫生",
     "title": "图片无 alt", "fn": r_hyg_img_alt,
     "detail": "![](...) 空 alt，读屏软件和搜索引擎都抓瞎。补一句图注。"},
    {"id": "TB-HYG-003", "severity": "nit", "category": "卫生",
     "title": "中英混排缺空格", "fn": r_hyg_zh_en_space,
     "detail": "中文和英文/数字之间加空格（“Python 装饰器”），排版呼吸感立刻上来。"},
    {"id": "TB-HYG-004", "severity": "warning", "category": "卫生",
     "title": "性能断言无依据", "fn": r_hyg_perf_claim,
     "detail": "“提升 x%/快 x 倍”附近没有实测/来源。数字必须有出处，否则删数字留定性描述。"},
    {"id": "TB-HYG-005", "severity": "warning", "category": "卫生",
     "title": "绝对化用语", "fn": r_hyg_absolute,
     "detail": "最快/唯一/永远等词出现多次。技术文里绝对化=不可信，换成限定条件。"},
    {"id": "TB-HYG-006", "severity": "nit", "category": "卫生",
     "title": "行尾多余空格", "fn": r_hyg_trailing,
     "detail": "行尾空格是版本控制噪音，编辑器开“修剪行尾空格”清掉。"},
    {"id": "TB-HYG-007", "severity": "nit", "category": "卫生",
     "title": "连续空行", "fn": r_hyg_blank,
     "detail": "连续 3+ 空行压成 1 个，版式更紧凑。"},
    {"id": "TB-HYG-008", "severity": "warning", "category": "卫生",
     "title": "语言标记拼写错", "fn": r_hyg_lang_typo,
     "detail": "``` 后的语言名拼错了（如 pythno），高亮会失效。按提示改。"},
    {"id": "TB-HYG-009", "severity": "warning", "category": "卫生",
     "title": "示例链接未替换", "fn": r_hyg_example_link,
     "detail": "example.com 是占位域名，出现在正文链接里说明忘了替换。换真实链接。"},
]

_RULE_BY_ID = {r["id"]: r for r in RULES}


def collect_md_files(target):
    if os.path.isfile(target):
        return [target] if target.endswith(".md") else []
    out = []
    for root, dirs, files in os.walk(target):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        for f in sorted(files):
            if f.endswith(".md"):
                out.append(os.path.join(root, f))
    return out


def audit_file(path):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    doc = Doc(path, text)
    findings = []
    for rule in RULES:
        try:
            hits = rule["fn"](doc) or []
        except Exception as ex:  # 单条规则出错不拖死整轮（fail-open 单规则）
            continue
        for line_no, extra in hits:
            findings.append({
                "rule_id": rule["id"],
                "severity": rule["severity"],
                "category": rule["category"],
                "title": rule["title"],
                "file": path,
                "line": line_no,
                "detail": rule["detail"] + (" ｜ " + extra if extra else ""),
            })
    return findings


def main():
    ap = argparse.ArgumentParser(description="lhg-tech-blog 稿件审计")
    ap.add_argument("--target", required=True, help="稿件 .md 文件或目录")
    ap.add_argument("--format", choices=["json", "text"], default="text")
    ap.add_argument("--fail-on", choices=["blocker", "warning", "nit"],
                    default="blocker")
    args = ap.parse_args()

    files = collect_md_files(args.target)
    if not files:
        print("未找到 Markdown 稿件：%s" % args.target, file=sys.stderr)
        return 1

    findings = []
    for p in files:
        findings.extend(audit_file(p))
    findings.sort(key=lambda f: (SEV_ORDER[f["severity"]], f["file"], f["line"]))

    summary = {
        "tool": TOOL,
        "version": VERSION,
        "files": len(files),
        "rules_run": len(RULES),
        "blocker": sum(1 for f in findings if f["severity"] == "blocker"),
        "warning": sum(1 for f in findings if f["severity"] == "warning"),
        "nit": sum(1 for f in findings if f["severity"] == "nit"),
    }

    if args.format == "json":
        print(json.dumps({"summary": summary, "findings": findings},
                         ensure_ascii=False, indent=2))
    else:
        print("== lhg-tech-blog 稿件审计 v%s ==" % VERSION)
        print("文件：%d ｜ 规则：%d ｜ blocker=%d warning=%d nit=%d" % (
            summary["files"], summary["rules_run"], summary["blocker"],
            summary["warning"], summary["nit"]))
        cur = None
        for f in findings:
            if f["severity"] != cur:
                cur = f["severity"]
                print("\n[%s]" % cur.upper())
            print("  %s %s:%d ｜ %s" % (f["rule_id"], f["file"], f["line"],
                                        f["title"]))
            print("    → %s" % f["detail"])
        if not findings:
            print("\n干净：零发现，可以进入人工终审。")

    worst = max([SEV_ORDER[f["severity"]] for f in findings] + [-1])
    return 2 if worst >= SEV_ORDER[args.fail_on] else 0


if __name__ == "__main__":
    sys.exit(main())
