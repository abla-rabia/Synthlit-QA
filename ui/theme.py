"""Look « scientifique mignon » vert (d'après la maquette) : CSS, en-tête, pied de page."""
import streamlit as st

from ui.render import esc

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=Nunito:wght@400;600;700;800&display=swap');
:root{--ink:#17321F;--green:#1E5B3A;--accent:#2F7D4F;--muted:#4A6554;--line:#CFE5D0;--soft:#E3F3E4;--mint:#DDEFDC;--hl:#BFE3BC}
html,body,.stApp,[class*="css"]{font-family:'Nunito',system-ui,sans-serif;color:var(--ink)}
.stApp{background-color:#F2F8F1;background-image:linear-gradient(#E1EEDF 1px,transparent 1px),linear-gradient(90deg,#E1EEDF 1px,transparent 1px);background-size:28px 28px}
[data-testid="stSidebar"],[data-testid="stSidebarCollapsedControl"],[data-testid="stHeader"],[data-testid="stToolbar"],#MainMenu,footer{display:none!important}
.block-container{max-width:%(width)spx;padding:1rem 1rem 3rem}
a,[data-testid="stMarkdownContainer"] a{color:var(--green)}a:hover{color:#123F27}
/* en-tête */
.brand{display:flex;align-items:center;gap:12px}
.brand-logo{width:42px;height:42px;border-radius:13px;background:var(--accent);display:flex;align-items:center;justify-content:center}
.brand-name{font-size:21px;font-weight:800;color:var(--green)}
[data-testid="stPageLink"] a{text-decoration:none;font-weight:700;font-size:16px;color:var(--green);justify-content:center;padding:.4rem .2rem}
[data-testid="stPageLink"] a p{font-size:16px;font-weight:700;color:var(--green)}
[data-testid="stPageLink"] a:hover{background:var(--soft);border-radius:10px}
/* zone de saisie du chat (fixée en bas) */
[data-testid="stBottom"],[data-testid="stBottom"]>div,[data-testid="stBottomBlockContainer"]{background:transparent!important}
[data-testid="stBottomBlockContainer"]{max-width:%(width)spx;padding-bottom:1.2rem}
[data-testid="stChatInput"]{background:#fff;border:2px solid var(--line);border-radius:22px;box-shadow:0 10px 28px rgba(30,91,58,.10)}
[data-testid="stChatInput"] textarea{font-family:'Nunito',sans-serif;font-size:17px;color:var(--ink)}
[data-testid="stChatInput"] button{background:var(--accent);color:#fff;border-radius:12px}
/* titre */
.hero{text-align:center;display:flex;flex-direction:column;align-items:center;gap:14px;margin:26px 0 8px}
.tag{font-family:'IBM Plex Mono',monospace;font-size:13px;font-weight:500;color:var(--green);background:var(--mint);border-radius:999px;padding:6px 14px}
.hero h1,.title h1{margin:0;padding:0;font-size:52px;line-height:1.1;font-weight:800;color:var(--green)}
.hl{background-image:linear-gradient(transparent 62%%,var(--hl) 62%%)}
.hero p{margin:0;font-size:18px;line-height:1.55;color:var(--muted);max-width:600px}
/* cartes */
[class*="st-key-card"]{background:#fff;border:2px solid var(--line)!important;border-radius:22px;padding:14px 18px;box-shadow:0 10px 28px rgba(30,91,58,.08)}
[data-testid="stTextInput"] label p{font-size:14px;font-weight:700;color:var(--green)}
[data-testid="stTextInput"] input{font-family:'Nunito',sans-serif;font-size:17px;background:#F7FBF6;border:1.5px solid var(--line);border-radius:14px;padding:14px 16px;color:var(--ink)}
.stButton button,[data-testid="stFormSubmitButton"] button{font-family:'Nunito',sans-serif;font-weight:700;border-radius:999px;border:0;background:var(--soft);color:var(--green);min-height:44px}
.stButton button:hover{background:var(--hl);color:var(--green)}
[data-testid="stFormSubmitButton"] button{background:var(--accent);color:#fff;font-size:17px;font-weight:800;border-radius:14px;min-height:48px}
[data-testid="stFormSubmitButton"] button:hover{background:#25683f;color:#fff}
.stButton button p{white-space:normal;line-height:1.25}.stButton button{height:auto;padding:.5rem .8rem}
.try{font-size:14px;color:var(--muted);font-weight:600;margin:4px 0}
/* question / réponse */
.bubble-wrap{display:flex;justify-content:flex-end;margin:28px 0 12px}
.bubble{max-width:80%%;background:var(--accent);color:#fff;border-radius:18px 18px 4px 18px;padding:12px 18px;font-size:16px;font-weight:600}
.ans-top{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:10px;margin-bottom:6px}
.label{font-family:'IBM Plex Mono',monospace;font-size:12px;font-weight:500;letter-spacing:.1em;color:var(--green)}
.badge{font-size:13px;font-weight:700;color:var(--green);background:var(--mint);border-radius:999px;padding:5px 12px;margin-left:6px}
[class*="st-key-card"] p,[class*="st-key-card"] li{font-size:17px;line-height:1.7}
a.cite,span.cite{font-family:'IBM Plex Mono',monospace;font-size:14px;font-weight:500;text-decoration:none;background:var(--soft);border-radius:8px;padding:2px 8px}
h2.sources{margin:14px 0 8px;padding:0;font-size:16px;font-weight:800;color:var(--green)}
details.src{background:#F7FBF6;border:1.5px solid var(--line);border-radius:16px;padding:14px 16px;margin-bottom:10px}
details.src summary{cursor:pointer;display:flex;flex-wrap:wrap;align-items:baseline;gap:10px;min-height:32px}
.src-cite{font-size:16px;font-weight:800}
.src-where{font-family:'IBM Plex Mono',monospace;font-size:13px;color:var(--muted)}
details.src p.src-title{margin:12px 0 0;font-size:14px!important;font-weight:700;color:var(--green)}
details.src p.src-quote{margin:10px 0;font-size:15px!important;line-height:1.65;color:#2B4A37;border-left:4px solid var(--hl);padding-left:14px;font-style:italic}
a.src-link{font-size:14px;font-weight:700}
.note{font-size:13px;line-height:1.5;color:var(--muted);margin:6px 0 0}
.refusal{display:flex;align-items:flex-start;gap:14px;background:#fff;border:2px dashed #9CCBA0;border-radius:18px;padding:18px 20px}
.refusal-icon{flex:none;width:36px;height:36px;border-radius:50%%;background:var(--mint);display:flex;align-items:center;justify-content:center}
.refusal p{margin:0;font-size:16px;line-height:1.6}
.infobox{display:flex;align-items:flex-start;gap:14px;background:#E8F4E7;border-radius:18px;padding:18px 20px;margin-top:22px}
.infobox p{margin:0;font-size:15px;line-height:1.6}
.foot{text-align:center;font-size:14px;line-height:1.6;color:var(--muted);margin-top:44px}
/* crédits */
.title{margin-top:24px}.title h1{font-size:44px}
.intro{font-size:17px;line-height:1.65;color:var(--muted);margin:10px 0 22px}
.tablebox{background:#fff;border:2px solid var(--line);border-radius:20px;padding:8px 20px;overflow-x:auto;box-shadow:0 10px 28px rgba(30,91,58,.08)}
.tablebox table{width:100%%;min-width:640px;border-collapse:collapse;font-size:15px;line-height:1.5}
.tablebox th{text-align:left;font-family:'IBM Plex Mono',monospace;font-size:12px;letter-spacing:.08em;color:var(--muted);font-weight:500;padding:14px 10px 10px}
.tablebox table,.tablebox th{border:0!important}
.tablebox td{padding:14px 10px;border:0!important;border-top:1.5px solid #E3F0E2!important;vertical-align:top}
.tablebox td.paper{font-weight:700}
.tablebox td.year{font-family:'IBM Plex Mono',monospace}
@media (max-width:640px){.hero h1{font-size:38px}.title h1{font-size:34px}.bubble{max-width:92%%}}
</style>
"""

LOGO = ('<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2" '
        'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 19C5 10 10 5 20 4c0 10-5 15-13 15"/>'
        '<path d="M5 19c3-4 6-7 10-10"/></svg>')


def setup(title, width=800):
    st.set_page_config(page_title=title, page_icon="🌿", layout="centered")
    st.markdown(CSS % {"width": width}, unsafe_allow_html=True)


def header(name):
    """Logo + nom, liens Ask / Credits (st.page_link garde la session)."""
    cols = st.columns([3.2, 0.9, 1.3, 2.4], vertical_alignment="center")
    cols[0].markdown(f'<div class="brand"><div class="brand-logo">{LOGO}</div>'
                     f'<span class="brand-name">{esc(name)}</span></div>', unsafe_allow_html=True)
    cols[1].page_link("app.py", label="Ask")
    cols[2].page_link("pages/Credits.py", label="Credits")
