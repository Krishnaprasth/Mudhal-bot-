import streamlit as st
import openai
import os

# Set your OpenAI API key from Streamlit Secrets
openai.api_key = os.getenv("OPENAI_API_KEY")

st.set_page_config(page_title="Deal Evaluation Bot", layout="centered")
st.title("🧠 Startup Deal Evaluation Bot")
st.write("Evaluate early-stage startups using a structured scoring rubric.")

# User input
startup_text = st.text_area("Paste founder note, pitch summary, or transcript here", height=300)
submit = st.button("🚀 Evaluate Deal")

# Only run evaluation if user clicks button
if submit and startup_text:
    # Prompt template
    prompt_template = f"""
You are a startup analyst. Based on the input below, evaluate the startup using this rubric:
- Team (20%)
- Traction (20%)
- Business Model (20%)
- Market (20%)
- Product (10%)
- Risks (10%)

Give a 1–10 score for each category, then calculate a weighted total score (/10). 
Also provide a 2–3 line summary and highlight red flags or missing information.

Input:
{startup_text}

Respond in this format:

Summary:
- [2-3 line summary]

Scores:
- Team: x/10
- Traction: x/10
- Business Model: x/10
- Market: x/10
- Product: x/10
- Risks: x/10

Weighted Score: x.xx / 10

Red Flags:
- [List of any concerns or missing data]
"""

    # Run GPT
    with st.spinner("Evaluating the startup..."):
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a startup investment analyst."},
                    {"role": "user", "content": prompt_template}
                ],
                temperature=0.3
            )
            result = response.choices[0].message.content
            st.markdown("---")
            st.markdown("### 📋 Evaluation Output")
            st.text(result)
            st.download_button("📥 Download Evaluation", result, file_name="deal_evaluation.txt")
        except Exception as e:
            st.error(f"Error: {str(e)}")
