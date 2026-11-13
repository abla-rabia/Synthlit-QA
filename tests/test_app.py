"""Tests de l'interface : aucun modèle, aucun réseau."""
from types import SimpleNamespace

from ui.quota import Quota
from ui.render import (badge_text, format_pages, license_url, link_citations, refusal_html, safe_url,
                       sources_html)


def test_quota_goes_down_then_stops_at_zero():
    q = Quota(2)
    assert q.premium and q.left == 2
    q.consume(); q.consume(); q.consume()
    assert q.left == 0 and not q.premium


def test_pages():
    assert format_pages((3,)) == "p.3" and format_pages([4, 3]) == "pp.3–4"
    assert format_pages("4-5") == "pp.4–5" and format_pages("") == ""


def test_citations_become_links_and_html_is_escaped():
    out = link_citations("A <script>x</script> [1] and [catalogue]", 2)
    assert "&lt;script&gt;" in out and "<script>" not in out
    assert 'href="#t2-src-1"' in out and 'href="#t2-catalogue"' in out


def test_license_and_url_safety():
    assert license_url("CC BY 4.0") == "https://creativecommons.org/licenses/by/4.0/"
    assert license_url("CC BY-SA 3.0") == "https://creativecommons.org/licenses/by-sa/3.0/"
    assert license_url("MIT") == ""
    assert safe_url("javascript:alert(1)") == "" and safe_url("https://doi.org/x") == "https://doi.org/x"


def _answer():
    hit = SimpleNamespace(text="Some passage " * 60, chunk_id="c1")
    cit = {"n": 1, "citation": "Wang et al., 2023", "title": "T", "link": "https://x.org", "license": "CC BY 4.0",
           "section": "2 Methods", "pages": (3,), "chunk_id": "c1"}
    return SimpleNamespace(citations=[cit], hits=[hit], used_catalogue=False)


def test_sources_card_and_badge():
    html = sources_html(_answer(), 0)
    assert 'id="t0-src-1"' in html and "Wang et al., 2023" in html and "p.3" in html and "…" in html
    assert badge_text(_answer()) == "Grounded in 1 passage"


def test_refusal_language():
    assert "Try asking" in refusal_html("No.", False) and "Essaie" in refusal_html("Non.", True)


def test_with_llm_shares_everything_but_the_llm():
    from rag.pipeline import RagPipeline
    retriever = SimpleNamespace(llm="main", index="shared")
    pipe = RagPipeline(retriever, "main", {}, "prompt", {"generation": {}})
    light = pipe.with_llm("light")
    assert light.llm == "light" and light.retriever.llm == "light"
    assert pipe.llm == "main" and pipe.retriever.llm == "main"          # l'original ne change pas
    assert light.retriever.index == "shared"
