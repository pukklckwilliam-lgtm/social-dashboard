# 🎵 TikTok数据监控 - 多方式尝试版
import streamlit as st
import requests

st.set_page_config(layout="wide")

st.title("🎵 TikTok数据监控 - API调试")

# API Key
with st.sidebar:
    api_key = st.text_input("TikHub API Key", type="password", value="vpA5E99O82r1tnSpPrLO...")  # 替换你的Key

if not api_key:
    st.warning("请输入 API Key")
    st.stop()

username = st.text_input("用户名", value="photorevive.ai")

st.write(f"**测试账号:** @{username}")

# 尝试不同的请求方式
st.subheader("🔧 尝试不同的API调用方式")

methods = [
    {
        "name": "方式1: GET + Query Params",
        "method": "GET",
        "url": "https://api.tikhub.io/api/v1/tiktok/app/v3/fetch_user_post_videos_v3",
        "params": {"unique_id": username, "count": 10},
        "json": None
    },
    {
        "name": "方式2: POST + JSON Body",
        "method": "POST",
        "url": "https://api.tikhub.io/api/v1/tiktok/app/v3/fetch_user_post_videos_v3",
        "params": None,
        "json": {"unique_id": username, "count": 10}
    },
    {
        "name": "方式3: GET + 不同端点",
        "method": "GET",
        "url": "https://api.tikhub.io/api/v1/tiktok/web/fetch_user_profile",
        "params": {"unique_id": username},
        "json": None
    }
]

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

for i, test in enumerate(methods, 1):
    with st.expander(f"📡 {test['name']}", expanded=(i==1)):
        st.write(f"**URL:** `{test['url']}`")
        st.write(f"**方法:** {test['method']}")
        st.write(f"**参数:** {test['params'] or test['json']}")
        
        if st.button(f"🚀 测试 {test['name']}", key=f"test_{i}"):
            try:
                if test['method'] == "GET":
                    response = requests.get(
                        test['url'],
                        params=test['params'],
                        headers=headers,
                        timeout=30
                    )
                else:
                    response = requests.post(
                        test['url'],
                        json=test['json'],
                        headers=headers,
                        timeout=30
                    )
                
                st.write(f"**状态码:** {response.status_code}")
                
                if response.status_code == 200:
                    st.success("✅ 请求成功！")
                    st.json(response.json())
                else:
                    st.error(f"❌ HTTP {response.status_code}")
                    st.write(response.text[:500])
                    
            except Exception as e:
                st.error(f"❌ 请求异常: {str(e)}")

# 显示API文档链接
st.divider()
st.info("""
📚 **建议检查：**
1. TikHub API 文档：https://api.tikhub.io/
2. 确认 API Key 是否有效
3. 确认账号是否存在且公开
4. 检查账户余额是否充足
""")
