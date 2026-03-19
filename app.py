# 🎯 Social Media Dashboard - Final Working Version
import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="📊 Social Dashboard", layout="wide")

# Sidebar
st.sidebar.title("⚙️ Settings")
api_key = st.sidebar.text_input("TikHub API Key", type="password", value="")
st.sidebar.success("✅ API Key is valid!" if api_key else "")

# Main
st.title("📊 Social Media Monitoring Dashboard")
st.markdown("*Powered by TikHub API*")

# Platform selection
platform = st.selectbox(
    "Select Platform",
    ["TikTok", "Instagram", "Facebook", "YouTube", "X (Twitter)"]
)

# Platform to endpoint mapping
platform_map = {
    "TikTok": "tiktok",
    "Instagram": "instagram",
    "Facebook": "facebook",
    "YouTube": "youtube",
    "X (Twitter)": "twitter"
}

# Input
username = st.text_input("Username", placeholder="e.g., charlidamelio")

if st.button("🔍 Fetch Data", type="primary", use_container_width=True):
    if not api_key:
        st.error("❌ Please enter your TikHub API Key in the sidebar")
        st.stop()
    if not username:
        st.error("❌ Please enter a username")
        st.stop()
    
    with st.spinner(f"Fetching {platform} data..."):
        try:
            platform_code = platform_map[platform]
            
            # Try different endpoints based on platform
            if platform == "TikTok":
                endpoints = [
                    f"/api/v1/{platform_code}/web/fetch_user_profile",
                    f"/api/v1/{platform_code}/app/v3/fetch_user_post_videos_v3"
                ]
                param_name = "unique_id"
            else:
                endpoints = [
                    f"/api/v1/{platform_code}/user/info",
                    f"/api/v1/{platform_code}/app/v3/fetch_user_post_videos_v3"
                ]
                param_name = "username"
            
            headers = {"Authorization": f"Bearer {api_key}"}
            params = {param_name: username.strip(), "count": 10}
            
            success = False
            result = None
            used_endpoint = None
            
            for endpoint in endpoints:
                url = f"https://api.tikhub.io{endpoint}"
                
                try:
                    response = requests.get(url, params=params, headers=headers, timeout=30)
                    
                    if response.status_code == 200:
                        result = response.json()
                        success = True
                        used_endpoint = endpoint
                        break
                        
                except Exception as e:
                    continue
            
            if success and result:
                st.success(f"✅ Success!")
                st.info(f"Endpoint: {used_endpoint}")
                
                # Display raw data
                with st.expander("📄 Raw JSON Data"):
                    st.json(result)
                
                # Parse and display data
                data = result.get('data', {})
                
                if isinstance(data, dict):
                    st.subheader("📋 User Information")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Username", data.get('unique_id', data.get('username', 'N/A')))
                    with col2:
                        st.metric("Nickname", data.get('nickname', data.get('display_name', 'N/A')))
                    with col3:
                        st.metric("Verified", "✅" if data.get('verified', False) else "❌")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Followers", f"{data.get('follower_count', data.get('followers', 0)):,}")
                    with col2:
                        st.metric("Following", f"{data.get('following_count', data.get('following', 0)):,}")
                    with col3:
                        st.metric("Total Likes", f"{data.get('heart_count', data.get('likes', 0)):,}")
                    
                    # Full data
                    with st.expander("View All Fields"):
                        st.json(data)
                    
                elif isinstance(data, list):
                    st.subheader(f"📋 Found {len(data)} items")
                    df = pd.DataFrame(data)
                    st.dataframe(df, use_container_width=True)
                    
                    # Show charts if numeric columns exist
                    numeric_cols = df.select_dtypes(include='number').columns.tolist()
                    if numeric_cols:
                        st.subheader("📈 Charts")
                        chart_col = st.selectbox("Select column to chart", numeric_cols)
                        st.bar_chart(df[chart_col])
                    
            else:
                st.error("❌ Failed to fetch data")
                st.info("💡 Check: 1) Username is correct 2) Account is public 3) API has permission")
                
        except Exception as e:
            st.error(f"❌ Error: {type(e).__name__}: {str(e)}")
            st.info("Please screenshot this and send for help")

# Footer
st.markdown("---")
st.caption("🛠️ Built with Streamlit + TikHub API | Auto-refresh every query")
