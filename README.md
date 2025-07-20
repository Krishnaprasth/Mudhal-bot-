# QSR CEO Performance Bot

This is a Streamlit-based NLP bot that helps Quick Service Restaurant (QSR) CEOs analyze store-level performance from a cleaned dataset of FY22 to FY26.

---

## 📁 Included Files

- `app.py`: Main Streamlit app with logic-based and NLP-based answering
- `preload_questions.py`: Pre-generates 10,000+ CEO-style performance queries and embeds them into ChromaDB
- `requirements.txt`: All necessary Python libraries
- `QSR_CEO_CLEANED_FY22_TO_FY26_FULL_FINAL.csv`: Cleaned, structured 50-month dataset

---

## 🚀 Setup Instructions

### 1. Clone the repository or unzip the folder
```bash
git clone <your_repo_url>
# or unzip qsr_ceo_bot_package.zip
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Add your OpenAI API Key
Create a file at `.streamlit/secrets.toml` with this content:
```toml
OPENAI_API_KEY = "your-api-key-here"
```

### 4. (Optional) Preload NLP Questions into ChromaDB
```bash
python preload_questions.py
```

### 5. Run the App
```bash
streamlit run app.py
```

---

## 🧠 Capabilities

- Logic-driven analysis for Net Sales, EBITDA, Rent, etc.
- Natural language understanding (via GPT-4 fallback)
- Vector semantic search using ChromaDB
- Supports 50-months of data across 100+ stores and 30+ metrics

---

## ✅ Example Questions

- "What is the Net Sales trend for store KOR in FY24?"
- "Top 5 stores by EBITDA in FY25?"
- "What was the Rent-to-Sales ratio for BTM in FY23?"
- "Which store had the highest COGS in FY26?"

---

Built with ❤️ to empower data-driven restaurant leadership.