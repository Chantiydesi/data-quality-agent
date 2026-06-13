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

# --- 3. Remediation Engine ---
def apply_fix(df, column, strategy):
    try:
        # Transformation logic based on agent recommendations
        if "fill" in strategy.lower():
            if df[column].dtype in ['float64', 'int64']:
                df[column] = df[column].fillna(df[column].mean())
            else:
                df[column] = df[column].fillna(df[column].mode()[0])
        elif "remove" in strategy.lower():
            df = df.dropna(subset=[column])
        return df, True
    except Exception:
        return df, False

# --- 4. Gateway: API Connection ---
def call_ai_api(prompt_text):
    api_key = st.secrets.get("OPENROUTER_API_KEY")
    if not api_key:
        st.error("❌ API Key missing! Check your Streamlit Secrets.")
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

# --- 5. Sidebar: Design & Team Info ---
with st.sidebar:
    st.markdown("""
        <style>
        .nav-link { color: var(--primary-color); font-weight: bold; text-decoration: none; font-size: 1.2em; }
        .team-card { 
            background-color: var(--secondary-background-color); 
            padding: 15px; border-radius: 10px; margin-bottom: 10px; 
            border-left: 4px solid var(--primary-color); 
        }
        .team-name { color: var(--text-color); font-weight: bold; }
        .team-roll { color: var(--text-color); opacity: 0.7; font-size: 0.9em; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<a href="/" class="nav-link">🏠 Dashboard</a>', unsafe_allow_html=True)
    st.markdown("---")
    st.subheader("👥 Team 11")
    
    def render_card(name, roll):
        st.markdown(f'<div class="team-card"><div class="team-name">{name}</div><div class="team-roll">{roll}</div></div>', unsafe_allow_html=True)

    render_card("YDESI CHANTI BABU", "23U41A0560")
    render_card("PRAGADA HARIKA", "23U41A0547")
    render_card("NANEPALLI DEEPIKA", "23U41A4430")
    render_card("Jyothula Bhargavi", "23U41A0428")

# --- 6. Main UI Logic ---
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
                col_name = anomaly.get('column')
                with st.expander(f"⚠️ Issue in {col_name}", expanded=True):
                    st.markdown(f"**Issue:** {anomaly.get('detected_issue')}")
                    st.markdown(f"**Why:** {anomaly.get('explanation')}")
                    st.markdown(f"**Fix:** {anomaly.get('remediation_strategy')}")
                    
                    if st.button(f"🚀 Apply Fix to {col_name}", key=f"fix_{col_name}"):
                        st.session_state.raw_df, success = apply_fix(
                            st.session_state.raw_df, col_name, anomaly.get('remediation_strategy')
                        )
                        if success:
                            st.success(f"✅ Data in {col_name} corrected!")
                            st.rerun()
                        else:
                            st.error("❌ Failed to apply fix.")
