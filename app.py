# 🎯 社媒数据监控看板 - 自动保存 API Key 版
import streamlit as st
import requests
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="📊 社媒监控看板", layout="wide", page_icon="📈")

# 侧边栏配置
st.sidebar.title("⚙️ 设置")

# 优先从 secrets 读取 API Key，如果没有则使用输入框
if "tikhub_api_key" in st.secrets:
    api_key = st.secrets["tikhub_api_key"]
    st.sidebar.success("✅ API Key 已自动加载")
else:
    api_key = st.sidebar.text_input("TikHub API Key", type="password", help="输入后会自动保存")
    if api_key:
        st.session_state["api_key"] = api_key
        st.sidebar.success("✅ API Key 已保存（本次会话）")

# 如果没有 API Key，尝试从 session_state 读取
if not api_key and "api_key" in st.session_state:
    api_key = st.session_state["api_key"]

# 主界面
st.title("📊 社媒数据监控看板")
st.markdown("*支持 TikTok • Instagram • Facebook • YouTube • X*")

# 输入区域
col1, col2 = st.columns(2)
with col1:
    platform = st.selectbox("平台", ["tiktok", "instagram", "facebook", "youtube", "twitter"])
with col2:
    username = st.text_input("账号用户名", placeholder="例如：photorevive.ai")

# 获取数据按钮
if st.button("🚀 获取最新数据", type="primary", use_container_width=True):
    if not api_key:
        st.error("❌ 请先在左侧输入 API Key")
        st.stop()
    if not username:
        st.error("❌ 请输入账号用户名")
        st.stop()
    
    with st.spinner(f'正在从 TikHub 抓取 {username} 的数据...'):
        try:
            # 构建请求
            url = f"https://api.tikhub.io/api/v1/{platform}/app/v3/fetch_user_post_videos_v3"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "unique_id": username if platform == "tiktok" else username,
                "count": 10
            }
            
            # 发送请求
            response = requests.get(url, params=payload, headers=headers, timeout=30)
            
            # 检查响应
            if response.status_code == 200:
                result = response.json()
                
                # 检查业务状态码
                if result.get('code') == 200 or result.get('status_code') == 0:
                    st.success("✅ 数据获取成功！")
                    
                    # 解析数据
                    data_content = result.get('data', {})
                    video_list = data_content.get('aweme_list', [])
                    
                    if not video_list:
                        st.warning("⚠️ 未找到视频数据，请检查账号是否正确或是否为私密账号")
                        st.stop()
                    
                    # 构建 DataFrame
                    rows = []
                    for video in video_list:
                        stats = video.get('statistics', {})
                        author = video.get('author', {})
                        
                        # 转换时间戳
                        create_time = video.get('create_time', 0)
                        date_str = datetime.fromtimestamp(create_time).strftime('%Y-%m-%d %H:%M')
                        
                        row = {
                            '发布时间': date_str,
                            '视频描述': (video.get('desc', '')[:50] + '...') if video.get('desc') else '无描述',
                            '播放量': stats.get('play_count', 0),
                            '点赞数': stats.get('digg_count', 0),
                            '评论数': stats.get('comment_count', 0),
                            '分享数': stats.get('share_count', 0),
                            '收藏数': stats.get('collect_count', 0),
                            '视频链接': video.get('share_url', ''),
                            '作者昵称': author.get('nickname', ''),
                            '作者 ID': author.get('unique_id', '')
                        }
                        rows.append(row)
                    
                    df = pd.DataFrame(rows)
                    
                    # 显示核心指标
                    st.subheader("📈 核心数据概览")
                    col1, col2, col3, col4 = st.columns(4)
                    total_play = df['播放量'].sum()
                    total_like = df['点赞数'].sum()
                    total_comment = df['评论数'].sum()
                    avg_play = int(df['播放量'].mean())
                    
                    col1.metric("总播放量", f"{total_play:,}")
                    col2.metric("总点赞数", f"{total_like:,}")
                    col3.metric("总评论数", f"{total_comment:,}")
                    col4.metric("平均播放", f"{avg_play:,}")
                    
                    # 显示数据表格
                    st.subheader("📋 视频数据明细")
                    st.dataframe(df, use_container_width=True)
                    
                    # 下载按钮
                    csv = df.to_csv(index=False).encode('utf-8-sig')
                    st.download_button(
                        label="📥 下载 CSV 数据",
                        data=csv,
                        file_name=f'{platform}_{username}_{datetime.now().strftime("%Y%m%d")}.csv',
                        mime='text/csv',
                    )
                    
                    # 简单图表
                    st.subheader("📊 视频表现图表")
                    chart_col1, chart_col2 = st.columns(2)
                    with chart_col1:
                        st.bar_chart(df.set_index('发布时间')['播放量'])
                    with chart_col2:
                        st.bar_chart(df.set_index('发布时间')['点赞数'])
                    
                else:
                    st.error(f"❌ API 返回错误：{result.get('message', '未知错误')}")
                    st.json(result)
            else:
                st.error(f"❌ 请求失败：状态码 {response.status_code}")
                st.text(response.text[:500])
                
        except Exception as e:
            st.error(f"❌ 程序错误：{str(e)}")
            st.info("💡 建议：检查 API Key 是否正确，或联系支持团队")

# 页脚
st.markdown("---")
st.caption("🛠️ powered by TikHub API & Streamlit | 数据仅供参考")
