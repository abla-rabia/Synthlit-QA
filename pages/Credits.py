"""Page Crédits : générée automatiquement depuis la table des sources (aucun texte à maintenir à la main)."""
import streamlit as st
from dotenv import load_dotenv

from ui import render, theme

load_dotenv()


@st.cache_data
def load_table():
    from rag.config import load_settings
    from rag.sources import load_sources, short_authors
    settings = load_settings("config/settings.yaml")
    sources = load_sources(settings["paths"]["sources"]).values()
    rows = sorted(sources, key=lambda s: (s.get("year", ""), s.get("title", "")), reverse=True)
    return settings.get("app", {}).get("name", "SynthLit"), [
        {**s, "short": short_authors(s.get("authors", ""))} for s in rows]


def _row(s):
    link = render.safe_url(s.get("link"))
    title = render.esc(s.get("title"))
    paper = f'<a href="{render.esc(link)}" target="_blank" rel="noopener">{title}</a>' if link else title
    lic = s.get("license") or "CC BY"
    lic_url = render.license_url(lic)
    lic_html = (f'<a href="{lic_url}" target="_blank" rel="noopener">{render.esc(lic)}</a>'
                if lic_url else render.esc(lic))
    return (f'<tr><td class="paper">{paper}</td><td>{render.esc(s["short"])}</td>'
            f'<td class="year">{render.esc(s.get("year"))}</td><td>{lic_html}</td></tr>')


theme.setup("Credits and licences", width=920)
name, rows = load_table()
theme.header(name)

st.markdown(
    '<div class="title"><h1>Credits and <span class="hl">licences</span></h1></div>'
    '<p class="intro">Every indexed paper is open access under a Creative Commons licence '
    '(<a href="https://creativecommons.org/licenses/by/4.0/" target="_blank" rel="noopener">CC BY</a>). '
    'Excerpts are shown with attribution. Changes made by this project: text extracted from the PDFs, '
    'cleaned, and split into passages for search.</p>'
    '<div class="tablebox"><table><thead><tr><th>PAPER</th><th>AUTHORS</th><th>YEAR</th><th>LICENCE</th></tr></thead>'
    f'<tbody>{"".join(_row(s) for s in rows)}</tbody></table></div>'
    '<div class="infobox"><p>Papers published under a non-commercial or no-derivatives licence were excluded. '
    'No question asked here is stored.</p></div>', unsafe_allow_html=True)
