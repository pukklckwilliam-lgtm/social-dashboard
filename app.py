# 🎯 TikHub 社媒数据监控看板 - 完整版
import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import json

# 页面配置
st.set_page_config(page_title="📊 TikHub 社媒监控看板", layout="wide", page_icon="📈")

# ============================================
# 🔑 API Key 管理
# ============================================
def get_api_key():
    # 优先从 Streamlit Secrets 读取
    if "tikhub_api_key" in st.secrets:
        return st.secrets["tikhub_api_key"]
    
    # 从侧边栏输入
    with st.sidebar:
        api_key = st.text_input("🔑 TikHub API Key", type="password", 
                               help="在 TikHub 后台获取 API Key")
        if api_key:
            st.session_state["api_key"] = api_key
            st.success("✅ API Key 已保存（本次会话）")
        elif "api_key" in st.session_state:
            api_key = st.session_state["api_key"]
            st.success("✅ API Key 已加载（本次会话）")
    
    return api_key if 'api_key' in locals() else None

# ============================================
# 📡 数据抓取函数
# ============================================
def fetch_tiktok_data(api_key, username):
    """从 TikHub 获取 TikTok 视频数据"""
    url = "https://api.tikhub.io/api/v1/tiktok/app/v3/fetch_user_post_videos_v3"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    params = {
        "unique_id": username,
        "count": 10
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"HTTP {response.status_code}", "details": response.text[:300]}
    except Exception as e:
        return {"error": f"请求失败：{str(e)}"}

# ============================================
# 📊 数据解析函数
# ============================================
def parse_video_data(result):
    """解析 TikHub 返回的视频数据"""
    if 'data' not in result or 'aweme_list' not in result['data']:
        return [], {}
    
    video_list = result['data']['aweme_list']
    rows = []
    
    # 统计总数
    total_stats = {'play': 0, 'like': 0, 'comment': 0, 'share': 0}
    
    for video in video_list:
        stats = video.get('statistics', {})
        author = video.get('author', {})
        
        # 时间转换
        create_time = video.get('create_time', 0)
        if create_time:
            date_str = datetime.fromtimestamp(create_time).strftime('%Y-%m-%d %H:%M')
        else:
            date_str = 'N/A'
        
        # 提取统计数据
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
            '视频链接': video.get('share_url', '')
        })
    
    return rows, total_stats

# ============================================
# 🎨 主界面
# ============================================
def main():
    st.title("📊 TikHub 社媒数据监控看板")
    st.markdown("*支持 TikTok 视频数据分析*")
    
    # 获取 API Key
    api_key = get_api_key()
    
    if not api_key:
        st.warning("⚠️ **请先配置 API Key！**\n\n在左侧侧边栏输入你的 TikHub API Key")
        st.stop()
    
    # 侧边栏配置
    with st.sidebar:
        st.header("⚙️ 配置")
        username = st.text_input("TikTok 用户名", placeholder="例如：photorevive.ai", value="photorevive.ai")
        
        if st.button("🚀 获取数据", type="primary", use_container_width=True):
            st.session_state['fetch_data'] = True
    
    # 抓取数据
    if st.session_state.get('fetch_data', False):
        st.session_state['fetch_data'] = False
        
        if not username:
            st.error("❌ 请输入用户名")
            st.stop()
        
        with st.spinner(f'正在抓取 @{username} 的数据...'):
            result = fetch_tiktok_data(api_key, username)
            
            if 'error' in result:
                st.error(f"❌ {result['error']}")
                if 'details' in result:
                    st.text(result['details'])
            else:
                st.success("✅ 数据获取成功！")
                
                # 显示原始数据（可折叠）
                with st.expander("📄 查看原始 JSON 数据", expanded=False):
                    st.json(result)
                
                # 解析数据
                rows, total_stats = parse_video_data(result)
                
                if not rows:
                    st.warning("⚠️ 未找到视频数据，请检查账号是否正确")
                else:
                    df = pd.DataFrame(rows)
                    
                    # === 核心数据概览 ===
                    st.subheader(f"📈 @{username} 的核心数据概览 (最近 {len(rows)} 条视频)")
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
                    
                    # === 数据表格 ===
                    st.subheader("📋 视频详细列表")
                    st.dataframe(df, use_container_width=True, hide_index=True)
                    
                    # === 图表 ===
                    st.subheader("📊 视频表现趋势")
                    chart_col1, chart_col2 = st.columns(2)
                    with chart_col1:
                        st.bar_chart(df.set_index('发布时间')['播放量'], use_container_width=True)
                    with chart_col2:
                        st.bar_chart(df.set_index('发布时间')['点赞数'], use_container_width=True)
                    
                    # === 下载按钮 ===
                    st.divider()
                    col1, col2 = st.columns(2)
                    with col1:
                        csv = df.to_csv(index=False).encode('utf-8-sig')
                        st.download_button(
                            label="📥 下载 CSV 数据",
                            data=csv,
                            file_name=f'tiktok_{username}_{datetime.now().strftime("%Y%m%d")}.csv',
                            mime='text/csv',
                            use_container_width=True
                        )
                    with col2:
                        json_str = json.dumps(result, indent=2, ensure_ascii=False)
                        st.download_button(
                            label="📥 下载完整 JSON",
                            data=json_str,
                            file_name=f'tiktok_{username}_{datetime.now().strftime("%Y%m%d")}.json',
                            mime='application/json',
                            use_container_width=True
                        )

# ============================================
# 页脚
# ============================================
st.markdown("---")
st.caption("🛠️ powered by TikHub API & Streamlit | 数据仅供参考")

if __name__ == "__main__":
    main()
