# app.py — Unified natural language bot with OpenAI v1+ compatibility

import streamlit as st
import pandas as pd
from openai import OpenAI

@st.cache_data
def load_data():
    csv_data = '''Store,Month,Net Sales,COGS (food +packaging),Gross margin,store Labor Cost,Utility Cost,Rent,CAM,Aggregator commission,Marketing & advertisement,Other opex expenses,Total outlet expenses,Outlet EBITDA
ADM,Apr 24,1520149,542125,978024,220009,41067,85000,11656,84029,105799,60599,1040159,480990
AKA,Apr 24,1312149,476250,835899,186823,33684,108000,11835,79250,57917,42950,1012459,299690
ANN,Apr 24,2184577,742748,1441829,292971,50157,160000,21769,112798,123963,62557,1391215,793362
ARK,Apr 24,1983214,763945,1219269,277578,51915,142000,17111,108902,127127,69985,1341618,641596
AUR,Apr 24,,,,,,,,,,,,
'''
    from io import StringIO
    return pd.read_csv(StringIO(csv_data))

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
