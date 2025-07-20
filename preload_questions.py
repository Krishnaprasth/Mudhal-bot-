# preload_questions.py
import pandas as pd
from sentence_transformers import SentenceTransformer
import chromadb
from tqdm import tqdm

# Load your dataset
df = pd.read_csv("QSR_CEO_CLEANED_FY22_TO_FY26_FULL_FINAL.csv")

# Load embedding model
embedder = SentenceTransformer("all-MiniLM-L6-v2")

# Initialize ChromaDB
client = chromadb.Client()
collection_name = "qsr_ceo_questions"
if collection_name in client.list_collections():
    collection = client.get_collection(name=collection_name)
else:
    collection = client.create_collection(name=collection_name)

# Unique dimensions
metrics = df["Metric"].dropna().unique()
stores = df["Store"].dropna().unique()
fys = df["FY"].dropna().unique()
months = df["Month-Year"].dropna().unique()

# Template bank
templates = [
    "What is the {metric} for store {store} in {fy}?",
    "Show me {metric} trend for {store} across {fy}.",
    "Compare {metric} between stores for {fy}.",
    "What was {metric} for {store} in {month}?",
    "Which store had the highest {metric} in {fy}?",
    "What % of Net Sales was spent on {metric} by {store} in {fy}?",
    "Give me the {metric} vs Net Sales ratio for {store} in {fy}.",
    "How did {metric} change for {store} between FY25 and FY26?",
    "What was the monthly trend of {metric} for {store}?",
    "Top 5 stores by {metric} in {fy}?"
]

# Generate and embed questions
questions = []
metadatas = []
ids = []

qid = 0
for metric in metrics:
    for store in stores:
        for fy in fys:
            for template in templates:
                q = template.format(metric=metric, store=store, fy=fy, month="March 2023")
                questions.append(q)
                metadatas.append({"metric": metric, "store": store, "fy": fy})
                ids.append(f"q_{qid}")
                qid += 1

# Batch embedding and adding to ChromaDB
batch_size = 1000
for i in tqdm(range(0, len(questions), batch_size)):
    batch = questions[i:i+batch_size]
    batch_ids = ids[i:i+batch_size]
    batch_metas = metadatas[i:i+batch_size]
    embeddings = embedder.encode(batch).tolist()
    collection.add(documents=batch, embeddings=embeddings, metadatas=batch_metas, ids=batch_ids)

print(f"✅ {len(questions)} questions embedded into ChromaDB")
