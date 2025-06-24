import streamlit as st
import pandas as pd
import openai
from pathlib import Path

# ===== CONFIGURATION =====
DATA_FILE = "QSR_CEO_CLEANED_FULL.csv"  # Your exact filename
AI_MODEL = "gpt-4-1106-preview"         # Latest model for JSON support

# ===== DATA LOADING =====
@st.cache_data
def load_data():
    data_path = Path(__file__).parent / "data" / DATA_FILE
    try:
        df = pd.read_csv(data_path)
        st.toast(f"✅ Loaded {len(df)} rows from {DATA_FILE}", icon="✅")
        return df
    except Exception as e:
        st.error(f"Failed to load {DATA_FILE}: {str(e)}")
        return None

# ===== STREAMLIT UI =====
st.set_page_config(layout="wide", page_title=f"QSR Analytics - {DATA_FILE}")
df = load_data()

if df is not None:
    # Securely handle OpenAI key
    if "openai_key" not in st.session_state:
        with st.sidebar:
            st.session_state.openai_key = st.text_input("🔑 OpenAI Key", type="password")
    
    if st.session_state.openai_key:
        openai.api_key = st.session_state.openai_key
        
        # Dynamic query interface
        tab1, tab2 = st.tabs(["Ask Question", "View Data"])
        
        with tab1:
            query = st.text_area("📝 Ask about your data:", height=100)
            if query:
                with st.spinner("🧠 Analyzing..."):
                    response = openai.ChatCompletion.create(
                        model=AI_MODEL,
                        response_format={ "type": "json_object" },
                        messages=[
                            {
                                "role": "system",
                                "content": f"""You're a QSR data analyst. Analyze this data with key columns: 
                                {df.columns.tolist()}. Respond in JSON format with 'insight', 'trend', and 'action_items'."""
                            },
                            {
                                "role": "user",
                                "content": query
                            }
                        ]
                    )
                    result = json.loads(response.choices[0].message.content)
                    st.json(result)
        
        with tab2:
            st.dataframe(df.style.format({'Amount (₹ Lakhs)': '₹{:,.1f}'}))
