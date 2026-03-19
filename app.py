# 🎯 Social Media Dashboard - Final Fix
import streamlit as st
import requests
import pandas as pd
import json

st.set_page_config(page_title="Social Dashboard", layout="wide")

# Sidebar
st.sidebar.header("Settings")
api_key = st.sidebar.text_input("API Key", type="password")

# Main
st.title("📊 Social Media Dashboard")

col1, col2 = st.columns(2)
with col1:
    platform = st.selectbox("Platform", ["tiktok", "instagram", "facebook", "youtube", "twitter"])
with col2:
    username = st.text_input("Username", "charlidamelio")

if st.button("Fetch Data", type="primary"):
    if not api_key:
        st.error("Please enter API Key")
        st.stop()
    
    with st.spinner("Fetching..."):
        try:
            # Build URL
            url = f"https://api.tikhub.io/api/v1/{platform}/app/v3/fetch_user_post_videos_v3"
            
            # Prepare headers - use raw string
            headers = {
                "Authorization": "Bearer " + str(api_key).strip(),
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0"
            }
            
            # Prepare body - ensure ASCII
            body = json.dumps({
                "username": str(username).strip(),
                "count": 10
            }, ensure_ascii=True)
            
            # Debug info
            with st.expander("Debug Info"):
                st.write("URL:", url)
                st.write("Method: POST")
                st.write("Body:", body)
            
            # Make request - use data instead of json parameter
            response = requests.post(
                url,
                data=body.encode('utf-8'),  # Explicitly encode as UTF-8
                headers=headers,
                timeout=30
            )
            
            # Show response
            st.write("Status Code:", response.status_code)
            
            if response.status_code == 200:
                st.success("Success!")
                result = response.json()
                st.json(result)
                
                # Try to display as table
                if 'data' in result and isinstance(result['data'], list):
                    df = pd.DataFrame(result['data'])
                    st.dataframe(df)
            else:
                st.error(f"Failed: {response.status_code}")
                st.text(response.text[:500])
                
        except Exception as e:
            st.error(f"Error: {type(e).__name__}: {str(e)}")
            st.info("Please screenshot this and send to me")
