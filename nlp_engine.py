
import faiss
import numpy as np
import pandas as pd
import openai
from sentence_transformers import SentenceTransformer

# Load data and index
df = pd.read_csv("QSR_CEO_Full_Integrated.csv")
qa_data = pd.read_csv("QSR_CEO_NLP_QA_Preview.csv") if "QSR_CEO_NLP_QA_Preview.csv" in globals() else pd.DataFrame({
    "Question": ["Which store had the highest net sales in April 2024?"],
    "Answer": ["HSR with ₹14.5 Lakhs net sales."]
})
index = faiss.read_index("qa_faiss_index.pkl")

# Load embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")
qa_embeddings = np.load("qa_vectors.npy") if "qa_vectors.npy" in globals() else model.encode(qa_data["Question"].tolist(), normalize_embeddings=True)

def gpt_fallback(query):
    openai.api_key = "YOUR_OPENAI_API_KEY"
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
        query_vec = model.encode([query], normalize_embeddings=True)
        D, I = index.search(np.array(query_vec), k=1)
        best_match = qa_data.iloc[I[0][0]]["Answer"]
        return best_match
    except Exception:
        return gpt_fallback(query)
