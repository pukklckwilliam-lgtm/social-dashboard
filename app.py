import streamlit as st
import requests
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="📊 TikHub 社媒监控看板", layout="wide", page_icon="📈")

def get_api_key():
    if "tikhub_api_key" in st.secrets:
        return st.secrets["tikhub_api_key"]
    with st.sidebar:
        st.header("⚙️ 设置")
        api_key_input = st.text_input("TikHub API Key", type="password")
        if api_key_input:
            return api_key_input
    return None

def fetch_and_display_data(api_key, username):
    # ✅ 修复 1：删除 URL 末尾空格
    url = "https://api.tikhub.io/api/v1/tiktok/app/v3/fetch_user_post_videos_v3"
    
    # ✅ 修复 3：尝试多种认证方式
    headers_options = [
        {"Authorization": api_key.strip(), "Content-Type": "application/json"},
        {"Authorization": f"Bearer {api_key.strip()}", "Content-Type": "application/json"},
        {"X-API-Key": api_key.strip(), "Content-Type": "application/json"},
    ]
    
    payload = {"unique_id": username, "count": 10}
    
    try:
        with st.spinner(f'正在抓取 @{username} 的数据...'):
            success = False
            result = None
            
            # 尝试不同的 Header 和请求方法
            for headers in headers_options:
                for method in ["get", "post"]:
                    try:
                        if method == "get":
                            response = requests.get(url, params=payload, headers=headers, timeout=30)
                        else:
                            response = requests.post(url, json=payload, headers=headers, timeout=30)
                        
                        if response.status_code == 200:
                            result = response.json()
                            success = True
                            break
                    except:
                        continue
                if success:
                    break
            
            if not success:
                st.error("❌ 请求失败，请检查 API Key 或账号名称")
                return
            
            # 清洗键名空格
            def clean_keys(obj):
                if isinstance(obj, dict):
                    return {k.strip(): clean_keys(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [clean_keys(item) for item in obj]
                return obj
            
            clean_result = clean_keys(result)
            
            if clean_result.get('code') == 200:
                st.success("✅ 数据获取成功！")
                data_content = clean_result.get('data', {})
                video_list = data_content.get('aweme_list', [])
                
                if not video_list:
                    st.warning("⚠️ 未找到视频数据")
                    return
                
                rows = []
                total_stats = {'play': 0, 'like': 0, 'comment': 0, 'share': 0}
                
                for video in video_list:
                    stats = video.get('statistics', {})
                    create_time = video.get('create_time', 0)
                    date_str = datetime.fromtimestamp(create_time).strftime('%Y-%m-%d %H:%M')
                    
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
                    })
                
                df = pd.DataFrame(rows)
                
                st.subheader(f"📈 @{username} 的核心数据概览")
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("总播放量", f"{total_stats['play']:,}")
                m2.metric("总点赞数", f"{total_stats['like']:,}")
                m3.metric("总评论数", f"{total_stats['comment']:,}")
                m4.metric("总分享数", f"{total_stats['share']:,}")
                
                st.divider()
                st.subheader("📋 视频详细列表")
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                st.subheader("📊 视频表现趋势")
                col1, col2 = st.columns(2)
                with col1:
                    st.bar_chart(df.set_index('发布时间')['播放量'])
                with col2:
                    st.bar_chart(df.set_index('发布时间')['点赞数'])
            else:
                st.error(f"❌ API 错误：{clean_result.get('message', '未知错误')}")
                
    except Exception as e:
        st.error(f"❌ 程序错误：{str(e)}")

def main():
    st.title("📊 TikHub 社媒数据监控看板")
    api_key = get_api_key()
    
    if not api_key:
        st.warning("⚠️ 请先在侧边栏输入 API Key")
        st.stop()
    
    col1, col2 = st.columns([3, 1])
    with col1:
        username = st.text_input("TikTok 用户名", value="photorevive.ai")
    with col2:
        st.write("")
        st.write("")
        if st.button("🚀 开始监控", type="primary", use_container_width=True):
            fetch_and_display_data(api_key, username)

if __name__ == "__main__":
    main()
