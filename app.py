import streamlit as st
import pandas as pd
from openai import OpenAI
import os
import io
from fpdf import FPDF

st.set_page_config(layout="centered")
st.image("https://www.californiaburrito.in/assets/images/logo.png", width=250)
st.title("🤖 California Burrito GPT Analyst")

uploaded_files = st.file_uploader("📁 Upload FY Store Excel files", type="xlsx", accept_multiple_files=True)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@st.cache_data
def load_data(file):
    xls = pd.ExcelFile(file)
    df_all = pd.DataFrame()
    for sheet in xls.sheet_names:
        df = xls.parse(sheet)
        df.columns = [str(c).strip() for c in df.columns]

        # Mapping relevant columns
        col_map = {}
        for col in df.columns:
            lower_col = col.lower()
            if 'store' in lower_col:
                col_map[col] = 'Store'
            elif 'net' in lower_col and 'sales' in lower_col:
                col_map[col] = 'Net Sales'
            elif 'gross' in lower_col and 'sales' in lower_col:
                col_map[col] = 'Gross Sales'
            elif 'cogs' in lower_col:
                col_map[col] = 'COGS'
            elif 'rent' in lower_col:
                col_map[col] = 'Rent'
            elif 'aggregator' in lower_col and 'commission' in lower_col:
                col_map[col] = 'Aggregator Commission'
            elif 'online' in lower_col and 'sales' in lower_col:
                col_map[col] = 'Online Sales'
            elif 'ebitda' in lower_col:
                col_map[col] = 'EBITDA'

        df.rename(columns=col_map, inplace=True)
        df['Month'] = sheet  # Ensure Month is always added
        df_all = pd.concat([df_all, df], ignore_index=True)
    return df_all

if uploaded_files:
    df_list = [load_data(file) for file in uploaded_files]
    df = pd.concat(df_list, ignore_index=True)
    st.success("✅ Data successfully loaded")

    st.markdown("### 💬 Ask any question about your store data")
    user_question = st.text_area("Type your question below:", height=120)

    if user_question:
        try:
            clean_df = df.dropna(axis=1, how='all')
            clean_df = clean_df.loc[:, ~clean_df.columns.astype(str).str.contains("Unnamed", case=False)]
            if clean_df.empty:
                st.warning("⚠️ Your uploaded file doesn't contain recognizable store data.")
            else:
                schema = ', '.join(clean_df.columns)
                sample_df = clean_df.head(5).copy().applymap(lambda x: str(x)[:100])
                sample_data = sample_df.to_csv(index=False)

                prompt = f"""
You are a senior business analyst specializing in restaurant operations.
Below is store-wise performance data.

Analyze the following:
- Revenue trends
- Profitability problems
- Store-level performance differences
- Operational insights and recommendations

Columns: {schema}
Sample Data (first 5 rows):
{sample_data}

User question: {user_question}
Answer:
"""

                with st.spinner("🤖 Thinking..."):
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

                    excel_buffer = io.BytesIO()
                    pd.DataFrame({"GPT Answer": [output]}).to_excel(excel_buffer, index=False, engine='xlsxwriter')
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
            st.error(f"❌ Error: {e}")

else:
    st.info("👆 Please upload at least one Excel file to begin.")
