# 🎯 多产品社媒监控系统 - 最终修复版
import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import json

# ============================================
# 📦 产品配置
# ============================================
PRODUCTS_CONFIG = {
    "PhotoRevive.AI": {
        "image": "https://p16-common-sign.tiktokcdn-us.com/tos-useast8-avt-0068-tx2/a62a32b54c026de51797e4862fd4ecd2~tplv-tiktokx-cropcenter:300:300.webp",
        "description": "AI 照片修复工具",
        "accounts": {
            "TikTok": {
                "username": "photorevive.ai",
                "api_endpoint": "/api/v1/tiktok/app/v3/fetch_user_post_videos_v3",
                "param_name": "unique_id",
                "method": "GET"
            },
            "Instagram": {
                "username": "123456789",
                "api_endpoint": "/api/v1/instagram/v3/get_user_profile",
                "param_name": "user_id",
                "method": "GET"
            }
        }
    }
}

# ============================================
# 🔑 API Key 管理（最终修复版）
# ============================================
def get_api_key():
    """安全获取 API Key"""
    
    # 尝试从 Secrets 读取
    try:
        if hasattr(st, 'secrets') and "tikhub_api_key" in st.secrets:
            key = st.secrets["tikhub_api_key"]
            if key and isinstance(key, str) and key.strip():
                return key.strip()
    except Exception:
        pass
    
    # 从侧边栏读取
    with st.sidebar:
        st.header("🔑 API 配置")
        api_key = st.text_input("TikHub API Key", type="password",
                               placeholder="vpA5E99O82r...",
                               help="在 TikHub 后台获取")
        
        if api_key and api_key.strip():
            api_key = api_key.strip()
            st.session_state["api_key"] = api_key
            st.sidebar.success("✅ 已保存")
            return api_key
        elif "api_key" in st.session_state and st.session_state["api_key"]:
            return st.session_state["api_key"]
    
    return None

# ============================================
# 📡 数据获取函数
# ============================================
def fetch_account_data(api_key, platform, username, endpoint, param_name, method="GET"):
    """获取账号数据"""
    
    # ✅ 关键检查
    if not api_key or api_key in ["None", "null", ""]:
        return {"success": False, "error": "API Key 无效"}
    
    # ✅ 修复 URL 拼接
    url = f"https://api.tikhub.io{endpoint}"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    params = {param_name: username, "count": 10}
    
    try:
        if method.upper() == "POST":
            response = requests.post(url, json=params, headers=headers, timeout=30)
        else:
            response = requests.get(url, params=params, headers=headers, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('code') == 200 or 'data' in result:
                return {"success": True, "data": result}
            else:
                return {"success": False, "error": result.get('message', 'API错误')}
        else:
            return {"success": False, "error": f"HTTP {response.status_code}", 
                    "details": response.text[:300]}
    except Exception as e:
        return {"success": False, "error": f"请求异常: {str(e)}"}

# ============================================
# 🎨 页面状态
# ============================================
if "current_page" not in st.session_state:
    st.session_state.current_page = "home"
if "selected_product" not in st.session_state:
    st.session_state.selected_product = None

# ============================================
# 🏠 首页
# ============================================
def render_home_page():
    st.title("📊 社媒产品监控系统")
    
    cols = st.columns(min(3, len(PRODUCTS_CONFIG)))
    for idx, (name, config) in enumerate(PRODUCTS_CONFIG.items()):
        with cols[idx % 3]:
            with st.container(border=True):
                st.image(config["image"], use_container_width=True)
                st.subheader(name)
                st.caption(config["description"])
                st.metric("平台数", len(config["accounts"]))
                
                if st.button("查看详情", key=f"view_{name}", use_container_width=True):
                    st.session_state.selected_product = name
                    st.session_state.current_page = "product"
                    st.rerun()

# ============================================
# 📱 产品详情页
# ============================================
def render_product_page():
    product_name = st.session_state.selected_product
    config = PRODUCTS_CONFIG[product_name]
    
    if st.button("← 返回首页"):
        st.session_state.current_page = "home"
        st.session_state.selected_product = None
        st.rerun()
    
    st.title(f"📱 {product_name}")
    
    platforms = list(config["accounts"].keys())
    selected_platform = st.selectbox("选择平台", platforms)
    
    if selected_platform:
        account_config = config["accounts"][selected_platform]
        
        api_key = get_api_key()
        
        # ✅ 关键：如果 API Key 无效，直接提示
        if not api_key:
            st.error("❌ 请先在侧边栏输入有效的 API Key")
            st.stop()
        
        username = st.text_input("用户名/ID", value=account_config["username"])
        
        if st.button("🚀 获取数据", type="primary"):
            with st.spinner(f'正在获取 {selected_platform} 数据...'):
                data = fetch_account_data(
                    api_key,
                    selected_platform,
                    username,
                    account_config["api_endpoint"],
                    account_config["param_name"],
                    account_config.get("method", "GET")
                )
                
                if not data.get("success"):
                    st.error(f"❌ {data.get('error')}")
                    if 'details' in data:
                        with st.expander("🔍 详细错误"):
                            st.code(data['details'])
                else:
                    st.success("✅ 成功！")
                    
                    if selected_platform == "TikTok":
                        display_tiktok_data(data["data"], username)
                    else:
                        with st.expander("📄 原始数据"):
                            st.json(data["data"])

# ============================================
# 📊 TikTok 展示
# ============================================
def display_tiktok_data(data, username):
    aweme_list = data.get("data", {}).get("aweme_list", [])
    
    if not aweme_list:
        st.warning("⚠️ 未找到视频")
        return
    
    total_stats = {"play": 0, "like": 0, "comment": 0, "share": 0}
    for video in aweme_list:
        stats = video.get("statistics", {})
        total_stats["play"] += stats.get("play_count", 0)
        total_stats["like"] += stats.get("digg_count", 0)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("总播放", f"{total_stats['play']:,}")
    with col2:
        st.metric("总点赞", f"{total_stats['like']:,}")
    
    st.divider()
    
    video_cols = st.columns(3)
    for idx, video in enumerate(aweme_list[:6]):
        with video_cols[idx % 3]:
            cover = video.get("video", {}).get("cover", {}).get("url_list", [""])[0]
            if cover:
                st.image(cover, use_container_width=True)
            desc = (video.get("desc", "")[:40] + "...") if video.get("desc") else "无描述"
            st.caption(desc)
            stats = video.get("statistics", {})
            st.write(f"👁 {stats.get('play_count', 0):,} | ❤ {stats.get('digg_count', 0):,}")

# ============================================
# 🚀 主程序
# ============================================
def main():
    api_key = get_api_key()
    
    # ✅ 全局检查
    if not api_key:
        st.warning("⚠️ 请先配置 API Key")
    
    if st.session_state.current_page == "home":
        render_home_page()
    elif st.session_state.current_page == "product":
        render_product_page()

if __name__ == "__main__":
    main()

st.markdown("---")
st.caption("🛠️ powered by TikHub API | 最终修复版")
