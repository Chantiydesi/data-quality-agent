import streamlit as st
import pandas as pd
import json
import os
import yaml
import google.generativeai as genai
from pathlib import Path
from dotenv import load_dotenv

# --- 1. Environment & Setup ---
current_dir = Path(__file__).resolve().parent
env_path = current_dir / '.env'
load_dotenv(dotenv_path=env_path)

st.set_page_config(page_title="DQ-Agent Pipeline", layout="wide")

# Secure API Key Loading
def get_api_key():
    return st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")

RAW_API_KEY = get_api_key()

# Configure SDK - This handles the AQ. key handshake automatically
if RAW_API_KEY:
    genai.configure(api_key=RAW_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')

# --- 2. Load Configuration ---
yaml_path = current_dir / 'rules.yaml'
VALIDATION_RULES = yaml.safe_load(open(yaml_path)) if yaml_path.exists() else {}

# --- 3. Upstream Gateway (Using Official SDK) ---
def call_gemini_api(prompt_text):
    if not RAW_API_KEY:
        st.error("❌ Valid GEMINI_API_KEY missing!")
        return None
    try:
        response = model.generate_content(
            prompt_text,
            generation_config={"response_mime_type": "application/json"}
        )
        return response.text
    except Exception as e:
        st.error(f"❌ SDK Authentication Error: {e}")
        return None

# --- 4. UI Development ---
with st.sidebar:
    st.title("⚙️ DQ-Agent Control")
    use_llm = st.toggle("Activate AI Engine", value=True)
    st.markdown("---")
    st.subheader("Team 11")
    st.markdown("**YDESI CHANTI BABU** (23U41A0560)")
    st.markdown("**PRAGADA HARIKA** (23U41A0547)")
    st.markdown("**NANEPALLI DEEPIKA** (23U41A4430)")
    st.markdown("**Jyothula Bhargavi** (23u41a0428)")

st.title("Data Quality Agent: Deterministic YAML & LLM Engine")

# --- 5. Data Pipeline ---
uploaded_file = st.file_uploader("Upload CSV", type=["csv"])
if uploaded_file:
    if 'raw_df' not in st.session_state:
        st.session_state.raw_df = pd.read_csv(uploaded_file)
    
    df = st.session_state.raw_df
    tab1, tab2 = st.tabs(["📋 Inspector", "📊 Diagnostics & Remediation"])
    
    with tab1:
        st.dataframe(df.head(10))
    
    with tab2:
        if st.button("🔍 Run Audit"):
            rules = VALIDATION_RULES.get("financial_transactions", {})
            prompt = f"Audit this data: {df.head(10).to_json()}. Rules: {rules}. Return ONLY JSON."
            response = call_gemini_api(prompt)
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

# 6. Downstream Delivery
if st.session_state.get("healed_df") is not None:
    st.download_button("📥 Download Cleaned CSV", data=st.session_state.healed_df.to_csv(), file_name="cleaned.csv")
