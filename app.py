import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import openai

# Load your QSR data
@st.cache_data
def load_data():
    return pd.read_csv('QSR_CEO_CLEANED_FULL.csv')

# Initialize the app
def main():
    st.set_page_config(page_title="QSR Analyst Bot", layout="wide")
    st.title("🍟 QSR Data Analysis Bot")
    
    # Load data
    df = load_data()
    
    # Connect to OpenAI (paste your API key when prompted)
    if 'openai_key' not in st.session_state:
        st.session_state.openai_key = st.text_input("Enter your OpenAI API key:", type="password")
    
    if st.session_state.openai_key:
        openai.api_key = st.session_state.openai_key
        
        # Question input
        question = st.text_input("Ask anything about your QSR data:", 
                               placeholder="e.g. Which store has highest sales?")
        
        if question:
            with st.spinner("Analyzing..."):
                try:
                    # Get AI response
                    response = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",
                        messages=[{
                            "role": "user",
                            "content": f"""Analyze this QSR data and answer: {question}
                            Data info:
                            - Stores: {df['Store'].nunique()}
                            - Months: {df['Month'].nunique()}
                            - Metrics: {', '.join(df['Metric'].unique()[:5])}...
                            """
                        }],
                        temperature=0.3
                    )
                    
                    answer = response.choices[0].message['content']
                    st.success(answer)
                    
                    # Simple visualization
                    if "sales" in question.lower():
                        st.subheader("Top Stores")
                        top_stores = df[df['Metric']=='Gross Sales'].groupby('Store')['Amount (Rs Lakhs)'].mean().nlargest(5)
                        st.bar_chart(top_stores)
                    
                    elif "cost" in question.lower():
                        st.subheader("Cost Breakdown")
                        costs = df[df['Metric'].str.contains('Cost')].groupby('Metric')['Amount (Rs Lakhs)'].mean()
                        st.pie_chart(costs)
                        
                except Exception as e:
                    st.error(f"Error: {e}")
    
    st.sidebar.markdown("""
    **Sample Questions:**
    - Show top 5 stores by sales
    - What's our cost structure?
    - Compare April and May sales
    """)

if __name__ == "__main__":
    main()
