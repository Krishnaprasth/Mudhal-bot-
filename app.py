import streamlit as st
import pandas as pd
from logic_module import logic_blocks, extract_standard_month, fallback_message
import matplotlib.pyplot as plt

# Load data
@st.cache_data
def load_data():
    return pd.read_csv("cleaned_store_data_final.csv")

df = load_data()

# App UI
st.title("🧠 Store Intelligence Bot")
user_input = st.text_input("Ask a question about your stores...")

if user_input:
    matched = False
    for trigger, func, filename in logic_blocks:
        if trigger in user_input.lower():
            try:
                df_temp = func(df)
                st.success("✅ Here's the result:")
                st.dataframe(df_temp)
                st.download_button("📥 Download CSV", df_temp.to_csv(index=False), file_name=filename)
                matched = True
                break
            except Exception as e:
                st.error(f"⚠️ Error processing: {e}")
                matched = True
                break

    if not matched:
        st.warning(fallback_message)
