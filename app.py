# 🎯 多产品社媒监控系统 - 带搜索下载版
import streamlit as st
import requests
import pandas as pd
import json
import os
from datetime import datetime

st.set_page_config(page_title="📊 社媒监控系统", layout="wide", page_icon="🎵")

# ============================================
# 🔑 API Key
# ============================================
API_KEY = "vpA5E99O82r1tnSpPrLOwkiJKgm9arlJ1AH7g2ulb9jmm12uGiejcCi/aA=="

def get_api_key():
    try:
        if hasattr(st, 'secrets') and "tikhub_api_key" in st.secrets:
            return st.secrets["tikhub_api_key"].strip()
    except:
        pass
    
    with st.sidebar:
        api_key = st.text_input("🔑 TikHub API Key", type="password", value=API_KEY)
        if api_key:
            st.session_state["api_key"] = api_key.strip()
    
    return st.session_state.get("api_key", API_KEY)

# ============================================
# 📡 TikTok 数据抓取
# ============================================
def fetch_tiktok_data(username, count=20):
    """抓取 TikTok 账号数据"""
    url = "https://api.tikhub.io/api/v1/tiktok/app/v3/fetch_user_post_videos_v2"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    params = {"unique_id": username, "count": count}
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)
        if response.status_code == 200:
            result = response.json()
            if result.get('code') == 200:
                return {"success": True, "data": result}
            else:
                return {"success": False, "error": result.get('message', 'API错误')}
        else:
            return {"success": False, "error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"success": False, "error": f"请求异常：{str(e)}"}

# ============================================
# 📊 数据解析
# ============================================
def parse_tiktok_videos(result):
    """解析 TikTok 视频数据"""
    if not result or not result.get('success'):
        return [], {}
    
    data_content = result['data'].get('data', {})
    video_list = data_content.get('aweme_list', [])
    
    # 账号信息
    account_info = {}
    if video_list and 'author' in video_list[0]:
        author = video_list[0]['author']
        account_info = {
            'username': author.get('unique_id', ''),
            'nickname': author.get('nickname', ''),
            'followers': author.get('follower_count', 0),
            'following': author.get('following_count', 0),
            'total_likes': author.get('total_favorited', 0)
        }
    
    # 视频数据
    rows = []
    for video in video_list:
        stats = video.get('statistics', {})
        create_time = video.get('create_time', 0)
        
        rows.append({
            '发布时间': datetime.fromtimestamp(create_time).strftime('%Y-%m-%d %H:%M') if create_time else '',
            '视频描述': (video.get('desc', '')[:100] + '...') if video.get('desc') else '无描述',
            '播放量': stats.get('play_count', 0),
            '点赞数': stats.get('digg_count', 0),
            '评论数': stats.get('comment_count', 0),
            '分享数': stats.get('share_count', 0),
            '视频链接': video.get('share_url', '')
        })
    
    return rows, account_info

# ============================================
# 💾 CSV 下载
# ============================================
def download_csv(df, filename):
    """生成 CSV 下载按钮"""
    csv = df.to_csv(index=False, encoding='utf-8-sig')
    return csv

# ============================================
# 🎨 页面状态管理
# ============================================
if "current_page" not in st.session_state:
    st.session_state.current_page = "home"
if "selected_product" not in st.session_state:
    st.session_state.selected_product = None
if "search_results" not in st.session_state:
    st.session_state.search_results = None
if "search_account_info" not in st.session_state:
    st.session_state.search_account_info = None

# ============================================
# 🏠 首页：搜索 + 产品总览
# ============================================
def render_home_page():
    st.title("📊 社媒监控系统")
    st.markdown("*TikTok 数据抓取 • 一键下载 CSV*")
    
    # ========== 搜索区域 ==========
    st.subheader("🔍 快速抓取 TikTok 数据")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        search_username = st.text_input(
            "TikTok 用户名",
            placeholder="例如：photorevive.ai",
            help="输入 TikTok 账号名（不需要 @ 符号）",
            key="search_username"
        )
    with col2:
        search_count = st.number_input(
            "抓取数量",
            min_value=1,
            max_value=30,
            value=20,
            key="search_count"
        )
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        search_btn = st.button("🔍 抓取数据", type="primary", use_container_width=True)
    with col2:
        if st.session_state.search_results is not None:
            if st.button("📥 下载 CSV", use_container_width=True):
                df = pd.DataFrame(st.session_state.search_results)
                csv = download_csv(df, f"tiktok_data_{datetime.now().strftime('%Y%m%d')}.csv")
                st.download_button(
                    label="⬇️ 点击下载",
                    data=csv,
                    file_name=f"tiktok_{st.session_state.search_account_info.get('username', 'data')}_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
    with col3:
        if st.session_state.search_results is not None:
            st.success(f"✅ {len(st.session_state.search_results)} 条视频")
    
    # 执行搜索
    if search_btn:
        if not search_username:
            st.error("❌ 请输入 TikTok 用户名")
        else:
            with st.spinner(f"正在抓取 @{search_username} 的数据..."):
                result = fetch_tiktok_data(search_username, search_count)
                
                if result['success']:
                    rows, account_info = parse_tiktok_videos(result)
                    
                    if rows:
                        st.session_state.search_results = rows
                        st.session_state.search_account_info = account_info
                        
                        # 显示账号信息
                        if account_info:
                            st.divider()
                            st.subheader(f"👤 @{account_info.get('username', search_username)}")
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("粉丝数", f"{account_info.get('followers', 0):,}")
                            with col2:
                                st.metric("关注数", f"{account_info.get('following', 0):,}")
                            with col3:
                                st.metric("总获赞", f"{account_info.get('total_likes', 0):,}")
                        
                        # 显示数据表格
                        st.divider()
                        st.subheader("📋 视频数据")
                        df = pd.DataFrame(rows)
                        st.dataframe(df, use_container_width=True, hide_index=True)
                        
                        # 统计信息
                        st.divider()
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            total_play = df['播放量'].sum()
                            st.metric("总播放量", f"{total_play:,}")
                        with col2:
                            total_like = df['点赞数'].sum()
                            st.metric("总点赞数", f"{total_like:,}")
                        with col3:
                            avg_play = int(df['播放量'].mean())
                            st.metric("平均播放", f"{avg_play:,}")
                        with col4:
                            avg_like = int(df['点赞数'].mean())
                            st.metric("平均点赞", f"{avg_like:,}")
                        
                        # 下载按钮
                        st.divider()
                        csv = download_csv(df, f"tiktok_data_{datetime.now().strftime('%Y%m%d')}.csv")
                        st.download_button(
                            label="📥 下载 CSV 文件",
                            data=csv,
                            file_name=f"tiktok_{account_info.get('username', search_username)}_{datetime.now().strftime('%Y%m%d')}.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
                    else:
                        st.warning("⚠️ 未找到视频数据，请检查账号名是否正确")
                        st.session_state.search_results = None
                else:
                    st.error(f"❌ 抓取失败：{result['error']}")
                    st.info("💡 请检查：1) 账号名是否正确 2) 账号是否公开 3) API Key 是否有效")
                    st.session_state.search_results = None
    
    # ========== 产品卡片区域 ==========
    st.divider()
    st.subheader("📦 我的产品")
    
    # 产品配置（简化版）
    PRODUCTS_CONFIG = {
        "PhotoRevive.AI": {
            "image": "https://p16-common-sign.tiktokcdn-us.com/tos-useast8-avt-0068-tx2/a62a32b54c026de51797e4862fd4ecd2~tplv-tiktokx-cropcenter:300:300.webp",
            "description": "AI 照片修复工具",
            "tiktok_username": "photorevive.ai"
        }
    }
    
    cols = st.columns(min(3, len(PRODUCTS_CONFIG)))
    for idx, (product_name, config) in enumerate(PRODUCTS_CONFIG.items()):
        with cols[idx % 3]:
            with st.container(border=True):
                try:
                    if config.get("image"):
                        st.image(config["image"], use_container_width=True)
                except:
                    st.write("🖼️")
                
                st.subheader(product_name)
                st.caption(config.get("description", ""))
                
                # 快速抓取按钮
                if st.button(f"抓取 {config.get('tiktok_username', '数据')}", key=f"quick_{product_name}", use_container_width=True):
                    st.session_state.search_username_input = config.get('tiktok_username', '')
                    st.rerun()
    
    # 页脚
    st.divider()
    st.caption("🛠️ powered by TikHub API & Streamlit")

# ============================================
# 🚀 主程序
# ============================================
def main():
    api_key = get_api_key()
    
    if st.session_state.current_page == "home":
        render_home_page()

if __name__ == "__main__":
    main()
