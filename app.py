import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# 页面配置
st.set_page_config(page_title="📊 TikHub 社媒监控看板", layout="wide", page_icon="📈")

# ============================================
# 🔑 API Key 获取函数（自动保存，不用每次输入）
# ============================================
def get_api_key():
    # 优先从 Streamlit Secrets 读取（最安全）
    if "tikhub_api_key" in st.secrets:
        st.sidebar.success("✅ API Key 已自动加载")
        return st.secrets["tikhub_api_key"]
    
    # 备用：从侧边栏输入
    with st.sidebar:
        api_key = st.text_input("TikHub API Key", type="password", help="在 TikHub 后台获取")
        if api_key:
            st.session_state["api_key"] = api_key
            st.sidebar.success("✅ API Key 已保存（本次会话）")
        elif "api_key" in st.session_state:
            api_key = st.session_state["api_key"]
            st.sidebar.success("✅ API Key 已加载（本次会话）")
    
    return api_key if 'api_key' in locals() else None

# ============================================
# 📡 数据抓取函数
# ============================================
def fetch_tiktok_data(api_key, username):
    url = "https://api.tikhub.io/api/v1/tiktok/app/v3/fetch_user_post_videos_v3"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "unique_id": username,
        "count": 10
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"HTTP {response.status_code}", "details": response.text[:500]}
    except Exception as e:
        return {"error": "请求失败", "details": str(e)}

# ============================================
# 📊 数据解析函数
# ============================================
def parse_video_data(result):
    if 'data' not in result or 'aweme_list' not in result['data']:
        return []
    
    video_list = result['data']['aweme_list']
    rows = []
    
    for video in video_list:
        stats = video.get('statistics', {})
        author = video.get('author', {})
        
        # 时间转换
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
        }
        rows.append(row)
    
    return rows

# ============================================
# 🎨 主界面
# ============================================
def main():
    st.title("📊 TikHub 社媒数据监控看板")
    st.markdown("*支持 TikTok • Instagram • Facebook • YouTube • X*")
    
    # 获取 API Key
    api_key = get_api_key()
    
    if not api_key:
        st.warning("⚠️ **请先配置 API Key！**\n\n在左侧侧边栏输入你的 TikHub API Key")
        st.stop()
    
    # 输入区域
    col1, col2 = st.columns([3, 1])
    with col1:
        username = st.text_input("TikTok 用户名", placeholder="例如：photorevive.ai", value="photorevive.ai")
    with col2:
        st.write("")
        st.write("")
        if st.button("🚀 开始监控", type="primary", use_container_width=True):
            st.session_state['fetch_data'] = True
    
    # 抓取数据
    if st.session_state.get('fetch_data', False):
        with st.spinner(f'正在抓取 @{username} 的数据...'):
            result = fetch_tiktok_data(api_key, username)
            st.session_state['fetch_data'] = False
            
            if 'error' in result:
                st.error(f"❌ {result['error']}")
                st.text(result.get('details', ''))
            else:
                st.success("✅ 数据获取成功！")
                
                # 解析数据
                rows = parse_video_data(result)
                
                if not rows:
                    st.warning("⚠️ 未找到视频数据，请检查账号是否正确")
                else:
                    df = pd.DataFrame(rows)
                    
                    # 核心数据概览
                    st.subheader(f"📈 @{username} 的核心数据概览 (最近 10 条视频)")
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("总播放量", f"{df['播放量'].sum():,}")
                    with col2:
                        st.metric("总点赞数", f"{df['点赞数'].sum():,}")
                    with col3:
                        st.metric("总评论数", f"{df['评论数'].sum():,}")
                    with col4:
                        st.metric("平均播放", f"{int(df['播放量'].mean()):,}")
                    
                    st.divider()
                    
                    # 数据表格
                    st.subheader("📋 视频详细列表")
                    st.dataframe(df, use_container_width=True, hide_index=True)
                    
                    # 图表
                    st.subheader("📊 视频表现趋势")
                    chart_col1, chart_col2 = st.columns(2)
                    with chart_col1:
                        st.bar_chart(df.set_index('发布时间')['播放量'], use_container_width=True)
                    with chart_col2:
                        st.bar_chart(df.set_index('发布时间')['点赞数'], use_container_width=True)
                    
                    # 下载按钮
                    csv = df.to_csv(index=False).encode('utf-8-sig')
                    st.download_button(
                        label="📥 下载 CSV 数据",
                        data=csv,
                        file_name=f'tiktok_{username}_{datetime.now().strftime("%Y%m%d")}.csv',
                        mime='text/csv',
                        use_container_width=True
                    )

# ============================================
# 页脚
# ============================================
st.markdown("---")
st.caption("🛠️ powered by TikHub API & Streamlit | 数据仅供参考")

if __name__ == "__main__":
    main()
