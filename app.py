# 🎯 社媒数据监控看板 - 编码修复版
import streamlit as st
import requests
import pandas as pd
import urllib.parse

st.set_page_config(page_title="Social Media Dashboard", layout="wide", page_icon="📈")

# 侧边栏配置
st.sidebar.header("Settings")
api_key = st.sidebar.text_input("TikHub API Key", type="password")
test_mode = st.sidebar.checkbox("Debug Mode", value=True)

# 主界面
st.title("📊 Social Media Dashboard")
st.markdown("*Support: TikTok, Instagram, Facebook, YouTube, X*")

# 平台映射（英文，避免编码问题）
platform_map = {
    "TikTok": "tiktok",
    "Instagram": "instagram", 
    "Facebook": "facebook",
    "YouTube": "youtube",
    "X (Twitter)": "twitter"
}

# 输入区域
col1, col2, col3 = st.columns(3)
with col1:
    platform_display = st.selectbox("Platform", list(platform_map.keys()))
    platform = platform_map[platform_display]
with col2:
    account_id = st.text_input("Username", placeholder="e.g., charlidamelio")
with col3:
    data_type = st.selectbox("Data Type", ["User Info", "Videos", "Comments"])

# 获取数据按钮
if st.button("🔍 Fetch Data", type="primary", use_container_width=True):
    if not api_key:
        st.error("❌ Please enter API Key in sidebar")
        st.stop()
    if not account_id:
        st.error("❌ Please enter username")
        st.stop()
    
    with st.spinner(f"Fetching {platform} data..."):
        try:
            # 构建 URL（确保 ASCII 编码）
            base_url = "https://api.tikhub.io"
            endpoint = f"/api/v1/{platform}/app/v3/fetch_user_post_videos_v3"
            url = base_url + endpoint
            
            # 构建请求头（纯 ASCII）
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            # 构建请求参数（确保 ASCII）
            payload = {
                "username": str(account_id),
                "count": 10
            }
            
            # 显示调试信息
            if test_mode:
                with st.expander("🔍 Debug Info"):
                    st.write("**URL:**")
                    st.code(url)
                    st.write("**Headers:**")
                    st.json({"Authorization": "Bearer ***", "Content-Type": "application/json"})
                    st.write("**Payload:**")
                    st.json(payload)
            
            # 发送请求（使用纯 ASCII）
            response = requests.post(
                url.encode('ascii'),
                json=payload,
                headers=headers,
                timeout=30
            )
            
            # 检查响应
            if response.status_code == 200:
                result = response.json()
                st.success(f"✅ Successfully fetched data for {account_id}!")
                
                # 显示原始数据
                if test_mode:
                    with st.expander("📄 Raw JSON Response"):
                        st.json(result)
                
                # 解析数据
                data_list = []
                if isinstance(result, dict):
                    for key in ['data', 'results', 'videos', 'items', 'list']:
                        if key in result and isinstance(result[key], list):
                            data_list = result[key]
                            break
                    if not data_list and 'data' in result and isinstance(result['data'], dict):
                        data_list = [result['data']]
                
                if data_list:
                    df = pd.DataFrame(data_list)
                    st.subheader("📋 Data Preview")
                    st.dataframe(df, use_container_width=True)
                    
                    # 图表
                    numeric_cols = df.select_dtypes(include='number').columns.tolist()
                    if numeric_cols:
                        st.subheader("📈 Visualization")
                        x_col = st.selectbox("X Axis", df.columns.tolist())
                        y_col = st.selectbox("Y Axis", numeric_cols)
                        st.bar_chart(df.set_index(x_col)[y_col])
                else:
                    st.warning("⚠️ Data format is unusual, check raw JSON above")
            else:
                st.error(f"❌ Request failed with status {response.status_code}")
                with st.expander("📄 Response Details"):
                    st.text(response.text[:1000])
                    
        except UnicodeEncodeError as e:
            st.error(f"❌ Encoding error: {str(e)}")
            st.info("💡 This usually means the username contains special characters. Try using a simple username.")
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            st.info("💡 Screenshot the error and send it to me for help")

st.markdown("---")
st.caption("🛠️ Powered by AI Assistant | Feedback welcome")
