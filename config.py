import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()


def get_api_key() -> str:
    # Try Streamlit Cloud Secrets first
    try:
        api_key = st.secrets.get("API_KEY", "").strip()
    except Exception:
        api_key = ""

    # Fall back to local .env
    if not api_key:
        api_key = os.getenv("API_KEY", "").strip()

    if not api_key:
        raise ValueError(
            "API_KEY is missing. Configure it in .env or Streamlit Secrets."
        )

    if api_key == "gsk_your_real_key_here":
        raise ValueError("Please replace the placeholder with your real API key.")

    return api_key