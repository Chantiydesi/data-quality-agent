import streamlit as st
import pandas as pd
import json
import os
from openai import OpenAI
from pathlib import Path

# --- 1. Page Configuration ---
st.set_page_config(page_title="Data Quality Agent", layout="wide", initial_sidebar_state="expanded")

# --- 2. Sidebar Navigation & Team Info ---
with st.sidebar:
    # Navigation
    st.title("Dashboard")
    menu = ["Dashboard", "Generate", "Settings"]
    choice = st.radio("", menu)
    
    st.markdown("---")
    
    # Team Info Section (styled as cards)
    st.subheader("👥 Team 14")
    
    # Function to create team cards
    def team_card(name, roll):
        st.markdown(f"""
        <div style="background-color: #1e1e2e; padding: 10px; border-radius: 10px; border-left: 5px solid #3498db; margin-bottom: 10px;">
            <div style="font-weight: bold; color: white;">{name}</div>
            <div style="font-size: 0.8em; color: #b3b3b3;">Roll: {roll}</div>
        </div>
        """, unsafe_allow_html=True)

    team_card("Padala Kuladeep Satya Kishore", "23U41A0541 · CSE")
    team_card("Pentakota Charishma", "23U41A0544 · CSE")
    team_card("Madisa Thanu Sri", "24U45A0419 · ECE")
    team_card("Malla Hemanjali", "23U41A4236 · CSM")

# --- 3. Main Content Area ---
st.title("Mock Data Generator")
st.subheader("Agent · Team 14 · DE-15")

# Integration of your API Gateway logic
def call_ai_api(prompt_text):
    api_key = st.secrets.get("OPENROUTER_API_KEY")
    if not api_key:
        st.error("❌ API Key missing!")
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

# Logic for Generate tab
if choice == "Generate":
    if st.button("Generate Mock Data"):
        result = call_ai_api("Generate a sample JSON for a financial transaction.")
        if result:
            st.json(result)
