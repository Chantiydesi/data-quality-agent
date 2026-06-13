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

# ============================================================
# 1. Environment & Project Initialization (Blueprint 1.1-1.4)
# ============================================================
current_dir = Path(__file__).resolve().parent if '__file__' in locals() else Path.cwd()
env_path = current_dir / '.env'
load_dotenv(dotenv_path=env_path)

st.set_page_config(
    page_title="Data Quality Agent with Auto-Fix Suggestions", 
    page_icon="🔮", 
    layout="wide"
)

# Secure API Key Loading (Blueprint 4.1 & 4.2)
def get_api_key():
    try:
        return st.secrets["GEMINI_API_KEY"]
    except (KeyError, FileNotFoundError):
        return os.getenv("GEMINI_API_KEY")

RAW_API_KEY = get_api_key()

# ============================================================
# 2. Global System Configuration (Blueprint 2.1-2.2)
# ============================================================
yaml_path = current_dir / 'rules.yaml'
if yaml_path.exists():
    with open(yaml_path, 'r') as file:
        VALIDATION_RULES = yaml.safe_load(file)
else:
    VALIDATION_RULES = {}

# Upstream HTTP JSON Payload Architecture (Blueprint 4.3)
def call_gemini_api(prompt_text):
    if not RAW_API_KEY or RAW_API_KEY.strip() == "":
        st.error("❌ Valid GEMINI_API_KEY is missing!")
        return None

    # URL without ?key= parameter to avoid 401 errors
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
    
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": RAW_API_KEY # Secure Header Auth
    }
    
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

# ============================================================
# 3. UI Architecture Development (Blueprint 3.1-3.6)
# ============================================================
with st.sidebar:
    st.markdown("## ⚙️ QA Agent Control")
    use_llm = st.toggle("Gemini Pro LLM Engine", value=True)
    st.markdown("---")
    st.markdown("### Team 11")
    # ... [Keep your team card CSS/HTML here] ...

st.title("Data Quality Agent: Deterministic YAML & LLM Engine")

# ============================================================
# 5. Pipeline Execution (Blueprint 5.1-5.6)
# ============================================================
uploaded_file = st.file_uploader("Upload your target CSV file", type=["csv"])

if uploaded_file is not None:
    if 'raw_df' not in st.session_state:
        st.session_state.raw_df = pd.read_csv(uploaded_file)
    
    df = st.session_state.raw_df
    tab1, tab2 = st.tabs(["📋 Inspector", "📊 Diagnostics & Remediation"])
    
    with tab1:
        st.dataframe(df.head(10), use_container_width=True)
    
    with tab2:
        if st.button("🔍 Run Diagnostic Audit"):
            # Contextual Prompt Assembly (YAML Schema + Data Samples)
            rules = VALIDATION_RULES.get("financial_transactions", {})
            audit_prompt = f"Audit this data: {df.head(10).to_json()}. Rules: {rules}."
            
            response = call_gemini_api(audit_prompt)
            st.session_state.audit_report = json.loads(response)
            st.rerun()

        # 6. Real-Time Auto-Fix Execution Sandboxing (Blueprint 6.1-6.3)
        if st.session_state.get("audit_report"):
            # ... [Insert your auto-fix remediation logic here] ...
            if st.button("🚀 Execute Code Patch Repair Pipeline"):
                # Sandboxed exec() logic
                pass

# 7. Downstream Output Delivery (Blueprint 7.1-7.3)
# ... [Keep your CSV buffer and download button logic here] ...
