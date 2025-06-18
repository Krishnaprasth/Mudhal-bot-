import streamlit as st
import pandas as pd
import openai
import tempfile
import os
from io import BytesIO

st.set_page_config(page_title="Store Metrics ChatBot", layout="wide")
st.title("📊 California Burrito - Store Metrics ChatBot")

# --- SIDEBAR SETTINGS ---
st.sidebar.header("Upload Raw MIS Files")
openai.api_key = st.sidebar.text_input("🔑 Enter your OpenAI API Key", type="password")
uploaded_files = st.sidebar.file_uploader("Upload multiple Excel files (MIS format)", type=[".xlsx", ".xls"], accept_multiple_files=True)

@st.cache_data(show_spinner=False)
def parse_mis_files(files):
    all_rows = []
    for uploaded_file in files:
        try:
            xl = pd.ExcelFile(uploaded_file)
            for sheet in xl.sheet_names:
                df = xl.parse(sheet, header=None)
                try:
                    store_names = df.iloc[2]
                    types = df.iloc[3]
                    for row_idx in range(4, 25):
                        row_label = df.iloc[row_idx, 1]
                        if isinstance(row_label, str) and row_label.strip():
                            metric = row_label.strip()
                            values = df.iloc[row_idx]
                            for col_idx, (store, val_type) in enumerate(zip(store_names, types)):
                                if val_type == "Amount" and isinstance(store, str):
                                    try:
                                        value = float(values[col_idx])
                                        all_rows.append({
                                            "Month": sheet.strip(),
                                            "Store": store.strip(),
                                            "Metric": metric,
                                            "Value": value
                                        })
                                    except:
                                        continue
                except Exception:
                    continue
        except Exception:
            continue
    return pd.DataFrame(all_rows)

if uploaded_files:
    df = parse_mis_files(uploaded_files)
    if not df.empty:
        st.success(f"✅ Parsed {len(uploaded_files)} files. {df.shape[0]} rows loaded.")

        with st.expander("🔍 Preview Extracted Data"):
            st.dataframe(df.head(50))

        # --- DOWNLOAD DATA ---
        buffer = BytesIO()
        df.to_excel(buffer, index=False)
        st.download_button("📥 Download Extracted Data as Excel", data=buffer.getvalue(), file_name="Extracted_MIS_Data.xlsx")

        # --- CHAT INTERFACE ---
        st.markdown("---")
        st.subheader("💬 Ask a Question")
        query = st.text_input("Type your question (e.g., 'Compare sales in May vs April')")

        if query and openai.api_key:
            with st.spinner("Thinking..."):
                prompt = f"""
You are a smart data analyst. You are given a DataFrame with the following columns:
- Month
- Store
- Metric
- Value

The user will ask questions about the data such as:
- What was the Net Sales in May?
- How does Gross Sales in May compare to April for EGL?
- Show Rent % of Sales for ARK
- Compare EBITDA across stores in Oct

Use the DataFrame named `df`. Pivot or filter as needed. Always return clean, clear answers. Format numbers with commas and show % if applicable.

User Query: "{query}"

Respond only with the answer. Do not explain.
"""
                try:
                    response = openai.ChatCompletion.create(
                        model="gpt-4",
                        messages=[{"role": "system", "content": "You are a Python Pandas analyst."},
                                 {"role": "user", "content": prompt}],
                        temperature=0.2
                    )
                    answer = response['choices'][0]['message']['content']
                    st.markdown("### ✅ Answer")
                    st.markdown(answer)
                except Exception as e:
                    st.error("Error from OpenAI: " + str(e))
    else:
        st.warning("Could not extract data from uploaded files.")
else:
    st.info("Upload raw MIS Excel files from California Burrito to begin.")
