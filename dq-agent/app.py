import streamlit as st
import pandas as pd
import json
import yaml
import os
from openai import OpenAI
from pathlib import Path

# --- 1. Page Configuration ---
st.set_page_config(page_title="DQ-Agent Pipeline", layout="wide")

# --- 2. Configuration & Rules ---
yaml_path = Path(__file__).resolve().parent / 'rules.yaml'
VALIDATION_RULES = yaml.safe_load(open(yaml_path)) if yaml_path.exists() else {}

# --- 3. Gateway: API Connection ---
def call_ai_api(prompt_text):
    # Retrieve key securely from Streamlit Secrets
    api_key = st.secrets.get("OPENROUTER_API_KEY")
    
    if not api_key:
        st.error("❌ API Key not found! Check Streamlit Secrets.")
        return None
        
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
        default_headers={"HTTP-Referer": "https://streamlit.io/"}
    )
    
    try:
        response = client.chat.completions.create(
            model="nex-agi/nex-n2-pro:free", 
            messages=[{"role": "user", "content": prompt_text}],
            extra_body={"response_format": {"type": "json_object"}}
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"❌ API Connection Error: {e}")
        return None

# --- 4. Sidebar (Team Info) ---
with st.sidebar:
    st.title("⚙️ DQ-Agent Control")
    st.subheader("Team 11")
    st.markdown("---")
    st.markdown("**YDESI CHANTI BABU** (23U41A0560)")
    st.markdown("**PRAGADA HARIKA** (23U41A0547)")
    st.markdown("**NANEPALLI DEEPIKA** (23U41A4430)")
    st.markdown("**Jyothula Bhargavi** (23u41a0428)")

# --- 5. Main UI ---
st.title("Data Quality Agent: Deterministic YAML & LLM Engine")

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
            prompt = f"Audit this data: {df.head(10).to_json()}. Rules: {rules}. Return ONLY JSON with an 'anomalies' key."
            
            with st.spinner("Agent is analyzing..."):
                response = call_ai_api(prompt)
                if response:
                    try:
                        st.session_state.audit_report = json.loads(response)
                        st.rerun()
                    except json.JSONDecodeError:
                        st.error("❌ Failed to parse JSON response.")

        if st.session_state.get("audit_report"):
            st.write("### Audit Results")
            for anomaly in st.session_state.audit_report.get("anomalies", []):
                st.warning(f"Issue in **{anomaly.get('column')}**: {anomaly.get('detected_issue')}")
