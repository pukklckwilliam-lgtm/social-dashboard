# 🎯 Social Media Dashboard - Correct Params
import streamlit as st
import requests
import json
from datetime import datetime

st.set_page_config(page_title="📊 Social Dashboard", layout="wide")

st.sidebar.title("⚙️ Settings")
api_key = st.sidebar.text_input("TikHub API Key", type="password")

st.title("📊 Social Media Data Downloader")

platform = st.selectbox("Platform", ["TikTok", "Instagram", "Facebook", "YouTube", "X"])
username = st.text_input("Username", "charlidamelio")

if st.button("📥 Download Data", type="primary"):
    if not api_key:
        st.error("Please enter API Key")
        st.stop()
    
    with st.spinner("Fetching..."):
        try:
            platform_code = platform.lower()
            if platform_code == "x":
                platform_code = "twitter"
            
            # Try different endpoints
            endpoints_to_try = [
                {
                    "url": f"https://api.tikhub.io/api/v1/{platform_code}/web/fetch_user_profile",
                    "params": {"unique_id": username} if platform == "TikTok" else {"username": username},
                    "name": "User Profile"
                },
                {
                    "url": f"https://api.tikhub.io/api/v1/{platform_code}/user/info",
                    "params": {"username": username},
                    "name": "User Info"
                },
                {
                    "url": f"https://api.tikhub.io/api/v1/{platform_code}/app/v3/fetch_user_post_videos_v3",
                    "params": {"unique_id": username, "count": 10} if platform == "TikTok" else {"username": username, "count": 10},
                    "name": "Videos V3"
                }
            ]
            
            headers = {"Authorization": f"Bearer {api_key}"}
            
            for endpoint in endpoints_to_try:
                st.write(f"Trying: {endpoint['name']}...")
                
                try:
                    response = requests.get(
                        endpoint['url'],
                        params=endpoint['params'],
                        headers=headers,
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        st.success(f"✅ Success with {endpoint['name']}!")
                        
                        # Download
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"{platform_code}_{username}_{timestamp}.json"
                        json_str = json.dumps(result, indent=2, ensure_ascii=False)
                        
                        st.download_button(
                            label="📥 Download JSON",
                            data=json_str,
                            file_name=filename,
                            mime="application/json"
                        )
                        
                        st.write("Endpoint used:", endpoint['url'])
                        st.write("Params:", endpoint['params'])
                        st.write("Keys:", list(result.keys()))
                        break
                        
                    else:
                        st.warning(f"❌ {endpoint['name']} failed: {response.status_code}")
                        
                except Exception as e:
                    st.warning(f"⚠️ {endpoint['name']} error: {e}")
                    
        except Exception as e:
            st.error(f"❌ Error: {e}")
