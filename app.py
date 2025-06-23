import streamlit as st
import pandas as pd
from pandasai import SmartDataframe
from pandasai.llm.openai import OpenAI
import io

# Clean, centered layout
st.set_page_config(layout="centered")
st.markdown("""
    <style>
        .block-container {padding-top: 1rem;}
        header, footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# Sidebar: Q&A History
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

# File upload
uploaded_file = st.file_uploader("", type=["xlsx"])

if uploaded_file:
    try:
        df_raw = pd.read_excel(uploaded_file, sheet_name=0)

        # Pivot store-level data to structured form
        df_pivot = df_raw.pivot_table(
            index=["Month", "Store"],
            columns="Metric",
            values="Amount"
        ).reset_index()

        # OpenAI key input
        openai_api_key = st.text_input("", placeholder="Enter your OpenAI API Key", type="password")

        if openai_api_key:
            llm = OpenAI(api_token=openai_api_key)
            smart_df = SmartDataframe(df_pivot, config={"llm": llm})

            # Chat input that runs on Enter
            user_query = st.chat_input("Ask your store performance question")

            if user_query:
                with st.spinner("Analyzing..."):
                    try:
                        response = smart_df.chat(user_query)

                        if isinstance(response, pd.DataFrame):
                            st.dataframe(response)

                            # Excel download option
                            buffer = io.BytesIO()
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

                        # Add to history
                        st.session_state.qa_history.append((user_query, response))

                    except Exception as e:
                        st.error(f"⚠️ Error: {e}")

    except Exception as e:
        st.error(f"❌ Failed to process Excel file: {e}")
