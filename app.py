import streamlit as st
import pandas as pd
import os

# ===== 1. SUPER SIMPLE DATA LOADING =====
try:
    # DIRECTLY LOAD FROM ROOT FOLDER (where your files are)
    df = pd.read_csv("QSR_CEO_CLEANED_FULL.csv")
    st.success("✅ Data loaded successfully!")
    
    # ===== 2. DISPLAY DATA =====
    st.title("🍔 QSR Analytics (Working!)")
    st.write("First 5 rows:")
    st.dataframe(df.head())
    
    # ===== 3. BASIC CHART =====
    st.line_chart(df.set_index("Month")["Amount (₹ Lakhs)"])
    
except Exception as e:
    st.error(f"❌ Error: {str(e)}")
    st.write("Current files in directory:", os.listdir())
