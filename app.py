# 🎵 TikTok账号数据监控看板 - 调试版
import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import json

st.set_page_config(page_title="🎵 TikTok数据监控看板", layout="wide", page_icon="🎵")

# ============================================
# 🔑 API Key 管理
# ============================================
def get_api_key():
    if "tikhub_api_key" in st.secrets:
        return st.secrets["tikhub_api_key"]
    
    with st.sidebar:
        api_key = st.text_input("🔑 TikHub API Key", type="password", 
                               help="在 TikHub 后台获取")
        if api_key:
            st.session_state["api_key"] = api_key
            st.success("✅ API Key 已保存")
        elif "api_key" in st.session_state:
            api_key = st.session_state["api_key"]
            st.success("✅ API Key 已加载")
    
    return api_key if 'api_key' in locals() else None

# ============================================
# 📡 数据抓取（带详细错误信息）
# ============================================
def fetch_tiktok_data(api_key, username, count=10):
    url = "https://api.tikhub.io/api/v1/tiktok/app/v3/fetch_user_post_videos_v3"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    params = {
        "unique_id": username,
        "count": count
    }
    
    try:
        # 打印请求详情（用于调试）
        st.write(f"**请求 URL:** {url}")
        st.write(f"**请求参数:** {params}")
        st.write(f"**请求头:** Authorization: Bearer {api_key[:20]}...")
        
        response = requests.get(url, params=params, headers=headers, timeout=30)
        
        st.write(f"**HTTP 状态码:** {response.status_code}")
        st.write(f"**响应内容:** {response.text[:500]}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('code') == 200:
                return {"success": True, "data": result}
            else:
                return {"success": False, "error": result.get('message', 'API返回错误'), "raw": result}
        else:
            return {"success": False, "error": f"HTTP {response.status_code}", "raw": response.text}
    except Exception as e:
        return {"success": False, "error": f"请求异常：{str(e)}"}

# ============================================
# 🎨 主界面
# ============================================
def main():
    st.title("🎵 TikTok账号数据监控看板")
    st.markdown("*支持任意公开账号数据抓取*")
    
    # 获取 API Key
    api_key = get_api_key()
    
    if not api_key:
        st.warning("⚠️ **请先配置 API Key！**\n\n在左侧侧边栏输入你的 TikHub API Key")
        st.stop()
    
    # 侧边栏配置
    with st.sidebar:
        st.header("⚙️ 配置")
        username = st.text_input("TikTok 用户名", placeholder="photorevive.ai", value="photorevive.ai")
        count = st.slider("抓取数量", min_value=1, max_value=30, value=10)
        
        if st.button("🚀 获取数据", type="primary", use_container_width=True):
            st.session_state['fetch_data'] = True
    
    # 抓取数据
    if st.session_state.get('fetch_data', False):
        st.session_state['fetch_data'] = False
        
        if not username:
            st.error("❌ 请输入用户名")
            st.stop()
        
        with st.spinner(f'正在抓取 @{username} 的数据...'):
            result = fetch_tiktok_data(api_key, username, count)
            
            if not result['success']:
                st.error(f"❌ {result['error']}")
                
                # 显示详细错误信息
                if 'raw' in result:
                    with st.expander("🔍 查看原始响应（调试用）"):
                        st.write(result['raw'])
            else:
                st.success("✅ 数据获取成功！")
                
                # 解析数据
                data_content = result['data'].get('data', {})
                video_list = data_content.get('aweme_list', [])
                
                if not video_list:
                    st.warning("⚠️ 未找到视频数据")
                else:
                    st.write(f"✅ 成功获取 {len(video_list)} 个视频！")
                    
                    # 显示第一个视频的原始数据（用于调试）
                    with st.expander("🔍 查看第一个视频的原始数据结构"):
                        st.json(video_list[0])

if __name__ == "__main__":
    main()
