# 🎯 多产品社媒监控系统 - 修复版
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
                "method": "GET"  # ✅ 明确指定方法
            },
            "Instagram": {
                "username": "123456789",  # ⚠️ 需要替换为数字 ID
                "api_endpoint": "/api/v1/instagram/v3/get_user_profile",
                "param_name": "user_id",
                "method": "GET",
                "note": "需要 Instagram 权限 + 数字用户 ID"
            },
            "YouTube": {
                "username": "@PhotoReviveAI",
                "api_endpoint": "/api/v1/youtube/web/get_channel_videos_v2",
                "param_name": "channel_id",
                "method": "GET"
            },
            "X (Twitter)": {
                "username": "photorevive_ai",
                "api_endpoint": "/api/v1/twitter/web/fetch_user_profile",
                "param_name": "username",
                "method": "GET"
            }
        }
    }
}

# ============================================
# 🔑 API Key 管理（修复版）
# ============================================
def get_api_key():
    """安全获取 API Key"""
    # 尝试从 Secrets 读取（带异常处理）
    try:
        if "tikhub_api_key" in st.secrets:
            return st.secrets["tikhub_api_key"]
    except Exception:
        pass
    
    # 从侧边栏读取
    with st.sidebar:
        api_key = st.text_input("🔑 TikHub API Key", type="password",
                               help="在 TikHub 后台获取")
        if api_key:
            st.session_state["api_key"] = api_key
            st.sidebar.success("✅ 已保存")
        elif "api_key" in st.session_state:
            api_key = st.session_state["api_key"]
            st.sidebar.success("✅ 已加载")
    
    return api_key if 'api_key' in locals() else None

# ============================================
# 📡 数据获取函数（修复版）
# ============================================
def fetch_account_data(api_key, platform, username, endpoint, param_name, method="GET"):
    """获取账号数据 - 修复 URL 拼接 + 支持多方法"""
    
    # ✅ 修复：URL 拼接无空格
    url = f"https://api.tikhub.io{endpoint}"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    params = {param_name: username, "count": 10}
    
    try:
        # ✅ 支持 GET/POST 自适应
        if method.upper() == "POST":
            response = requests.post(url, json=params, headers=headers, timeout=30)
        else:
            response = requests.get(url, params=params, headers=headers, timeout=30)
        
        # 调试信息
        st.write(f"🔍 请求: {response.status_code} - {url[:80]}...")
        
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
# 🎨 页面状态管理
# ============================================
if "current_page" not in st.session_state:
    st.session_state.current_page = "home"
if "selected_product" not in st.session_state:
    st.session_state.selected_product = None
if "selected_platform" not in st.session_state:
    st.session_state.selected_platform = None

# ============================================
# 🏠 首页：产品总览
# ============================================
def render_home_page():
    st.title("📊 社媒产品监控系统")
    st.markdown("*查看所有产品的社媒数据概览*")
    
    cols = st.columns(min(3, len(PRODUCTS_CONFIG)))
    
    for idx, (product_name, config) in enumerate(PRODUCTS_CONFIG.items()):
        with cols[idx % 3]:
            with st.container(border=True):
                st.image(config["image"], use_container_width=True)
                st.subheader(product_name)
                st.caption(config["description"])
                st.metric("平台数量", len(config["accounts"]))
                
                if st.button("查看详情", key=f"view_{product_name}", use_container_width=True):
                    st.session_state.selected_product = product_name
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
    st.markdown(f"*{config['description']}*")
    
    platforms = list(config["accounts"].keys())
    selected_platform = st.selectbox("选择平台", platforms)
    
    if selected_platform:
        st.session_state.selected_platform = selected_platform
        account_config = config["accounts"][selected_platform]
        
        api_key = get_api_key()
        if api_key:
            with st.spinner(f'正在获取 {selected_platform} 数据...'):
                data = fetch_account_data(
                    api_key,
                    selected_platform,
                    account_config["username"],
                    account_config["api_endpoint"],
                    account_config["param_name"],
                    account_config.get("method", "GET")
                )
                
                if "error" in data or not data.get("success"):
                    st.error(f"❌ {data.get('error', '未知错误')}")
                    if 'details' in data:
                        with st.expander("🔍 查看详细错误"):
                            st.code(data['details'])
                    
                    # Instagram 特殊提示
                    if selected_platform == "Instagram":
                        st.info("""
                        **Instagram 403 常见原因：**
                        1. API Key 没有 Instagram 权限 → 在 TikHub 后台开通
                        2. 需要数字用户 ID → 用查询接口先获取 ID
                        3. 账号私密或不存在 → 确认账号公开
                        """)
                else:
                    st.success("✅ 数据获取成功！")
                    st.subheader(f"@{account_config['username']}")
                    
                    if selected_platform == "TikTok":
                        display_tiktok_data(data["data"], account_config["username"])
                    else:
                        with st.expander("📄 查看原始数据"):
                            st.json(data["data"])
                    
                    # 主页链接
                    platform_lower = selected_platform.lower().replace(' ', '')
                    st.markdown(f"**[访问 {selected_platform} 主页](https://{platform_lower}.com/{account_config['username']})**")
        else:
            st.warning("请先在侧边栏输入 API Key")

# ============================================
# 📊 TikTok 数据展示
# ============================================
def display_tiktok_data(data, username):
    aweme_list = data.get("data", {}).get("aweme_list", [])
    
    if not aweme_list:
        st.warning("⚠️ 未找到视频数据")
        return
    
    total_stats = {"play": 0, "like": 0, "comment": 0, "share": 0}
    
    for video in aweme_list:
        stats = video.get("statistics", {})
        total_stats["play"] += stats.get("play_count", 0)
        total_stats["like"] += stats.get("digg_count", 0)
        total_stats["comment"] += stats.get("comment_count", 0)
        total_stats["share"] += stats.get("share_count", 0)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("总播放量", f"{total_stats['play']:,}")
    with col2:
        st.metric("总点赞数", f"{total_stats['like']:,}")
    with col3:
        st.metric("总评论数", f"{total_stats['comment']:,}")
    with col4:
        st.metric("总分享数", f"{total_stats['share']:,}")
    
    st.divider()
    st.subheader("📹 最新视频")
    video_cols = st.columns(3)
    
    for idx, video in enumerate(aweme_list[:6]):
        with video_cols[idx % 3]:
            cover_url = video.get("video", {}).get("cover", {}).get("url_list", [""])[0]
            if cover_url:
                st.image(cover_url, use_container_width=True)
            
            desc = video.get("desc", "无描述")[:50] + "..."
            st.caption(desc)
            
            share_url = video.get("share_url", "")
            if share_url:
                st.markdown(f"[观看视频]({share_url})")
            
            stats = video.get("statistics", {})
            st.write(f"👁 {stats.get('play_count', 0):,} | ❤ {stats.get('digg_count', 0):,}")

# ============================================
# 🚀 主程序
# ============================================
def main():
    api_key = get_api_key()
    
    if not api_key and st.session_state.current_page != "home":
        st.warning("⚠️ 请先在侧边栏输入 API Key")
    
    if st.session_state.current_page == "home":
        render_home_page()
    elif st.session_state.current_page == "product":
        render_product_page()

if __name__ == "__main__":
    main()

st.markdown("---")
st.caption("🛠️ powered by TikHub API & Streamlit | 修复版")
