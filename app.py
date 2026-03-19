import streamlit as st
import requests

st.set_page_config(layout="wide")
st.title("🔍 TikHub API 诊断工具")

api_key = st.text_input("API Key", type="password")

if not api_key:
    st.warning("请输入 API Key")
    st.stop()

# 测试1：检查账户状态
st.subheader("1️⃣ 检查账户状态")
if st.button("💰 检查余额"):
    url = "https://api.tikhub.io/api/v1/user/credits"
    headers = {"Authorization": f"Bearer {api_key}"}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        st.write(f"状态码：{response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            st.success("✅ API Key 有效！")
            st.json(data)
            
            # 检查余额
            credits = data.get('credits', data.get('balance', 0))
            if credits <= 0:
                st.error("❌ 余额为0！需要充值")
            else:
                st.info(f"💵 当前余额：${credits}")
        else:
            st.error(f"❌ {response.status_code}")
            st.write(response.text)
    except Exception as e:
        st.error(f"错误：{e}")

# 测试2：尝试不同的API端点
st.subheader("2️⃣ 测试不同API端点")

endpoints = [
    "/api/v1/tiktok/app/v3/fetch_user_post_videos_v3",
    "/api/v1/tiktok/web/fetch_user_profile",
    "/api/v1/tiktok/app/v2/fetch_user_post_videos",
]

for endpoint in endpoints:
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write(f"`{endpoint}`")
    with col2:
        if st.button(f"测试", key=endpoint):
            url = f"https://api.tikhub.io{endpoint}"
            headers = {"Authorization": f"Bearer {api_key}"}
            params = {"unique_id": "photorevive.ai", "count": 1}
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            st.write(f"状态码：{response.status_code}")
            if response.status_code == 200:
                st.success("✅ 成功！")
            else:
                st.error(f"❌ {response.status_code}")

st.divider()
st.info("""
💡 **下一步：**
1. 如果余额检查失败 → 充值
2. 如果所有端点都401 → 联系TikHub客服
3. 如果某个端点成功 → 用那个端点
""")
