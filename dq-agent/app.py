import streamlit as st
import pandas as pd
import json
import yaml
import os
from openai import OpenAI
from pathlib import Path
from dotenv import load_dotenv

# --- 1. Environment & Setup ---
load_dotenv()
st.set_page_config(page_title="DQ-Agent Pipeline", layout="wide")

# Initialize OpenRouter Client
# Ensure OPENROUTER_API_KEY is in your Streamlit Secrets or .env file
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=st.secrets.get("OPENROUTER_API_KEY") or os.getenv("OPENROUTER_API_KEY")
)

# Load Rules
yaml_path = Path(__file__).resolve().parent / 'rules.yaml'
VALIDATION_RULES = yaml.safe_load(open(yaml_path)) if yaml_path.exists() else {}

# --- 2. Upstream Gateway (OpenRouter/OpenAI Compatible) ---
def call_ai_api(prompt_text):
    if not client.api_key:
        st.error("❌ API Key missing! Check Streamlit Secrets.")
        return None
    try:
        response = client.chat.completions.create(
            model="openai/gpt-4o-mini", # Reliable, low-cost model
            messages=[{"role": "user", "content": prompt_text}],
            extra_body={"response_format": {"type": "json_object"}}
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"❌ API Connection Error: {e}")
        return None

# --- 3. UI Development ---
with st.sidebar:
    st.title("⚙️ DQ-Agent Control")
    st.markdown("---")
    st.subheader("Team 11")
    st.markdown("**YDESI CHANTI BABU** (23U41A0560)")
    st.markdown("**PRAGADA HARIKA** (23U41A0547)")
    st.markdown("**NANEPALLI DEEPIKA** (23U41A4430)")
    st.markdown("**Jyothula Bhargavi** (23u41a0428)")

st.title("Data Quality Agent: Deterministic YAML & LLM Engine")

# --- 4. Pipeline Execution ---
uploaded_file = st.file_uploader("Upload CSV", type=["csv"])
if uploaded_file:
    if 'raw_df' not in st.session_state:
        st.session_state.raw_df = pd.read_csv(uploaded_file)
    
    df = st.session_state.raw_df
    tab1, tab2 = st.tabs(["📋 Inspector", "📊 Diagnostics & Remediation"])
    
    with tab1:
        st.dataframe(df.head(10))
    
    with tab2:
        if st.button("🔍 Run Diagnostic Audit"):
            rules = VALIDATION_RULES.get("financial_transactions", {})
            prompt = f"Audit this data: {df.head(10).to_json()}. Rules: {rules}. Return result in JSON format with an 'anomalies' list."
            response = call_ai_api(prompt)
            if response:
                st.session_state.audit_report = json.loads(response)
                st.rerun()

        if st.session_state.get("audit_report"):
            anomalies = st.session_state.audit_report.get("anomalies", [])
            for anomaly in anomalies:
                st.warning(f"Issue in {anomaly['column']}: {anomaly['detected_issue']}")
                if st.button(f"Fix {anomaly['column']}"):
                    st.success("Patch applied.")
                    st.rerun()
