import streamlit as st
import pandas as pd
import io
from fpdf import FPDF
from openai import OpenAI

st.set_page_config(layout="centered", page_title="California Burrito CEO Bot", page_icon="🌯")

# UI Header
st.markdown("""
    <div style='text-align: center;'>
        <img src='https://www.californiaburrito.in/assets/img/logo.svg' width='220'>
        <h1 style='font-family: sans-serif; color: #d62828;'>California Burrito CEO GPT Bot</h1>
        <p style='font-size: 16px; color: #6c757d;'>Upload monthly P&L files and ask any store performance question</p>
    </div>
    <hr style='margin-top:10px;margin-bottom:25px;'>
""", unsafe_allow_html=True)

# Upload Excel Files
uploaded_files = st.file_uploader("📁 Upload Raw Monthly Excel Files", type="xlsx", accept_multiple_files=True)

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

@st.cache_data(show_spinner=False)
def parse_excel(files):
    all_data = []
    for file in files:
        xls = pd.ExcelFile(file)
        for sheet in xls.sheet_names:
            try:
                df = pd.read_excel(xls, sheet_name=sheet, index_col=0)
                df = df.dropna(how="all")
                df.columns = df.columns.astype(str)
                df = df.transpose()
                df["Store"] = df.index
                df["Month"] = sheet.strip()
                df = df[~df["Store"].str.lower().eq("total")]
                all_data.append(df)
            except Exception as e:
                st.warning(f"⚠️ Skipping sheet '{sheet}': {e}")
    if not all_data:
        return pd.DataFrame()

    df_all = pd.concat(all_data, ignore_index=True)
    df_all.columns = df_all.columns.str.strip()
    df_all = df_all.apply(pd.to_numeric, errors="ignore")

    # Derived columns
    df_all["Gross Margin"] = df_all.get("Net Sales", 0) - df_all.get("COGS", 0)
    df_all["Operating Cost"] = df_all.get("Rent", 0) + df_all.get("store Labor Cost", 0) + df_all.get("Utility Cost", 0)
    df_all["EBITDA"] = df_all.get("Net Sales", 0) - df_all.get("GST", 0) - df_all.get("COGS", 0) \
        - df_all.get("Rent", 0) - df_all.get("store Labor Cost", 0) - df_all.get("Utility Cost", 0) \
        - df_all.get("Aggregator commission", 0) - df_all.get("Marketing & advertisement", 0) \
        - df_all.get("Other opex expenses", 0)

    return df_all

if uploaded_files:
    df = parse_excel(uploaded_files)
    if df.empty:
        st.error("🚫 No usable data. Please verify formatting.")
    else:
        st.success("✅ Data parsed successfully!")

        st.markdown("""
        <div style='background-color:#f8f9fa;padding:15px;border-radius:10px;margin-bottom:20px;'>
            <h4 style='color:#343a40;'>💬 Ask a Store Performance Question</h4>
        </div>
        """, unsafe_allow_html=True)

        user_q = st.text_area("CEO Question:", height=120)

        if user_q:
            preview = df.head(5).to_csv(index=False)
            schema = ', '.join(df.columns.astype(str))

            prompt = f"""
You are a senior analyst for a QSR chain (California Burrito).
Use this structured dataset to answer business performance queries.

Always try to use:
- EBITDA, Net Sales, COGS, GST, Rent, Utility, Labor, etc.
- If a store or month is mentioned, filter accordingly.
- Display tables for trend or comparison questions.

Columns: {schema}
Sample rows:
{preview}

Question: {user_q}
"""

            with st.spinner("🤖 GPT analyzing your data..."):
                try:
                    response = client.chat.completions.create(
                        model="gpt-4",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.3,
                        max_tokens=2000
                    )
                    result = response.choices[0].message.content
                    st.markdown("### ✅ GPT Answer")
                    st.write(result)

                    st.download_button("🗕 Download Answer (TXT)", result, file_name="gpt_answer.txt")

                    excel_data = pd.DataFrame({"GPT Answer": [result]})
                    buffer = io.BytesIO()
                    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                        excel_data.to_excel(writer, index=False)
                    st.download_button("🗕 Download Excel", buffer.getvalue(), file_name="gpt_answer.xlsx")

                    pdf = FPDF()
                    pdf.add_page()
                    pdf.set_font("Arial", size=12)
                    for line in result.split('\n'):
                        pdf.multi_cell(0, 10, line)
                    pdf_output = io.BytesIO()
                    pdf.output(pdf_output)
                    pdf_output.seek(0)
                    st.download_button("🗕 Download PDF", pdf_output.read(), file_name="gpt_answer.pdf")

                except Exception as e:
                    st.error(f"❌ GPT Error: {e}")
else:
    st.info("📥 Upload your Excel sheets (monthly store data) to begin.")
