# app.py — Unified natural language bot with OpenAI v1+ compatibility

import streamlit as st
import pandas as pd
from openai import OpenAI

@st.cache_data
def load_data():
    return pd.read_csv("data/cleaned_store_data.csv")

df = load_data()

api_key = st.secrets["OPENAI_API_KEY"] if "OPENAI_API_KEY" in st.secrets else "sk-your-key"
client = OpenAI(api_key=api_key)

st.set_page_config(layout="centered")
st.markdown("""<style>textarea, .stTextInput input {font-size: 18px;}</style>""", unsafe_allow_html=True)
st.title(":burrito: QSR CEO Bot")
query = st.text_input("", placeholder="Ask a store performance question...", label_visibility="collapsed")

if query:
    if query.strip().lower() == "which store has the highest revenue":
        df_clean = df.dropna(subset=["Net Sales"])
        store_revenue = df_clean.groupby("Store")["Net Sales"].sum()
        top_store = store_revenue.idxmax()
        st.success(f"🏆 Store with highest revenue: **{top_store}** with ₹{store_revenue[top_store]:,.0f}")
    else:
        try:
            df_head_str = df.head(10).to_string(index=False)
            user_message = f"DataFrame Preview:\n{df_head_str}\n\nNow answer this question using pandas dataframe logic only:\n{query}"

            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful data analyst for a QSR company. You analyze the provided pandas dataframe and return structured answers, especially tables if relevant."},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.1
            )
            answer = response.choices[0].message.content
            st.markdown(answer)
        except Exception as e:
            st.error(f"Error: {str(e)}")
