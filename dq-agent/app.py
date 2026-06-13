import streamlit as st
import pandas as pd
import json
import yaml
import os
from openai import OpenAI
from pathlib import Path

# --- 1. Page Configuration ---
st.set_page_config(page_title="DQ-Agent Dashboard", layout="wide")

# --- 2. Configuration & Rules ---
yaml_path = Path(__file__).resolve().parent / 'rules.yaml'
VALIDATION_RULES = yaml.safe_load(open(yaml_path)) if yaml_path.exists() else {}

# --- 3. Gateway: API Connection ---
def call_ai_api(prompt_text):
    api_key = st.secrets.get("OPENROUTER_API_KEY")
    if not api_key:
        st.error("❌ API Key missing in Streamlit Secrets.")
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
        st.error(f"❌ API Error: {e}")
        return None

# --- 4. Sidebar: Design & Navigation ---
with st.sidebar:
    st.markdown("""
        <style>
        [data-testid="stSidebar"] { background-color: #0e1117; padding: 20px; }
        .nav-link { color: #3498db; font-weight: bold; text-decoration: none; font-size: 1.2em; }
        .team-card { background-color: #1c1c1c; padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 4px solid #3498db; }
        .team-name { color: white; font-weight: bold; }
        .team-roll { color: #888; font-size: 0.9em; }
        </style>
    """, unsafe_allow_html=True)

    # Simplified Sidebar
    st.markdown('<a href="/" class="nav-link">🏠 Dashboard</a>', unsafe_allow_html=True)
    st.markdown("---")
    st.subheader("👥 Team 11")
    
    def render_card(name, roll):
        st.markdown(f'<div class="team-card"><div class="team-name">{name}</div><div class="team-roll">{roll}</div></div>', unsafe_allow_html=True)

    render_card("YDESI CHANTI BABU", "23U41A0560")
    render_card("PRAGADA HARIKA", "23U41A0547")
    render_card("NANEPALLI DEEPIKA", "23U41A4430")
    render_card("Jyothula Bhargavi", "23U41A0428")

# --- 5. Main UI Logic ---
st.title("Data Quality Agent")
st.caption("Agent · Team 11")

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
            # Updated prompt to ensure actionable remediation
            prompt = f"""
            Audit this data: {df.head(10).to_json()}. 
            Rules: {rules}. 
            Return JSON with an 'anomalies' list. 
            Each anomaly must have: 'column', 'detected_issue', 'explanation', and 'remediation_strategy'.
            """
            
            with st.spinner("Analyzing data quality..."):
                response = call_ai_api(prompt)
                if response:
                    st.session_state.audit_report = json.loads(response)
                    st.rerun()

        if st.session_state.get("audit_report"):
            for anomaly in st.session_state.audit_report.get("anomalies", []):
                with st.expander(f"⚠️ Issue in {anomaly.get('column')}", expanded=True):
                    st.markdown(f"**Issue:** {anomaly.get('detected_issue')}")
                    st.markdown(f"**Why this is an issue:** {anomaly.get('explanation')}")
                    st.markdown(f"**How to fix it:** {anomaly.get('remediation_strategy')}")
