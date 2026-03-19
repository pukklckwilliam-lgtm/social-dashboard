# 🎯 社媒数据监控看板 - 双 API 源支持版
# 支持：TikHub（任意账号） + Post Bridge（自有账号）
import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import json

st.set_page_config(page_title="📊 社媒数据监控看板", layout="wide", page_icon="📈")

# ============================================
# 🔑 API Key 管理（支持双平台）
# ============================================
def get_api_keys():
    """获取所有平台的 API Key"""
    keys = {}
    
    # TikHub API Key
    if "tikhub_api_key" in st.secrets:
        keys['tikhub'] = st.secrets["tikhub_api_key"]
        st.sidebar.success("✅ TikHub API Key 已加载")
    else:
        with st.sidebar:
            keys['tikhub'] = st.text_input("🎵 TikHub API Key", type="password", 
                                          help="用于抓取任意 TikTok 账号数据")
    
    # Post Bridge API Key
    if "postbridge_api_key" in st.secrets:
        keys['postbridge'] = st.secrets["postbridge_api_key"]
        st.sidebar.success("🌉 Post Bridge API Key 已加载")
    else:
        with st.sidebar:
            keys['postbridge'] = st.text_input("🌉 Post Bridge API Key", type="password",
                                              help="用于管理已连接的自有账号")
    
    return keys

# ============================================
# 🌐 数据源选择
# ============================================
def select_data_source():
    """选择数据源"""
    source = st.sidebar.selectbox(
        "📡 数据源",
        ["TikHub（任意账号）", "Post Bridge（自有账号）"],
        help="TikHub: 可抓取任意公开账号 | Post Bridge: 仅限已连接的自有账号"
    )
    return source

# ============================================
# 📡 TikHub 数据获取
# ============================================
def fetch_tikhub_data(api_key, username):
    """从 TikHub 获取 TikTok 数据"""
    url = "https://api.tikhub.io/api/v1/tiktok/app/v3/fetch_user_post_videos_v3"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    params = {"unique_id": username, "count": 10}
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)
        if response.status_code == 200:
            result = response.json()
            if result.get('code') == 200:
                return {"success": True, "data": result}
            else:
                return {"success": False, "error": result.get('message', 'API 返回错误')}
        else:
            return {"success": False, "error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ============================================
# 📡 Post Bridge 数据获取
# ============================================
def fetch_postbridge_accounts(api_key):
    """从 Post Bridge 获取已连接的账号列表"""
    url = "https://api.post-bridge.com/v1/social-accounts"
    headers = {"Authorization": f"Bearer {api_key}"}
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        else:
            return {"success": False, "error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def fetch_postbridge_analytics(api_key, account_id=None):
    """从 Post Bridge 获取分析数据"""
    url = "https://api.post-bridge.com/v1/analytics"
    headers = {"Authorization": f"Bearer {api_key}"}
    params = {}
    if account_id:
        params["account_id"] = account_id
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        else:
            return {"success": False, "error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ============================================
# 📊 TikHub 数据展示
# ============================================
def display_tikhub_data(result, username):
    """展示 TikHub 获取的数据"""
    data_content = result.get('data', {})
    video_list = data_content.get('aweme_list', [])
    
    if not video_list:
        st.warning("⚠️ 未找到视频数据")
        return
    
    st.success(f"✅ 成功获取 {len(video_list)} 个视频！")
    
    # 核心指标
    total_stats = {'play': 0, 'like': 0, 'comment': 0, 'share': 0}
    rows = []
    
    for video in video_list:
        stats = video.get('statistics', {})
        create_time = video.get('create_time', 0)
        date_str = datetime.fromtimestamp(create_time).strftime('%Y-%m-%d') if create_time else 'N/A'
        
        play_count = stats.get('play_count', 0)
        digg_count = stats.get('digg_count', 0)
        comment_count = stats.get('comment_count', 0)
        share_count = stats.get('share_count', 0)
        
        total_stats['play'] += play_count
        total_stats['like'] += digg_count
        total_stats['comment'] += comment_count
        total_stats['share'] += share_count
        
        rows.append({
            '发布时间': date_str,
            '视频描述': (video.get('desc', '')[:50] + '...') if video.get('desc') else '无描述',
            '播放量': play_count,
            '点赞数': digg_count,
            '评论数': comment_count,
            '分享数': share_count,
            '视频链接': video.get('share_url', '')
        })
    
    # 指标卡片
    st.subheader(f"📈 @{username} 的核心数据概览")
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
    
    # 数据表格
   
