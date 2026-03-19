import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# 页面配置 - 使用宽布局
st.set_page_config(page_title="📊 TikHub 社媒监控看板", layout="wide", page_icon="📈")

# 标题
st.title("📊 TikHub 社媒数据监控看板")
st.markdown("*支持 TikTok • Instagram • Facebook • YouTube • X*")

# 侧边栏配置
with st.sidebar:
    st.header("⚙️ 设置")
    api_key = st.text_input("TikHub API Key", type="password", help="在 TikHub 后台获取")
    platform = st.selectbox("选择平台", ["tiktok", "instagram", "facebook", "youtube", "twitter"])

# 主输入区域
col1, col2 = st.columns([3, 1])
with col1:
    username = st.text_input("TikTok 用户名", placeholder="例如：photorevive.ai", value="photorevive.ai")
with col2:
    st.write("")  # 占位
    st.write("")  # 占位
    fetch_button = st.button("🚀 开始监控", type="primary", use_container_width=True)

# 获取数据
if fetch_button:
    if not api_key:
        st.error("❌ 请先在侧边栏输入 API Key")
        st.stop()
    if not username:
        st.error("❌ 请输入用户名")
        st.stop()
    
    with st.spinner(f'正在抓取 @{username} 的数据...'):
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
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                
                # 清洗 JSON 键名中的空格
                def clean_keys(obj):
                    if isinstance(obj, dict):
                        return {k.strip(): clean_keys(v) for k, v in obj.items()}
                    elif isinstance(obj, list):
                        return [clean_keys(item) for item in obj]
                    return obj
                
                clean_result = clean_keys(result)
                
                if clean_result.get('code') == 200:
                    st.success("✅ 数据获取成功！")
                    
                    # 提取数据
                    data_content = clean_result.get('data', {})
                    video_list = data_content.get('aweme_list', [])
                    
                    if not video_list:
                        st.warning("⚠️ 未找到视频数据")
                        st.stop()
                    
                    # 构建 DataFrame
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
                        })
                    
                    df = pd.DataFrame(rows)
                    
                    # === 修复布局问题：使用完整的宽度 ===
                    
                    # 1. 核心数据概览 - 使用完整宽度
                    st.subheader(f"📈 @{username} 的核心数据概览 (最近 10 条视频)")
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("总播放量", f"{total_stats['play']:,}")
                    with col2:
                        st.metric("总点赞数", f"{total_stats['like']:,}")
                    with col3:
                        st.metric("总评论数", f"{total_stats['comment']:,}")
                    with col4:
                        st.metric("总分享数", f"{total_stats['share']:,}")
                    
                    st.divider()
                    
                    # 2. 详细数据表格 - 使用完整宽度
                    st.subheader("📋 视频详细列表")
                    st.dataframe(df, use_container_width=True, hide_index=True)
                    
                    # 3. 图表 - 使用完整宽度
                    st.subheader("📊 视频表现趋势")
                    chart_col1, chart_col2 = st.columns(2)
                    with chart_col1:
                        st.bar_chart(df.set_index('发布时间')['播放量'], use_container_width=True)
                    with chart_col2:
                        st.bar_chart(df.set_index('发布时间')['点赞数'], use_container_width=True)
                    
                    # 4. 下载按钮
                    csv = df.to_csv(index=False).encode('utf-8-sig')
                    st.download_button(
                        label="📥 下载 CSV 数据",
                        data=csv,
                        file_name=f'{platform}_{username}_{datetime.now().strftime("%Y%m%d")}.csv',
                        mime='text/csv',
                        use_container_width=True
                    )
                    
                else:
                    st.error(f"❌ API 返回错误：{clean_result.get('message', '未知错误')}")
                    with st.expander("查看原始返回数据"):
                        st.json(clean_result)
            else:
                st.error(f"❌ 请求失败：HTTP {response.status_code}")
                st.text(response.text[:500])
                
        except Exception as e:
            st.error(f"❌ 程序错误：{str(e)}")
            st.info("💡 建议：检查 API Key 是否正确，或联系支持团队")

# 页脚
st.markdown("---")
st.caption("🛠️ powered by TikHub API & Streamlit | 数据仅供参考")
