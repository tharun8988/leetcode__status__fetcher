import streamlit as st
import requests
import os

st.title("LeetCode Stats Viewer")

uploaded_file = st.file_uploader("Upload Excel with LeetCode profile links", type=["xlsx", "xls"])

# Get the correct backend URL
backend_url = os.getenv("BACKEND_URL", "http://localhost:8000/upload-excel/")

if uploaded_file:
    files = {"file": (uploaded_file.name, uploaded_file, "application/vnd.ms-excel")}
    
    try:
        response = requests.post(backend_url, files=files)
        if response.status_code == 200:
            results = response.json()
            st.json(results)
            st.download_button(
                label="Download JSON results",
                data=response.content,
                file_name="leetcode_stats.json",
                mime="application/json"
            )
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
    except Exception as e:
        st.error(f"Failed to call API: {e}")
