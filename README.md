# SynthLit — cited Q&A over deep-learning papers on medical image synthesis

> Ask a question in plain language and get an answer grounded in 21 open-access papers,
> with numbered citations (paper, section, pages). If the papers do not contain
> the answer, the assistant says so instead of guessing.

<!-- TODO when the app is live: add the demo link and a screenshot here -->

<!-- TODO: demo link  ·  ![screenshot](docs/screenshot.png) -->

---

## What it does

- Answers questions about a fixed collection of 21 CC BY papers (reviews and method papers on MRI/CT/PET synthesis, GANs, transformers, diffusion models, CBCT-to-CT for radiotherapy).
- Every statement carries a citation `[n]` that points to the exact passage: article, section, pages.
- Questions about the collection itself ("which papers are reviews?") are answered from a catalogue and cited `[catalogue]`.
- Off-topic questions, including prompt-injection attempts, are refused.
- Follow-up questions work ("and for PET?") thanks to a conversation memory that is kept in RAM only.
- Nothing about the user's questions is stored.

## How it works

```
PDF ──► extraction ──► reading order ──► cleaning ──► chunks by section ──► table descriptions ──► index (Chroma)
        (hi_res)        (reorder)        (clean)       (≤450 tokens)         (LLM, for embedding)    + chunks.jsonl

question + history ─► standalone question ─► 3 queries (1 + 2 rewrites) ─► hybrid search per query
                                                                              (0.7 semantic + 0.3 BM25, weighted RRF, 10 each)
                                      ─► RRF over the 3 lists (10) ─► cross-encoder rerank (5) ─► LLM answer with [n] citations
```

**Ingestion** (`scripts/build_index.py`)
- Text and tables are extracted with `unstructured` (hi_res); the raw output is cached as JSON because it is slow to produce.
- Reading order is repaired for two-column pages, headers/footers and boilerplate are removed.
- Chunks follow the paper structure: one chunk per section or subsection, split at ≤ 450 tokens (embedding-model tokens) with a 60-token overlap made of whole sentences. A table never forms a chunk on its own.
- Tables keep their **original HTML** in the metadata. For search, an LLM writes a short description of each table that is appended to the text used for the embedding; the answering LLM always receives the original text and the original table, never the description.
- Each chunk is embedded with a header `Author et al., year · section` using `BAAI/bge-small-en-v1.5` and stored in Chroma (cosine). The same chunks are written to `chunks.jsonl` for the keyword search.

**Retrieval** (`rag/retrieval/`)
- A follow-up question is rewritten into a standalone question using the chat history.
- The LLM produces 2 alternative queries with structured output (`json_schema`); with the original, 3 queries are searched. If it fails, the original question is used alone.
- Each query runs a semantic search and a BM25 keyword search, merged with weighted Reciprocal Rank Fusion (0.7 / 0.3 on ranks, k = 60) down to 10 chunks.
- The three lists are fused again with RRF (10 candidates), then a cross-encoder (`ms-marco-MiniLM-L-6-v2`) keeps the best 5.
- Multi-query, hybrid search and reranking each have an on/off switch in `config/settings.yaml` so they can be measured separately.

**Generation** (`rag/generation/`)
- Groq `openai/gpt-oss-20b`, temperature 0. The prompt contains the 5 numbered passages and a compact catalogue of the 21 papers.
- Citations are validated by code: only `[1]`–`[5]` and `[catalogue]` are accepted; one retry on invalid or missing citations, then invalid numbers are stripped.
- Refusal uses a language-independent marker (`NO_ANSWER`), and the code prints the refusal message. The answer language is decided by code, not guessed by the model.
- Chat memory keeps the last 4 exchanges without their citations, so numbering never clashes between turns.

## Evaluation

**Protocol.** 14 hand-written questions over the 21 indexed papers: 8 answerable from a passage
(specific facts, definitions, a comparison, a discussion question, a dataset/table question),
1 catalogue question and 5 off-topic questions (including a prompt-injection attempt).
3 questions were held out and never used to tune anything. The gold passage is an
article + section + pages written by me; for 4 questions it was first seeded from the system's
output and then checked against the papers. Retrieval and generation are measured separately.

| Metric | Result |
|---|---|
| Recall@10 (gold passage in the 10 candidates) | 0.875 (7/8) |
| Recall@5 (still there after reranking) | 0.875 (7/8) |
| Off-topic questions refused | 5/5 |
| Answerable questions wrongly refused | 1 (q05) |
| Answers with valid citation numbers | 100% |
| Faithfulness (claims supported by the retrieved passages) | 85% (34/40 claims, 7 answers checked by hand) |

**Reranker ablation** (same questions, same gold):

| Config | Recall@10 | Recall@5 | Avg rank of 1st relevant passage | Wrongly refused |
|---|---|---|---|---|
| With reranker (default) | 0.88 | 0.88 | 2.29 → 1.14 | 1 |
| Without reranker | 0.88 | 0.88 | 1.57 | 2 |

Recall is identical, but the reranker moves the first relevant passage from rank 2.3 to 1.1
and one more answerable question was refused without it (q02, in both runs I made without it).
Hybrid search and multi-query were not ablated in v1.

**What works.** Questions answered by one passage (facts, definitions, a table question) are
retrieved reliably, off-topic questions are always refused, and every answer carries
validated citations.


Reproduce: `python scripts/eval.py --name baseline` then `python scripts/compare.py data/eval/runs/baseline data/eval/runs/sans_rerank`
(questions live in `data/eval/questions.yaml`; `scripts/find_gold.py` finds passages, `scripts/explain.py` shows where a gold passage is lost).

## Known limits

- **Wording sensitivity.** The generic question "What are different learning paradigms…" misses the dedicated section (the 5 retained passages are generic review chunks) and the system correctly refuses.
- **Broad, cross-paper questions** are poorly covered. q06 ("body regions") counts as a hit because my gold is broad, but the answer only lists the brain and whole-body; the retained passages often come from one review.
- **Small sample.** One question moves a score by ~7 points. Only one table question was tested. Gold for 4 questions was seeded from the system's output, so recall on those may be slightly optimistic.
- **English-first.** The embedding model and papers are English; questions in French are answered in French, but retrieval is weaker. Equations and figures are not indexed, and some headings are mis-detected by the extraction.
- **Free tier limits.** The Groq free tier limits tokens per minute; the evaluation script retries automatically.

## Project structure

```
config/            settings.yaml (numbers, paths, on/off switches) and prompts/
data/              pdf/, clean_sources.csv, chunks.jsonl, index/, eval/ (questions.yaml, runs/)
rag/ingestion/     extraction cache, reorder, clean, chunk_by_section, tables, index, pipeline
rag/retrieval/     queries, search (Chroma + BM25), fusion (RRF), rerank, retriever
rag/generation/    prompt, citations, answer
rag/               pipeline.py (RagPipeline, Conversation), evaluation.py, sources.py, config.py, types.py
scripts/           build_index.py, chat.py, eval.py, compare.py, find_gold.py, explain.py
tests/             unit tests with fake components (no model, no network)
```

## Run it locally

```bash
python -m venv .venv && source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install unstructured[pdf] langchain-core langchain-chroma langchain-huggingface langchain-groq \
            sentence-transformers rank-bm25 python-dotenv pyyaml pydantic pytest
# hi_res extraction also needs system tools (poppler, tesseract): see the unstructured docs
echo "GROQ_API_KEY=your_key" > .env                         # never commit .env
python scripts/build_index.py          # PDFs -> chunks -> index (long the first time)
python scripts/chat.py --debug         # terminal chat; --no-rerank / --no-hybrid / --no-multiquery
pytest -q                              # unit tests
```

<!-- TODO: add requirements.txt (app only) and requirements-ingest.txt (extraction) once the app is deployed -->

## Data, licences and privacy

- The collection contains only papers published under **CC BY** licences, selected one by one; the authors, titles, links and licences are listed in the Credits page / `CREDITS.md`. <!-- TODO: say whether the PDFs are included in the repo -->
- Papers with NC/ND licences were excluded and are never committed.
- The user's questions are not stored; chat memory lives in RAM only. The API key lives in `.env`, which is git-ignored.

## Design decisions (short)

| Decision | Why |
|---|---|
| Chunk by section, not by fixed size | Scientific papers are structured; headings give natural, citable units |
| Table descriptions only for the embedding | Tables are hard to embed, but the exact original table must reach the answering LLM |
| Hybrid 0.7 / 0.3 + multi-query + rerank | Standard recipe for recall and ranking, with switches to measure each |
| Citations validated by code | A cited number must point to a real passage; invalid ones are never shown |
| Language-independent refusal marker | Detecting a refusal by an exact sentence broke when the model translated it |
| Gold = article + section + pages | Robust to re-chunking; matches the citation the user sees |

## Author

Abla Rabia — AI engineer

