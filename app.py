import streamlit as st
import pandas as pd
import os

# DISABLE CACHE COMPLETELY (solves the error)
st.cache_data.clear()
st.cache_resource.clear()

# SIMPLE DATA LOADER WITHOUT CACHING
def load_data():
    try:
        df = pd.read_csv("QSR_CEO_CLEANED_FULL.csv")
        st.toast("✅ Data loaded!")
        return df
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        st.write("Files present:", os.listdir())
        return None

# MAIN APP
st.title("🍔 QSR Analytics (Fixed Cache Error)")
df = load_data()

if df is not None:
    st.dataframe(df.head())
    st.line_chart(df.set_index("Month")["Amount (₹ Lakhs)"])
