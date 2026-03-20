# 🎯 社媒数据抓取系统 - 简洁版
import streamlit as st
import requests
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="📊 社媒数据抓取系统", layout="wide", page_icon="🎵")

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
        st.header("⚙️ 设置")
        api_key = st.text_input("🔑 TikHub API Key", type="password", value=API_KEY)
        if api_key:
            st.session_state["api_key"] = api_key.strip()
        
        st.divider()
        st.info("💡 提示：API Key 已预填，可直接使用")
    
    return st.session_state.get("api_key", API_KEY)

# ============================================
# 📡 TikTok 数据抓取（分页版）
# ============================================
def fetch_tiktok_data_paginated(username, target_count=30):
    """分页抓取 TikTok 数据"""
    
    url = "https://api.tikhub.io/api/v1/tiktok/app/v3/fetch_user_post_videos_v2"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    all_videos = []
    cursor = 0
    max_per_request = 20
    max_pages = (target_count + max_per_request - 1) // max_per_request
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for page in range(max_pages):
        status_text.text(f"正在抓取第 {page + 1}/{max_pages} 页...")
        
        params = {
            "unique_id": username,
            "count": max_per_request
        }
        
        if page > 0 and cursor > 0:
            params["cursor"] = cursor
        
        try:
            response = requests.get(url, params=params, headers=headers, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 200:
                    video_list = result.get('data', {}).get('aweme_list', [])
                    
                    if not video_list:
                        status_text.text("✅ 没有更多视频了")
                        break
                    
                    # 去重
                    new_videos = []
                    existing_ids = {v.get('aweme_id') for v in all_videos}
                    for video in video_list:
                        video_id = video.get('aweme_id')
                        if video_id and video_id not in existing_ids:
                            new_videos.append(video)
                            existing_ids.add(video_id)
                    
                    all_videos.extend(new_videos)
                    
                    # 更新进度
                    progress = min((page + 1) / max_pages, len(all_videos) / target_count)
                    progress_bar.progress(progress)
                    
                    # 检查是否还需要继续
                    if len(video_list) < max_per_request:
                        status_text.text(f"✅ 已抓取所有可用视频（共 {len(all_videos)} 条）")
                        break
                    
                    # 获取下一页 cursor
                    cursor = result.get('data', {}).get('cursor', 0)
                    
                    # 已达到目标数量
                    if len(all_videos) >= target_count:
                        status_text.text(f"✅ 已抓取 {len(all_videos)} 条视频")
                        break
                else:
                    status_text.text(f"❌ API 错误：{result.get('message', '')}")
                    break
            else:
                status_text.text(f"❌ HTTP {response.status_code}")
                break
                
        except Exception as e:
            status_text.text(f"❌ 请求异常：{str(e)}")
            break
    
    progress_bar.progress(1.0)
    status_text.text(f"✅ 完成！共抓取 {len(all_videos)} 条视频")
    
    return {
        "success": True,
        "videos": all_videos[:target_count],
        "total_fetched": len(all_videos)
    }

# ============================================
# 📊 数据解析
# ============================================
def parse_tiktok_videos(result):
    """解析 TikTok 视频数据"""
    if not result or not result.get('success'):
        return [], {}
    
    video_list = result.get('videos', [])
    
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
    """生成 CSV 下载"""
    csv = df.to_csv(index=False, encoding='utf-8-sig')
    return csv

# ============================================
# 🎨 主界面
# ============================================
def main():
    api_key = get_api_key()
    
    # ========== 标题区域 ==========
    st.title("📊 社媒数据抓取系统")
    st.markdown("*快速抓取 TikTok 账号数据 • 支持批量下载 CSV*")
    
    # ========== 搜索区域 ==========
    st.subheader("🔍 抓取 TikTok 数据")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        search_username = st.text_input(
            "TikTok 用户名",
            placeholder="例如：photorevive.ai",
            help="输入 TikTok 账号名（不需要 @ 符号）",
            key="search_username"
        )
    with col2:
        search_count = st.slider(
            "抓取数量",
            min_value=1,
            max_value=100,
            value=20,
            key="search_count",
