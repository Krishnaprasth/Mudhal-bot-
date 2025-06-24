import faiss
import numpy as np
import pandas as pd
import openai
from sentence_transformers import SentenceTransformer

# Load cleaned store-level financial data
df = pd.read_csv("QSR_CEO_CLEANED_FULL.csv")  # ✅ Correct file name

# Load FAISS index and vectors
index = faiss.read_index("qa_faiss_index.pkl")
qa_vectors = np.load("qa_vectors.npy")

# Load question bank
with open("qa_question_bank.txt", "r") as f:
    questions = [line.strip() for line in f.readlines()]

# Load sentence transformer model
model = SentenceTransformer("all-MiniLM-L6-v2")

def gpt_fallback(query):
    openai.api_key = "YOUR_OPENAI_API_KEY"  # 🔁 Replace with your actual API key or load securely
    try:
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": query}],
            temperature=0.2
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"GPT fallback error: {str(e)}"

def nlp_router(query):
    try:
        # Encode the query and find the best match from pre-trained questions
        query_vec = model.encode([query], normalize_embeddings=True).astype("float32")
        _, I = index.search(query_vec, k=1)
        matched_question = questions[I[0][0]]
        return f"🔎 Matched: {matched_question}"
    except Exception:
        return gpt_fallback(query)
