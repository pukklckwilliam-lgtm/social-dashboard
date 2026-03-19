# 🎯 Social Media Dashboard - GET Method
import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Social Dashboard", layout="wide")

# Sidebar
st.sidebar.header("Settings")
api_key = st.sidebar.text_input("API Key", type="password")
auth_method = st.sidebar.selectbox("Auth Method", ["X-API-Key", "Bearer", "Authorization"])

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
        # Build URL with query parameters (GET method)
        url = f"https://api.tikhub.io/api/v1/{platform}/app/v3/fetch_user_post_videos_v3"
        
        # Headers
        if auth_method == "X-API-Key":
            headers = {"X-API-Key": api_key.strip()}
        elif auth_method == "Bearer":
            headers = {"Authorization": f"Bearer {api_key.strip()}"}
        else:
            headers = {"Authorization": api_key.strip()}
        
        # Query parameters (for GET request)
        params = {
            "username": username.strip(),
            "count": 10
        }
        
        # Debug
        with st.expander("Debug Info"):
            st.write("URL:", url)
            st.write("Method: GET")
            st.write("Params:", params)
            st.write("Auth:", auth_method)
        
        try:
            # GET request instead of POST
            response = requests.get(url, params=params, headers=headers, timeout=30)
            
            st.write("### Response")
            st.write("Status:", response.status_code)
            
            if response.status_code == 200:
                st.success("✅ Success!")
                result = response.json()
                st.json(result)
                
                # Display as table
                if 'data' in result:
                    if isinstance(result['data'], list):
                        df = pd.DataFrame(result['data'])
                        st.dataframe(df)
                    elif isinstance(result['data'], dict):
                        st.json(result['data'])
            else:
                st.error(f"❌ Status {response.status_code}")
                st.text(response.text[:500])
                
        except Exception as e:
            st.error(f"❌ Error: {type(e).__name__}: {str(e)}")
