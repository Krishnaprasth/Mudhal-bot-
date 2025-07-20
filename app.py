# app.py
import streamlit as st
import pandas as pd
import openai
import chromadb
from sentence_transformers import SentenceTransformer
import numpy as np

# --- Configurations ---
st.set_page_config(page_title="QSR CEO Bot", layout="wide")
st.title("QSR CEO Performance Bot")

# --- Load Data ---
@st.cache_data
def load_data():
    return pd.read_csv("QSR_CEO_CLEANED_FY22_TO_FY26_FULL_FINAL.csv")

df = load_data()

# --- Initialize Embeddings + ChromaDB ---
embedder = SentenceTransformer("all-MiniLM-L6-v2")
chroma_client = chromadb.Client()
collection_name = "qsr_ceo_questions"

if collection_name not in chroma_client.list_collections():
    chroma_client.create_collection(name=collection_name)
collection = chroma_client.get_collection(name=collection_name)

# --- OpenAI Setup ---
openai.api_key = st.secrets["OPENAI_API_KEY"]

# --- GPT Fallback Function ---
def gpt_fallback(question: str, context: str) -> str:
    messages = [
        {"role": "system", "content": "You are a helpful performance analytics bot for a QSR chain."},
        {"role": "user", "content": f"Context:\n{context}\n\nQuestion:\n{question}"}
    ]
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=messages
    )
    return response.choices[0].message.content.strip()

# --- Logic Answer Engine ---
def answer_with_logic(query: str):
    q = query.lower()
    if "net sales" in q and "fy" in q and "store" in q:
        try:
            store = next(w for w in q.split() if w.isupper() and len(w) in [3, 4])
            fy = next(w.upper() for w in q.split() if w.startswith("fy"))
            result = df[(df["Metric"] == "Net Sales") & (df["Store"] == store) & (df["FY"] == fy)]
            if result.empty:
                return None
            return result[["Month-Year", "Amount (in lakhs)"]].sort_values("Month-Year")
        except Exception:
            return None
    return None

# --- Main Query Handler ---
query = st.text_input("Ask a performance question:")

if query:
    response = answer_with_logic(query)

    if response is not None:
        st.success("Answered using logic engine")
        st.dataframe(response)
    else:
        # Vector Search from ChromaDB
        query_vec = embedder.encode([query])[0].tolist()
        results = collection.query(query_embeddings=[query_vec], n_results=5)
        context = "\n".join(results.get("documents", [])[0]) if results.get("documents") else ""

        gpt_response = gpt_fallback(query, context)
        st.info("Answered using GPT fallback")
        st.markdown(gpt_response)

    # Store query history
    if "history" not in st.session_state:
        st.session_state.history = []
    st.session_state.history.append((query, response if response is not None else gpt_response))

# --- Sidebar History ---
with st.sidebar:
    st.subheader("Query History")
    if "history" in st.session_state:
        for q, a in reversed(st.session_state.history):
            st.markdown(f"**Q:** {q}")
            if isinstance(a, pd.DataFrame):
                st.dataframe(a)
            else:
                st.markdown(f"**A:** {a}")
