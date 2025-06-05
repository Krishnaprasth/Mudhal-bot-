import streamlit as st
import openai
import os
import PyPDF2

# 🔐 Get API key from Streamlit Secrets
openai.api_key = os.getenv("OPENAI_API_KEY")

st.set_page_config(page_title="Startup Deal Memo Generator", layout="centered")
st.title("🧠 Comprehensive Startup Deal Evaluator")
st.write("Upload a pitch deck or paste a founder note to generate a full investment memo with scorecard.")

# Upload or paste pitch content
uploaded_file = st.file_uploader("📄 Upload pitch deck (PDF)", type=["pdf"])
startup_text = st.text_area("Or paste founder note / call summary", height=250)
submit = st.button("🚀 Generate Investment Memo")

# PDF to text extractor
def extract_text_from_pdf(file):
    pdf = PyPDF2.PdfReader(file)
    return "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])

# GPT prompt builder
def build_prompt(text):
    return f"""
You are a venture capital analyst. Based on the startup input below, write a detailed investment memo.

Include the following 10 sections:

1. Executive Summary  
2. Team  
3. Product  
4. Market  
5. Traction  
6. Business Model  
7. Go-to-Market Strategy  
8. Risks & Concerns  
9. Investment Recommendation (score out of 10 with rationale)

10. Scorecard Summary:
Format as a table:

| Category         | Score (1–10) |
|------------------|--------------|
| Team             |              |
| Product          |              |
| Market           |              |
| Traction         |              |
| Business Model   |              |
| GTM Strategy     |              |
| Risk Level       |              |

Then conclude with:
**→ Weighted Composite Score: x.xx / 10**

Startup Input:
{text}
"""

# Run GPT
if submit and (uploaded_file or startup_text.strip()):
    with st.spinner("🧠 Thinking like an analyst..."):
        try:
            content = startup_text.strip()
            if uploaded_file:
                content = extract_text_from_pdf(uploaded_file)

            prompt = build_prompt(content)

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a professional VC investment analyst."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4
            )

            result = response.choices[0].message.content
            st.markdown("---")
            st.markdown("### 📋 Full Investment Memo")
            st.text(result)

            st.download_button(
                label="📥 Download Memo",
                data=result,
                file_name="investment_memo.txt",
                mime="text/plain"
            )
        except Exception as e:
            st.error(f"Error: {str(e)}")
else:
    st.info("Please upload a pitch deck or paste startup input above.")
