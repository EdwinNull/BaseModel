#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把"医学数据集构建"调研的论文 PDF 下载到本目录的各阶段子文件夹。

在仓库根目录运行（Windows / macOS / Linux 都可以）：
    python paper/数据集构建调研_20261025/download_papers.py
常用参数：
    --only 01,05,27   只处理这些编号
    --force           已有的 PDF 也重新下载
    --dry-run         只列出计划，不下载

说明：
- 只用 Python 标准库；装了 pypdf（pip install pypdf）会额外读 PDF 首页核对标题。
- 来源只用 arXiv、出版社开放 PDF、PMC 官方开放数据桶（pmc-oa-opendata.s3.amazonaws.com，
  按 Europe PMC 接口查 PMCID）。不绕过任何网站的人机验证；下不了的会列出原因和落地页，请手动下载。
- 不读、不写仓库的 data/ 目录。PDF 已被 .gitignore 的 *.pdf 排除，不会进仓库。
- 结果写到本目录 下载核对结果.md 和 download_log.json。
"""
import argparse
import datetime
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
MANIFEST = os.path.join(HERE, "papers_manifest.json")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
S3 = "https://pmc-oa-opendata.s3.amazonaws.com"


def http_get(url, timeout=90, accept="application/pdf,*/*;q=0.8"):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": accept})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.geturl(), r.read()


def epmc_pmcid(doi):
    """用 Europe PMC 官方接口按 DOI 查 PMCID（查不到返回 None）。"""
    q = urllib.parse.quote(f'DOI:"{doi}"')
    url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/search?format=json&query={q}"
    try:
        _, body = http_get(url, timeout=30, accept="application/json")
        res = json.loads(body.decode("utf-8")).get("resultList", {}).get("result", [])
        for r in res:
            if r.get("pmcid"):
                return r["pmcid"]
    except Exception:
        return None
    return None


def s3_pdf_urls(pmcid):
    """PMC 开放数据桶：<PMCID>.<版本>/<PMCID>.<版本>.pdf；新版本优先。"""
    urls = []
    for v in range(1, 9):
        base = f"{S3}/{pmcid}.{v}/{pmcid}.{v}"
        try:
            _, body = http_get(base + ".json", timeout=30, accept="application/json")
        except urllib.error.HTTPError as e:
            if e.code in (403, 404):
                if urls:
                    break
                continue
            raise
        except Exception:
            break
        try:
            meta = json.loads(body.decode("utf-8"))
        except Exception:
            meta = {}
        pdf = meta.get("pdf_url") or ""
        if pdf.startswith("s3://pmc-oa-opendata/"):
            pdf = S3 + "/" + pdf[len("s3://pmc-oa-opendata/"):]
        pdf = pdf.split("?")[0] if pdf else base + ".pdf"
        urls.insert(0, pdf)
    return urls


def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def title_check(path, title):
    try:
        from pypdf import PdfReader
    except Exception:
        return None, "未装 pypdf，未读首页"
    try:
        rd = PdfReader(path)
        text = " ".join((rd.pages[i].extract_text() or "") for i in range(min(2, len(rd.pages))))
    except Exception as e:
        return None, f"读 PDF 失败：{e}"
    words = [w for w in norm(title).split() if len(w) >= 4]
    t = norm(text).replace(" ", "")
    hit = sum(1 for w in words if w in t)
    ratio = hit / max(1, len(words))
    return ratio >= 0.8, f"首页标题词命中 {hit}/{len(words)}"


def candidates(p):
    for s in p["sources"]:
        if s["type"] == "url":
            yield s["url"]
        elif s["type"] == "pmc_oa":
            pmcid = s.get("pmcid") or (epmc_pmcid(p["doi"]) if p.get("doi") else None)
            if pmcid:
                for u in s3_pdf_urls(pmcid):
                    yield u


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    with open(MANIFEST, encoding="utf-8") as f:
        man = json.load(f)
    only = {x.strip().zfill(2) for x in a.only.split(",") if x.strip()}
    log = []
    for p in man["papers"]:
        if only and p["no"] not in only:
            continue
        dest = os.path.join(HERE, p["stage_dir"], p["file"])
        rec = {"no": p["no"], "file": os.path.relpath(dest, HERE), "title": p["title"]}
        if os.path.exists(dest) and not a.force:
            rec["status"] = "已存在（跳过）"
        elif a.dry_run:
            rec["status"] = "计划下载"
        else:
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            errs = []
            for url in candidates(p):
                try:
                    final, body = http_get(url)
                except Exception as e:
                    errs.append(f"{url} → {e}")
                    continue
                if not body.startswith(b"%PDF-") or len(body) < 20000:
                    errs.append(f"{url} → 不是 PDF（可能是人机验证页）")
                    continue
                with open(dest, "wb") as f:
                    f.write(body)
                rec.update(status="已下载", url=final, bytes=len(body),
                           sha256=hashlib.sha256(body).hexdigest())
                break
            else:
                rec.update(status="下载失败", errors=errs[-3:], landing=p.get("landing"))
            time.sleep(1.0)
        if os.path.exists(dest):
            with open(dest, "rb") as f:
                h = hashlib.sha256(f.read()).hexdigest()
            rec["sha256"] = h
            exp = p.get("sha256")
            if exp and h == exp:
                rec["identity"] = "与浏览器核对时的 sha256 一致"
            else:
                ok, msg = title_check(dest, p["title"])
                rec["identity"] = ("标题匹配；" if ok else "标题待核；" if ok is False else "") + msg
        print(f'[{p["no"]}] {rec["status"]}  {rec.get("identity","")}  {rec["file"]}')
        if rec["status"] == "下载失败":
            print(f'      请在浏览器打开 {p.get("landing")} 手动下载，另存为 {dest}')
        log.append(rec)
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    with open(os.path.join(HERE, "download_log.json"), "w", encoding="utf-8") as f:
        json.dump({"time": now, "records": log}, f, ensure_ascii=False, indent=1)
    lines = [f"# 下载核对结果（{now}，由 download_papers.py 生成）", "",
             "| 编号 | 状态 | 身份核对 | 文件 |", "|---|---|---|---|"]
    for r in log:
        lines.append(f'| {r["no"]} | {r["status"]} | {r.get("identity","")} | {r["file"]} |')
    fails = [r for r in log if r["status"] == "下载失败"]
    if fails:
        lines += ["", "## 需要手动下载", ""]
        lines += [f'- {r["no"]} {r["title"]}：{r.get("landing")} → 保存为 `{r["file"]}`' for r in fails]
    with open(os.path.join(HERE, "下载核对结果.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"\n完成：{sum(r['status']=='已下载' for r in log)} 篇下载，{len(fails)} 篇失败。详见 下载核对结果.md")


if __name__ == "__main__":
    sys.exit(main())
