# 🎯 多产品社媒监控系统 - 调试版（显示请求详情）
import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import json

st.set_page_config(page_title="🔍 TikTok 调试工具", layout="wide")

# ============================================
# 🔑 API Key 管理
# ============================================
def get_api_key():
    try:
        if hasattr(st, 'secrets') and "tikhub_api_key" in st.secrets:
            key = st.secrets["tikhub_api_key"]
            if key and isinstance(key, str) and key.strip():
                return key.strip()
    except:
        pass
    
    with st.sidebar:
        api_key = st.text_input("🔑 TikHub API Key", type="password", placeholder="vpA5...")
        if api_key and api_key.strip():
            api_key = api_key.strip()
            st.session_state["api_key"] = api_key
            return api_key
        elif "api_key" in st.session_state:
            return st.session_state["api_key"]
    return None

# ============================================
# 📡 调试版数据获取函数
# ============================================
def fetch_with_debug(api_key, username, endpoint, param_name, method="GET"):
    """带详细调试信息的请求函数"""
    
    url = f"https://api.tikhub.io{endpoint}"
    
    # 清理参数值
    clean_username = username.strip().lstrip('@')
    
    # 尝试两种参数格式
    test_configs = [
        {
            "name": "方式1: GET + Query Params",
            "method": "GET",
            "url": url,
            "params": {param_name: clean_username, "count": 10},
            "json": None,
            "headers": {"Authorization": f"Bearer {api_key}"}
        },
        {
            "name": "方式2: POST + JSON Body",
            "method": "POST", 
            "url": url,
            "params": None,
            "json": {param_name: clean_username, "count": 10},
            "headers": {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        },
        {
            "name": "方式3: POST + 额外参数",
            "method": "POST",
            "url": url,
            "params": None,
            "json": {
                param_name: clean_username,
                "count": 10,
                "cursor": 0,
                "region": "US"
            },
            "headers": {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        }
    ]
    
    results = []
    
    for config in test_configs:
        with st.expander(f"📡 {config['name']}", expanded=False):
            st.write(f"**URL:** `{config['url']}`")
            st.write(f"**方法:** {config['method']}")
            st.write(f"**参数:** {config['params'] or config['json']}")
            
            if st.button(f"🚀 测试 {config['name']}", key=f"btn_{config['name']}"):
                try:
                    if config['method'] == "GET":
                        response = requests.get(
                            config['url'],
                            params=config['params'],
                            headers=config['headers'],
                            timeout=30
                        )
                    else:
                        response = requests.post(
                            config['url'],
                            json=config['json'],
                            headers=config['headers'],
                            timeout=30
                        )
                    
                    st.write(f"✅ **状态码:** {response.status_code}")
                    
                    if response.status_code == 200:
                        result = response.json()
                        st.success("🎉 请求成功！")
                        st.json(result)
                        
                        # 自动解析视频数据
                        if 'data' in result and 'aweme_list' in result['data']:
                            videos = result['data']['aweme_list']
                            st.write(f"📹 找到 {len(videos)} 个视频！")
                            return {"success": True, "data": result}
                    
                    else:
                        st.error(f"❌ HTTP {response.status_code}")
                        st.code(response.text[:500])
                    
                    results.append({
                        "name": config['name'],
                        "status": response.status_code,
                        "response": response.text[:200]
                    })
                    
                except Exception as e:
                    st.error(f"❌ 异常: {e}")
                    results.append({"name": config['name'], "error": str(e)})
    
    return {"success": False, "error": "所有方式都失败", "details": results}

# ============================================
# 🎨 主界面
# ============================================
st.title("🔍 TikTok API 调试工具")
st.markdown("*测试不同请求方式，找到正确的参数格式*")

api_key = get_api_key()

if not api_key:
    st.warning("⚠️ 请先在侧边栏输入 API Key")
    st.stop()

st.success(f"✅ API Key 已加载: `{api_key[:20]}...{api_key[-10:]}`")

# 输入区域
col1, col2 = st.columns(2)
with col1:
    username = st.text_input("TikTok 用户名", value="photorevive.ai")
with col2:
    param_name = st.selectbox("参数名", ["unique_id", "username", "user_id"], index=0)

endpoint = st.text_input("API 端点", value="/api/v1/tiktok/app/v3/fetch_user_post_videos_v3")

st.info("""
💡 **调试建议：**
1. 先测试"方式1: GET + Query Params"
2. 如果 400，测试"方式2: POST + JSON Body"  
3. 如果还失败，测试"方式3: POST + 额外参数"
4. 把成功的配置截图发给我，我帮你固化到代码中
""")

# 执行测试
if st.button("🔬 开始调试测试", type="primary"):
    with st.spinner("正在测试所有请求方式..."):
        result = fetch_with_debug(api_key, username, endpoint, param_name)
        
        if result.get("success"):
            st.success("🎉 找到正确的方式了！")
        else:
            st.warning("⚠️ 所有方式都失败，请截图发给我")
            st.write("测试结果汇总：")
            for r in result.get("details", []):
                st.write(f"- {r['name']}: {r.get('status', r.get('error'))}")

# 官方文档链接
st.divider()
st.markdown("""
📚 **参考文档：**
- [TikHub API Docs](https://docs.tikhub.io/)
- [API Token 介绍](https://docs.tikhub.io/4579297m0)
- [Discord 支持](https://discord.gg/aMEAS8Xsvz)
""")
