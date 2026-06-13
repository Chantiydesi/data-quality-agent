import streamlit as st
import pandas as pd
import numpy as np
import io
import json
import requests 
import os                      
import yaml                     
from dotenv import load_dotenv  
from pathlib import Path

# --- LOCAL SETUP ---
current_dir = Path(__file__).resolve().parent if '__file__' in locals() else Path.cwd()
env_path = current_dir / '.env'
load_dotenv(dotenv_path=env_path)

st.set_page_config(
    page_title="Data Quality Agent with Auto-Fix Suggestions", 
    page_icon="🔮", 
    layout="wide"
)

# --- SECURE API KEY LOADING ---
# First attempt to read from Streamlit Secrets (for Cloud Deployment)
# Then fall back to local environment variables (for Local Execution)
def get_api_key():
    try:
        return st.secrets["GEMINI_API_KEY"]
    except (KeyError, FileNotFoundError):
        return os.getenv("GEMINI_API_KEY")

RAW_API_KEY = get_api_key()

# --- LOAD THE YAML CONFIGURATION ---
yaml_path = current_dir / 'rules.yaml'
if yaml_path.exists():
    with open(yaml_path, 'r') as file:
        VALIDATION_RULES = yaml.safe_load(file)
else:
    VALIDATION_RULES = {}

def call_gemini_api(prompt_text):
    if not RAW_API_KEY or RAW_API_KEY.strip() == "":
        st.error("❌ Valid GEMINI_API_KEY is missing! Please set it in Streamlit Secrets or your local .env file.")
        return None

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={RAW_API_KEY}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt_text}]}],
        "generationConfig": {"responseMimeType": "application/json"}
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            st.error(f"❌ API Gate Error ({response.status_code}): {response.text}")
            return None
    except Exception as e:
        st.error(f"❌ Connection Failed: {e}")
        return None

# --- DYNAMIC SIDEBAR DESIGN ---
with st.sidebar:
    st.markdown("<h2 style='color: #4A90E2; font-family: sans-serif; margin-bottom: 5px;'>QA Agent</h2>", unsafe_allow_html=True)
    st.caption("v2.1.0 · Hybrid Rule Core")
    st.markdown("---")
    
    use_llm = st.toggle("Gemini Pro LLM Engine", value=True, help="Toggle AI parsing engine off or on.")
    if use_llm:
        st.caption("🟢 **ON** — Using Gemini AI Core")
    else:
        st.caption("⚪ **OFF** — Pipeline Suspended")
        
    st.markdown("---")
    
    # 👥 TEAM DETAILS HEADER
    st.markdown("<h4 style='color: #4A90E2; font-family: sans-serif; margin-bottom: 12px;'>Team 11</h4>", unsafe_allow_html=True)
    
    card_style = """
    <style>
    .team-card {
        background-color: #111625;
        border-left: 4px solid #00D2FF;
        border-radius: 6px;
        padding: 10px 12px;
        margin-bottom: 8px;
        font-family: sans-serif;
    }
    .team-name {
        color: #FFFFFF;
        font-weight: bold;
        font-size: 13px;
        margin: 0;
    }
    .team-meta {
        color: #8A99AD;
        font-size: 11px;
        margin-top: 2px;
        margin-bottom: 0;
    }
    </style>
    """
    st.markdown(card_style, unsafe_allow_html=True)
    
    # 1st Member
    st.markdown("<div class='team-card'><p class='team-name'>YDESI CHANTI BABU</p><p class='team-meta'>Roll: 23U41A0560 · CSE</p></div>", unsafe_allow_html=True)
    
    # 2nd Member
    st.markdown("<div class='team-card'><p class='team-name'>PRAGADA HARIKA</p><p class='team-meta'>Roll: 23U41A0547 · CSE</p></div>", unsafe_allow_html=True)
    
    # 3rd Member
    st.markdown("<div class='team-card'><p class='team-name'>NANEPALLI DEEPIKA</p><p class='team-meta'>Roll: 23U41A4430 · CSD</p></div>", unsafe_allow_html=True)
    
    # 4th Member
    st.markdown("<div class='team-card'><p class='team-name'>Jyothula Bhargavi</p><p class='team-meta'>Roll: 23u41a0428 · ECE</p></div>", unsafe_allow_html=True)

# --- MAIN INTERFACE RUNTIME PANEL ---
st.title("Data Quality Agent with Auto-Fix Suggestions")
st.write("Targeted Processing Pipeline backed by **Deterministic YAML Rules** and **Generative LLM Engine Patches**.")

chosen_domain = st.selectbox("🎯 Select Dataset Pipeline Domain", ["Healthcare Data", "Financial Transactions"])
domain_key = "healthcare_data" if chosen_domain == "Healthcare Data" else "financial_transactions"

uploaded_file = st.file_uploader("Upload your target CSV file", type=["csv"])

if uploaded_file is not None:
    if 'raw_df' not in st.session_state or st.session_state.get('current_file') != uploaded_file.name:
        st.session_state.raw_df = pd.read_csv(uploaded_file)
        st.session_state.current_file = uploaded_file.name
        st.session_state.audit_complete = False
        st.session_state.audit_report = None
        st.session_state.healed_df = None
        st.session_state.healing_complete = False

    df = st.session_state.raw_df
    
    tab1, tab2 = st.tabs(["📋 Data Source Inspector", "📊 Diagnostics & Remediation"])
    
    with tab1:
        st.subheader("Raw Data Sample Metrics")
        st.dataframe(df.head(10), use_container_width=True)
    
    with tab2:
        if not st.session_state.audit_complete:
            if st.button(f"🔍 Run Diagnostic Audit on {chosen_domain}", type="primary"):
                with st.spinner("Executing YAML validation matrix & querying LLM agent..."):
                    
                    rules = VALIDATION_RULES.get(domain_key, {})
                    columns_list = list(df.columns)
                    sample_rows = df.head(10).fillna("NaN").to_dict(orient="records")
                    missing_cols = [col for col in rules.get('required_columns', []) if col not in columns_list]
                    
                    audit_prompt = f"""
                    You are an expert Data Auditor specialized purely in {chosen_domain}.
                    Operational Rules: {json.dumps(rules)}
                    Missing Columns: {missing_cols}
                    Columns: {columns_list}
                    Samples: {sample_rows}
                    
                    Return ONLY a JSON object:
                    {{
                        "dataset_summary": "string",
                        "anomalies": [
                            {{
                                "column": "string",
                                "detected_issue": "string",
                                "severity": "High/Medium/Low",
                                "suggestion": "string description of how to fix it"
                            }}
                        ]
                    }}
                    Do not use markdown blocks.
                    """
                    
                    if use_llm:
                        raw_response = call_gemini_api(audit_prompt)
                        if raw_response:
                            try:
                                st.session_state.audit_report = json.loads(raw_response)
                                st.session_state.audit_complete = True
                                st.rerun()
                            except Exception as p_err:
                                st.error(f"JSON Parsing failed: {p_err}")
                    else:
                        st.warning("⚠️ LLM engine is turned off. Please enable the toggle in the sidebar to run the auto-audit.")

        if st.session_state.audit_complete and st.session_state.audit_report:
            report = st.session_state.audit_report
            st.header("📊 Automated Quality Log")
            st.info(f"**Pipeline Domain Profile:** {chosen_domain}")
            st.write(f"**Data Profile Summary:** {report.get('dataset_summary', '')}")
            
            anomalies = report.get('anomalies', [])
            if not anomalies:
                st.success("✅ Clean Bill of Health! No issues caught.")
            else:
                for idx, anomaly in enumerate(anomalies, 1):
                    with st.expander(f"⚠️ Issue #{idx} found in `{anomaly.get('column')}`", expanded=True):
                        st.markdown(f"**Detected Vulnerability:** {anomaly.get('detected_issue')}")
                        st.markdown(f"**Severity Level:** `{anomaly.get('severity')}`")
                        st.markdown(f"💡 **Remediation Suggestion:** *{anomaly.get('suggestion')}*")
                
                st.markdown("---")
                st.subheader("🛠️ Auto-Correction Remediation Core")
                if not st.session_state.healing_complete:
                    if st.button("🚀 Execute Code Patch Repair Pipeline", type="primary"):
                        with st.spinner("Compiling structural Pandas patch..."):
                            
                            fix_prompt = f"""
                            Write pure Python Pandas code to fix these anomalies in a dataframe called 'df': {anomalies}
                            Return ONLY a JSON object:
                            {{
                                "pandas_fix": "clean python string code operating directly on df"
                            }}
                            Do not wrap in markdown syntax.
                            """
                            
                            raw_fix_response = call_gemini_api(fix_prompt)
                            if raw_fix_response:
                                try:
                                    fix_data = json.loads(raw_fix_response)
                                    code_patch = fix_data.get('pandas_fix', '')
                                    
                                    st.session_state.patch_code = code_patch
                                    local_env = {"df": df.copy(), "pd": pd, "np": np}
                                    exec(code_patch, globals(), local_env)
                                    
                                    st.session_state.healed_df = local_env["df"]
                                    st.session_state.healing_complete = True
                                    st.rerun()
                                except Exception as exec_err:
                                    st.error(f"Failed to execute patch block: {exec_err}")
                
                if st.session_state.healing_complete and st.session_state.healed_df is not None:
                    st.success("🎉 Dataset Successfully Restored & Cleaned!")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("##### 🤖 Executed Production Script Patch")
                        st.code(st.session_state.patch_code, language="python")
                    with col2:
                        st.markdown("##### 📥 Downstream Cleaned Dataset")
                        st.dataframe(st.session_state.healed_df.head(10), use_container_width=True)
                    
                    csv_buffer = io.StringIO()
                    st.session_state.healed_df.to_csv(csv_buffer, index=False)
                    st.download_button(
                        label="📥 Download Cleaned CSV File",
                        data=csv_buffer.getvalue().encode('utf-8'),
                        file_name="cleaned_domain_data.csv",
                        mime="text/csv"
                    )
else:
    st.info("ℹ️ Upload a document data source to spin up the pipeline.")
