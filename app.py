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

uploaded_files = st.file_uploader("📁 Upload Monthly Store Data (All Months in Sheets)", type="xlsx", accept_multiple_files=True)

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

@st.cache_data(show_spinner=False)
def load_all_sheets(files):
    all_data = []
    for file in files:
        xls = pd.ExcelFile(file)
        for sheet in xls.sheet_names:
            try:
                df = pd.read_excel(xls, sheet_name=sheet, header=None)
                df = df.dropna(how='all', axis=0).dropna(how='all', axis=1)
                if df.shape[1] < 2:
                    continue
                df.columns = ["Metric"] + df.iloc[0, 1:].tolist()
                df = df[1:]
                df = df.loc[:, ~df.columns.str.contains('%', case=False, na=False)]
                df = df.drop(columns=[col for col in df.columns if str(col).strip().lower() == "total"], errors='ignore')
                df_melted = df.melt(id_vars="Metric", var_name="Store", value_name="Value")
                df_melted = df_melted.dropna(subset=["Value"])
                df_melted["Month"] = sheet
                df_melted["Value"] = pd.to_numeric(df_melted["Value"], errors="coerce")
                df_melted = df_melted.dropna(subset=["Value"])
                df_melted = df_melted[~df_melted["Store"].str.lower().eq("total")]
                all_data.append(df_melted)
            except Exception as e:
                st.warning(f"⚠️ Sheet '{sheet}' skipped: {e}")

    if all_data:
        combined = pd.concat(all_data, ignore_index=True)
        pivoted = combined.pivot_table(index=["Store", "Month"], columns="Metric", values="Value", aggfunc="sum").reset_index()

        # Derived Metrics
        pivoted["Store EBITDA"] = (
            pivoted.get("Net Sales", 0) -
            pivoted.get("GST", 0) -
            pivoted.get("COGS", 0) -
            pivoted.get("Rent", 0) -
            pivoted.get("store Labor Cost", 0) -
            pivoted.get("Utility Cost", 0) -
            pivoted.get("Aggregator commission", 0) -
            pivoted.get("Marketing & advertisement", 0) -
            pivoted.get("Other opex expenses", 0)
        )
        pivoted["Gross Margin"] = pivoted.get("Net Sales", 0) - pivoted.get("COGS", 0)
        pivoted["Operating Cost"] = (
            pivoted.get("Rent", 0) +
            pivoted.get("store Labor Cost", 0) +
            pivoted.get("Utility Cost", 0) +
            pivoted.get("Aggregator commission", 0)
        )
        return pivoted
    return pd.DataFrame()

if uploaded_files:
    with st.spinner("🔄 Processing uploaded Excel files..."):
        df_long = load_all_sheets(uploaded_files)

    if df_long.empty:
        st.error("🚫 Could not extract data from any sheet. Please verify formatting.")
    else:
        st.success("✅ Data parsed and consolidated successfully!")

        st.markdown("""
        <div style='background-color:#f8f9fa;padding:15px;border-radius:10px;margin-bottom:20px;'>
            <h4 style='color:#343a40;'>💬 Ask a Question</h4>
        </div>
        """, unsafe_allow_html=True)

        user_question = st.text_area("Type your question below:", height=120)

        if user_question:
            sample_data = df_long.head(5).to_csv(index=False)
            schema = ', '.join(df_long.columns.astype(str))

            prompt = f"""
You are a QSR financial analyst helping the CEO of California Burrito.
Use the below structured dataset to answer queries related to store performance and operations.
Your answers must include metrics and data points where applicable.
Be concise, analytical, and insightful.

Dataset Schema: {schema}
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
                        temperature=0.2,
                        max_tokens=2000
                    )
                    output = response.choices[0].message.content
                    st.markdown("### ✅ GPT Answer")
                    st.write(output)

                    # Downloads
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
    st.info("📂 Please upload the store-wise monthly data Excel files to get started.")
