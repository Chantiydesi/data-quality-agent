import streamlit as st
import pandas as pd
import json
import yaml
import os
from pathlib import Path
from dotenv import load_dotenv
from google import genai

# ----------------------------------------------------
# CONFIG
# ----------------------------------------------------
st.set_page_config(
    page_title="DQ-Agent Pipeline",
    layout="wide"
)

# ----------------------------------------------------
# LOAD ENV
# ----------------------------------------------------
current_dir = Path(__file__).resolve().parent

env_file = current_dir / ".env"

if env_file.exists():
    load_dotenv(env_file)

# ----------------------------------------------------
# API KEY
# ----------------------------------------------------
def get_api_key():
    try:
        if "GEMINI_API_KEY" in st.secrets:
            return st.secrets["GEMINI_API_KEY"]
    except:
        pass

    return os.getenv("GEMINI_API_KEY")

API_KEY = get_api_key()

client = None

if API_KEY:
    try:
        client = genai.Client(api_key=API_KEY)
    except Exception as e:
        st.error(f"Gemini Client Error: {e}")
else:
    st.error("GEMINI_API_KEY not found")

# ----------------------------------------------------
# LOAD YAML RULES
# ----------------------------------------------------
yaml_path = current_dir / "rules.yaml"

if yaml_path.exists():
    with open(yaml_path, "r", encoding="utf-8") as f:
        VALIDATION_RULES = yaml.safe_load(f)
else:
    VALIDATION_RULES = {}

# ----------------------------------------------------
# GEMINI CALL
# ----------------------------------------------------
def call_gemini(prompt):

    if client is None:
        return None

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        return response.text

    except Exception as e:
        st.error(f"Gemini Error: {e}")
        return None

# ----------------------------------------------------
# SIDEBAR
# ----------------------------------------------------
with st.sidebar:

    st.title("⚙️ DQ-Agent Control")

    use_llm = st.toggle(
        "Activate AI Engine",
        value=True
    )

    st.markdown("---")

    st.subheader("Team 11")

    st.markdown("**YDESI CHANTI BABU** (23U41A0560)")
    st.markdown("**PRAGADA HARIKA** (23U41A0547)")
    st.markdown("**NANEPALLI DEEPIKA** (23U41A4430)")
    st.markdown("**Jyothula Bhargavi** (23U41A0428)")

    st.markdown("---")

    if API_KEY:
        st.success("Gemini Connected")
        st.caption(API_KEY[:8] + "...")
    else:
        st.error("No API Key")

# ----------------------------------------------------
# TITLE
# ----------------------------------------------------
st.title("📊 Data Quality Agent")
st.markdown("Deterministic YAML + Gemini Engine")

# ----------------------------------------------------
# FILE UPLOAD
# ----------------------------------------------------
uploaded_file = st.file_uploader(
    "Upload CSV",
    type=["csv"]
)

if uploaded_file:

    if "raw_df" not in st.session_state:
        st.session_state.raw_df = pd.read_csv(uploaded_file)

    df = st.session_state.raw_df

    tab1, tab2 = st.tabs(
        [
            "📋 Inspector",
            "📊 Diagnostics"
        ]
    )

    # ------------------------------------------------
    # TAB 1
    # ------------------------------------------------
    with tab1:

        st.dataframe(
            df.head(10),
            use_container_width=True
        )

        st.write("Rows:", len(df))
        st.write("Columns:", len(df.columns))

    # ------------------------------------------------
    # TAB 2
    # ------------------------------------------------
    with tab2:

        if st.button("🔍 Run Audit"):

            rules = VALIDATION_RULES.get(
                "financial_transactions",
                {}
            )

            sample = df.head(10).to_dict(
                orient="records"
            )

            prompt = f"""
You are a Data Quality Auditor.

Dataset:
{json.dumps(sample)}

Rules:
{json.dumps(rules)}

Return ONLY valid JSON.

Example:

{{
  "anomalies":[
    {{
      "column":"amount",
      "detected_issue":"negative values"
    }}
  ]
}}
"""

            with st.spinner("Auditing..."):

                result = call_gemini(prompt)

                if result:

                    try:

                        report = json.loads(result)

                        st.session_state.audit_report = report

                        st.success(
                            "Audit completed"
                        )

                    except Exception:

                        st.error(
                            "Invalid JSON returned"
                        )

                        st.code(result)

        # --------------------------------------------
        # SHOW REPORT
        # --------------------------------------------
        if "audit_report" in st.session_state:

            report = st.session_state.audit_report

            anomalies = report.get(
                "anomalies",
                []
            )

            if not anomalies:

                st.success(
                    "No anomalies detected"
                )

            for i, anomaly in enumerate(anomalies):

                col = anomaly.get(
                    "column",
                    "Unknown"
                )

                issue = anomaly.get(
                    "detected_issue",
                    "Unknown"
                )

                st.warning(
                    f"{col}: {issue}"
                )

                if st.button(
                    f"Fix {col}",
                    key=f"fix_{i}"
                ):

                    healed = df.copy()

                    st.session_state.healed_df = healed

                    st.success(
                        f"Patched {col}"
                    )

# ----------------------------------------------------
# DOWNLOAD
# ----------------------------------------------------
if "healed_df" in st.session_state:

    csv_data = st.session_state.healed_df.to_csv(
        index=False
    )

    st.download_button(
        "📥 Download Cleaned CSV",
        csv_data,
        "cleaned.csv",
        "text/csv"
    )
