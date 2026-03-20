# 🎯 社媒数据抓取系统 - 最终修复版
import streamlit as st
import requests
import pandas as pd
import json
from datetime import datetime

st.set_page_config(page_title="📊 社媒数据抓取系统", layout="wide", page_icon="🎵")

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
        st.info("💡 API Key 已预填，可直接使用")
    return st.session_state.get("api_key", API_KEY)

# ============================================
# 🎵 TikTok 抓取
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
    max_loops = 4
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for loop in range(max_loops):
        status_text.text(f"正在抓取 TikTok 第 {loop + 1}/{max_loops} 页...")
        params = {"sec_user_id": sec_user_id, "count": 20, "max_cursor": cursor, "sort_type": 0}
        try:
            response = requests.get(url, params=params, headers=headers, timeout=30)
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 200:
                    data = result.get('data', {})
                    if isinstance(data, str):
                        try:
                            data = json.loads(data)
                        except:
                            pass
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
    status_text.text(f"✅ TikTok 完成！共抓取 {len(all_videos)} 条视频")
    return {"success": True, "videos": all_videos[:target_count], "platform": "TikTok"}

# ============================================
# 📺 YouTube 抓取（修复版 - 使用新API）
# ============================================
def fetch_youtube_data(channel_username, target_count=30):
    """抓取 YouTube 视频 - 修复参数格式"""
    
    # 🔍 清理频道名：确保格式正确
    clean_channel = channel_username.strip()
    # 如果不是 UC 开头，自动添加 @
    if not clean_channel.startswith('UC'):
        if not clean_channel.startswith('@'):
            clean_channel = '@' + clean_channel
    
    url = "https://api.tikhub.io/api/v1/youtube/web/get_channel_videos_v2"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    all_videos = []
    next_token = None  # ✅ 第一页用 None（不是空字符串！）
    max_loops = 4
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for loop in range(max_loops):
        status_text.text(f"正在抓取 YouTube 第 {loop + 1}/{max_loops} 页...")
        
        # ✅ 严格按文档参数格式
        params = {
            "channel_id": clean_channel,      # @频道名 或 UCxxx
            "contentType": "shorts",          # ✅ 小写 shorts
            "sortBy": "newest",               # ✅ 小写 newest
            "lang": "en-US"
        }
        
        # ✅ 关键修复：只有 next_token 有值时才添加参数
        if next_token and next_token != "None" and next_token != "":
            params["nextToken"] = next_token  # ✅ 注意大小写：nextToken
        
        try:
            response = requests.get(url, params=params, headers=headers, timeout=30)
            
            # 🔍 调试：打印请求详情
            if loop == 0:
                st.write(f"🔍 请求 URL：{response.url}")
                st.write(f"📋 参数：{params}")
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('code') == 200:
                    # 🔍 处理 data 可能是 JSON 字符串
                    data = result.get('data')
                    if isinstance(data, str):
                        try:
                            data = json.loads(data)
                        except:
                            pass
                    
                    video_list = []
                    if isinstance(data, dict):
                        video_list = (
                            data.get('videos', []) or 
                            data.get('items', []) or 
                            data.get('videoList', []) or
                            []
                        )
                    
                    if not video_list:
                        status_text.text("✅ 没有更多视频了")
                        break
                    
                    all_videos.extend(video_list)
                    progress_bar.progress((loop + 1) / max_loops)
                    status_text.text(f"✅ 已抓取 {len(all_videos)} 条视频")
                    
                    if len(all_videos) >= target_count:
                        break
                    
                    # ✅ 获取下一页 token
                    next_token = data.get('nextToken')  # ✅ 注意大小写
                    if not next_token or next_token == "":
                        status_text.text("✅ 已抓取所有可用视频")
                        break
                else:
                    status_text.text(f"❌ API 错误：{result.get('message', '')}")
                    st.error(f"📦 完整响应：{result}")
                    break
            else:
                status_text.text(f"❌ HTTP {response.status_code}")
                st.error(f"📦 响应内容：{response.text[:500]}")
                break
        except Exception as e:
            status_text.text(f"❌ 请求异常：{str(e)}")
            st.exception(e)
            break
    
    progress_bar.progress(1.0)
    status_text.text(f"✅ YouTube 完成！共抓取 {len(all_videos)} 条视频")
    
    return {"success": True, "videos": all_videos[:target_count], "platform": "YouTube"}
# ============================================
# 📊 数据解析
# ============================================
def parse_tiktok_videos(result):
    if not result.get('success'):
        return [], {}
    video_list = result.get('videos', [])
    account_info = {}
    if video_list and 'author' in video_list[0]:
        author = video_list[0]['author']
        account_info = {
            'username': author.get('unique_id', ''),
            'nickname': author.get('nickname', ''),
            'followers': author.get('follower_count', 0),
            'total_likes': author.get('total_favorited', 0)
        }
    rows = []
    for video in video_list:
        stats = video.get('statistics', {})
        create_time = video.get('create_time', 0)
        rows.append({
            '发布时间': datetime.fromtimestamp(create_time).strftime('%Y-%m-%d %H:%M') if create_time else '未知',
            '视频描述': (video.get('desc', '')[:100] + '...') if video.get('desc') else '无描述',
            '播放量': int(stats.get('play_count', 0) or 0),
            '点赞数': int(stats.get('digg_count', 0) or 0),
            '评论数': int(stats.get('comment_count', 0) or 0),
            '分享数': int(stats.get('share_count', 0) or 0),
            '视频链接': video.get('share_url', '')
        })
    return rows, account_info

def parse_youtube_videos(result):
    """解析 YouTube 数据 - 使用 :time 字段"""
    if not result.get('success'):
        return [], {}
    
    video_list = result.get('videos', [])
    account_info = {}
    
    if video_list:
        first = video_list[0]
        if 'channel' in first:
            channel = first['channel']
            account_info = {
                'username': channel.get('title', ''),
                'subscribers': channel.get('subscriber_count', 0),
                'total_videos': channel.get('video_count', 0)
            }
    
    rows = []
    for video in video_list:
        # 🔍 尝试所有可能的时间字段
        time_value = (
            video.get(':time') or  # ✅ 优先使用 :time
            video.get('time') or
            video.get('published_time') or 
            video.get('published_at') or 
            video.get('publishDate') or
            video.get('publishedDate') or
            video.get('upload_date') or
            ''
        )
        
        # 格式化时间
        if time_value and time_value != '':
            try:
                if 'T' in str(time_value):
                    dt = datetime.fromisoformat(str(time_value).replace('Z', '+00:00'))
                else:
                    dt = datetime.strptime(str(time_value), '%Y-%m-%d %H:%M:%S')
                publish_time = dt.strftime('%Y-%m-%d %H:%M')
            except:
                publish_time = str(time_value)
        else:
            publish_time = "未知"
        
        # 播放量
        play_count = (
            video.get('number_of_views') or 
            video.get('view_count') or 
            video.get('viewCount') or
            video.get('statistics', {}).get('view_count') or
            0
        )
        try:
            play_count = int(play_count)
        except:
            play_count = 0
        
        # 点赞/评论
        like_count = (
            video.get('like_count') or 
            video.get('number_of_likes') or
            video.get('statistics', {}).get('like_count') or
            0
        )
        comment_count = (
            video.get('comment_count') or 
            video.get('number_of_comments') or
            video.get('statistics', {}).get('comment_count') or
            0
        )
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
# 💾 CSV 下载
# ============================================
def download_csv(df, filename):
    return df.to_csv(index=False, encoding='utf-8-sig')

# ============================================
# 🎨 主界面
# ============================================
def main():
    api_key = get_api_key()
    
    st.title("📊 社媒数据抓取系统")
    st.markdown("*支持 TikTok • YouTube • X (Twitter) 数据抓取*")
    
    # 平台选择
    st.subheader("🔍 选择平台")
    platform = st.radio(
        "选择要抓取的平台",
        ["🎵 TikTok", "📺 YouTube", "🐦 X (Twitter)"],
        horizontal=True
    )
    
    # 搜索区域
    st.subheader("📥 输入账号信息")
    col1, col2 = st.columns([3, 1])
    
    with col1:
        if platform == "🎵 TikTok":
            search_username = st.text_input("TikTok 用户名", placeholder="例如：photorevive.ai", key="search_username")
        elif platform == "📺 YouTube":
            st.info("⚠️ **YouTube 必须使用 Channel ID！**\n\n"
                   "**如何获取？**\n"
                   "🔹 方法 1：访问 [commentpicker.com](https://commentpicker.com/youtube-channel-id.php)\n"
                   "🔹 方法 2：查看频道页面源代码，搜索 `channel_id`\n"
                   "🔹 方法 3：从 URL `youtube.com/channel/UCxxx` 复制 UC 开头部分")
            use_manual = st.checkbox("✍️ 我已获取 Channel ID", value=True)
            if use_manual:
                search_username = st.text_input("YouTube Channel ID", placeholder="例如：UCHAqXV2p9ZtJTBwuiXSkbdw", key="search_username_yt")
            else:
                search_username = st.text_input("YouTube 频道名（可能失败）", placeholder="例如：@AISpanishTutor", key="search_username_yt_auto")
        else:
            search_username = st.text_input("X 用户名", placeholder="例如：photorevive_ai", key="search_username_x")
    
    with col2:
        search_count = st.slider("抓取数量", 1, 100, 20, key="search_count")
    
    if search_count > 20:
        st.info(f"💡 将发起 {(search_count + 19) // 20} 次请求")
    
    search_btn = st.button("🚀 开始抓取", type="primary", use_container_width=True)
    
    # 执行抓取
    if search_btn:
        if not search_username:
            st.error("❌ 请输入账号名")
        else:
            with st.spinner(f"正在抓取 {platform}..."):
                if platform == "🎵 TikTok":
                    result = fetch_tiktok_data(search_username, search_count)
                    rows, account_info = parse_tiktok_videos(result)
                elif platform == "📺 YouTube":
                    result = fetch_youtube_data(search_username, search_count)
                    rows, account_info = parse_youtube_videos(result)
                else:
                    st.warning("⚠️ X 功能开发中...")
                    rows, account_info = [], {}
                
                if rows:
                    st.success(f"✅ 抓取 {len(rows)} 条视频")
                    
                    # 账号信息
                    if account_info:
                        st.divider()
                        st.subheader("👤 账号信息")
                        if platform == "🎵 TikTok":
                            c1, c2, c3 = st.columns(3)
                            c1.metric("账号", f"@{account_info.get('username')}")
                            c2.metric("粉丝", f"{account_info.get('followers',0):,}")
                            c3.metric("获赞", f"{account_info.get('total_likes',0):,}")
                        elif platform == "📺 YouTube":
                            c1, c2, c3 = st.columns(3)
                            c1.metric("频道", account_info.get('username'))
                            c2.metric("订阅", f"{account_info.get('subscribers',0):,}")
                            c3.metric("视频数", f"{account_info.get('total_videos',0):,}")
                    
                    # 数据表格
                    st.divider()
                    st.subheader("📋 视频数据")
                    df = pd.DataFrame(rows)
                    st.dataframe(df, use_container_width=True, hide_index=True)
                    
                    # 统计
                    st.divider()
                    st.subheader("📊 统计")
                    c1, c2, c3, c4 = st.columns(4)
                    
                    def safe_sum(series):
                        numeric = pd.to_numeric(series, errors='coerce').fillna(0)
                        return int(numeric.sum())
                    
                    c1.metric("总播放", f"{safe_sum(df['播放量']):,}")
                    c2.metric("总点赞", f"{safe_sum(df['点赞数']):,}")
                    c3.metric("平均播放", f"{safe_sum(df['播放量']) // len(df) if len(df) > 0 else 0:,}")
                    c4.metric("平均点赞", f"{safe_sum(df['点赞数']) // len(df) if len(df) > 0 else 0:,}")
                    
                    # 下载
                    st.divider()
                    platform_name = platform.replace("🎵 ", "").replace("📺 ", "").replace("🐦 ", "").replace(" (Twitter)", "")
                    csv = download_csv(df, f"{platform_name.lower()}_{search_username}_{datetime.now().strftime('%Y%m%d')}.csv")
                    st.download_button("📥 下载 CSV", csv, f"data.csv", "text/csv", use_container_width=True)
                else:
                    st.warning("⚠️ 未找到数据")
    
    st.divider()
    st.caption("🛠️ powered by TikHub API & Streamlit")

if __name__ == "__main__":
    main()
