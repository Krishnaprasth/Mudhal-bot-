import streamlit as st
import pandas as pd
import io
from fpdf import FPDF
from openai import OpenAI

st.set_page_config(layout="centered", page_title="California Burrito GPT Analyst", page_icon="🌯")

# Header with logo
st.markdown("""
    <div style='text-align: center;'>
        <img src='https://www.californiaburrito.in/assets/img/logo.svg' width='220'>
        <h1 style='font-family: sans-serif; color: #d62828;'>California Burrito GPT Analyst</h1>
        <p style='font-size: 16px; color: #6c757d;'>Ask store-level questions across months and metrics.</p>
    </div>
    <hr style='margin-top:10px;margin-bottom:25px;'>
""", unsafe_allow_html=True)

# File upload
uploaded_files = st.file_uploader("📁 Upload Monthly Store Data Excel Files", type="xlsx", accept_multiple_files=True)

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

@st.cache_data(show_spinner=False)
def extract_data_from_sheets(files):
    full_df = []
    for file in files:
        xls = pd.ExcelFile(file)
        for sheet in xls.sheet_names:
            try:
                df = pd.read_excel(xls, sheet_name=sheet, header=None)
                df = df.dropna(how="all", axis=0).dropna(how="all", axis=1)
                df = df.set_index(0).transpose()
                df['Month'] = sheet
                full_df.append(df)
            except Exception as e:
                st.warning(f"⚠️ Sheet '{sheet}' skipped: {e}")
    if full_df:
        return pd.concat(full_df, ignore_index=True)
    else:
        return pd.DataFrame()

if uploaded_files:
    with st.spinner("🔄 Processing your uploaded Excel files..."):
        final_df = extract_data_from_sheets(uploaded_files)

    if final_df.empty:
        st.error("🚫 Could not extract usable data. Please check the formatting in your sheets.")
    else:
        st.success("✅ Data extracted and consolidated!")

        st.markdown("""
        <div style='background-color:#f8f9fa;padding:15px;border-radius:10px;margin-bottom:20px;'>
            <h4 style='color:#343a40;'>💬 Ask Your Business Question</h4>
        </div>
        """, unsafe_allow_html=True)

        question = st.text_area("Type your question about stores, metrics, or trends:", height=120)

        if question:
            clean_df = final_df.dropna(axis=1, how='all')
            clean_df = clean_df.loc[:, ~clean_df.columns.astype(str).str.contains("Unnamed", case=False)]
            schema = ', '.join(clean_df.columns.astype(str))
            sample_data = clean_df.head(5).astype(str).to_csv(index=False)

            prompt = f"""
You are a senior business analyst for a QSR chain. Use the data below to answer questions about store performance.

Columns: {schema}

Sample Data:
{sample_data}

User Question: {question}

Answer:
"""
            with st.spinner("🔎 GPT is analyzing your data..."):
                try:
                    response = client.chat.completions.create(
                        model="gpt-4",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.3,
                        max_tokens=1500
                    )
                    answer = response.choices[0].message.content
                    st.markdown("### ✅ GPT Answer")
                    st.write(answer)

                    # Export options
                    st.download_button("⬇️ Download as TXT", data=answer, file_name="gpt_answer.txt")

                    excel_buf = io.BytesIO()
                    pd.DataFrame({"GPT Answer": [answer]}).to_excel(excel_buf, index=False)
                    st.download_button("⬇️ Download as Excel", data=excel_buf.getvalue(), file_name="gpt_answer.xlsx")

                    pdf = FPDF()
                    pdf.add_page()
                    pdf.set_font("Arial", size=12)
                    for line in answer.split('\n'):
                        pdf.multi_cell(0, 10, line)
                    pdf_out = io.BytesIO()
                    pdf.output(pdf_out)
                    pdf_out.seek(0)
                    st.download_button("⬇️ Download as PDF", data=pdf_out.read(), file_name="gpt_answer.pdf")
                except Exception as e:
                    st.error(f"❌ GPT Error: {e}")
else:
    st.info("👆 Upload Excel files where each sheet represents a month, rows are stores, and columns are metrics.")
