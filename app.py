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

# Extract unique month/store values for prompt grounding
months_text = ", ".join(sorted(df_raw["Month"].dropna().unique()))
stores_text = ", ".join(sorted(df_raw["Store"].dropna().unique()))
preview_table = tabulate(df_pivot.head(), headers="keys", tablefmt="github", showindex=False)

if "qa_histo_
