import streamlit as st
import pandas as pd
import json
import yaml
from openai import OpenAI
from pathlib import Path

# --- 1. Page Configuration ---
st.set_page_config(page_title="DQ-Agent Dashboard", layout="wide")

# --- 2. Load Rules ---
def load_rules():
    rule_file = Path("rules.yaml")
    return yaml.safe_load(rule_file.read_text()) if rule_file.exists() else {}

RULES = load_rules()

# --- 3. Gateway: API Connection ---
def call_ai_api(prompt_text):
    api_key = st.secrets.get("OPENROUTER_API_KEY")
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
        default_headers={"HTTP-Referer": "https://streamlit.io/"}
    )
    response = client.chat.completions.create(
        model="nex-agi/nex-n2-pro:free",
        messages=[{"role": "user", "content": prompt_text}],
        extra_body={"response_format": {"type": "json_object"}}
    )
    return json.loads(response.choices[0].message.content)

# --- 4. Sidebar ---
with st.sidebar:
    st.markdown('<a href="/" style="color:var(--primary-color); font-weight:bold; font-size:1.2em; text-decoration:none;">🏠 Dashboard</a>', unsafe_allow_html=True)
    st.markdown("---")
    st.subheader("👥 Team 11")
    for name, roll in [("YDESI CHANTI BABU", "23U41A0560"), ("PRAGADA HARIKA", "23U41A0547"), 
                       ("NANEPALLI DEEPIKA", "23U41A4430"), ("Jyothula Bhargavi", "23U41A0428")]:
        st.markdown(f'<div style="background:var(--secondary-background-color); padding:10px; border-radius:8px; margin-bottom:8px; border-left:4px solid var(--primary-color);"><b>{name}</b><br><small>{roll}</small></div>', unsafe_allow_html=True)

# --- 5. Main UI Logic ---
st.title("Data Quality Agent")
uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

if uploaded_file:
    # Auto-refresh on new file
    if 'current_file' not in st.session_state or st.session_state.current_file != uploaded_file.name:
        st.session_state.raw_df = pd.read_csv(uploaded_file)
        st.session_state.audit_report = None
        st.session_state.current_file = uploaded_file.name
        st.rerun()
    
    tab1, tab2 = st.tabs(["📋 Inspector", "📊 Diagnostics & Remediation"])
    
    with tab1:
        st.dataframe(st.session_state.raw_df.head(10))
    
    with tab2:
        # Determine which rules to apply
        rule_key = "healthcare_data" if "health" in uploaded_file.name.lower() else "financial_transactions"
        active_rules = RULES.get(rule_key, {})

        if st.button("🔍 Run Diagnostic Audit"):
            prompt = f"""
            Analyze this CSV data: {st.session_state.raw_df.head(20).to_json()}.
            Apply these strict RULES: {active_rules}.
            Return JSON with an 'anomalies' list. Each anomaly: 
            'column', 'issue', 'explanation', 'fix_type' (must be exactly 'abs', 'fill', or 'drop').
            Do not invent values. Follow rules strictly.
            """
            with st.spinner("Agent is auditing..."):
                st.session_state.audit_report = call_ai_api(prompt)
                st.rerun()

        if st.session_state.get("audit_report"):
            st.write("### Detected Anomalies")
            anomalies = st.session_state.audit_report.get("anomalies", [])
            st.table(pd.DataFrame(anomalies)[['column', 'issue', 'explanation', 'fix_type']])
            
            if st.button("🚀 Apply All Fixes & Download"):
                for a in anomalies:
                    col, fix = a['column'], a['fix_type']
                    if fix == "abs":
                        st.session_state.raw_df[col] = st.session_state.raw_df[col].abs()
                    elif fix == "fill":
                        val = st.session_state.raw_df[col].mean() if pd.api.types.is_numeric_dtype(st.session_state.raw_df[col]) else "Missing"
                        st.session_state.raw_df[col] = st.session_state.raw_df[col].fillna(val)
                    elif fix == "drop":
                        st.session_state.raw_df = st.session_state.raw_df.dropna(subset=[col])
                
                st.success("✅ Fixes Applied! Preview:")
                st.dataframe(st.session_state.raw_df.head(10))
                csv = st.session_state.raw_df.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Download Cleaned CSV", data=csv, file_name="cleaned_data.csv", mime="text/csv")
