
import streamlit as st
import pandas as pd
import openai
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import requests
from PIL import Image
from io import BytesIO

# === CONFIG ===
st.set_page_config(page_title="QSR CEO Performance Bot", layout="wide")

# === LOGO ===
logo_url = "https://www.californiaburrito.in/images/logo.png"
try:
    response = requests.get(logo_url)
    if response.status_code == 200:
        logo = Image.open(BytesIO(response.content))
        st.image(logo, width=200)
except Exception:
    st.title("🤖 QSR CEO Store Performance Assistant")

# === LOAD DATA ===
@st.cache_data
def load_data():
    return pd.read_csv("QSR_CEO_CLEANED_READY.csv")

# === EMBEDDING SETUP ===
@st.cache_resource
def load_embedding_model():
    return SentenceTransformer("all-MiniLM-L6-v2")

@st.cache_resource
def build_semantic_index(questions):
    model = load_embedding_model()
    embeddings = model.encode(questions)
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(np.array(embeddings))
    return index, embeddings, questions

# Load prebuilt 10k Q&A
import json
@st.cache_resource
def load_semantic_qna():
    with open("semantic_qna.json") as f:
        data = json.load(f)
    return data["questions"], data["answers"]

prebuilt_questions, prebuilt_answers = load_semantic_qna()
index, embeddings, stored_questions = build_semantic_index(prebuilt_questions)

# === FILE UPLOAD ===
uploaded_file = st.sidebar.file_uploader("Upload cleaned store data (CSV)", type=["csv"])
if uploaded_file:
    df = pd.read_csv(uploaded_file)
else:
    df = load_data()

# === QUESTION HANDLER ===
st.sidebar.markdown("## Ask a question")
user_question = st.sidebar.text_area("E.g. Which store had highest net sales in April 2024?", height=100)

# === ANSWER HISTORY ===
if "history" not in st.session_state:
    st.session_state.history = []

# === GPT FALLBACK ===
def ask_gpt(query, data_sample):
    prompt = f"""You are a data analyst assistant. A CEO has asked the following question:

"{query}"

You have access to the following dataset sample:
{data_sample}

Return the answer in a clear table or summary, using only the data."""
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

# === HANDLE QUERY ===
if st.sidebar.button("Get Answer") and user_question:
    logic = semantic_match(user_question)
    if logic:
        try:
            answer = eval(logic)
        except Exception as e:
            answer = f"❌ Logic Error: {e}"
    else:
        sample = df.head(20).to_markdown()
        answer = ask_gpt(user_question, sample)
    st.session_state.history.append((user_question, answer))

# === DISPLAY CURRENT ANSWER ===
if st.session_state.history:
    last_q, last_a = st.session_state.history[-1]
    st.subheader("💬 Question")
    st.write(last_q)
    st.subheader("📊 Answer")
    st.write(last_a)

    if st.download_button("⬇️ Download Answer", data=str(last_a), file_name="answer.txt"):
        pass

# === HISTORY ===
st.sidebar.markdown("---")
st.sidebar.markdown("### 📜 History")
for i, (q, a) in enumerate(reversed(st.session_state.history[-10:])):
    st.sidebar.markdown(f"**Q{i+1}:** {q}")
