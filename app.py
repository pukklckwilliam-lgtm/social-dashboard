# 🎯 多产品社媒监控系统 - 完整版
import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import json

# ============================================
# 📦 产品配置（你可以在这里添加更多产品）
# ============================================
PRODUCTS_CONFIG = {
    "PhotoRevive.AI": {
        "image": "https://p16-common-sign.tiktokcdn-us.com/tos-useast8-avt-0068-tx2/a62a32b54c026de51797e4862fd4ecd2~tplv-tiktokx-cropcenter:300:300.webp",
        "description": "AI 照片修复工具",
        "accounts": {
            "TikTok": {
                "username": "photorevive.ai",
                "api_endpoint": "/api/v1/tiktok/app/v3/fetch_user_post_videos_v3",
                "param_name": "unique_id"
            },
            "Instagram": {
                "username": "photorevive.ai",
                "api_endpoint": "/api/v1/instagram/v3/get_user_profile",
                "param_name": "user_id"
            },
            "YouTube": {
                "username": "@PhotoReviveAI",
                "api_endpoint": "/api/v1/youtube/web/get_channel_videos_v2",
                "param_name": "channel_id"
            },
            "X (Twitter)": {
                "username": "photorevive_ai",
                "api_endpoint": "/api/v1/twitter/web/fetch_user_profile",
                "param_name": "username"
            }
        }
    },
    "产品 2（示例）": {
        "image": "https://via.placeholder.com/300",
        "description": "第二个产品",
        "accounts": {
            "TikTok": {
                "username": "charlidamelio",
                "api_endpoint": "/api/v1/tiktok/app/v3/fetch_user_post_videos_v3",
                "param_name": "unique_id"
            }
        }
    }
}

# ============================================
# 🔑 API Key 管理
# ============================================
def get_api_key():
    if "tikhub_api_key" in st.secrets:
        return st.secrets["tikhub_api_key"]
    
    with st.sidebar:
        api_key = st.text_input("TikHub API Key", type="password")
        if api_key:
            st.session_state["api_key"] = api_key
    
    return st.session_state.get("api_key", None)

# ============================================
# 📡 数据获取函数
# ============================================
def fetch_account_data(api_key, platform, username, endpoint, param_name):
    """获取账号数据"""
    url = f"https://api.tikhub.io{endpoint}"
    headers = {"Authorization": f"Bearer {api_key}"}
    params = {param_name: username, "count": 10}
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()
        return {"error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}

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
    
    # 产品卡片网格
    cols = st.columns(min(3, len(PRODUCTS_CONFIG)))
    
    for idx, (product_name, config) in enumerate(PRODUCTS_CONFIG.items()):
        with cols[idx % 3]:
            with st.container(border=True):
                # 产品图片
                st.image(config["image"], use_container_width=True)
                
                # 产品名称
                st.subheader(product_name)
                
                # 产品描述
                st.caption(config["description"])
                
                # 账号数量
                st.metric("平台数量", len(config["accounts"]))
                
                # 进入按钮
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
    
    # 返回按钮
    if st.button("← 返回首页"):
        st.session_state.current_page = "home"
        st.session_state.selected_product = None
        st.rerun()
    
    st.title(f"📱 {product_name}")
    st.markdown(f"*{config['description']}*")
    
    # 平台选择器
    platforms = list(config["accounts"].keys())
    selected_platform = st.selectbox("选择平台", platforms)
    
    if selected_platform:
        st.session_state.selected_platform = selected_platform
        account_config = config["accounts"][selected_platform]
        
        # 获取数据
        api_key = get_api_key()
        if api_key:
            with st.spinner(f'正在获取 {selected_platform} 数据...'):
                data = fetch_account_data(
                    api_key,
                    selected_platform,
                    account_config["username"],
                    account_config["api_endpoint"],
                    account_config["param_name"]
                )
                
                if "error" in data:
                    st.error(f"获取数据失败：{data['error']}")
                else:
                    # 显示账号信息
                    st.subheader(f"@{account_config['username']}")
                    
                    # 解析数据（根据不同平台调整）
                    if selected_platform == "TikTok":
                        display_tiktok_data(data, account_config["username"])
                    else:
                        st.json(data)  # 临时显示原始数据
                    
                    # 主页链接
                    st.markdown(f"**[访问 {selected_platform} 主页](https://{selected_platform.lower().replace(' ', '')}.com/{account_config['username']})**")
        else:
            st.warning("请先在侧边栏输入 API Key")

# ============================================
# 📊 TikTok 数据展示
# ============================================
def display_tiktok_data(data, username):
    """展示 TikTok 账号数据"""
    aweme_list = data.get("data", {}).get("aweme_list", [])
    
    if not aweme_list:
        st.warning("未找到视频数据")
        return
    
    # 核心指标
    total_stats = {"play": 0, "like": 0, "comment": 0, "share": 0}
    
    for video in aweme_list:
        stats = video.get("statistics", {})
        total_stats["play"] += stats.get("play_count", 0)
        total_stats["like"] += stats.get("digg_count", 0)
        total_stats["comment"] += stats.get("comment_count", 0)
        total_stats["share"] += stats.get("share_count", 0)
    
    # 指标卡片
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
    
    # 视频封面墙
    st.subheader("📹 最新视频")
    video_cols = st.columns(3)
    
    for idx, video in enumerate(aweme_list[:6]):
        with video_cols[idx % 3]:
            # 视频封面
            cover_url = video.get("video", {}).get("cover", {}).get("url_list", [""])[0]
            if cover_url:
                st.image(cover_url, use_container_width=True)
            
            # 视频描述
            desc = video.get("desc", "无描述")[:50] + "..."
            st.caption(desc)
            
            # 跳转链接
            share_url = video.get("share_url", "")
            if share_url:
                st.markdown(f"[观看视频]({share_url})")
            
            # 统计数据
            stats = video.get("statistics", {})
            st.write(f"👁 {stats.get('play_count', 0):,} | ❤ {stats.get('digg_count', 0):,}")

# ============================================
# 🚀 主程序
# ============================================
def main():
    api_key = get_api_key()
    
    if not api_key and st.session_state.current_page != "home":
        st.warning("⚠️ 请先在侧边栏输入 API Key")
    
    # 页面路由
    if st.session_state.current_page == "home":
        render_home_page()
    elif st.session_state.current_page == "product":
        render_product_page()

if __name__ == "__main__":
    main()

# ============================================
# 页脚
# ============================================
st.markdown("---")
st.caption("🛠️ powered by TikHub API & Streamlit")
