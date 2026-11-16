"""文档浏览器服务端的边界测试：路径越界、排除规则、PPT 页码与搜索片段。全部用虚构文件。"""
import zipfile

import pytest

import server


@pytest.fixture
def repo(tmp_path, monkeypatch):
    (tmp_path / "docs" / "sub").mkdir(parents=True)
    (tmp_path / "docs" / "sub" / "a.md").write_text("# 标题\n转重预测\n", encoding="utf-8")
    (tmp_path / "docs" / ".hidden").mkdir()
    (tmp_path / "docs" / ".hidden" / "x.md").write_text("x", encoding="utf-8")
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "patient.csv").write_text("虚构", encoding="utf-8")
    monkeypatch.setattr(server, "REPO", tmp_path)
    return tmp_path


CFG = {"roots": ["docs"], "exclude": [".*", "~$*"]}


def test_resolve_rejects_paths_outside_roots(repo):
    assert server.resolve_in_roots(CFG, "docs/sub/a.md") == repo / "docs" / "sub" / "a.md"
    for rel in ("data/patient.csv", "docs/../data/patient.csv", "../etc/passwd", "docs/.hidden/x.md"):
        with pytest.raises(server.ApiError) as e:
            server.resolve_in_roots(CFG, rel)
        assert e.value.status == 403


def test_normalize_roots_rejects_overlap_and_missing(repo):
    assert server.normalize_roots(["docs/", str(repo / "data")]) == ["docs", "data"]
    with pytest.raises(ValueError, match="互相包含"):
        server.normalize_roots(["docs", "docs/sub"])
    with pytest.raises(ValueError, match="不存在"):
        server.normalize_roots(["nope"])
    with pytest.raises(ValueError, match="之内"):
        server.normalize_roots(["../"])


def _slide(text, hidden=False):
    show = ' show="0"' if hidden else ""
    return (f'<p:sld xmlns:p="p" xmlns:a="a"{show}><p:cSld><a:p><a:r><a:t>{text}</a:t></a:r></a:p>'
            "</p:cSld></p:sld>")


def test_pptx_text_follows_presentation_order_and_skips_hidden(tmp_path):
    path = tmp_path / "deck.pptx"
    with zipfile.ZipFile(path, "w") as z:
        # slide1.xml 在演示里排第二，slide3.xml 是隐藏页
        z.writestr("ppt/presentation.xml",
                   '<p:presentation xmlns:p="p" xmlns:r="r"><p:sldIdLst>'
                   '<p:sldId id="256" r:id="rId2"/><p:sldId id="257" r:id="rId1"/><p:sldId id="258" r:id="rId3"/>'
                   "</p:sldIdLst></p:presentation>")
        z.writestr("ppt/_rels/presentation.xml.rels",
                   '<Relationships><Relationship Id="rId1" Target="slides/slide1.xml" Type="t"/>'
                   '<Relationship Target="slides/slide2.xml" Id="rId2" Type="t"/>'
                   '<Relationship Id="rId3" Type="t" Target="slides/slide3.xml"/></Relationships>')
        z.writestr("ppt/slides/slide1.xml", _slide("第二页 &amp; 结局"))
        z.writestr("ppt/slides/slide2.xml", _slide("第一页"))
        z.writestr("ppt/slides/slide3.xml", _slide("隐藏页", hidden=True))
    text = server.office_text(path)
    assert text.split("\f") == ["第一页", "第二页 & 结局"]
    hits = server.find_snippets(text, text.lower(), "结局", 3)
    assert hits == [{"text": "第二页 & 结局", "page": 2}]


def test_search_reports_skipped_and_matches_all_terms(repo):
    (repo / "docs" / "broken.docx").write_bytes(b"not a zip")
    _, files = server.scan(CFG)
    index = server.SearchIndex({"pdftotext": None, "soffice": None})
    res = index.search("转重 预测", files)
    assert [r["path"] for r in res["results"]] == ["docs/sub/a.md"]
    assert res["results"][0]["hits"] == [{"text": "转重预测", "line": 2}]
    assert [s["path"] for s in res["skipped"]] == ["docs/broken.docx"]
    assert index.search("转重 不存在的词", files)["results"] == []
