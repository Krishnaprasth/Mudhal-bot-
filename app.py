import streamlit as st
import pandas as pd
import openai
from tabulate import tabulate

st.set_page_config(layout="centered")
st.markdown("""
    <style>
        .block-container {padding-top: 1rem;}
        header, footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# ✅ Use OpenAI API key securely from Streamlit secrets
client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

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

# Extract unique months and stores for prompt grounding
months_text = ", ".join(sorted(df_raw["Month"].dropna().unique()))
stores_text = ", ".join(sorted(df_raw["Store"].dropna().unique()))
preview_table = tabulate(df_pivot.head(), headers="keys", tablefmt="github", showindex=False)

# Initialize Q&A memory
if "qa_history" not in st.session_state:
    st.session_state.qa_history = []

# Show sidebar history
with st.sidebar:
    st.markdown("### 🕑 History")
    for i, (q, a) in enumerate(reversed(st.session_state.qa_history[-10:]), 1):
        st.markdown(f"**{i}. {q}**")
        st.markdown(f"➤ {a[:500]}" if isinstance(a, str) else "➤ [table response]")

# User query input
user_query = st.chat_input("Ask your store performance question")

if user_query:
    with st.spinner("Analyzing..."):
        try:
            prompt = f"""
You are a data analyst for a QSR chain. The dataset contains store-level monthly financial performance metrics.

Available months: {months_text}
Available stores: {stores_text}

DataFrame structure:
{preview_table}

User asked: "{user_query}"

Use only available data. If a month or store isn't in the dataset, mention that clearly.
Prefer concise summaries, tables, or code suggestions. Do not assume missing values are zero.
"""

            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful data analyst."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
            )

            answer = response.choices[0].message.content
            st.markdown(answer)
            st.session_state.qa_history.append((user_query, answer))

        except Exception as e:
            st.error(f"⚠️ Error: {e}")
