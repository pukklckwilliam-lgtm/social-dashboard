# 🎯 YouTube 抓取 - 最小修复版（解决 400 错误）
import streamlit as st
import requests
import pandas as pd
import json
from datetime import datetime

st.set_page_config(page_title="📊 YouTube 数据抓取", layout="wide")

API_KEY = "vpA5E99O82r1tnSpPrLOwkiJKgm9arlJ1AH7g2ulb9jmm12uGiejcCi/aA=="

def fetch_youtube_shorts(channel_input, target_count=30):
    """
    严格按 TikTokHub 文档调用 YouTube API
    文档: https://api.tikhub.io/#/YouTube-Web-API/get_channel_videos_v2_api_v1_youtube_web_get_channel_videos_v2_get
    """
    # 1. 清理频道名
    channel_id = channel_input.strip()
    if not channel_id.startswith('UC') and not channel_id.startswith('@'):
        channel_id = '@' + channel_id
    
    # 2. API 端点（确保无空格！）
    url = "https://api.tikhub.io/api/v1/youtube/web/get_channel_videos_v2"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    all_videos = []
    next_token = None  # 第一页为 None
    max_loops = 4
    
    progress_bar = st.progress(0)
    
    for loop in range(max_loops):
        # 3. 构建参数（严格按文档，大小写敏感！）
        params = {
            "channel_id": channel_id,      # @频道名 或 UCxxx
            "contentType": "shorts",        # 小写 shorts
            "sortBy": "newest",             # 小写 newest
            "lang": "en-US"
        }
        
        # 4. 关键修复：第一页完全不传 nextToken！
        if next_token and next_token != "None" and next_token != "":
            params["nextToken"] = next_token  # 注意大小写：nextToken
        
        # 5. 调试信息
        if loop == 0:
            with st.expander("🔍 请求详情", expanded=True):
                st.code(f"URL: {url}\nParams: {params}", language="python")
        
        # 6. 发送请求
        try:
            response = requests.get(url, params=params, headers=headers, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('code') == 200:
                    # 7. 处理 data 可能是 JSON 字符串
                    data = result.get('data')
                    if isinstance(data, str):
                        data = json.loads(data)
                    
                    # 8. 获取视频列表
                    videos = data.get('videos', []) or data.get('items', []) or []
                    if not videos:
                        break
                    
                    all_videos.extend(videos)
                    progress_bar.progress((loop + 1) / max_loops)
                    
                    if len(all_videos) >= target_count:
                        break
                    
                    # 9. 获取下一页 token
                    next_token = data.get('nextToken')
                    if not next_token:
                        break
                else:
                    st.error(f"❌ API 错误: {result.get('message')}")
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
    return all_videos[:target_count]

def parse_youtube_videos(videos):
    """解析视频数据"""
    rows = []
    for v in videos:
        # 时间字段
        time_val = v.get(':time') or v.get('time') or v.get('published_time') or '未知'
        
        # 播放量
        views = v.get('number_of_views') or v.get('view_count') or 0
        try:
            views = int(views)
        except:
            views = 0
        
        rows.append({
            '发布时间': time_val,
            '标题': (v.get('title', '')[:80] + '...') if v.get('title') else '无标题',
            '播放量': views,
            '视频ID': v.get('video_id', ''),
            '链接': f"https://youtube.com/shorts/{v.get('video_id', '')}"
        })
    return rows

# 主界面
st.title("📺 YouTube Shorts 抓取")
st.info("⚠️ 输入格式：`@AISpanishTutor` 或 `UCHAqXV2p9ZtJTBwuiXSkbdw`")

channel = st.text_input("频道", placeholder="@AISpanishTutor", value="@AISpanishTutor")
count = st.slider("数量", 1, 100, 20)

if st.button("🚀 开始抓取", type="primary"):
    with st.spinner("正在抓取..."):
        videos = fetch_youtube_shorts(channel, count)
        
        if videos:
            st.success(f"✅ 抓取 {len(videos)} 条视频")
            df = pd.DataFrame(parse_youtube_videos(videos))
            st.dataframe(df, use_container_width=True)
            
            csv = df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button("📥 下载 CSV", csv, "youtube_shorts.csv", "text/csv")
        else:
            st.warning("⚠️ 未找到数据")
