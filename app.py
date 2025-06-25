import streamlit as st
import pandas as pd
import openai
import io

# === CONFIG ===
st.set_page_config(page_title="QSR CEO Performance Bot", layout="wide")
st.title("🤖 QSR CEO Store Performance Assistant")

# === LOAD DATA ===
@st.cache_data
def load_data():
    return pd.read_csv("QSR_CEO_CLEANED_READY.csv")

# Option to upload custom file
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

# === OPENAI GPT FUNCTION ===
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

# === HANDLE QUERY ===
if st.sidebar.button("Get Answer") and user_question:
    sample = df.head(20).to_markdown()
    answer = ask_gpt(user_question, sample)
    st.session_state.history.append((user_question, answer))

# === DISPLAY CURRENT ANSWER ===
if st.session_state.history:
    last_q, last_a = st.session_state.history[-1]
    st.subheader("💬 Question")
    st.write(last_q)
    st.subheader("📊 Answer")
    st.markdown(last_a)

    # Option to download last answer
    if st.download_button("⬇️ Download Answer", data=last_a, file_name="answer.txt"):
        pass

# === HISTORY ===
st.sidebar.markdown("---")
st.sidebar.markdown("### 📜 History")
for i, (q, a) in enumerate(reversed(st.session_state.history[-10:])):
    st.sidebar.markdown(f"**Q{i+1}:** {q}")
