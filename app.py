import streamlit as st
import pandas as pd
from pathlib import Path
import os

# ========== 1. SETUP ==========
st.set_page_config(layout="wide", page_title="QSR Analytics Bot")

# ========== 2. RELIABLE DATA LOADING ==========
@st.cache_data
def load_data():
    """Handles all possible file locations and errors"""
    try:
        # Try multiple possible paths (including root directory)
        possible_paths = [
            Path("QSR_CEO_CLEANED_FULL.csv"),          # Root (your current setup)
            Path("app/data/QSR_CEO_CLEANED_FULL.csv"),  # Alternative
            Path("data/QSR_CEO_CLEANED_FULL.csv")       # Another alternative
        ]
        
        for path in possible_paths:
            if path.exists():
                df = pd.read_csv(path)
                st.toast(f"✅ Data loaded from: {path}", icon="✅")
                return df
        
        # If no path worked
        st.error(f"❌ File not found. Checked: {[str(p) for p in possible_paths]}")
        return None
        
    except Exception as e:
        st.error(f"⚠️ Error loading file: {str(e)}")
        return None

# ========== 3. MAIN APP ==========
st.title("🍔 QSR CEO Analytics Bot")

# Load data
df = load_data()

if df is not None:
    # Show basic info
    st.subheader("Data Preview")
    st.write(f"Loaded {len(df)} rows")
    st.dataframe(df.head())

    # Add your analytics here
    st.subheader("Sales Trend")
    st.line_chart(df.set_index("Month")["Amount (₹ Lakhs)"])
    
    # Example AI integration
    if "openai_key" not in st.session_state:
        st.session_state.openai_key = st.text_input("Enter OpenAI Key (optional):", type="password")

# ========== 4. DEBUG INFO ==========
with st.expander("ℹ️ Debug Information", expanded=False):
    st.write("Current directory:", os.getcwd())
    st.write("Files in directory:", os.listdir())
    if df is not None:
        st.write("Data columns:", df.columns.tolist())
