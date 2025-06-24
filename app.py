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

# ========== STYLES ==========
st.markdown("""
<style>
    [data-testid="stSidebar"] {
        background: linear-gradient(135deg, #f16529, #e44d26);
    }
    .question-bank {
        padding: 10px;
        border-radius: 10px;
        margin: 5px 0;
        cursor: pointer;
    }
    .question-bank:hover {
        background-color: #ffffff20;
    }
</style>
""", unsafe_allow_html=True)

# ========== DATA LOADING ==========
@st.cache_data
def load_data():
    try:
        df = pd.read_csv(Path(__file__).parent / "QSR_CEO_CLEANED_FULL.csv")
        return df
    except Exception as e:
        st.error(f"Data loading failed: {str(e)}")
        return None

df = load_data()

# ========== SESSION STATE ==========
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hi! I'm BurritoBot 🌯 Ask me about your QSR data!"}]

if "answered_questions" not in st.session_state:
    st.session_state.answered_questions = []

# ========== CHAT FUNCTIONS ==========
def get_ai_response(query):
    if df is None:
        return "Data not loaded. Please check CSV file."
    
    prompt = f"""Analyze this QSR data:
    Columns: {df.columns.tolist()}
    First row: {df.iloc[0].to_dict()}
    
    Question: {query}
    Answer concisely with insights:"""
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    
    # Store answered question
    if query not in [q['question'] for q in st.session_state.answered_questions]:
        st.session_state.answered_questions.append({
            "question": query,
            "answer": response.choices[0].message.content
        })
    
    return response.choices[0].message.content

# ========== SIDEBAR ==========
with st.sidebar:
    st.title("🌯 BurritoBot")
    st.image("https://cdn-icons-png.flaticon.com/512/2927/2927347.png", width=100)
    
    # OpenAI Key Input
    if "openai_key" not in st.session_state:
        st.session_state.openai_key = st.text_input("🔑 OpenAI Key", type="password")
        openai.api_key = st.session_state.openai_key
    
    # Question Bank
    st.subheader("💡 Sample Questions")
    sample_questions = [
        "Show sales trends for Mumbai",
        "Compare Delhi and Bangalore stores",
        "What's our best performing month?",
        "Find stores with declining sales"
    ]
    
    for q in sample_questions:
        if st.button(f"🌯 {q}", key=f"sample_{q}"):
            st.session_state.messages.append({"role": "user", "content": q})
    
    # Answered Questions History
    st.subheader("📚 Answered Questions")
    for i, qa in enumerate(st.session_state.answered_questions[-5:]):  # Show last 5
        with st.expander(f"Q: {qa['question']}"):
            st.write(qa['answer'])

# ========== MAIN CHAT ==========
st.title("🌯 BurritoBot QSR Analytics")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

if prompt := st.chat_input("Ask about your QSR data..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)
    
    with st.spinner("🌯 Wrapping up your answer..."):
        response = get_ai_response(prompt)
        st.session_state.messages.append({"role": "assistant", "content": response})
    
    with st.chat_message("assistant"):
        st.write(response)

# ========== DATA VISUALIZATION ==========
if df is not None:
    with st.expander("📊 Data Dashboard"):
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Raw Data")
            st.dataframe(df.head())
        with col
