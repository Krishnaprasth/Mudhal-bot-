import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io
from logic_module import logic_blocks, fallback_message, extract_standard_month

st.set_page_config(layout="wide")
st.title("")
st.markdown("## QSR CEO Assistant")

@st.cache_data
def load_data():
    return pd.read_csv("cleaned_store_data_final.csv")

df = load_data()

user_query = st.text_input("Ask your question:", placeholder="e.g., Which store had the highest sales in May 2024")

if user_query:
    matched = False
    for pattern, logic_func, filename in logic_blocks:
        if pattern.lower() in user_query.lower():
            try:
                df_temp = logic_func(df)
                st.success("Here's the result for: " + pattern)
                st.dataframe(df_temp)

                # Visualize
                if df_temp.shape[1] >= 3:
                    fig, ax = plt.subplots(figsize=(8, 4))
                    df_temp.plot(x=df_temp.columns[1], y=df_temp.columns[2], kind='bar', ax=ax)
                    st.pyplot(fig)

                # Download option
                csv = df_temp.to_csv(index=False).encode('utf-8')
                st.download_button("📅 Download Table as CSV", csv, file_name=filename, mime='text/csv')
                matched = True
                break
            except Exception as e:
                st.error("Error computing logic: " + str(e))
                matched = True
                break

    if not matched:
        st.warning(fallback_message)
        st.markdown("Try questions like:")
        st.markdown("- Top 5 stores by Net Sales\n- MoM change in Gross margin\n- Which store did highest marketing spend in May 24\n- EBITDA for ANN store\n- Trend of revenue for EGL")
