import streamlit as st
import pandas as pd
from openai import OpenAI
import os
import io
from fpdf import FPDF
from PIL import Image

st.set_page_config(layout="centered")
st.image("https://upload.wikimedia.org/wikipedia/en/9/91/California_Burrito_logo.png", width=250)
st.title("🤖 California Burrito GPT Analyst")

# Upload Excel files
uploaded_files = st.file_uploader("📁 Upload FY Store Excel files", type="xlsx", accept_multiple_files=True)

# Initialize OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@st.cache_data
def load_data(file):
    xls = pd.ExcelFile(file)
    df_all = pd.DataFrame()
    for sheet in xls.sheet_names:
        df = xls.parse(sheet)
        df.columns = [str(c).strip() for c in df.columns]

        col_map = {}
        for col in df.columns:
            lower_col = col.lower()
            if 'store' in lower_col and 'name' in lower_col:
                col_map[col] = 'Store Name'
            elif 'net' in lower_col and 'sales' in lower_col:
                col_map[col] = 'Net Sales'
            elif 'gross' in lower_col and 'sales' in lower_col:
                col_map[col] = 'Gross Sales'
            elif 'cogs' in lower_col:
                col_map[col] = 'COGS'
            elif 'rent' in lower_col:
                col_map[col] = 'Rent'
            elif 'aggregator' in lower_col and 'commission' in lower_col:
                col_map[col] = 'Aggregator commission'
            elif 'online' in lower_col and 'sales' in lower_col:
                col_map[col] = 'Online Sales'
            elif 'ebitda' in lower_col:
                col_map[col] = 'EBITDA'

        df.rename(columns=col_map, inplace=True)
        df['Month'] = sheet
        df_all = pd.concat([df_all, df], ignore_index=True)
    return df_all

if uploaded_files:
    df_list = [load_data(file) for file in uploaded_files]
    df = pd.concat(df_list, ignore_index=True)
    st.success("✅ Data successfully loaded")

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
You are a senior business analyst specializing in retail and QSR metrics.
Use the data below to detect trends, highlight anomalies, or surface opportunities.

Your job is to give:
- Revenue drivers
- Store-level profit issues
- Recommendations
- Growth opportunities
- Correlation between metrics (like high rent and low EBITDA)

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

                st.download_button("📥 Download as TXT", data=output, file_name="answer.txt")

                excel_data = pd.DataFrame({"GPT Answer": [output]})
                excel_buffer = io.BytesIO()
                with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                    excel_data.to_excel(writer, index=False)
                st.download_button("📥 Download as Excel", data=excel_buffer.getvalue(), file_name="gpt_answer.xlsx")

                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=12)
                for line in output.split('\n'):
                    pdf.multi_cell(0, 10, line)
                pdf_buffer = io.BytesIO()
                pdf.output(pdf_buffer)
                pdf_buffer.seek(0)
                st.download_button("📥 Download as PDF", data=pdf_buffer, file_name="gpt_answer.pdf")

            except Exception as e:
                st.error(f"OpenAI Error: {e}")

else:
    st.info("👆 Please upload at least one Excel file to begin.")
