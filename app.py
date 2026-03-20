# 🎯 社媒数据抓取系统 - 稳定运行版
import streamlit as st
import requests
import pandas as pd
import json
from datetime import datetime

st.set_page_config(page_title="📊 社媒数据抓取系统", layout="wide", page_icon="🎵")

# 🔑 API Key
API_KEY = "vpA5E99O82r1tnSpPrLOwkiJKgm9arlJ1AH7g2ulb9jmm12uGiejcCi/aA=="

# ============================================
# ⚙️ 获取 API Key
# ============================================
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
        st.info("💡 API Key 已预填，可直接使用")
    return st.session_state.get("api_key", API_KEY)

# ============================================
# 🎵 TikTok 抓取（基于你的工作流）
# ============================================
def get_sec_user_id(username):
    url = "https://api.tikhub.io/api/v1/tiktok/app/v3/get_user_id_and_sec_user_id_by_username"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    params = {"username": username}
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            result = response.json()
            if result.get('code') == 200:
                return result.get('data', {}).get('sec_user_id', '')
    except:
        pass
    return ''

def fetch_tiktok_data(username, target_count=30):
    sec_user_id = get_sec_user_id(username)
    if not sec_user_id:
        return {"success": False, "error": "无法获取用户信息"}
    
    url = "https://api.tikhub.io/api/v1/tiktok/app/v3/fetch_user_post_videos_v2"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    all_videos = []
    cursor = "0"
    max_loops = 3  # 3次 = 60条
    
    progress_bar = st.progress(0)
    
    for loop in range(max_loops):
        params = {
            "sec_user_id": sec_user_id,
            "count": 20,
            "max_cursor": cursor,
            "sort_type": 0
        }
        
        try:
            response = requests.get(url, params=params, headers=headers, timeout=30)
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 200:
                    data = result.get('data', {})
                    if isinstance(data, str):
                        data = json.loads(data)
                    
                    video_list = data.get('aweme_list', []) if isinstance(data, dict) else []
                    if not video_list:
                        break
                    
                    all_videos.extend(video_list)
                    progress_bar.progress((loop + 1) / max_loops)
                    
                    if len(all_videos) >= target_count:
                        break
                    if not data.get('has_more'):
                        break
                    
                    cursor = str(data.get('max_cursor', '0'))
                    if cursor == '0':
                        break
        except:
            break
    
    progress_bar.progress(1.0)
    return {"success": True, "videos": all_videos[:target_count]}

# ============================================
# 📺 YouTube 抓取（严格按文档）
# ============================================
def fetch_youtube_data(channel_input, target_count=30):
    # 清理频道名
    channel_id = channel_input.strip()
    if not channel_id.startswith('UC') and not channel_id.startswith('@'):
        channel_id = '@' + channel_id
    
    url = "https://api.tikhub.io/api/v1/youtube/web/get_channel_videos_v2"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    all_videos = []
    next_token = None  # 第一页不传
    max_loops = 3
    
    progress_bar = st.progress(0)
    
    for loop in range(max_loops):
        # 构建参数（严格按文档，大小写敏感）
        params = {
            "channel_id": channel_id,
            "contentType": "shorts",
            "sortBy": "newest",
            "lang": "en-US"
        }
        
        # 关键：第一页不传 nextToken
        if next_token and next_token != "None" and next_token != "":
            params["nextToken"] = next_token
        
        # 调试信息
        if loop == 0:
            with st.expander("🔍 请求详情", expanded=False):
                st.code(f"URL: {url}\nParams: {params}", language="python")
        
        try:
            response = requests.get(url, params=params, headers=headers, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('code') == 200:
                    data = result.get('data')
                    if isinstance(data, str):
                        data = json.loads(data)
                    
                    video_list = data.get('videos', []) or data.get('items', []) or []
                    if not video_list:
                        break
                    
                    all_videos.extend(video_list)
                    progress_bar.progress((loop + 1) / max_loops)
                    
                    if len(all_videos) >= target_count:
                        break
                    
                    next_token = data.get('nextToken')
                    if not next_token:
                        break
                else:
                    st.error(f"❌ API: {result.get('message')}")
                    with st.expander("查看响应", expanded=False):
                        st.json(result)
                    break
            else:
                st.error(f"❌ HTTP {response.status_code}")
                st.code(response.text[:500])
                break
        except Exception as e:
            st.error(f"❌ 异常: {e}")
            break
    
    progress_bar.progress(1.0)
    return {"success": True, "videos": all_videos[:target_count]}

# ============================================
# 📊 数据解析
# ============================================
def parse_tiktok_videos(result):
    if not result.get('success'):
        return [], {}
    
    video_list = result.get('videos', [])
    rows = []
    for video in video_list:
        stats = video.get('statistics', {})
        create_time = video.get('create_time', 0)
        rows.append({
            '发布时间': datetime.fromtimestamp(create_time).strftime('%Y-%m-%d %H:%M') if create_time else '未知',
            '标题': (video.get('desc', '')[:80] + '...') if video.get('desc') else '无标题',
            '播放量': int(stats.get('play_count', 0) or 0),
            '点赞数': int(stats.get('digg_count', 0) or 0),
            '评论数': int(stats.get('comment_count', 0) or 0),
            '链接': video.get('share_url', '')
        })
    return rows

def parse_youtube_videos(result):
    if not result.get('success'):
        return [], {}
    
    video_list = result.get('videos', [])
    rows = []
    for video in video_list:
        time_val = video.get(':time') or video.get('time') or video.get('published_time') or '未知'
        views = video.get('number_of_views') or video.get('view_count') or 0
        try:
            views = int(views)
        except:
            views = 0
        
        rows.append({
            '发布时间': time_val,
            '标题': (video.get('title', '')[:80] + '...') if video.get('title') else '无标题',
            '播放量': views,
            '点赞数': video.get('like_count', 0),
            '评论数': video.get('comment_count', 0),
            '链接': f"https://youtube.com/shorts/{video.get('video_id', '')}"
        })
    return rows

# ============================================
# 🎨 主界面
# ============================================
def main():
    api_key = get_api_key()
    
    st.title("📊 社媒数据抓取系统")
    st.markdown("*TikTok • YouTube 数据抓取*")
    
    # 平台选择
    platform = st.radio("选择平台", ["🎵 TikTok", "📺 YouTube"], horizontal=True)
    
    # 输入区域
    st.subheader("📥 输入账号")
    col1, col2 = st.columns([3, 1])
    
    with col1:
        if platform == "🎵 TikTok":
            search_input = st.text_input("TikTok 用户名", placeholder="photorevive.ai", key="tt")
        else:
            st.info("⚠️ 格式：`@AISpanishTutor` 或 `UCHAqXV2p9ZtJTBwuiXSkbdw`")
            search_input = st.text_input("YouTube 频道", placeholder="@AISpanishTutor", key="yt")
    
    with col2:
        count = st.slider("数量", 1, 100, 20, key="cnt")
    
    # 抓取按钮
    if st.button("🚀 开始抓取", type="primary", use_container_width=True):
        if not search_input:
            st.error("❌ 请输入账号")
        else:
            with st.spinner("正在抓取..."):
                # 调用对应函数
                if platform == "🎵 TikTok":
                    result = fetch_tiktok_data(search_input, count)
                    rows = parse_tiktok_videos(result)
                else:
                    result = fetch_youtube_data(search_input, count)
                    rows = parse_youtube_videos(result)
                
                # 显示结果
                if rows:
                    st.success(f"✅ 抓取 {len(rows)} 条")
                    df = pd.DataFrame(rows)
                    st.dataframe(df, use_container_width=True, hide_index=True)
                    
                    # 统计
                    st.divider()
                    c1, c2 = st.columns(2)
                    c1.metric("总播放", f"{df['播放量'].sum():,}")
                    c2.metric("平均播放", f"{int(df['播放量'].mean()):,}")
                    
                    # 下载
                    csv = df.to_csv(index=False, encoding='utf-8-sig')
                    st.download_button("📥 下载 CSV", csv, "data.csv", "text/csv", use_container_width=True)
                else:
                    st.warning("⚠️ 未找到数据")
    
    st.divider()
    st.caption("🛠️ powered by TikHub API")

# ============================================
# 🚀 主程序
# ============================================
if __name__ == "__main__":
    main()
