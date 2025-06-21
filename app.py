import streamlit as st
import pandas as pd
import os
import io
from fpdf import FPDF
from openai import OpenAI

st.set_page_config(layout="centered")
st.image("https://www.californiaburrito.in/assets/images/logo.png", width=250)
st.title("🤖 California Burrito GPT Analyst")

uploaded_files = st.file_uploader("📁 Upload FY Store Excel files", type="xlsx", accept_multiple_files=True)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@st.cache_data
def load_matrix_excel(file):
    xls = pd.ExcelFile(file)
    all_data = []
    for sheet in xls.sheet_names:
        raw_df = xls.parse(sheet, header=None)

        # Extract merged headers (rows 1 and 2)
        store_names = raw_df.iloc[1, 3:].fillna(method='ffill').astype(str).str.strip()
        metric_types = raw_df.iloc[2, 3:].astype(str).str.strip()
        combined_headers = store_names + ' - ' + metric_types

        df = raw_df.iloc[3:, :]
        df.columns = ['Metric'] + list(combined_headers)
        df = df.dropna(subset=['Metric'])

        df = df.set_index('Metric').T.reset_index()
        df[['Store', 'Metric Type']] = df['index'].str.split(' - ', expand=True)
        df['Month'] = sheet
        df = df.drop(columns=['index'])
        all_data.append(df)

    final_df = pd.concat(all_data, ignore_index=True)
    return final_df

if uploaded_files:
    df_list = [load_matrix_excel(file) for file in uploaded_files]
    df = pd.concat(df_list, ignore_index=True)
    st.success("✅ Data successfully loaded and cleaned")

    st.markdown("### 💬 Ask any question about your store data")
    user_question = st.text_area("Type your question below:", height=120)

    if user_question:
        clean_df = df.dropna(axis=1, how='all')
        clean_df = clean_df.loc[:, ~clean_df.columns.astype(str).str.contains("Unnamed", case=False)]
        schema = ', '.join(clean_df.columns)

        sample_df = clean_df.head(5).copy()
        sample_df = sample_df.applymap(lambda x: str(x)[:100])
        sample_data = sample_df.to_csv(index=False)

        prompt = f"""
You are a senior business analyst specializing in QSR and multi-store chains.
Use the below data to identify trends, anomalies, opportunities, and respond to user queries accurately.

Columns: {schema}
Sample Data (first 5 rows):
{sample_data}

User question: {user_question}
Answer:
"""

        with st.spinner("Generating insight..."):
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

                st.download_button("📅 Download as TXT", data=output, file_name="answer.txt")

                excel_data = pd.DataFrame({"GPT Answer": [output]})
                excel_buffer = io.BytesIO()
                with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                    excel_data.to_excel(writer, index=False)
                excel_buffer.seek(0)
                st.download_button("📅 Download as Excel", data=excel_buffer.read(), file_name="gpt_answer.xlsx")

                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=12)
                for line in output.split('\n'):
                    pdf.multi_cell(0, 10, line)
                pdf_buffer = io.BytesIO()
                pdf.output(pdf_buffer)
                pdf_buffer.seek(0)
                st.download_button("📅 Download as PDF", data=pdf_buffer.read(), file_name="gpt_answer.pdf")

            except Exception as e:
                st.error(f"OpenAI Error: {e}")
else:
    st.info("👆 Please upload at least one Excel file to begin.")
