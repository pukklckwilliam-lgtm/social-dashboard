# 🎵 TikTok数据监控 - 正确接口版本 (v2)
import streamlit as st
import requests
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="🎵 TikTok数据监控", layout="wide")

# ============================================
# 🔑 API Key
# ============================================
API_KEY = "vpA5E99O82r1tnSpPrLOwkiJKgm9arlJ1AH7g2ulb9jmm12uGiejcCi/aA=="

# ============================================
# 📡 数据抓取（正确的 v2 接口）
# ============================================
def fetch_tiktok_data(username, count=10):
    """抓取 TikTok 数据 - v2 接口"""
    
    # ✅ 正确的接口：v2 不是 v3
    url = "https://api.tikhub.io/api/v1/tiktok/app/v3/fetch_user_post_videos_v2"
    
    headers = {
        "Authorization": f"Bearer {API_KEY}"
    }
    
    params = {
        "unique_id": username,
        "count": count
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)
        
        st.write(f"**请求 URL:** {response.url}")
        st.write(f"**状态码:** {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            st.success("✅ 请求成功！")
            return result
        else:
            st.error(f"❌ HTTP {response.status_code}")
            st.write(response.text[:500])
            return None
            
    except Exception as e:
        st.error(f"❌ 错误：{e}")
        return None

# ============================================
# 📊 数据展示
# ============================================
def display_data(result, username):
    """展示 TikTok 数据"""
    
    if not result:
        return
    
    # v2 接口的数据结构可能不同，需要适配
    data_content = result.get('data', {})
    
    # 尝试不同的数据路径
    video_list = data_content.get('aweme_list', 
                   data_content.get('videos', 
                   data_content.get('items', [])))
    
    if not video_list:
        st.warning("⚠️ 未找到视频数据")
        st.json(result)
        return
    
    st.success(f"✅ 获取到 {len(video_list)} 个视频！")
    
    # 账号信息
    if video_list and 'author' in video_list[0]:
        author = video_list[0]['author']
        st.subheader(f"👤 @{author.get('unique_id', username)}")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("昵称", author.get('nickname', 'N/A'))
        with col2:
            st.metric("粉丝数", f"{author.get('follower_count', 0):,}")
        with col3:
            st.metric("总获赞", f"{author.get('total_favorited', 0):,}")
    
    st.divider()
    
    # 统计数据
    total_stats = {'play': 0, 'like': 0, 'comment': 0, 'share': 0}
    rows = []
    
    for video in video_list:
        stats = video.get('statistics', video.get('stats', {}))
        create_time = video.get('create_time', video.get('created_time', 0))
        date_str = datetime.fromtimestamp(create_time).strftime('%Y-%m-%d') if create_time else 'N/A'
        
        play = stats.get('play_count', stats.get('view_count', 0))
        like = stats.get('digg_count', stats.get('like_count', 0))
        comment = stats.get('comment_count', stats.get('comments', 0))
        share = stats.get('share_count', stats.get('shares', 0))
        
        total_stats['play'] += play
        total_stats['like'] += like
        total_stats['comment'] += comment
        total_stats['share'] += share
        
        rows.append({
            '发布时间': date_str,
            '描述': (video.get('desc', video.get('description', ''))[:40] + '...') if video.get('desc') or video.get('description') else '无',
            '播放量': play,
            '点赞数': like,
            '评论数': comment,
            '分享数': share
        })
    
    # 核心指标
    st.subheader("📊 数据概览")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("总播放", f"{total_stats['play']:,}")
    with col2:
        st.metric("总点赞", f"{total_stats['like']:,}")
    with col3:
        st.metric("总评论", f"{total_stats['comment']:,}")
    with col4:
        st.metric("视频数", len(rows))
    
    st.divider()
    
    # 数据表格
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True)
    
    # 图表
    if not df.empty:
        st.bar_chart(df.set_index('发布时间')['播放量'])

# ============================================
# 🎨 主界面
# ============================================
st.title("🎵 TikTok 数据监控看板")
st.markdown("*接口版本：v2*")

# 输入
col1, col2 = st.columns([3, 1])
with col1:
    username = st.text_input("TikTok 用户名", value="photorevive.ai")
with col2:
    count = st.number_input("抓取数量", min_value=1, max_value=30, value=10)

# 获取数据按钮
if st.button("🚀 获取数据", type="primary", use_container_width=True):
    with st.spinner(f"正在获取 @{username} 的数据..."):
        result = fetch_tiktok_data(username, count)
        display_data(result, username)

# 页脚
st.markdown("---")
st.caption("🛠️ powered by TikHub API v2")
