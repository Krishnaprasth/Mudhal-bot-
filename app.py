import streamlit as st
import pandas as pd
from openai import OpenAI
import os
import json

st.set_page_config(layout="wide")
st.title("📊 QSR CEO Assistant")

client = OpenAI()

@st.cache_data
def load_data():
    default_path = "cleaned_store_data_embedded.csv"
    if os.path.exists(default_path):
        return pd.read_csv(default_path)
    else:
        uploaded_file = st.file_uploader("📤 Upload your cleaned store data CSV", type=["csv"])
        if uploaded_file is not None:
            return pd.read_csv(uploaded_file)
        else:
            st.warning("⚠️ Please upload a cleaned_store_data_embedded.csv file to proceed.")
            return pd.DataFrame()

# Load data
df = load_data()
if df.empty:
    st.stop()

query = st.text_input("Ask a question about store performance:")

if query:
    prompt = f"""You are an analyst assistant. Given the user's question, extract and return what they are asking using structured language.

    Question: \"{query}\"

    Respond in JSON with fields: 
    - metric (e.g. \"Net Sales\", \"Gross margin\", etc.),
    - store (e.g. \"VEL\", if mentioned),
    - month (e.g. \"June 24\", if mentioned),
    - intent (e.g. \"top_store_by_metric\", \"store_trend\", \"compare_stores\", etc.)

    Only respond with JSON."""

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        reply = response.choices[0].message.content.strip()
        interpretation = json.loads(reply)
        metric = interpretation.get("metric")
        store = interpretation.get("store")
        month = interpretation.get("month")
        intent = interpretation.get("intent")

        if intent == "top_store_by_metric" and metric and month:
            df_temp = df[df['Month'] == month].sort_values(by=metric, ascending=False).head(1)
            st.dataframe(df_temp)
            st.download_button("📥 Download Table as CSV", df_temp.to_csv(index=False), file_name=f"top_store_{metric}_{month}.csv")

        elif intent == "store_trend" and metric and store:
            df_temp = df[df['Store'] == store][['Month', 'Store', metric]].sort_values(by='Month')
            st.dataframe(df_temp)
            st.download_button("📥 Download Table as CSV", df_temp.to_csv(index=False), file_name=f"{store}_{metric}_trend.csv")

        else:
            st.warning("🤖 Could not interpret your question fully. Try simpler phrasing or verify month/store names.")

    except Exception as e:
        st.error(f"GPT interpretation failed: {e}")
