import streamlit as st
import pandas as pd
import openai
from io import BytesIO

st.set_page_config(layout="centered")
st.markdown("""
    <style>
        .block-container {padding-top: 1rem;}
        header, footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    return pd.read_csv("cleaned_store_data_embedded.csv")

try:
    df_raw = load_data()
except Exception as e:
    st.error(f"❌ Could not load data: {e}")
    st.stop()

try:
    df_pivot = df_raw.pivot_table(
        index=["Month", "Store"],
        columns="Metric",
        values="Amount"
    ).reset_index()
except Exception as e:
    st.error(f"❌ Pivoting failed: {e}")
    st.stop()

if "qa_history" not in st.session_state:
    st.session_state.qa_history = []

with st.sidebar:
    st.markdown("### 🕑 History")
    for i, (q, a) in enumerate(reversed(st.session_state.qa_history[-10:]), 1):
        st.markdown(f"**{i}. {q}**")
        st.markdown(f"➤ {a[:500]}" if isinstance(a, str) else "➤ [table response]")

openai_api_key = st.text_input("", placeholder="Enter your OpenAI API Key", type="password")

if openai_api_key:
    openai.api_key = openai_api_key
    user_query = st.chat_input("Ask your store performance question")

    if user_query:
        with st.spinner("Analyzing..."):
            try:
                prompt = f"""
You are a data analyst for a QSR chain. Given this DataFrame schema:

{df_pivot.head().to_markdown(index=False)}

User asked: "{user_query}"

Write a concise, relevant summary using data logic or suggest a pandas filter to answer this.
Do not assume facts not in the table. Prefer short tabular answers when applicable.
"""

                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a helpful data analyst."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2,
                )

                answer = response.choices[0].message['content']
                st.markdown(answer)
                st.session_state.qa_history.append((user_query, answer))

            except Exception as e:
                st.error(f"⚠️ Error: {e}")
