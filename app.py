# 🎯 社媒数据抓取系统 - TikTok + YouTube 完整版
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
# 🎵 TikTok 数据抓取
# ============================================
def get_sec_user_id(username):
    """获取 TikTok sec_user_id"""
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
    """抓取 TikTok 视频数据 - 4次循环版"""
    sec_user_id = get_sec_user_id(username)
    if not sec_user_id:
        return {"success": False, "error": "无法获取用户信息"}
    
    url = "https://api.tikhub.io/api/v1/tiktok/app/v3/fetch_user_post_videos_v2"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    all_videos = []
    cursor = "0"
    max_loops = 4  # 4次循环 = 最多80条
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for loop in range(max_loops):
        status_text.text(f"正在抓取 TikTok 第 {loop + 1}/{max_loops} 页...")
        
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
                    video_list = data.get('aweme_list', [])
                    
                    if not video_list:
                        status_text.text("✅ 没有更多视频了")
                        break
                    
                    all_videos.extend(video_list)
                    progress_bar.progress((loop + 1) / max_loops)
                    status_text.text(f"✅ 已抓取 {len(all_videos)} 条视频")
                    
                    if len(all_videos) >= target_count:
                        status_text.text(f"✅ 已达到目标数量")
                        break
                    
                    if not data.get('has_more'):
                        status_text.text("✅ 已抓取所有可用视频")
                        break
                    
                    cursor = str(data.get('max_cursor', '0'))
                    if cursor == '0':
                        break
            else:
                status_text.text(f"❌ HTTP {response.status_code}")
                break
        except Exception as e:
            status_text.text(f"❌ 请求异常：{str(e)}")
            break
    
    progress_bar.progress(1.0)
    status_text.text(f"✅ TikTok 完成！共抓取 {len(all_videos)} 条视频")
    
    return {"success": True, "videos": all_videos[:target_count], "platform": "TikTok"}

# ============================================
# 📺 YouTube 数据抓取
# ============================================
def get_youtube_channel_id(username):
    """获取 YouTube Channel ID"""
    url = "https://api.tikhub.io/api/v1/youtube/web/search_channel"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    params = {"query": username}
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            result = response.json()
            if result.get('code') == 200:
                channels = result.get('data', {}).get('channels', [])
                if channels:
                    return channels[0].get('channel_id', '')
    except:
        pass
    return ''

def fetch_youtube_data(channel_username, target_count=30):
    """抓取 YouTube Shorts 短视频数据 - 4次循环版"""
    # 尝试直接用 username 作为 channel_id
    channel_id = channel_username
    if not channel_id.startswith('UC'):
        channel_id = get_youtube_channel_id(channel_username)
    
    if not channel_id:
        return {"success": False, "error": "无法找到 YouTube 频道"}
    
    # ✅ 使用 Shorts 端点
    url = "https://api.tikhub.io/api/v1/youtube/web/get_channel_short_videos"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    all_videos = []
    next_page_token = ""
    max_loops = 4  # 4次循环 = 最多80条
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for loop in range(max_loops):
        status_text.text(f"正在抓取 YouTube Shorts 第 {loop + 1}/{max_loops} 页...")
        
        params = {
            "channel_id": channel_id,
            "count": 20
        }
        
        if next_page_token:
            params["next_page_token"] = next_page_token
        
        try:
            response = requests.get(url, params=params, headers=headers, timeout=30)
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 200:
                    data = result.get('data', {})
                    video_list = data.get('videos', [])
                    
                    if not video_list:
                        status_text.text("✅ 没有更多短视频了")
                        break
                    
                    all_videos.extend(video_list)
                    progress_bar.progress((loop + 1) / max_loops)
                    status_text.text(f"✅ 已抓取 {len(all_videos)} 条短视频")
                    
                    if len(all_videos) >= target_count:
                        status_text.text(f"✅ 已达到目标数量")
                        break
                    
                    next_page_token = data.get('next_page_token', '')
                    if not next_page_token:
                        status_text.text("✅ 已抓取所有可用短视频")
                        break
            else:
                status_text.text(f"❌ HTTP {response.status_code}")
                break
        except Exception as e:
            status_text.text(f"❌ 请求异常：{str(e)}")
            break
    
    progress_bar.progress(1.0)
    status_text.text(f"✅ YouTube Shorts 完成！共抓取 {len(all_videos)} 条短视频")
    
    return {"success": True, "videos": all_videos[:target_count], "platform": "YouTube"}

# ============================================
# 🐦 X (Twitter) 数据抓取（预留）
# ============================================
def fetch_x_data(username, target_count=30):
    """抓取 X (Twitter) 数据 - 预留功能"""
    return {"success": False, "error": "X (Twitter) 功能开发中..."}

# ============================================
# 📊 数据解析
# ============================================
def parse_tiktok_videos(result):
    """解析 TikTok 数据"""
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
            '发布时间': datetime.fromtimestamp(create_time).strftime('%Y-%m-%d %H:%M') if create_time else '',
            '视频描述': (video.get('desc', '')[:100] + '...') if video.get('desc') else '无描述',
            '播放量': stats.get('play_count', 0),
            '点赞数': stats.get('digg_count', 0),
            '评论数': stats.get('comment_count', 0),
            '分享数': stats.get('share_count', 0),
            '视频链接': video.get('share_url', '')
        })
    
    return rows, account_info

def parse_youtube_videos(result):
    """解析 YouTube Shorts 数据"""
    if not result.get('success'):
        return [], {}
    
    video_list = result.get('videos', [])
    account_info = {}
    
    if video_list and 'channel' in video_list[0]:
        channel = video_list[0]['channel']
        account_info = {
            'username': channel.get('title', ''),
            'subscribers': channel.get('subscriber_count', 0),
            'total_videos': channel.get('video_count', 0)
        }
    
    rows = []
    for video in video_list:
        stats = video.get('statistics', {})
        publish_time = video.get('published_at', '')
        if publish_time:
            try:
                dt = datetime.fromisoformat(publish_time.replace('Z', '+00:00'))
                publish_time = dt.strftime('%Y-%m-%d %H:%M')
            except:
                pass
        
        rows.append({
            '发布时间': publish_time,
            '视频标题': (video.get('title', '')[:100] + '...') if video.get('title') else '无标题',
            '播放量': stats.get('view_count', 0),
            '点赞数': stats.get('like_count', 0),
            '评论数': stats.get('comment_count', 0),
            '视频链接': f"https://youtube.com/shorts/{video.get('video_id', '')}"
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
    st.markdown("*支持 TikTok • YouTube • X (Twitter) 数据抓取*")
    
    # ========== 平台选择 ==========
    st.subheader("🔍 选择平台")
    platform = st.radio(
        "选择要抓取的平台",
        ["🎵 TikTok", "📺 YouTube", "🐦 X (Twitter)"],
        horizontal=True
    )
    
    # ========== 搜索区域 ==========
    st.subheader("📥 输入账号信息")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        if platform == "🎵 TikTok":
            search_username = st.text_input(
                "TikTok 用户名",
                placeholder="例如：photorevive.ai",
                key="search_username"
            )
        elif platform == "📺 YouTube":
            search_username = st.text_input(
                "YouTube 频道名",
                placeholder="例如：AISpanishTutor 或 @AISpanishTutor",
                key="search_username_yt"
            )
        else:
            search_username = st.text_input(
                "X 用户名",
                placeholder="例如：photorevive_ai",
                key="search_username_x"
            )
    
    with col2:
        search_count = st.slider(
            "抓取数量",
            min_value=1,
            max_value=100,
            value=20,
            key="search_count"
        )
    
    # 显示预估请求次数
    if search_count > 20:
        pages_needed = (search_count + 19) // 20
        st.info(f"💡 将发起 {pages_needed} 次请求（API 单次最多 20 条）")
    
    search_btn = st.button("🚀 开始抓取", type="primary", use_container_width=True)
    
    # ========== 执行抓取 ==========
    if search_btn:
        if not search_username:
            st.error("❌ 请输入账号名")
        else:
            with st.spinner(f"正在抓取 {platform} @{search_username} 的数据..."):
                # 根据平台调用不同函数
                if platform == "🎵 TikTok":
                    result = fetch_tiktok_data(search_username, search_count)
                    rows, account_info = parse_tiktok_videos(result)
                elif platform == "📺 YouTube":
                    result = fetch_youtube_data(search_username, search_count)
                    rows, account_info = parse_youtube_videos(result)
                else:
                    st.warning("⚠️ X (Twitter) 功能开发中...")
                    rows, account_info = [], {}
                
                if rows:
                    st.success(f"✅ 成功抓取 {len(rows)} 条视频（目标：{search_count} 条）")
                    
                    # 账号信息
                    if account_info:
                        st.divider()
                        st.subheader("👤 账号信息")
                        if platform == "🎵 TikTok":
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("账号", f"@{account_info.get('username', '')}")
                            with col2:
                                st.metric("粉丝数", f"{account_info.get('followers', 0):,}")
                            with col3:
                                st.metric("总获赞", f"{account_info.get('total_likes', 0):,}")
                        elif platform == "📺 YouTube":
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("频道", account_info.get('username', ''))
                            with col2:
                                st.metric("订阅数", f"{account_info.get('subscribers', 0):,}")
                            with col3:
                                st.metric("总视频数", f"{account_info.get('total_videos', 0):,}")
                    
                    # 数据表格
                    st.divider()
                    st.subheader("📋 视频数据")
                    df = pd.DataFrame(rows)
                    st.dataframe(df, use_container_width=True, hide_index=True)
                    
                    # 统计信息
                    st.divider()
                    st.subheader("📊 数据统计")
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("总播放量", f"{df['播放量'].sum():,}")
                    with col2:
                        st.metric("总点赞数", f"{df['点赞数'].sum():,}")
                    with col3:
                        st.metric("平均播放", f"{int(df['播放量'].mean()):,}")
                    with col4:
                        st.metric("平均点赞", f"{int(df['点赞数'].mean()):,}")
                    
                    # 下载按钮
                    st.divider()
                    st.subheader("📥 导出数据")
                    platform_name = platform.replace("🎵 ", "").replace("📺 ", "").replace("🐦 ", "").replace(" (Twitter)", "")
                    csv = download_csv(df, f"{platform_name.lower()}_data_{datetime.now().strftime('%Y%m%d')}.csv")
                    st.download_button(
                        label="📥 下载 CSV 文件",
                        data=csv,
                        file_name=f"{platform_name.lower()}_{search_username}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                else:
                    st.warning("⚠️ 未找到视频数据，请检查账号名是否正确")
    
    # ========== 使用说明 ==========
    st.divider()
    st.subheader("📖 使用说明")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        **🎵 TikTok**
        - 输入用户名
        - 不需要 @ 符号
        - 例如：photorevive.ai
        """)
    with col2:
        st.markdown("""
        **📺 YouTube**
        - 输入频道名或 @用户名
        - 例如：AISpanishTutor
        - 或：@AISpanishTutor
        """)
    with col3:
        st.markdown("""
        **🐦 X (Twitter)**
        - 功能开发中
        - 敬请期待
        """)
    
    # ========== 页脚 ==========
    st.divider()
    st.caption("🛠️ powered by TikHub API & Streamlit | 社媒数据抓取系统")

# ============================================
# 🚀 主程序
# ============================================
if __name__ == "__main__":
    main()
