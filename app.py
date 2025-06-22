import streamlit as st
import pandas as pd
import io
from fpdf import FPDF
from openai import OpenAI

st.set_page_config(layout="centered", page_title="California Burrito Analyst", page_icon="🌯")

# Logo and Title
st.markdown("""
    <div style='text-align: center;'>
        <img src='https://www.californiaburrito.in/assets/img/logo.svg' width='220'>
        <h1 style='font-family: sans-serif; color: #d62828;'>California Burrito GPT Analyst</h1>
        <p style='font-size: 16px; color: #6c757d;'>Ask store-level business questions and get intelligent responses.</p>
    </div>
    <hr style='margin-top:10px;margin-bottom:25px;'>
""", unsafe_allow_html=True)

# File upload
uploaded_files = st.file_uploader("📁 Upload Monthly Store Data (All Months in Sheets)", type="xlsx", accept_multiple_files=True)

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

@st.cache_data(show_spinner=False)
def load_all_sheets_as_long_df(files):
    all_data = []
    for file in files:
        xls = pd.ExcelFile(file)
        for sheet_name in xls.sheet_names:
            try:
                df = pd.read_excel(xls, sheet_name=sheet_name, header=0)
                df = df.loc[:df[df.iloc[:, 0].astype(str).str.lower().str.contains("store ebitda")].index[0]]
                df = df.dropna(how='all')

                # Drop percentage columns
                df = df.loc[:, ~df.columns.astype(str).str.contains("%", case=False)]

                # Melt the DataFrame to long format
                metric_col = df.columns[0]
                df = df.melt(id_vars=[metric_col], var_name="Store", value_name="Value")

                # Remove 'Total' column if present
                df = df[df["Store"].str.lower() != "total"]

                df.rename(columns={metric_col: "Metric"}, inplace=True)
                df["Month"] = sheet_name

                all_data.append(df)
            except Exception as e:
                st.warning(f"⚠️ Sheet '{sheet_name}' skipped: {e}")
    if all_data:
        return pd.concat(all_data, ignore_index=True)
    else:
        return pd.DataFrame()

if uploaded_files:
    with st.spinner("🔄 Processing uploaded Excel files..."):
        long_df = load_all_sheets_as_long_df(uploaded_files)

    if long_df.empty:
        st.error("🚫 Could not extract data from any sheet. Please verify formatting.")
    else:
        st.success("✅ Data parsed and consolidated successfully!")

        # Show Q&A interface
        st.markdown("""
        <div style='background-color:#f8f9fa;padding:15px;border-radius:10px;margin-bottom:20px;'>
            <h4 style='color:#343a40;'>💬 Ask a Question</h4>
        </div>
        """, unsafe_allow_html=True)
        user_question = st.text_area("Type your question below:", height=120)

        if user_question:
            clean_df = long_df.dropna(axis=1, how='all')
            clean_df = clean_df.loc[:, ~clean_df.columns.astype(str).str.contains("Unnamed", case=False)]
            schema = ', '.join(clean_df.columns.astype(str))
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
            with st.spinner("🔎 GPT is analyzing your data..."):
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

                    st.download_button("🗕️ Download as TXT", data=output, file_name="answer.txt")

                    excel_data = pd.DataFrame({"GPT Answer": [output]})
                    excel_buffer = io.BytesIO()
                    with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                        excel_data.to_excel(writer, index=False)
                    excel_buffer.seek(0)
                    st.download_button("🗕️ Download as Excel", data=excel_buffer.read(), file_name="gpt_answer.xlsx")

                    pdf = FPDF()
                    pdf.add_page()
                    pdf.set_font("Arial", size=12)
                    for line in output.split('\n'):
                        pdf.multi_cell(0, 10, line)
                    pdf_buffer = io.BytesIO()
                    pdf.output(pdf_buffer)
                    pdf_buffer.seek(0)
                    st.download_button("🗕️ Download as PDF", data=pdf_buffer.read(), file_name="gpt_answer.pdf")

                except Exception as e:
                    st.error(f"OpenAI Error: {e}")
else:
    st.info("📏 Please upload your raw Excel files (monthly sheets) to begin.")
