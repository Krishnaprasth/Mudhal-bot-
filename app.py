import streamlit as st
import pandas as pd
import openai
from pathlib import Path

# ========== SETUP ==========
st.set_page_config(
    page_title="🌯 BurritoBot QSR Analytics",
    page_icon="🌯",
    layout="wide"
)

# ========== DATA LOADING ==========
@st.cache_data
def load_data():
    try:
        df = pd.read_csv(Path(__file__).parent / "QSR_CEO_CLEANED_FULL.csv")
        # Convert 'Month' to datetime and extract year/month
        df['Month'] = pd.to_datetime(df['Month'], format='%B')
        df['Year'] = df['Month'].dt.year
        df['MonthName'] = df['Month'].dt.month_name()
        return df
    except Exception as e:
        st.error(f"Data loading failed: {str(e)}")
        return pd.DataFrame()  # Return empty DataFrame instead of None

df = load_data()

# ========== ANALYTICS FUNCTIONS ==========
def get_top_store(month="November", year=2024):
    if df.empty:
        return "No data available"
    
    try:
        # Filter for November 2024
        nov_data = df[(df['MonthName'] == month) & (df['Year'] == year)]
        
        if nov_data.empty:
            return f"No data found for {month} {year}"
            
        # Find store with max sales
        top_store = nov_data.loc[nov_data['Amount (₹ Lakhs)'].idxmax()]
        return f"🏆 Top store in {month} {year}: {top_store['Store']} with ₹{top_store['Amount (₹ Lakhs)']}L"
    
    except Exception as e:
        return f"Analysis error: {str(e)}"

# ========== CHAT FUNCTION ==========
def get_ai_response(query):
    if df.empty:
        return "Data not loaded. Please check CSV file."
    
    # Handle specific queries directly
    if "highest sales in nov" in query.lower():
        return get_top_store()
    
    try:
        prompt = f"""Analyze this QSR data with columns: {df.columns.tolist()}
        Question: {query}
        Answer concisely with insights:"""
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return response.choices[0].message.content
        
    except Exception as e:
        return f"AI error: {str(e)}"

# ========== MAIN APP ==========
st.title("🌯 BurritoBot QSR Analytics")

if not df.empty:
    # Quick analysis buttons
    st.subheader("Quick Analysis")
    if st.button("🏆 Show top store in November 2024"):
        result = get_top_store()
        st.write(result)

# Chat interface
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hi! Ask me about store performance"}]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

if prompt := st.chat_input("Ask about store performance..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)
    
    with st.spinner("Analyzing..."):
        response = get_ai_response(prompt)
        st.session_state.messages.append({"role": "assistant", "content": response})
    
    with st.chat_message("assistant"):
        st.write(response)

# Data preview
if not df.empty:
    with st.expander("📊 View Raw Data"):
        st.dataframe(df)
