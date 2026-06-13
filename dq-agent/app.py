import streamlit as st
import pandas as pd
import json
import yaml
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
        st.error("❌ API Key missing! Check Streamlit Secrets.")
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

# --- 4. Sidebar: Design ---
with st.sidebar:
    st.markdown('<a href="/" style="color:var(--primary-color); font-weight:bold; font-size:1.2em; text-decoration:none;">🏠 Dashboard</a>', unsafe_allow_html=True)
    st.markdown("---")
    st.subheader("👥 Team 11")
    def render_card(name, roll):
        st.markdown(f'<div style="background:var(--secondary-background-color); padding:10px; border-radius:8px; margin-bottom:10px; border-left:4px solid var(--primary-color);"><b>{name}</b><br><small>{roll}</small></div>', unsafe_allow_html=True)
    render_card("YDESI CHANTI BABU", "23U41A0560")
    render_card("PRAGADA HARIKA", "23U41A0547")
    render_card("NANEPALLI DEEPIKA", "23U41A4430")
    render_card("Jyothula Bhargavi", "23U41A0428")

# --- 5. Main UI Logic ---
st.title("Data Quality Agent")
uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

if uploaded_file:
    if 'raw_df' not in st.session_state:
        st.session_state.raw_df = pd.read_csv(uploaded_file)
    
    tab1, tab2 = st.tabs(["📋 Inspector", "📊 Diagnostics & Remediation"])
    with tab1:
        st.dataframe(st.session_state.raw_df.head(10))
    
    with tab2:
        if st.button("🔍 Run Diagnostic Audit"):
            prompt = f"""
            Audit this data: {st.session_state.raw_df.head(10).to_json()}. 
            Rules: {VALIDATION_RULES.get('financial_transactions', {})}. 
            Return JSON with an 'anomalies' list. 
            Each anomaly must have: 'column', 'detected_issue', 'explanation', and 'remediation_strategy'.
            """
            with st.spinner("Analyzing..."):
                response = call_ai_api(prompt)
                if response:
                    st.session_state.audit_report = json.loads(response)
                    st.rerun()

        if st.session_state.get("audit_report"):
            st.write("### Detected Anomalies")
            for anomaly in st.session_state.audit_report.get("anomalies", []):
                with st.expander(f"⚠️ Issue in {anomaly.get('column')}", expanded=True):
                    st.markdown(f"**Issue:** {anomaly.get('detected_issue')}")
                    st.markdown(f"**Explanation:** {anomaly.get('explanation')}")
                    st.markdown(f"**Strategy:** {anomaly.get('remediation_strategy')}")
            
            if st.button("🚀 Apply All Fixes & Download"):
                for anomaly in st.session_state.audit_report.get("anomalies", []):
                    col = anomaly.get('column')
                    strat = anomaly.get('remediation_strategy', '').lower()
                    # Enhanced Remediation Logic
                    if "positive" in strat or "abs" in strat:
                        st.session_state.raw_df[col] = st.session_state.raw_df[col].abs()
                    elif "fill" in strat:
                        val = st.session_state.raw_df[col].mean() if pd.api.types.is_numeric_dtype(st.session_state.raw_df[col]) else st.session_state.raw_df[col].mode()[0]
                        st.session_state.raw_df[col] = st.session_state.raw_df[col].fillna(val)
                    elif "remove" in strat:
                        st.session_state.raw_df = st.session_state.raw_df.dropna(subset=[col])
                
                st.success("✅ Fixes applied!")
                st.dataframe(st.session_state.raw_df.head(10))
                csv = st.session_state.raw_df.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Download Cleaned CSV", data=csv, file_name="cleaned_data.csv", mime="text/csv")
