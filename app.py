"""Page principale : un chat. Question en bas, réponses citées au-dessus.

Lancer : streamlit run app.py
Rien n'est stocké : l'historique vit dans la session du navigateur (RAM)."""
import logging
import os

import streamlit as st
from dotenv import load_dotenv

from ui import render, theme

load_dotenv()
SETTINGS_PATH = "config/settings.yaml"
VERSION = "v1.0.0"
log = logging.getLogger("app")

DEFAULT_EXAMPLES = ["How do vision transformers work?", "Which papers are reviews?",
                    "What challenges does the field face?"]


@st.cache_resource(show_spinner="Loading the papers (first visit only)…")
def load_everything():
    """Chargé UNE fois pour tous les visiteurs : (settings, pipeline)."""
    from rag.config import load_settings
    from rag.pipeline import load_pipeline

    if "GROQ_API_KEY" not in os.environ:               # Hugging Face : secret du Space
        try:
            os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]
        except Exception:
            pass
    settings = load_settings(SETTINGS_PATH)
    return settings, load_pipeline(settings)


def _error_message(exc):
    """Message clair pour l'utilisateur (limite Groq par minute ou par jour, ou autre problème)."""
    text = str(exc).lower()
    if "429" in text or "rate limit" in text or "rate_limit" in text:
        if "per day" in text or "tpd" in text or "rpd" in text:
            return "The free daily limit of the language model has been reached. Please come back tomorrow."
        return "The free language model is busy right now (per-minute limit). Wait about a minute and ask again."
    return "Something went wrong while answering. Please try again."


def _ask(question, pipeline, max_turns):
    from rag.pipeline import Conversation

    if "chat" not in st.session_state:
        st.session_state.chat = Conversation(pipeline, max_turns=max_turns)
    return st.session_state.chat.ask(question)


def _bubble(question):
    st.markdown(f'<div class="bubble-wrap"><div class="bubble">{render.esc(question)}</div></div>',
                unsafe_allow_html=True)


def _render_answer(answer, index):
    if answer.refused:
        st.markdown(render.refusal_html(answer.text), unsafe_allow_html=True)
        return
    with st.container(key=f"card_{index}"):
        badge = render.badge_text(answer)
        tags = f'<span class="badge">{badge}</span>' if badge else ""
        st.markdown(f'<div class="ans-top"><span class="label">ANSWER</span><span>{tags}</span></div>',
                    unsafe_allow_html=True)
        st.markdown(render.link_citations(answer.text, index), unsafe_allow_html=True)
        sources = render.sources_html(answer, index)
        if sources:
            st.markdown('<h2 class="sources">Sources</h2>' + sources, unsafe_allow_html=True)
        if answer.used_catalogue:
            st.markdown(f'<p class="note" id="t{index}-catalogue"><span class="cite">[catalogue]</span> '
                        'is the list of the indexed papers (see the Credits page).</p>', unsafe_allow_html=True)
        st.markdown('<p class="note">Answers use only the indexed papers. Not medical advice.</p>',
                    unsafe_allow_html=True)


def main():
    theme.setup("Ask the papers")

    try:
        settings, pipeline = load_everything()
    except Exception as exc:              # clé absente, index manquant…
        log.exception("startup failed")
        st.error("The app could not start (missing index or API key). Check the logs.")
        st.stop()
    cfg = settings.get("app", {})
    theme.header(cfg.get("name", "SynthLit"))
    max_chars = cfg.get("max_question_chars", 500)
    examples = cfg.get("examples", DEFAULT_EXAMPLES)
    n_papers = len(pipeline.sources)

    st.session_state.setdefault("turns", [])
    turns = st.session_state.turns
    pending = None

    welcome = st.empty()                  # écran d'accueil : effacé dès qu'une question est posée
    if not turns:
        with welcome.container():
            st.markdown(
                f'<div class="hero"><span class="tag">{n_papers} open-access papers · CC BY</span>'
                '<h1>Ask the <span class="hl">papers</span></h1>'
                '<p>Cited answers about deep learning for medical image synthesis. '
                'Every claim points to its paper, section and page.</p></div>', unsafe_allow_html=True)
            st.markdown('<div class="try" style="text-align:center">Try:</div>', unsafe_allow_html=True)
            for column, example in zip(st.columns(len(examples)), examples):
                if column.button(example, key=f"ex_{example}", use_container_width=True):
                    pending = example
            st.markdown(f'<div class="foot">Built on {n_papers} CC BY papers · {VERSION} · '
                        'No question is stored.</div>', unsafe_allow_html=True)

    typed = st.chat_input("Ask a question about the papers…", max_chars=max_chars)
    pending = pending or (typed.strip() if typed else None)
    if pending:
        welcome.empty()

    for index, turn in enumerate(turns):  # ordre normal : le plus ancien en haut
        _bubble(turn["question"])
        _render_answer(turn["answer"], index)

    if pending:
        index = len(turns)
        _bubble(pending)
        try:
            with st.spinner("Searching the papers…"):
                answer = _ask(pending, pipeline, settings["retrieval"].get("history_turns", 4))
            turns.append({"question": pending, "answer": answer})
            _render_answer(answer, index)
        except Exception as exc:
            log.exception("answer failed")
            st.warning(_error_message(exc))

    if turns and st.button("New conversation", key="reset"):
        st.session_state.turns = []
        st.session_state.pop("chat", None)
        st.rerun()


main()
