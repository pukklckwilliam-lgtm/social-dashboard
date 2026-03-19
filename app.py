# 🎯 Social Media Dashboard - Correct Auth
import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Social Dashboard", layout="wide")

# Sidebar
st.sidebar.header("Settings")
api_key = st.sidebar.text_input("API Key", type="password", help="Your TikHub API Key")

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
        # Build URL
        base_url = "https://api.tikhub.io"
        endpoint = f"/api/v1/{platform}/app/v3/fetch_user_post_videos_v3"
        url = base_url + endpoint
        
        # Try multiple auth header formats
        auth_headers = [
            {"Authorization": api_key.strip()},
            {"api-token": api_key.strip()},
            {"X-Api-Token": api_key.strip()},
            {"X-API-Key": api_key.strip()},
            {"Authorization": f"Bearer {api_key.strip()}"}
        ]
        
        # Query parameters
        params = {
            "username": username.strip(),
            "count": 10
        }
        
        # Debug
        with st.expander("Debug Info"):
            st.write("URL:", url)
            st.write("Params:", params)
            st.write("Trying multiple auth methods...")
        
        success = False
        result = None
        
        for i, headers in enumerate(auth_headers):
            try:
                response = requests.get(url, params=params, headers=headers, timeout=30)
                
                if response.status_code == 200:
                    st.success(f"✅ Success! (Auth method #{i+1} worked)")
                    result = response.json()
                    success = True
                    
                    with st.expander("Auth Method Used"):
                        st.json(headers)
                    break
                elif response.status_code == 401:
                    st.warning(f"⚠️ Method #{i+1} failed (401)")
                else:
                    st.warning(f"⚠️ Method #{i+1} returned {response.status_code}")
                    
            except Exception as e:
                st.warning(f"⚠️ Method #{i+1} error: {e}")
        
        if success and result:
            st.json(result)
            
            # Display as table
            if 'data' in result:
                if isinstance(result['data'], list):
                    df = pd.DataFrame(result['data'])
                    st.dataframe(df)
                elif isinstance(result['data'], dict):
                    st.json(result['data'])
        elif not success:
            st.error("❌ All auth methods failed")
            st.info("Please check: 1) API Key is correct 2) Account has API access")
