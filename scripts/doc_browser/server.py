#!/usr/bin/env python3
"""研究文档浏览器的本地服务。

只用标准库。把 config.json 里登记的仓库目录做成网页：目录树、Markdown 渲染、
PDF / Word / Excel / 网页 / 图片预览（PPT 和旧版 Office 借 LibreOffice 转成 PDF）、
文件名与全文搜索，以及 AI 助手（assistant.py，OpenAI 兼容协议）。服务只监听 127.0.0.1，
只写 config.json、本机缓存目录和存 API key 的本机配置目录，不改动被浏览的文件。

用法：python scripts/doc_browser/server.py [--port 8765] [--no-browser]
"""
from __future__ import annotations

import argparse
import errno
import fnmatch
import hashlib
import html
import json
import mimetypes
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import traceback
import urllib.parse
import urllib.request
import webbrowser
import zipfile
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import assistant

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
STATIC = HERE / "static"
CONFIG_PATH = HERE / "config.json"
APP_ID = "basemodel-doc-browser"

# 纯文本和网页超过这个大小就不进全文索引（在搜索结果里列出）；Office 和 PDF 只取文字，不受限
INDEX_MAX_BYTES = 10 * 1024 * 1024
PLAIN_EXTS = {
    ".md", ".markdown", ".txt", ".csv", ".tsv", ".json", ".jsonl", ".py", ".sh", ".bat", ".ps1",
    ".r", ".sql", ".yaml", ".yml", ".toml", ".xml", ".log", ".tex", ".bib", ".ipynb", ".ini", ".cfg",
}
MARKUP_EXTS = {".html", ".htm", ".svg"}
OFFICE_TEXT_EXTS = {".docx", ".pptx", ".xlsx"}
CONVERT_EXTS = {".pptx", ".ppt", ".pps", ".ppsx", ".odp", ".docx", ".doc", ".odt", ".rtf", ".xls", ".xlsx", ".ods"}
EXTRA_TYPES = {
    ".md": "text/markdown", ".markdown": "text/markdown", ".mjs": "text/javascript",
    # Windows 注册表可能把 .js 登记成 text/plain，浏览器会拒绝执行
    ".js": "text/javascript", ".wasm": "application/wasm", ".ftl": "text/plain",
    ".jsonl": "application/x-ndjson", ".woff2": "font/woff2", ".svg": "image/svg+xml",
    ".py": "text/plain", ".log": "text/plain", ".sha256": "text/plain", ".tsv": "text/tab-separated-values",
}
# 被浏览的网页和 SVG 放进独立源里运行，里面的脚本碰不到本服务的接口
SANDBOX_CSP = "sandbox allow-scripts allow-popups allow-forms allow-modals allow-downloads"


class ApiError(Exception):
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status
        self.message = message


class ClientGone(Exception):
    """浏览器那端断开了（点了停止、关了页面）。单独成类，免得和上游模型服务断开（同为 ConnectionError）混在一起。"""


class Skip(Exception):
    """文件没能进全文索引；原因会显示在搜索结果里。"""


def cache_root() -> Path:
    if sys.platform == "darwin":
        base = Path.home() / "Library" / "Caches"
    elif sys.platform == "win32":
        base = Path(os.environ["LOCALAPPDATA"])
    else:
        base = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
    return base / APP_ID


def config_root() -> Path:
    """API key 放这里：在仓库之外，不随 Syncthing 和 git 走。"""
    if sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    elif sys.platform == "win32":
        base = Path(os.environ["APPDATA"])
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / APP_ID


def find_tool(name: str, known: list[str]) -> str | None:
    """在 PATH 和常见安装位置里找外部程序；从 Finder 双击启动时 PATH 往往不全。"""
    found = shutil.which(name)
    if found:
        return found
    for cand in known:
        if Path(cand).is_file():
            return cand
    return None


def detect_tools() -> dict[str, str | None]:
    return {
        "soffice": find_tool("soffice", [
            "/opt/homebrew/bin/soffice",
            "/usr/local/bin/soffice",
            "/Applications/LibreOffice.app/Contents/MacOS/soffice",
            r"C:\Program Files\LibreOffice\program\soffice.exe",
            r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
        ]),
        "pdftotext": find_tool("pdftotext", [
            "/opt/homebrew/bin/pdftotext",
            "/usr/local/bin/pdftotext",
            str(Path.home() / ".local" / "bin" / "pdftotext"),
        ]),
    }


# ---------------------------------------------------------------- 配置


def normalize_roots(raw: list[str]) -> list[str]:
    """把用户给的目录（仓库相对路径或仓库内的绝对路径）规整成仓库相对路径，并检查能否浏览。"""
    out: list[str] = []
    for item in raw:
        text = item.strip().replace("\\", "/").rstrip("/")
        if not text:
            raise ValueError("目录不能为空")
        p = Path(text) if Path(text).is_absolute() else REPO / text
        p = p.resolve()
        if p != REPO and REPO not in p.parents:
            raise ValueError(f"{item}：不在仓库 {REPO} 之内")
        if not p.is_dir():
            raise ValueError(f"{item}：目录不存在")
        rel = p.relative_to(REPO).as_posix()
        if rel == ".":
            raise ValueError("不能把整个仓库作为一个目录，请分别添加需要浏览的子目录")
        for prev in out:
            if rel == prev or rel.startswith(prev + "/") or prev.startswith(rel + "/"):
                raise ValueError(f"{rel} 与 {prev} 重复或互相包含")
        out.append(rel)
    return out


def load_config() -> dict:
    cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    cfg["roots"] = normalize_roots(cfg["roots"])
    cfg["assistant"] = assistant.normalize_settings(cfg["assistant"])
    return cfg


def save_config(cfg: dict) -> None:
    CONFIG_PATH.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def is_excluded(name: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatchcase(name, pat) for pat in patterns)


# ---------------------------------------------------------------- 扫描


def scan(cfg: dict) -> tuple[list[dict], list[tuple[str, Path, os.stat_result]]]:
    """返回目录树和平铺的文件列表（相对路径、磁盘路径、stat）。"""
    files: list[tuple[str, Path, os.stat_result]] = []
    patterns = cfg["exclude"]

    def walk(path: Path, rel: str) -> dict:
        children = []
        with os.scandir(path) as it:
            entries = sorted(it, key=lambda e: e.name)
        for e in entries:
            if is_excluded(e.name, patterns):
                continue
            crel = f"{rel}/{e.name}"
            # 目录不跟随符号链接，避免环；文件跟随，打开时再检查真实位置
            if e.is_dir(follow_symlinks=False):
                children.append(walk(Path(e.path), crel))
            elif e.is_file():
                st = e.stat()
                files.append((crel, Path(e.path), st))
                children.append({"n": e.name, "p": crel, "s": st.st_size, "m": st.st_mtime_ns // 1_000_000})
        return {"n": path.name, "p": rel, "d": 1, "c": children}

    tree = [walk(REPO / rel, rel) for rel in cfg["roots"]]
    return tree, files


def resolve_in_roots(cfg: dict, rel: str) -> Path:
    """仓库相对路径 → 磁盘路径；不在已登记目录内、或落在排除规则里，就拒绝。"""
    p = (REPO / rel).resolve()
    for root_rel in cfg["roots"]:
        root = (REPO / root_rel).resolve()
        if p == root or root in p.parents:
            if any(is_excluded(part, cfg["exclude"]) for part in p.relative_to(root).parts):
                raise ApiError(403, f"{rel} 在排除规则内")
            if not p.exists():
                raise ApiError(404, f"{rel} 不存在")
            return p
    raise ApiError(403, f"{rel} 不在浏览目录内")


# ---------------------------------------------------------------- 文字提取（全文搜索用）


def decode_text(data: bytes) -> str:
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            return data.decode("gb18030")
        except UnicodeDecodeError:
            raise Skip("既不是 UTF-8 也不是 GB18030 编码") from None


def strip_markup(text: str) -> str:
    text = re.sub(r"(?is)<(script|style)\b.*?</\1\s*>", " ", text)
    text = re.sub(r"(?i)<br\s*/?>|</(p|div|li|tr|h[1-6]|table|section|text|tspan)>", "\n", text)
    return html.unescape(re.sub(r"<[^>]+>", "", text))


def xml_paragraphs(xml: str, para_tag: str, text_tag: str) -> str:
    text_re = re.compile(rf"<{text_tag}(?:\s[^>]*)?>([^<]*)</{text_tag}>")
    lines = []
    for chunk in xml.split(f"</{para_tag}>"):
        line = "".join(text_re.findall(chunk))
        if line:
            lines.append(html.unescape(line))
    return "\n".join(lines)


def xml_attrs(tag: str) -> dict[str, str]:
    return dict(re.findall(r'([\w:]+)="([^"]*)"', tag))


def pptx_slides(z: zipfile.ZipFile) -> list[str]:
    """按演示顺序列出要导出的幻灯片；隐藏页 LibreOffice 不导出，跳过后页码才和 PDF 对得上。"""
    rels = {}
    for tag in re.findall(r"<Relationship\b[^>]*>", z.read("ppt/_rels/presentation.xml.rels").decode("utf-8")):
        a = xml_attrs(tag)
        rels[a["Id"]] = a["Target"]
    names = []
    for tag in re.findall(r"<p:sldId\b[^>]*>", z.read("ppt/presentation.xml").decode("utf-8")):
        target = rels[xml_attrs(tag)["r:id"]]
        names.append(target.lstrip("/") if target.startswith("/") else "ppt/" + target)
    texts = []
    for name in names:
        xml = z.read(name).decode("utf-8")
        if re.search(r'<p:sld\b[^>]*\bshow="0"', xml):
            continue
        texts.append(xml_paragraphs(xml, "a:p", "a:t"))
    return texts


def office_text(path: Path) -> str:
    ext = path.suffix.lower()
    try:
        with zipfile.ZipFile(path) as z:
            if ext == ".docx":
                return xml_paragraphs(z.read("word/document.xml").decode("utf-8"), "w:p", "w:t")
            if ext == ".pptx":
                # 用换页符分隔幻灯片，搜索结果据此给出页码
                return "\f".join(pptx_slides(z))
            if "xl/sharedStrings.xml" not in z.namelist():
                return ""
            return xml_paragraphs(z.read("xl/sharedStrings.xml").decode("utf-8"), "si", "t")
    except (zipfile.BadZipFile, KeyError) as e:
        raise Skip(f"不是有效的 Office 文件（{e}）") from None


def pdf_text(path: Path, st: os.stat_result, tools: dict) -> str:
    exe = tools["pdftotext"]
    if exe is None:
        raise Skip("未找到 pdftotext，PDF 只按文件名搜索")
    cached = cache_root() / "pdftext" / f"{file_key(path, st)}.txt"
    if cached.exists():
        return cached.read_text(encoding="utf-8")
    r = subprocess.run([exe, "-enc", "UTF-8", str(path), "-"], capture_output=True, timeout=180)
    if r.returncode != 0:
        raise Skip("pdftotext 失败：" + r.stderr.decode("utf-8", "replace").strip()[-200:])
    text = r.stdout.decode("utf-8")
    cached.parent.mkdir(parents=True, exist_ok=True)
    cached.write_text(text, encoding="utf-8")
    return text


def extract_text(path: Path, st: os.stat_result, tools: dict) -> str:
    ext = path.suffix.lower()
    try:
        if ext in OFFICE_TEXT_EXTS:
            return office_text(path)
        if ext == ".pdf":
            return pdf_text(path, st, tools)
        if st.st_size > INDEX_MAX_BYTES:
            raise Skip(f"超过 {INDEX_MAX_BYTES // 1024 // 1024} MB")
        text = decode_text(path.read_bytes())
        return strip_markup(text) if ext in MARKUP_EXTS else text
    except OSError as e:
        raise Skip(f"读取失败：{e}") from None


def indexable(path: Path) -> bool:
    ext = path.suffix.lower()
    return ext in PLAIN_EXTS or ext in MARKUP_EXTS or ext in OFFICE_TEXT_EXTS or ext == ".pdf"


def file_key(path: Path, st: os.stat_result) -> str:
    return hashlib.sha1(f"{path}|{st.st_mtime_ns}|{st.st_size}".encode("utf-8")).hexdigest()


def find_snippets(text: str, low: str, term: str, limit: int) -> list[dict]:
    paged = "\f" in text
    out, pos = [], 0
    while len(out) < limit:
        i = low.find(term, pos)
        if i < 0:
            break
        start = max(text.rfind("\n", 0, i), text.rfind("\f", 0, i)) + 1
        ends = [x for x in (text.find("\n", i), text.find("\f", i)) if x >= 0]
        end = min(ends) if ends else len(text)
        line = text[start:end]
        if len(line) > 160:
            a = max(start, i - 60)
            b = min(end, i + len(term) + 90)
            line = ("…" if a > start else "") + text[a:b] + ("…" if b < end else "")
        hit: dict[str, str | int] = {"text": line.strip()}
        if paged:
            hit["page"] = text.count("\f", 0, i) + 1
        else:
            hit["line"] = text.count("\n", 0, i) + 1
        out.append(hit)
        pos = end + 1
    return out


class SearchIndex:
    def __init__(self, tools: dict):
        self.tools = tools
        self._lock = threading.Lock()
        # 相对路径 → (mtime_ns, size, 显示用文字, 小写文字, 未索引原因)
        self._docs: dict[str, tuple] = {}

    def refresh(self, files: list[tuple[str, Path, os.stat_result]]) -> None:
        with self._lock:
            todo = [
                (rel, p, st) for rel, p, st in files
                if indexable(p) and self._docs.get(rel, (None, None))[:2] != (st.st_mtime_ns, st.st_size)
            ]

            def work(item):
                rel, p, st = item
                try:
                    return rel, st, extract_text(p, st, self.tools), None
                except Skip as e:
                    return rel, st, None, str(e)

            with ThreadPoolExecutor(max_workers=6) as ex:
                for rel, st, text, reason in ex.map(work, todo):
                    if text is None:
                        self._docs[rel] = (st.st_mtime_ns, st.st_size, None, None, reason)
                        continue
                    low = text.lower()
                    # 极少数字符小写后长度会变，那时用小写文字显示片段，保证位置对得上
                    shown = text if len(low) == len(text) else low
                    self._docs[rel] = (st.st_mtime_ns, st.st_size, shown, low, None)
            live = {rel for rel, _, _ in files}
            for rel in [r for r in self._docs if r not in live]:
                del self._docs[rel]

    def search(self, query: str, files: list[tuple[str, Path, os.stat_result]], limit: int = 200) -> dict:
        terms = query.lower().split()
        if not terms:
            raise ApiError(400, "搜索词为空")
        self.refresh(files)
        results, skipped = [], []
        with self._lock:
            for rel, p, st in files:
                doc = self._docs.get(rel)
                if doc is not None and doc[4] is not None:
                    skipped.append({"path": rel, "reason": doc[4]})
                shown, low = (doc[2], doc[3]) if doc is not None else (None, None)
                path_hit = all(t in rel.lower() for t in terms)
                hits, count = [], 0
                if shown is not None and low is not None and all(t in low for t in terms):
                    count = low.count(terms[0])
                    hits = find_snippets(shown, low, terms[0], 3)
                elif not path_hit:
                    continue
                score = min(count, 200)
                if path_hit:
                    score += 300
                if all(t in p.name.lower() for t in terms):
                    score += 1000
                results.append({
                    "path": rel,
                    "m": st.st_mtime_ns // 1_000_000,
                    "score": score,
                    "count": count,
                    "hits": hits,
                })
        results.sort(key=lambda r: (-r["score"], -r["m"]))
        return {
            "results": results[:limit],
            "total": len(results),
            "searched": len(files),
            "skipped": skipped,
            "terms": terms,
        }


# ---------------------------------------------------------------- LibreOffice 转 PDF


class Converter:
    def __init__(self, tools: dict):
        self.tools = tools
        self._lock = threading.Lock()

    def to_pdf(self, src: Path) -> Path:
        out = cache_root() / "pdf" / f"{file_key(src, src.stat())}.pdf"
        if out.exists():
            return out
        exe = self.tools["soffice"]
        if exe is None:
            raise ApiError(501, "没有找到 LibreOffice（soffice），无法预览这种文件。安装 LibreOffice 后重启文档库，或点“用默认程序打开”。")
        # LibreOffice 同一个用户配置目录不能并发转换，所以串行；配置目录单独放，不和用户自己开的 LibreOffice 冲突
        with self._lock:
            if out.exists():
                return out
            out.parent.mkdir(parents=True, exist_ok=True)
            profile = (cache_root() / "lo_profile").as_uri()
            with tempfile.TemporaryDirectory(dir=out.parent) as tmp:
                cmd = [exe, f"-env:UserInstallation={profile}", "--headless", "--norestore",
                       "--convert-to", "pdf", "--outdir", tmp, str(src)]
                r = subprocess.run(cmd, capture_output=True, timeout=300)
                produced = Path(tmp) / (src.stem + ".pdf")
                if r.returncode != 0 or not produced.exists():
                    detail = (r.stderr or r.stdout).decode("utf-8", "replace").strip()[-400:]
                    raise ApiError(500, f"LibreOffice 转换失败（退出码 {r.returncode}）：{detail}")
                shutil.move(str(produced), out)
        return out


# ---------------------------------------------------------------- 打开本机程序


def open_in_os(path: Path, reveal: bool) -> None:
    if sys.platform == "darwin":
        subprocess.run(["open", "-R", str(path)] if reveal else ["open", str(path)], check=True)
    elif sys.platform == "win32":
        if reveal:
            subprocess.Popen(f'explorer /select,"{path}"')
        else:
            os.startfile(path)  # noqa: S606 —— 本机文件，用系统默认程序打开
    else:
        subprocess.run(["xdg-open", str(path.parent if reveal else path)], check=True)


# ---------------------------------------------------------------- HTTP


class App:
    def __init__(self, port: int):
        self.port = port
        self.cfg = load_config()
        self.cfg_lock = threading.Lock()
        self.tools = detect_tools()
        self.index = SearchIndex(self.tools)
        self.converter = Converter(self.tools)
        self.assistant = assistant.Assistant(self, REPO, config_root() / "keys.json", (ApiError, Skip))

    def scan(self):
        with self.cfg_lock:
            cfg = dict(self.cfg)
        return scan(cfg)

    def read_text(self, rel: str) -> str:
        p = resolve_in_roots(self.cfg, rel)
        if not p.is_file():
            raise ApiError(400, f"{rel} 是目录")
        if not indexable(p):
            raise Skip(f"{p.suffix or '这种'} 文件没有可读取的文字")
        return extract_text(p, p.stat(), self.tools)

    def save_assistant(self, raw: dict) -> None:
        with self.cfg_lock:
            sect = assistant.normalize_settings({**raw, "exclude": self.cfg["assistant"]["exclude"]})
            self.cfg = {**self.cfg, "assistant": sect}
            save_config(self.cfg)

    def config_payload(self) -> dict:
        tops = sorted(
            e.name for e in os.scandir(REPO)
            if e.is_dir() and not is_excluded(e.name, self.cfg["exclude"])
        )
        return {
            "repo": REPO.name,
            "repo_path": str(REPO),
            "config_path": str(CONFIG_PATH),
            "roots": self.cfg["roots"],
            "candidates": tops,
            "tools": self.tools,
            "platform": sys.platform,
        }


def guess_type(path: Path) -> str:
    ext = path.suffix.lower()
    return EXTRA_TYPES.get(ext) or mimetypes.guess_type(path.name)[0] or "application/octet-stream"


class Handler(BaseHTTPRequestHandler):
    server_version = "DocBrowser/1.0"

    @property
    def app(self) -> App:
        return self.server.app  # type: ignore[attr-defined]

    def log_request(self, code="-", size="-"):
        if isinstance(code, int) and code >= 400:
            super().log_request(code, size)

    def do_GET(self):
        self.dispatch("GET")

    def do_POST(self):
        self.dispatch("POST")

    def dispatch(self, method: str) -> None:
        try:
            # 只接受本机地址访问，挡住借 DNS 重绑定从网页读本机文件
            host = self.headers.get("Host", "")
            if host not in (f"127.0.0.1:{self.app.port}", f"localhost:{self.app.port}"):
                raise ApiError(403, f"不接受来自 {host} 的访问")
            url = urllib.parse.urlsplit(self.path)
            path = urllib.parse.unquote(url.path)
            query = {k: v[-1] for k, v in urllib.parse.parse_qs(url.query).items()}
            if method == "GET":
                self.route_get(path, query)
            else:
                # 跨站页面发不出带自定义头的请求（预检不会通过），以此挡住跨站调用
                if self.headers.get("X-Doc-Browser") != "1":
                    raise ApiError(403, "缺少 X-Doc-Browser 请求头")
                length = int(self.headers["Content-Length"])
                body = json.loads(self.rfile.read(length).decode("utf-8"))
                self.route_post(path, body)
        except ApiError as e:
            self.send_json({"error": e.message}, e.status)
        except (BrokenPipeError, ConnectionResetError, ClientGone):
            pass  # 浏览器中途取消了请求（例如切换文件），没有人等这个响应
        except Exception as e:  # noqa: BLE001 —— 把未预料的错误显示在页面上，同时在终端留下完整堆栈
            traceback.print_exc()
            self.send_json({"error": f"{type(e).__name__}: {e}"}, 500)

    def route_get(self, path: str, query: dict) -> None:
        app = self.app
        if path == "/":
            return self.send_file(STATIC / "index.html")
        if path == "/favicon.ico":
            return self.send_file(STATIC / "favicon.svg")
        if path.startswith("/static/"):
            p = (STATIC / path[len("/static/"):]).resolve()
            if STATIC not in p.parents or not p.is_file():
                raise ApiError(404, "没有这个文件")
            return self.send_file(p)
        if path.startswith("/raw/"):
            p = resolve_in_roots(app.cfg, path[len("/raw/"):])
            if not p.is_file():
                raise ApiError(400, "这是目录")
            sandbox = p.suffix.lower() in MARKUP_EXTS
            return self.send_file(p, sandbox=sandbox)
        if path == "/api/ping":
            return self.send_json({"app": APP_ID})
        if path == "/api/config":
            return self.send_json(app.config_payload())
        if path == "/api/tree":
            tree, _ = app.scan()
            return self.send_json({"repo": REPO.name, "roots": tree})
        if path == "/api/search":
            _, files = app.scan()
            t0 = time.perf_counter()
            res = app.index.search(query.get("q", ""), files)
            res["ms"] = round((time.perf_counter() - t0) * 1000)
            return self.send_json(res)
        if path == "/api/convert":
            src = resolve_in_roots(app.cfg, query["path"])
            if src.suffix.lower() not in CONVERT_EXTS:
                raise ApiError(400, f"{src.suffix} 不需要转换")
            pdf = app.converter.to_pdf(src)
            if query.get("check") == "1":
                return self.send_json({"ok": True, "size": pdf.stat().st_size})
            return self.send_file(pdf, ctype="application/pdf", filename=src.stem + ".pdf")
        if path == "/api/stat":
            rel = query["path"]
            p = (REPO / rel).resolve()
            if p != REPO and REPO not in p.parents:
                raise ApiError(403, "仓库之外的路径")
            parts = p.relative_to(REPO).parts
            return self.send_json({
                "exists": p.exists(),
                "is_dir": p.is_dir(),
                "top": parts[0] if parts else "",
                "excluded": any(is_excluded(x, app.cfg["exclude"]) for x in parts),
            })
        if path == "/api/assistant/settings":
            return self.send_json(app.assistant.payload())
        raise ApiError(404, "没有这个地址")

    def route_post(self, path: str, body: dict) -> None:
        app = self.app
        if path == "/api/open":
            open_in_os(resolve_in_roots(app.cfg, body["path"]), bool(body["reveal"]))
            return self.send_json({"ok": True})
        if path == "/api/roots":
            try:
                roots = normalize_roots(body["roots"])
            except ValueError as e:
                raise ApiError(400, str(e)) from None
            if not roots:
                raise ApiError(400, "至少保留一个目录")
            with app.cfg_lock:
                app.cfg = {**app.cfg, "roots": roots}
                save_config(app.cfg)
            return self.send_json(app.config_payload())
        if path.startswith("/api/assistant/"):
            return self.route_assistant(path[len("/api/assistant/"):], body)
        raise ApiError(404, "没有这个地址")

    def route_assistant(self, action: str, body: dict) -> None:
        ai = self.app.assistant
        try:
            if action == "settings":
                self.app.save_assistant(body)
                return self.send_json(ai.payload())
            if action == "key":
                ai.save_key(body["name"], body["key"])
                return self.send_json(ai.payload())
            if action == "models":
                return self.send_json({"models": ai.list_models(body["provider"])})
            if action == "chat":
                req = assistant.check_chat_body(body)
            else:
                raise ApiError(404, "没有这个地址")
        except ValueError as e:
            raise ApiError(400, str(e)) from None
        except assistant.AssistantError as e:
            raise ApiError(502, str(e)) from None
        self.stream_chat(req)

    def stream_chat(self, req: dict) -> None:
        """以 Server-Sent Events 逐段推给前端；浏览器断开时下一次写入抛 ClientGone，由 dispatch 收尾。"""
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()

        def emit(ev: dict) -> None:
            try:
                self.wfile.write(b"data: " + json.dumps(ev, ensure_ascii=False).encode("utf-8") + b"\n\n")
                self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                raise ClientGone from None

        try:
            self.app.assistant.chat(req, emit)
        except assistant.AssistantError as e:
            emit({"t": "error", "message": str(e)})
        except ClientGone:
            raise
        except Exception as e:  # noqa: BLE001 —— 响应头已经发出，只能把错误作为一条事件交给前端，堆栈留在终端
            traceback.print_exc()
            emit({"t": "error", "message": f"{type(e).__name__}: {e}"})

    def send_json(self, data, status: int = 200) -> None:
        raw = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw)

    def send_file(self, path: Path, ctype: str | None = None, sandbox: bool = False,
                  filename: str | None = None) -> None:
        st = path.stat()
        etag = f'"{st.st_mtime_ns:x}-{st.st_size:x}"'
        if self.headers.get("If-None-Match") == etag:
            self.send_response(304)
            self.send_header("ETag", etag)
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Type", ctype or guess_type(path))
        self.send_header("Content-Length", str(st.st_size))
        self.send_header("ETag", etag)
        self.send_header("Cache-Control", "no-cache")
        if sandbox:
            self.send_header("Content-Security-Policy", SANDBOX_CSP)
        if filename:
            # PDF.js 用它给下载的文件命名；转换结果的网址里没有原文件名
            self.send_header("Content-Disposition", "inline; filename*=UTF-8''" + urllib.parse.quote(filename))
        self.end_headers()
        with path.open("rb") as f:
            shutil.copyfileobj(f, self.wfile, 1 << 20)


class Server(ThreadingHTTPServer):
    daemon_threads = True
    # Windows 上 SO_REUSEADDR 允许两个进程绑同一端口，那样请求会随机落到旧进程上
    allow_reuse_address = sys.platform != "win32"


def already_running(port: int) -> bool:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/ping", timeout=2) as r:
            return json.load(r).get("app") == APP_ID
    except (OSError, ValueError):
        return False


def main() -> None:
    ap = argparse.ArgumentParser(description="研究文档浏览器")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--no-browser", action="store_true", help="启动后不自动打开浏览器")
    args = ap.parse_args()
    url = f"http://127.0.0.1:{args.port}/"

    app = App(args.port)
    try:
        httpd = Server(("127.0.0.1", args.port), Handler)
    except OSError as e:
        if e.errno != errno.EADDRINUSE:
            raise
        if already_running(args.port):
            print(f"文档库已经在运行：{url}")
            if not args.no_browser:
                webbrowser.open(url)
            return
        sys.exit(f"端口 {args.port} 被其他程序占用，用 --port 换一个端口")
    httpd.app = app  # type: ignore[attr-defined]

    def warm_index():
        _, files = app.scan()
        app.index.refresh(files)

    threading.Thread(target=warm_index, daemon=True).start()
    print(f"文档库：{url}")
    print(f"浏览目录：{'、'.join(app.cfg['roots'])}（改目录：页面左下角“管理目录”，或编辑 {CONFIG_PATH.name}）")
    for name, label in (("soffice", "LibreOffice（PPT 与旧版 Office 预览）"), ("pdftotext", "pdftotext（PDF 全文搜索）")):
        print(f"  {label}：{app.tools[name] or '未找到'}")
    print("按 Ctrl+C 退出")
    if not args.no_browser:
        webbrowser.open(url)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n已退出")


if __name__ == "__main__":
    main()
