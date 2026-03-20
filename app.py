# 🎯 社媒数据抓取系统 - 4次循环版
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
# 🔑 获取 sec_user_id
# ============================================
def get_sec_user_id(username):
    """第一步：获取 sec_user_id"""
    url = "https://api.tikhub.io/api/v1/tiktok/app/v3/get_user_id_and_sec_user_id_by_username"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    params = {"username": username}
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            result = response.json()
            if result.get('code') == 200:
                sec_user_id = result.get('data', {}).get('sec_user_id', '')
                return sec_user_id
    except Exception as e:
        st.error(f"获取用户ID失败：{e}")
    
    return ''

# ============================================
# 📡 TikTok 数据抓取（4次循环版）
# ============================================
def fetch_tiktok_data_paginated(username, target_count=30):
    """分页抓取 TikTok 数据 - 4次循环版"""
    
    # 第1步：获取 sec_user_id
    sec_user_id = get_sec_user_id(username)
    if not sec_user_id:
        return {"success": False, "error": "无法获取用户信息，请检查账号名是否正确"}
    
    # 第2步：循环抓取视频
    url = "https://api.tikhub.io/api/v1/tiktok/app/v3/fetch_user_post_videos_v2"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    all_videos = []
    cursor = "0"
    max_per_request = 20
    max_loops = 4  # ✅ 4次循环 = 最多80条
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for loop in range(max_loops):
        status_text.text(f"正在抓取第 {loop + 1}/{max_loops} 页...")
        
        params = {
            "sec_user_id": sec_user_id,
            "count": max_per_request,
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
                    
                    # 更新进度
                    progress = (loop + 1) / max_loops
                    progress_bar.progress(progress)
                    
                    status_text.text(f"✅ 已抓取 {len(all_videos)} 条视频")
                    
                    # 检查是否还有更多
                    if not data.get('has_more'):
                        status_text.text("✅ 已抓取所有可用视频")
                        break
                    
                    # 更新 cursor
                    cursor = str(data.get('max_cursor', '0'))
                    if cursor == '0':
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
        "videos": all_videos[:target_count] if target_count > 0 else all_videos,
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
            help="最多 100 条（API 单次最多 20 条）"
        )
    
    # 显示预估请求次数
    if search_count > 20:
        pages_needed = (search_count + 19) // 20
        st.info(f"💡 将发起 {pages_needed} 次请求（API 单次最多 20 条）")
    
    search_btn = st.button("🚀 开始抓取", type="primary", use_container_width=True)
    
    # 执行搜索
    if search_btn:
        if not search_username:
            st.error("❌ 请输入 TikTok 用户名")
        else:
            with st.spinner(f"正在抓取 @{search_username} 的数据..."):
                result = fetch_tiktok_data_paginated(search_username, search_count)
                
                if result['success']:
                    rows, account_info = parse_tiktok_videos(result)
                    
                    if rows:
                        st.session_state.search_results = rows
                        st.session_state.search_account_info = account_info
                        
                        # 显示抓取结果
                        st.success(f"✅ 成功抓取 {len(rows)} 条视频（目标：{search_count} 条）")
                        
                        # 显示账号信息
                        if account_info:
                            st.divider()
                            st.subheader(f"👤 账号信息")
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("账号", f"@{account_info.get('username', '')}")
                            with col2:
                                st.metric("粉丝数", f"{account_info.get('followers', 0):,}")
                            with col3:
                                st.metric("总获赞", f"{account_info.get('total_likes', 0):,}")
                        
                        # 显示数据表格
                        st.divider()
                        st.subheader("📋 视频数据")
                        df = pd.DataFrame(rows)
                        st.dataframe(df, use_container_width=True, hide_index=True)
                        
                        # 统计信息
                        st.divider()
                        st.subheader("📊 数据统计")
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
                        st.subheader("📥 导出数据")
                        csv = download_csv(df, f"tiktok_data_{datetime.now().strftime('%Y%m%d')}.csv")
                        st.download_button(
                            label="📥 下载 CSV 文件",
                            data=csv,
                            file_name=f"tiktok_{account_info.get('username', search_username)}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
                    else:
                        st.warning("⚠️ 未找到视频数据，请检查账号名是否正确")
                        st.session_state.search_results = None
                else:
                    st.error(f"❌ 抓取失败：{result.get('error', '未知错误')}")
                    st.info("💡 请检查：1) 账号名是否正确 2) 账号是否公开 3) API Key 是否有效")
                    st.session_state.search_results = None
    
    # ========== 使用说明 ==========
    st.divider()
    st.subheader("📖 使用说明")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        **1️⃣ 输入账号**
        - 输入 TikTok 用户名
        - 不需要 @ 符号
        - 例如：photorevive.ai
        """)
    with col2:
        st.markdown("""
        **2️⃣ 选择数量**
        - 滑动选择抓取数量
        - 最多 100 条
        - 超过 20 条会自动分页
        """)
    with col3:
        st.markdown("""
        **3️⃣ 下载数据**
        - 抓取完成后显示数据
        - 点击下载 CSV 按钮
        - 用 Excel 打开查看
        """)
    
    # ========== 页脚 ==========
    st.divider()
    st.caption("🛠️ powered by TikHub API & Streamlit | 社媒数据抓取系统")

# ============================================
# 🚀 主程序
# ============================================
if __name__ == "__main__":
    main()
