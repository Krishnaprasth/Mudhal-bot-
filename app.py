csv_data = """Month,Store,Metric,Amount
Apr 24,EGL,Gross Sales,1443916.0
Apr 24,EGL,Net Sales,1382617.82
Apr 24,EGL,COGS (food +packaging),541505.3072999845
Apr 24,EGL,Gross margin,841112.5127000156
Apr 24,EGL,store Labor Cost,262392.3408
Apr 24,EGL,Utility Cost,83000.0
Apr 24,EGL,CAM,0.0
Apr 24,EGL,Aggregator commission,0.0
Apr 24,EGL,Marketing & advertisement,21471.89
Apr 24,EGL,Other opex expenses,128807.075
Apr 24,ITPL,Gross Sales,6681978.0
Apr 24,ITPL,Net Sales,6565784.7
Apr 24,ITPL,COGS (food +packaging),2287132.58
Apr 24,ITPL,Gross margin,4278652.12
Apr 24,ITPL,store Labor Cost,877823.6528
Apr 24,ITPL,Utility Cost,141657.66
Apr 24,ITPL,CAM,0.0
Apr 24,ITPL,Aggregator commission,153491.86
Apr 24,ITPL,Marketing & advertisement,105453.5
Apr 24,ITPL,Other opex expenses,466223.195
Dec 24,EGL,Gross Sales,1530000.0
Dec 24,EGL,Net Sales,1450000.0
Dec 24,EGL,COGS (food +packaging),550000.0
Dec 24,EGL,Gross margin,900000.0
Dec 24,EGL,store Labor Cost,275000.0
Dec 24,EGL,Utility Cost,85000.0
Dec 24,EGL,CAM,5000.0
Dec 24,EGL,Aggregator commission,20000.0
Dec 24,EGL,Marketing & advertisement,25000.0
Dec 24,EGL,Other opex expenses,135000.0
..."""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from openai import OpenAI
from io import StringIO

@st.cache_data
def load_data():
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
        df_str = df.to_string(index=False)
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
