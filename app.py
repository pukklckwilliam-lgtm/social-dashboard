# 🎯 Social Media Dashboard - Download Version
import streamlit as st
import requests
import json
from datetime import datetime

st.set_page_config(page_title="📊 Social Dashboard", layout="wide")

# Sidebar
st.sidebar.title("⚙️ Settings")
api_key = st.sidebar.text_input("TikHub API Key", type="password")

# Main
st.title("📊 Social Media Data Downloader")
st.markdown("*Download full data and send to AI for analysis*")

platform = st.selectbox("Platform", ["TikTok", "Instagram", "Facebook", "YouTube", "X"])
username = st.text_input("Username", "photorevive.ai")

if st.button("📥 Download Data", type="primary"):
    if not api_key:
        st.error("Please enter API Key")
        st.stop()
    if not username:
        st.error("Please enter username")
        st.stop()
    
    with st.spinner("Fetching data from TikHub..."):
        try:
            platform_code = platform.lower()
            if platform_code == "x":
                platform_code = "twitter"
            
            url = f"https://api.tikhub.io/api/v1/{platform_code}/app/v3/fetch_user_post_videos_v3"
            headers = {"Authorization": f"Bearer {api_key}"}
            params = {"username": username, "count": 30}
            
            response = requests.get(url, params=params, headers=headers, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                
                # Generate filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{platform_code}_{username}_{timestamp}.json"
                
                # Pretty print JSON
                json_str = json.dumps(result, indent=2, ensure_ascii=False)
                
                # Download button
                st.download_button(
                    label="✅ Click to Download JSON File",
                    data=json_str,
                    file_name=filename,
                    mime="application/json"
                )
                
                st.success(f"✅ Data fetched successfully!")
                st.info(f"📁 File: {filename}")
                st.write("**Response size:**", len(json_str), "bytes")
                st.write("**Top-level keys:**", list(result.keys()))
                
                st.markdown("""
                ### 📤 Next Steps:
                1. Click the download button above
                2. Save the JSON file
                3. Send the file to AI assistant
                4. AI will analyze the structure and optimize the dashboard
                """)
                
            else:
                st.error(f"❌ Status {response.status_code}")
                st.text(response.text[:500])
                
        except Exception as e:
            st.error(f"❌ Error: {type(e).__name__}: {str(e)}")

# Footer
st.markdown("---")
st.caption("💡 After downloading, share the JSON file for dashboard optimization")
