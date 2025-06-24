import numpy as np
import faiss
import openai

# Load FAISS index and question vectors
index = faiss.read_index("qa_faiss_index.pkl")
vectors = np.load("qa_vectors.npy")

# Dummy list of 10K questions (index to actual questions)
with open("qa_question_bank.txt", "r") as f:
    question_bank = [line.strip() for line in f.readlines()]

def get_embedding(query):
    response = openai.Embedding.create(
        input=[query],
        model="text-embedding-ada-002"
    )
    return np.array(response['data'][0]['embedding'], dtype=np.float32)

def search_index(query, top_k=3):
    query_vec = get_embedding(query)
    faiss.normalize_L2(query_vec.reshape(1, -1))
    scores, indices = index.search(query_vec.reshape(1, -1), top_k)
    return [(question_bank[i], float(scores[0][j])) for j, i in enumerate(indices[0])]

def gpt_fallback(query):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a financial analyst helping a QSR CEO analyze store performance."},
            {"role": "user", "content": query}
        ],
        temperature=0.3
    )
    return response["choices"][0]["message"]["content"]

def nlp_router(user_query):
    try:
        results = search_index(user_query, top_k=1)
        top_q, score = results[0]
        if score > 0.80:
            return f"Matched FAQ: {top_q} (Score: {score:.2f})"
        else:
            return gpt_fallback(user_query)
    except Exception as e:
        return f"Error processing query: {str(e)}"
