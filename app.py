import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from openai import OpenAI
from io import StringIO
import re

@st.cache_data
def load_data():
    csv_data = open("cleaned_store_data_embedded.csv", "r").read()
    return pd.read_csv(StringIO(csv_data))

df_raw = load_data()
df = df_raw.pivot_table(index=['Month', 'Store'], columns='Metric', values='Amount').reset_index()

api_key = st.secrets["OPENAI_API_KEY"] if "OPENAI_API_KEY" in st.secrets else "sk-your-key"
client = OpenAI(api_key=api_key)

st.set_page_config(layout="centered")
st.markdown("""<style>textarea, .stTextInput input {font-size: 18px;} .stDownloadButton button {margin-top: 10px;}</style>""", unsafe_allow_html=True)
st.title(":burrito: QSR CEO Bot")
query = st.text_input("", placeholder="Ask a store performance question...", label_visibility="collapsed")

if "qa_history" not in st.session_state:
    st.session_state.qa_history = []

if query:
    try:
        months = df['Month'].dropna().unique().tolist()
        stores = df['Store'].dropna().unique().tolist()

        def normalize(text):
            return re.sub(r"[^a-z0-9]", "", text.lower())

        query_norm = normalize(query)

        query_months = [m for m in months if normalize(m) in query_norm]
        query_stores = [s for s in stores if normalize(s) in query_norm]

        filtered_df = df.copy()
        if query_months:
            filtered_df = filtered_df[filtered_df['Month'].isin(query_months)]
        if query_stores:
            filtered_df = filtered_df[filtered_df['Store'].isin(query_stores)]

        if not query_months and not query_stores:
            filtered_df = filtered_df.head(200)

        df_str = filtered_df.to_string(index=False)
        user_message = f"DataFrame:\n{df_str}\n\nNow answer this question using pandas dataframe logic only:\n{query}"

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful data analyst for a QSR company. You analyze the provided pandas dataframe and return structured answers, especially tables if relevant. If the question refers to trends or comparisons, provide a matplotlib chart. Keep the markdown tight and clean."},
                {"role": "user", "content": user_message}
            ],
            temperature=0.1
        )
        answer = response.choices[0].message.content
        st.markdown(answer)

        if "|" in answer:
            import io
            df_temp = pd.read_csv(io.StringIO(answer.split("\n\n")[-1]), sep="|").dropna(axis=1, how="all")
            if len(df_temp.columns) >= 2:
                fig2, ax2 = plt.subplots()
                df_temp.iloc[:, 1:].plot(kind="bar", ax=ax2)
                ax2.set_title("Chart Based on Answer")
                st.pyplot(fig2)
                st.download_button("📥 Download Table as CSV", df_temp.to_csv(index=False), file_name="answer_table.csv")

        st.session_state.qa_history.append((query, answer))
    except Exception as e:
        st.error(f"Error: {str(e)}")

with st.sidebar:
    st.markdown("### 🔁 Q&A History")
    for q, a in st.session_state.qa_history[-10:]:
        st.markdown(f"**Q:** {q}\n\n*A:* {a}")
