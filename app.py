import streamlit as st
import pandas as pd
import os
import io
from fpdf import FPDF
from openai import OpenAI

st.set_page_config(layout="centered", page_title="California Burrito Analyst", page_icon="🌯")

# Custom header with logo
st.markdown("""
    <div style='text-align: center;'>
        <img src='/mnt/data/cb_dec2020Logo.png' width='220'>
        <h1 style='font-family: sans-serif; color: #d62828;'>California Burrito GPT Analyst</h1>
        <p style='font-size: 16px; color: #6c757d;'>Ask store-level questions powered by your uploaded data.</p>
    </div>
    <hr style='margin-top:10px;margin-bottom:25px;'>
""", unsafe_allow_html=True)

uploaded_files = st.file_uploader("📁 Upload FY Store Excel files", type="xlsx", accept_multiple_files=True)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@st.cache_data
def load_clean_matrix(file):
    xls = pd.ExcelFile(file)
    all_data = []

    for sheet in xls.sheet_names:
        df = xls.parse(sheet, header=None)

        try:
            # Store codes are in row 1 (index 1), metric names in col 0, values start row 3
            stores = df.iloc[1, 3:].fillna(method="ffill").astype(str).str.strip()
            metrics = df.iloc[2:, 0].dropna().astype(str).str.strip()

            for col_idx, store in enumerate(stores, start=3):
                values = df.iloc[2:, col_idx].values[:len(metrics)]
                temp = pd.DataFrame({
                    "Month": sheet,
                    "Store": store,
                    "Metric": metrics.values,
                    "Value": values
                })
                all_data.append(temp)

        except Exception as e:
            st.warning(f"⚠️ Could not process sheet '{sheet}' — {e}")

    if not all_data:
        return pd.DataFrame()

    return pd.concat(all_data, ignore_index=True)

if uploaded_files:
    df_list = [load_clean_matrix(file) for file in uploaded_files]
    df = pd.concat(df_list, ignore_index=True)
    if df.empty:
        st.error("🚫 Could not extract usable data. Please check file format.")
        st.stop()

    st.success("✅ Store performance data loaded successfully")

    # GPT question UI
    st.markdown("""
    <div style='background-color:#f8f9fa;padding:15px;border-radius:10px;margin-bottom:20px;'>
        <h4 style='color:#343a40;'>💬 Ask a Business Question</h4>
    </div>
    """, unsafe_allow_html=True)
    user_question = st.text_area("What do you want to ask?", height=120)

    if user_question:
        sample_df = df.head(10).copy()
        sample_df = sample_df.applymap(lambda x: str(x)[:100])
        sample_data = sample_df.to_csv(index=False)
        schema = ', '.join(df.columns)

        prompt = f"""
You are a data analyst working on multi-store QSR business performance.

Instructions:
- Analyze the data based on month, metric, and store.
- Help answer questions like highest sales, profitability issues, rent outliers, etc.

Columns: {schema}
Sample Data (10 rows):
{sample_data}

User Question: {user_question}
Answer:
"""

        with st.spinner("🧠 GPT is analyzing the data..."):
            try:
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=1500
                )
                output = response.choices[0].message.content
                st.markdown("### ✅ GPT Answer")
                st.write(output)

                st.download_button("⬇ Download Answer (TXT)", data=output, file_name="answer.txt")

                # Excel Download
                excel_df = pd.DataFrame({"GPT Answer": [output]})
                excel_buf = io.BytesIO()
                with pd.ExcelWriter(excel_buf, engine='xlsxwriter') as writer:
                    excel_df.to_excel(writer, index=False)
                st.download_button("⬇ Download Answer (Excel)", data=excel_buf.getvalue(), file_name="answer.xlsx")

                # PDF Download
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=12)
                for line in output.split('\n'):
                    pdf.multi_cell(0, 10, line)
                pdf_buf = io.BytesIO()
                pdf.output(pdf_buf)
                pdf_buf.seek(0)
                st.download_button("⬇ Download Answer (PDF)", data=pdf_buf.read(), file_name="answer.pdf")

            except Exception as e:
                st.error(f"❌ GPT Error: {e}")
else:
    st.info("👆 Upload Excel files to get started.")
