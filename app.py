# 🎯 社媒数据抓取系统 - YouTube 最终修复版
import streamlit as st
import requests
import pandas as pd
import json
from datetime import datetime

st.set_page_config(page_title="📊 社媒数据抓取系统", layout="wide", page_icon="🎵")

API_KEY = "vpA5E99O82r1tnSpPrLOwkiJKgm9arlJ1AH7g2ulb9jmm12uGiejcCi/aA=="

# ============================================
# 📺 YouTube 抓取（严格按文档修复）
# ============================================
def fetch_youtube_data(channel_input, target_count=30):
    """
    使用 /api/v1/youtube/web/get_channel_videos_v2
    严格遵循 TikTokHub 英文文档
    """
    try:
        # 1. 清理频道名（去掉空格）
        channel_id = channel_input.strip()
        
        # 2. 自动添加 @（如果不是 UC 开头）
        if not channel_id.startswith('UC'):
            if not channel_id.startswith('@'):
                channel_id = '@' + channel_id
        
        # 3. API 端点（确保没有空格！）
        url = "https://api.tikhub.io/api/v1/youtube/web/get_channel_videos_v2"
        headers = {"Authorization": f"Bearer {API_KEY}"}
        
        all_videos = []
        next_token = None  # 第一页为 None
        max_loops = 4
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for loop in range(max_loops):
            status_text.text(f"正在抓取 YouTube 第 {loop + 1}/{max_loops} 页...")
            
            # 4. 构建参数（严格按文档）
            params = {
                "channel_id": channel_id,
                "contentType": "shorts",
                "sortBy": "newest",
                "lang": "en-US"
            }
            
            # 5. 关键修复：第一页不传 nextToken！
            if next_token and next_token != "None" and next_token != "":
                params["nextToken"] = next_token
            
            # 6. 调试信息（第一次请求显示）
            if loop == 0:
                with st.expander("🔍 请求详情（调试用）", expanded=False):
                    st.write(f"**URL:** `{url}`")
                    st.write(f"**参数:** `{params}`")
            
            # 7. 发送请求
            response = requests.get(url, params=params, headers=headers, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('code') == 200:
                    # 8. 处理 data 可能是 JSON 字符串
                    data = result.get('data')
                    if isinstance(data, str):
                        try:
                            data = json.loads(data)
                        except:
                            pass
                    
                    # 9. 获取视频列表
                    video_list = []
                    if isinstance(data, dict):
                        video_list = data.get('videos', []) or data.get('items', []) or []
                    
                    if not video_list:
                        status_text.text("✅ 没有更多视频了")
                        break
                    
                    all_videos.extend(video_list)
                    progress_bar.progress((loop + 1) / max_loops)
                    status_text.text(f"✅ 已抓取 {len(all_videos)} 条视频")
                    
                    if len(all_videos) >= target_count:
                        break
                    
                    # 10. 获取下一页 token
                    next_token = data.get('nextToken')
                    if not next_token:
                        break
                else:
                    st.error(f"❌ API 错误：{result.get('message', '')}")
                    break
            else:
                st.error(f"❌ HTTP {response.status_code}")
                st.error(f"响应：{response.text[:300]}")
                break
    except Exception as e:
        st.error(f"❌ 异常：{str(e)}")
        return {"success": False, "error": str(e)}
    
    progress_bar.progress(1.0)
    status_text.text(f"✅ YouTube 完成！共抓取 {len(all_videos)} 条视频")
    
    return {"success": True, "videos": all_videos[:target_count], "platform": "YouTube"}

# ============================================
# 📊 数据解析
# ============================================
def parse_youtube_videos(result):
    if not result.get('success'):
        return [], {}
    
    video_list = result.get('videos', [])
    account_info = {}
    
    rows = []
    for video in video_list:
        # 时间字段
        time_value = video.get(':time') or video.get('time') or video.get('published_time') or ''
        publish_time = time_value if time_value else "未知"
        
        # 播放量
        play_count = video.get('number_of_views') or video.get('view_count') or 0
        try:
            play_count = int(play_count)
        except:
            play_count = 0
        
        # 点赞/评论
        like_count = video.get('like_count') or video.get('number_of_likes') or 0
        comment_count = video.get('comment_count') or video.get('number_of_comments') or 0
        try:
            like_count = int(like_count)
            comment_count = int(comment_count)
        except:
            like_count = 0
            comment_count = 0
        
        rows.append({
            '发布时间': publish_time,
            '视频标题': (video.get('title', '')[:100] + '...') if video.get('title') else '无标题',
            '播放量': play_count,
            '点赞数': like_count,
            '评论数': comment_count,
            '视频链接': f"https://youtube.com/shorts/{video.get('video_id', '')}"
        })
    
    return rows, account_info

# ============================================
# 🎨 主界面
# ============================================
def main():
    st.title("📊 社媒数据抓取系统")
    st.markdown("*支持 TikTok • YouTube 数据抓取*")
    
    # 平台选择
    st.subheader("🔍 选择平台")
    platform = st.radio("选择平台", ["🎵 TikTok", "📺 YouTube"], horizontal=True)
    
    # 输入区域
    st.subheader("📥 输入账号信息")
    col1, col2 = st.columns([3, 1])
    
    with col1:
        if platform == "📺 YouTube":
            st.info("⚠️ **输入格式：** `@AISpanishTutor` 或 `UCHAqXV2p9ZtJTBwuiXSkbdw`")
            search_username = st.text_input("YouTube 频道", placeholder="例如：@AISpanishTutor", key="yt_user")
        else:
            search_username = st.text_input("TikTok 用户名", placeholder="例如：photorevive.ai", key="tt_user")
    
    with col2:
        search_count = st.slider("抓取数量", 1, 100, 20, key="count")
    
    search_btn = st.button("🚀 开始抓取", type="primary", use_container_width=True)
    
    if search_btn:
        if not search_username:
            st.error("❌ 请输入账号名")
        else:
            with st.spinner(f"正在抓取 {platform}..."):
                if platform == "📺 YouTube":
                    result = fetch_youtube_data(search_username, search_count)
                    rows, _ = parse_youtube_videos(result)
                else:
                    st.warning("⚠️ TikTok 功能请参考之前代码")
                    rows = []
                
                if rows:
                    st.success(f"✅ 抓取 {len(rows)} 条视频")
                    df = pd.DataFrame(rows)
                    st.dataframe(df, use_container_width=True)
                    
                    # 下载
                    csv = df.to_csv(index=False, encoding='utf-8-sig')
                    st.download_button("📥 下载 CSV", csv, "data.csv", "text/csv")
                else:
                    st.warning("⚠️ 未找到数据")

if __name__ == "__main__":
    main()
