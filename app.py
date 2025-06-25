import streamlit as st
import pandas as pd
import openai
import faiss
import numpy as np
import json
from sentence_transformers import SentenceTransformer
import requests
from PIL import Image
from io import BytesIO

# === CONFIG ===
st.set_page_config(page_title="Query Buddy: Store Metrics HQ", layout="centered", initial_sidebar_state="expanded")

# === LOGO ===
logo_url = "https://www.californiaburrito.in/images/logo.png"
try:
    response = requests.get(logo_url)
    if response.status_code == 200:
        logo = Image.open(BytesIO(response.content))
        st.image(logo, width=180)
except Exception:
    st.title("🤖 QSR CEO Store Performance Assistant")

st.markdown("""
    <style>
    .stApp {
        font-family: 'Segoe UI', sans-serif;
        background-color: #f6f9fc;
    }
    .question-box {
        background: white;
        padding: 1.2rem;
        border-radius: 1rem;
        box-shadow: 0 0 10px rgba(0,0,0,0.05);
        margin-bottom: 1rem;
    }
    .answer-box {
        background: #ffffff;
        padding: 1.2rem;
        border-left: 6px solid #2E8B57;
        border-radius: 1rem;
        box-shadow: 0 0 10px rgba(0,0,0,0.05);
        margin-bottom: 2rem;
    }
    .suggestions {
        font-size: 0.85rem;
        color: #666;
        margin-top: 0.5rem;
    }
    .css-1kyxreq.edgvbvh3 { padding-top: 0rem; }
    </style>
""", unsafe_allow_html=True)

# === LOAD DATA ===
@st.cache_data
def load_data():
    return pd.read_csv("QSR_CEO_CLEANED_READY.csv")

df = load_data()

# === EMBEDDING SETUP ===
@st.cache_resource
def load_embedding_model():
    return SentenceTransformer("all-MiniLM-L6-v2")

@st.cache_resource
def load_semantic_qna():
    with open("semantic_qna.json") as f:
        data = json.load(f)
    return data["questions"], data["answers"]

@st.cache_resource
def build_semantic_index(questions):
    model = load_embedding_model()
    embeddings = model.encode(questions)
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(np.array(embeddings))
    return index, embeddings, questions

# Load semantic Q&A
prebuilt_questions, prebuilt_answers = load_semantic_qna()
index, embeddings, stored_questions = build_semantic_index(prebuilt_questions)

# === GPT FALLBACK ===
def ask_gpt(query, data_sample):
    prompt = f"""
You are a data analyst assistant. A CEO has asked the following question:

"{query}"

You have access to the following dataset sample:
{data_sample}

Return the answer in a clear table or summary, using only the data.
"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"❌ GPT failed: {e}"

# === SEMANTIC ROUTER ===
def semantic_match(user_q):
    model = load_embedding_model()
    user_embedding = model.encode([user_q])
    D, I = index.search(np.array(user_embedding), k=1)
    if D[0][0] < 50:
        return prebuilt_answers[I[0][0]]
    else:
        return None

# === INPUT & QUERY ===
example_questions = [
    "What was the net sales of KOR in May 2025?",
    "Which store had the highest EBITDA in FY2024?",
    "Rank stores by rent in Q2 FY2025",
    "What is the SSG of EGL in Q3 FY2024?"
]
st.markdown("<div class='suggestions'>💡 Try: " + " | ".join(example_questions) + "</div>", unsafe_allow_html=True)
user_question = st.text_input("Ask your question about store performance", placeholder="e.g. What is the rent of KOR in April 2024?")

if "history" not in st.session_state:
    st.session_state.history = []

if user_question:
    logic = semantic_match(user_question)
    if logic:
        try:
            result = eval(logic)
            if isinstance(result, (pd.DataFrame, pd.Series)):
                st.session_state.history.append((user_question, result.to_frame() if isinstance(result, pd.Series) else result))
            else:
                st.session_state.history.append((user_question, str(result)))
        except Exception as e:
            st.session_state.history.append((user_question, f"❌ Logic Error: {e}"))
    else:
        sample = df.head(20).to_markdown()
        response = ask_gpt(user_question, sample)
        st.session_state.history.append((user_question, response))

# === DISPLAY ===
if st.session_state.history:
    last_q, last_a = st.session_state.history[-1]
    st.markdown(f"<div class='question-box'><h4>💬 Question</h4>{last_q}</div>", unsafe_allow_html=True)
    if isinstance(last_a, (pd.DataFrame, pd.Series)):
        st.markdown("<div class='answer-box'><h4>📊 Answer</h4></div>", unsafe_allow_html=True)
        st.dataframe(last_a, use_container_width=True)
        st.download_button("⬇️ Download as Excel", data=last_a.to_csv(index=False), file_name="answer.csv")
    else:
        st.markdown(f"<div class='answer-box'><h4>📊 Answer</h4>{last_a}</div>", unsafe_allow_html=True)

# === SIDEBAR HISTORY ===
st.sidebar.markdown("### 📜 Question History")
for i, (q, a) in enumerate(reversed(st.session_state.history[-10:])):
    st.sidebar.markdown(f"**Q{i+1}:** {q}")
