import streamlit as st
import pandas as pd
from pandasai import SmartDataframe
from pandasai.llm.openai import OpenAI
from io import StringIO, BytesIO

# --- Minimal UI Setup ---
st.set_page_config(layout="centered")
st.markdown("""
    <style>
        .block-container {padding-top: 1rem;}
        header, footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- Embedded full dataset as CSV string ---
@st.cache_data
def load_data():
    csv_data = """Month,Store,Metric,Amount,Percent of Net Sales
Apr 24,Total,Gross Sales,217111011.0704762,1.015938336445032
Apr 24,Total,Net Sales,213704910.31,1.0
Apr 24,Total,COGS (food +packaging),79924764.28825268,0.3739959188224264
Apr 24,Total,Gross margin,133780146.0217473,0.6260040811775736
Apr 24,Total,store Labor Cost,24883500.32447865,0.1164385988528887
Apr 24,Total,Utility Cost,8276984.57,0.0387309049567154
Apr 24,Total,CAM,2084097.9,0.009752222805628617
Apr 24,Total,Aggregator commission,31595403.83000001,0.1478459422582652
Apr 24,Total,Marketing & advertisement,7226502.010000004,0.03381532974379134
Apr 24,Total,Other opex expenses,9703112.720161805,0.0454042572352993
Apr 24,EGL,Gross Sales,1443916.0,1.044334869052968
Apr 24,EGL,Net Sales,1382617.82,1.0
Apr 24,EGL,COGS (food +packaging),541505.3072999845,0.3916521973512423
Apr 24,EGL,Gross margin,841112.5127000156,0.6083478026487577
Apr 24,EGL,store Labor Cost,262392.3408,0.1897793714245633
Apr 24,EGL,Utility Cost,83000.0,0.06003105037370
"""  # This is partial; insert full CSV string here.

    return pd.read_csv(StringIO(csv_data))

# ---- Load + Pivot ----
df_raw = load_data()
df_pivot = df_raw.pivot_table(
    index=["Month", "Store"],
    columns="Metric",
    values="Amount"
).reset_index()

# ---- Sidebar Q&A History ----
if "qa_history" not in st.session_state:
    st.session_state.qa_history = []

with st.sidebar:
    st.markdown("### 🕑 History")
    for i, (q, a) in enumerate(reversed(st.session_state.qa_history[-10:]), 1):
        st.markdown(f"**{i}. {q}**")
        if isinstance(a, pd.DataFrame):
            st.markdown(a.to_markdown(index=False), unsafe_allow_html=True)
        else:
            st.markdown(f"➤ {a}")

# ---- OpenAI Key ----
openai_api_key = st.text_input("", placeholder="Enter your OpenAI API Key", type="password")

if openai_api_key:
    llm = OpenAI(api_token=openai_api_key)
    smart_df = SmartDataframe(df_pivot, config={"llm": llm})

    user_query = st.chat_input("Ask your store performance question")

    if user_query:
        with st.spinner("Analyzing..."):
            try:
                response = smart_df.chat(user_query)

                if isinstance(response, pd.DataFrame):
                    st.dataframe(response)

                    buffer = BytesIO()
                    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                        response.to_excel(writer, index=False)
                    st.download_button(
                        label="Download as Excel",
                        data=buffer.getvalue(),
                        file_name="response.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                else:
                    st.write(response)

                st.session_state.qa_history.append((user_query, response))

            except Exception as e:
                st.error(f"⚠️ Error: {e}")
