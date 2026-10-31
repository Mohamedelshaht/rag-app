import io
import os
from pathlib import Path

import numpy as np
import streamlit as st
from anthropic import Anthropic
from fastembed import TextEmbedding
from pypdf import PdfReader

EMBED_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"  # يدعم العربي
DOCS_DIR = Path(__file__).parent / "docs"
CHUNK_SIZE = 900
CHUNK_OVERLAP = 150
TOP_K = 4
ALLOWED = {".pdf", ".txt", ".md"}

SYSTEM_PROMPT = (
    "You are a helpful assistant that answers ONLY from the provided context passages. "
    "If the answer is not in the context, say you could not find it in the documents. "
    "Reply in the same language as the user's question. "
    "Cite the source file name in square brackets after each claim, e.g. [file.pdf]."
)

st.set_page_config(page_title="مساعد المستندات", page_icon="📚")


# ---------- الإعدادات والأسرار ----------
def get_secret(name, default=None):
    try:
        return st.secrets[name]
    except Exception:
        return os.getenv(name, default)


API_KEY = get_secret("ANTHROPIC_API_KEY")
MODEL = get_secret("CLAUDE_MODEL", "claude-sonnet-5-5")
APP_PASSWORD = get_secret("APP_PASSWORD")  # اختياري: يحمي التطبيق من استهلاك رصيدك


def check_password():
    if not APP_PASSWORD or st.session_state.get("authed"):
        return
    pwd = st.text_input("كلمة المرور", type="password")
    if pwd and pwd == APP_PASSWORD:
        st.session_state["authed"] = True
        st.rerun()
    elif pwd:
        st.error("كلمة المرور غلط")
    st.stop()


# ---------- قراءة وتقطيع المستندات ----------
def read_file(name: str, data: bytes) -> str:
    if name.lower().endswith(".pdf"):
        reader = PdfReader(io.BytesIO(data))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    return data.decode("utf-8", errors="ignore")


def chunk_text(text: str, source: str):
    text = " ".join(text.split())
    chunks, start = [], 0
    while start < len(text):
        chunks.append({"source": source, "text": text[start : start + CHUNK_SIZE]})
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks


# ---------- Embeddings ----------
@st.cache_resource(show_spinner="جاري تحميل نموذج التضمين (أول مرة بس)...")
def get_embedder():
    return TextEmbedding(model_name=EMBED_MODEL)


def embed(texts):
    vecs = np.array(list(get_embedder().embed(texts)), dtype="float32")
    return vecs / np.linalg.norm(vecs, axis=1, keepdims=True)


@st.cache_resource(show_spinner="جاري فهرسة المستندات...")
def build_base_index():
    chunks = []
    for path in sorted(DOCS_DIR.glob("*")):
        if path.suffix.lower() in ALLOWED:
            chunks += chunk_text(read_file(path.name, path.read_bytes()), path.name)
    if not chunks:
        return [], np.zeros((0, 384), dtype="float32")
    return chunks, embed([c["text"] for c in chunks])


def retrieve(query, chunks, vecs):
    if not chunks:
        return []
    scores = vecs @ embed([query])[0]
    top = np.argsort(-scores)[:TOP_K]
    return [chunks[i] for i in top]


# ---------- الواجهة ----------
check_password()
st.title("📚 مساعد المستندات")

if not API_KEY:
    st.error("ضيف ANTHROPIC_API_KEY في Secrets (شوف README).")
    st.stop()

client = Anthropic(api_key=API_KEY)
base_chunks, base_vecs = build_base_index()

# رفع ملفات إضافية خلال الجلسة (مش بتتخزن بعد ما تقفل الصفحة)
with st.sidebar:
    st.header("ملفات إضافية")
    uploads = st.file_uploader("PDF / TXT / MD", type=["pdf", "txt", "md"], accept_multiple_files=True)
    st.caption(f"مستندات المشروع: {len({c['source'] for c in base_chunks})} ملف")

all_chunks, all_vecs = base_chunks, base_vecs
if uploads:
    extra = []
    for f in uploads:
        extra += chunk_text(read_file(f.name, f.getvalue()), f.name)
    if extra:
        extra_vecs = embed([c["text"] for c in extra])
        all_chunks = base_chunks + extra
        all_vecs = np.vstack([base_vecs, extra_vecs]) if len(base_chunks) else extra_vecs

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if question := st.chat_input("اسأل عن المستندات..."):
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    hits = retrieve(question, all_chunks, all_vecs)
    context = "\n\n".join(f"[{h['source']}]\n{h['text']}" for h in hits) or "(no documents)"

    history = st.session_state.messages[:-1][-6:]  # آخر 3 تبادلات
    messages = history + [
        {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"}
    ]

    def stream_answer():
        with client.messages.stream(
            model=MODEL, max_tokens=1000, system=SYSTEM_PROMPT, messages=messages
        ) as stream:
            yield from stream.text_stream

    with st.chat_message("assistant"):
        try:
            answer = st.write_stream(stream_answer())
        except Exception as e:
            answer = f"حصل خطأ أثناء الاتصال بالنموذج: {e}"
            st.error(answer)
        with st.expander("المصادر المستخدمة"):
            for h in hits:
                st.caption(h["source"])
                st.write(h["text"][:300] + "...")

    st.session_state.messages.append({"role": "assistant", "content": answer})
