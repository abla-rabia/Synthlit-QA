"""Fabrique le HTML des réponses et des sources (fonctions pures, testables sans Streamlit).

Tout ce qui vient du LLM ou des PDF est échappé avant d'être mis dans le HTML."""
import html
import re

try:                                    # nettoie les marqueurs de références "[12]" des extraits
    from rag.generation.prompt import clean_passage
except ImportError:                     # tests sans le reste du projet
    def clean_passage(text):
        return text

_CITE = re.compile(r"\[(\d+|catalogue)\]", re.IGNORECASE)
_CC = re.compile(r"CC[\s_-]*BY(?P<variant>[\s_-]*SA)?[\s_-]*(?P<ver>\d\.\d)?", re.IGNORECASE)


def esc(text):
    return html.escape(str(text or ""), quote=True)


def format_pages(pages):
    """3 -> 'p.3' ; (3, 4) / '3-4' -> 'pp.3–4' ; vide -> ''."""
    if pages in (None, "", (), []):
        return ""
    if isinstance(pages, (list, tuple, set)):
        nums = sorted({int(p) for p in pages})
        if not nums:
            return ""
        return f"p.{nums[0]}" if len(nums) == 1 else f"pp.{nums[0]}–{nums[-1]}"
    text = str(pages).strip().replace("-", "–")
    if text.lower().startswith("p"):                  # déjà "p. 4" ou "pp. 6–7" : on garde tel quel
        return text.replace("p. ", "p.").replace("pp. ", "pp.")
    return f"pp.{text}" if "–" in text else f"p.{text}"


def link_citations(text, turn):
    """Échappe le texte, puis transforme [n] / [catalogue] en pastilles cliquables."""
    def repl(match):
        tag = match.group(1).lower()
        target = f"t{turn}-catalogue" if tag == "catalogue" else f"t{turn}-src-{tag}"
        return f'<a class="cite" href="#{target}" target="_self">[{tag}]</a>'
    return _CITE.sub(repl, esc(text))


def excerpt(text, limit=420):
    text = re.sub(r"\s+", " ", clean_passage(text or "")).strip()
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0].rstrip(" ,;:.")
    return cut + "…"


def license_url(license_text):
    """'CC BY 4.0' -> https://creativecommons.org/licenses/by/4.0/ ('' si on ne sait pas)."""
    match = _CC.search(license_text or "")
    if not match:
        return ""
    kind = "by-sa" if match.group("variant") else "by"
    return f"https://creativecommons.org/licenses/{kind}/{match.group('ver') or '4.0'}/"


def safe_url(url):
    url = (url or "").strip()
    return url if url.lower().startswith(("http://", "https://")) else ""


def cited_numbers(answer):
    return sorted({c["n"] for c in (answer.citations or []) if isinstance(c.get("n"), int)})


def _hit_for(answer, info):
    hits = answer.hits or []
    n = info.get("n")
    if isinstance(n, int) and 1 <= n <= len(hits):
        return hits[n - 1]
    return next((h for h in hits if getattr(h, "chunk_id", None) == info.get("chunk_id")), None)


def sources_html(answer, turn):
    """Une carte repliable par passage cité : citation, section, pages, extrait, lien."""
    cards = []
    infos = sorted((c for c in (answer.citations or []) if isinstance(c.get("n"), int)),
                   key=lambda c: c["n"])
    for position, info in enumerate(infos):
        hit = _hit_for(answer, info)
        where = " · ".join(x for x in (info.get("section") or "", format_pages(info.get("pages"))) if x)
        quote = excerpt(hit.text) if hit is not None else ""
        link = safe_url(info.get("link"))
        lic = info.get("license") or "CC BY"
        title = esc(info.get("title"))
        body = f'<p class="src-title">{title}</p>' if title else ""
        if quote:
            body += f'<p class="src-quote">“{esc(quote)}”</p>'
        if link:
            body += f'<a class="src-link" href="{esc(link)}" target="_blank" rel="noopener">Open the paper ({esc(lic)}) →</a>'
        cards.append(
            f'<details class="src" id="t{turn}-src-{info["n"]}"{" open" if position == 0 else ""}>'
            f'<summary><span class="cite">[{info["n"]}]</span>'
            f'<span class="src-cite">{esc(info.get("citation"))}</span>'
            f'<span class="src-where">{esc(where)}</span></summary>{body}</details>')
    return "".join(cards)


def badge_text(answer):
    n = len(cited_numbers(answer))
    if n:
        return f"Grounded in {n} passage{'s' if n != 1 else ''}"
    return "From the paper catalogue" if answer.used_catalogue else ""


def refusal_html(text, french=False):
    hint = ("Essaie une question sur la synthèse d'images médicales, les modèles utilisés, les jeux de données ou l'évaluation."
            if french else
            "Try asking about medical image synthesis, the models used, datasets or evaluation.")
    return (f'<div class="refusal"><div class="refusal-icon">'
            '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#1E5B3A" stroke-width="2" '
            'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="11" cy="11" r="7"/>'
            '<path d="M21 21l-4.3-4.3"/></svg></div>'
            f'<p><strong>{esc(text)}</strong> {esc(hint)}</p></div>')
