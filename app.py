import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import json

# 页面配置
st.set_page_config(page_title="📊 TikHub 社媒监控看板", layout="wide", page_icon="📈")

# --- 1. 安全获取 API Key 的逻辑 ---
def get_api_key():
    # 优先尝试从 Streamlit Secrets (保险箱) 读取
    if "tikhub_api_key" in st.secrets:
        return st.secrets["tikhub_api_key"]
    
    # 如果 Secrets 里没有，尝试从侧边栏输入框读取
    # 为了安全，我们不在代码里硬编码 Key
    with st.sidebar:
        st.header("⚙️ 设置")
        api_key_input = st.text_input("TikHub API Key", type="password", help="如果在上方配置了 Secrets，这里可以留空")
        
        if api_key_input:
            return api_key_input
        
    return None

# --- 2. 数据清洗与展示逻辑 ---
def fetch_and_display_data(api_key, username):
    url = "https://api.tikhub.io/api/v1/tiktok/app/v3/fetch_user_post_videos_v3"
    
    # 注意：TikHub 的 API 有时返回的 JSON key 带有空格，我们需要处理一下
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "unique_id": username,
        "count": 10  # 每次获取 10 条
    }

    try:
        with st.spinner(f'正在抓取 @{username} 的数据...'):
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                
                # 🔧 关键修复：清洗 JSON 键名中的空格 (例如 "code " -> "code")
                # 这是为了防止 API 返回格式不规范导致代码报错
                def clean_keys(obj):
                    if isinstance(obj, dict):
                        return {k.strip(): clean_keys(v) for k, v in obj.items()}
                    elif isinstance(obj, list):
                        return [clean_keys(item) for item in obj]
                    else:
                        return obj
                
                clean_result = clean_keys(result)

                # 检查业务状态码
                if clean_result.get('code') == 200:
                    st.success("✅ 数据获取成功！")
                    
                    # 提取视频列表
                    data_content = clean_result.get('data', {})
                    video_list = data_content.get('aweme_list', [])
                    
                    if not video_list:
                        st.warning("⚠️ 未找到视频数据，请检查账号是否正确。")
                        return

                    # --- 数据解析与表格化 ---
                    rows = []
                    total_stats = {'play': 0, 'like': 0, 'comment': 0, 'share': 0}
                    
                    for video in video_list:
                        stats = video.get('statistics', {})
                        author = video.get('author', {})
                        
                        # 时间转换
                        create_time = video.get('create_time', 0)
                        date_str = datetime.fromtimestamp(create_time).strftime('%Y-%m-%d %H:%M')
                        
                        # 提取核心指标
                        play_count = stats.get('play_count', 0)
                        digg_count = stats.get('digg_count', 0)
                        comment_count = stats.get('comment_count', 0)
                        share_count = stats.get('share_count', 0)
                        
                        # 累加总数
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
                            '视频链接': f"[查看视频]({video.get('share_url', '')})"
                        })
                    
                    df = pd.DataFrame(rows)
                    
                    # --- 界面展示 ---
                    
                    # 1. 核心数据概览 (Metrics)
                    st.subheader(f"📈 @{username} 的核心数据概览 (最近 10 条视频)")
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("总播放量", f"{total_stats['play']:,}")
                    m2.metric("总点赞数", f"{total_stats['like']:,}")
                    m3.metric("总评论数", f"{total_stats['comment']:,}")
                    m4.metric("总分享数", f"{total_stats['share']:,}")
                    
                    st.divider()
                    
                    # 2. 详细数据表格
                    st.subheader("📋 视频详细列表")
                    st.dataframe(df, use_container_width=True, hide_index=True)
                    
                    # 3. 简单图表
                    st.subheader("📊 视频表现趋势")
                    col_chart1, col_chart2 = st.columns(2)
                    with col_chart1:
                        st.bar_chart(df.set_index('发布时间')['播放量'])
                    with col_chart2:
                        st.bar_chart(df.set_index('发布时间')['点赞数'])

                else:
                    st.error(f"❌ API 返回错误：{clean_result.get('message', '未知错误')}")
                    with st.expander("查看原始返回数据"):
                        st.json(clean_result)
            else:
                st.error(f"❌ 请求失败：HTTP {response.status_code}")
                st.text(response.text[:200])
                
    except Exception as e:
        st.error(f"❌ 程序发生错误：{str(e)}")
        st.info("💡 提示：请检查 API Key 是否正确，或者网络连接是否正常。")

# --- 主程序入口 ---
def main():
    st.title("📊 TikHub 社媒数据监控看板")
    st.markdown("*支持 TikTok 数据深度分析 | 自动保存配置*")
    
    # 获取 API Key
    api_key = get_api_key()
    
    if not api_key:
        st.warning("⚠️ **请先配置 API Key！**\n\n为了安全且不用每次输入，建议按照以下步骤操作：\n1. 点击左侧侧边栏（如果没有显示，点击左上角 `<<`）。\n2. 在 Streamlit Cloud 后台的 **Secrets** 中配置 `tikhub_api_key`。\n3. 或者暂时在左侧输入框输入 Key（刷新页面后需重输）。")
        st.stop()
    
    # 输入账号
    col1, col2 = st.columns([3, 1])
    with col1:
        username = st.text_input("输入 TikTok 用户名 (不带 @)", placeholder="例如：photorevive.ai", value="photorevive.ai")
    with col2:
        st.write("") # 占位
        st.write("") # 占位
        if st.button("🚀 开始监控", type="primary", use_container_width=True):
            fetch_and_display_data(api_key, username)

if __name__ == "__main__":
    main()
