import streamlit as st
import pandas as pd
import json
import yaml
import os
from openai import OpenAI
from pathlib import Path

# --- 1. Page Configuration ---
st.set_page_config(page_title="DQ-Agent Pipeline", layout="wide")

# --- 2. Secure API Client Loader ---
def get_client():
    # This fetches the key securely from the Streamlit Cloud Secrets dashboard
    api_key = st.secrets.get("OPENROUTER_API_KEY")
    if not api_key:
        return None
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
        default_headers={
            "HTTP-Referer": "https://streamlit.io/", # Required by OpenRouter
            "X-Title": "Data Quality Agent"         # Optional for leaderboards
        }
    )

# --- 3. Rules Engine Loader ---
yaml_path = Path(__file__).resolve().parent / 'rules.yaml'
VALIDATION_RULES = yaml.safe_load(open(yaml_path)) if yaml_path.exists() else {}

# --- 4. API Gateway ---
def call_ai_api(prompt_text):
    client = get_client()
    if not client:
        st.error("❌ API Key not found! Please check your Streamlit Secrets configuration.")
        return None
    try:
        response = client.chat.completions.create(
            # Using the Nex AGI free model as requested
            model="nex-agi/nex-n2-pro:free", 
            messages=[{"role": "user", "content": prompt_text}],
            extra_body={"response_format": {"type": "json_object"}}
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"❌ API Connection Error: {e}")
        return None

# --- 5. User Interface ---
st.title("Data Quality Agent: Deterministic YAML & LLM Engine")
st.subheader("Team 11")

uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

if uploaded_file:
    # Initialize session state for dataframe
    if 'raw_df' not in st.session_state:
        st.session_state.raw_df = pd.read_csv(uploaded_file)
    
    df = st.session_state.raw_df
    
    tab1, tab2 = st.tabs(["📋 Data Preview", "📊 Diagnostic Audit"])
    
    with tab1:
        st.dataframe(df.head(10))
    
    with tab2:
        if st.button("🔍 Run Diagnostic Audit"):
            rules = VALIDATION_RULES.get("financial_transactions", {})
            prompt = f"Audit this data: {df.head(10).to_json()}. Rules: {rules}. Return result in JSON format with an 'anomalies' list."
            
            with st.spinner("Agent is analyzing data..."):
                response = call_ai_api(prompt)
                if response:
                    st.session_state.audit_report = json.loads(response)
                    st.rerun()

        # Display results if available
        if st.session_state.get("audit_report"):
            st.write("### Audit Results")
            anomalies = st.session_state.audit_report.get("anomalies", [])
            for anomaly in anomalies:
                st.warning(f"Issue in **{anomaly.get('column')}**: {anomaly.get('detected_issue')}")
