# 🎵 TikTok数据监控看板 - 修复版
import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import json

st.set_page_config(page_title="🎵 TikTok数据监控", layout="wide", page_icon="🎵")

# ============================================
# 🔑 API Key 管理（修复版）
# ============================================
def get_api_key():
    """安全获取 API Key"""
    api_key = None
    
    # 尝试从 Secrets 读取（带异常处理）
    try:
        if hasattr(st, 'secrets') and "tikhub_api_key" in st.secrets:
            api_key = st.secrets["tikhub_api_key"]
            st.sidebar.success("✅ API Key 已从 Secrets 加载")
    except Exception:
        pass  # Secrets 不存在或格式错误，忽略
    
    # 从侧边栏读取
    if not api_key:
        with st.sidebar:
            api_key = st.text_input("🔑 TikHub API Key", type="password",
                                  help="在 TikHub 后台获取 API Key")
            if api_key:
                st.session_state["api_key"] = api_key
                st.sidebar.success("✅ API Key 已保存（本次会话）")
            elif "api_key" in st.session_state:
                api_key = st.session_state["api_key"]
                st.sidebar.success("✅ API Key 已加载（本次会话）")
    
    return api_key

# ============================================
# 📡 数据抓取函数
# ============================================
def fetch_tiktok_data(api_key, username, count=10):
    """从 TikHub 获取 TikTok 视频数据"""
    url = "https://api.tikhub.io/api/v1/tiktok/app/v3/fetch_user_post_videos_v3"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    params = {
        "unique_id": username,
        "count": count
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('code') == 200 or 'data' in result:
                return {"success": True, "data": result}
            else:
                return {"success": False, "error": result.get('message', 'API返回错误')}
        else:
            return {"success": False, "error": f"HTTP {response.status_code}", 
                    "details": response.text[:300]}
    except Exception as e:
        return {"success": False, "error": f"请求异常：{str(e)}"}

# ============================================
# 📊 数据解析
# ============================================
def parse_tiktok_data(result, username):
    """解析 TikTok 视频数据"""
    if 'data' not in result or 'aweme_list' not in result['data']:
        return [], {}, {}
    
    video_list = result['data']['aweme_list']
    rows = []
    total_stats = {'play': 0, 'like': 0, 'comment': 0, 'share': 0}
    
    account_info = {}
    if video_list and 'author' in video_list[0]:
        author = video_list[0]['author']
        account_info = {
            'nickname': author.get('nickname', username),
            'unique_id': author.get('unique_id', username),
            'follower_count': author.get('follower_count', 0),
            'total_favorited': author.get('total_favorited', 0),
            'signature': author.get('signature', '')
        }
    
    for video in video_list:
        stats = video.get('statistics', {})
        create_time = video.get('create_time', 0)
        date_str = datetime.fromtimestamp(create_time).strftime('%Y-%m-%d %H:%M') if create_time else 'N/A'
        
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
    
    return rows, total_stats, account_info

# ============================================
# 🎨 主界面
# ============================================
def main():
    st.title("🎵 TikTok数据监控看板")
    st.markdown("*支持任意公开账号数据抓取*")
    
    # 获取 API Key
    api_key = get_api_key()
    
    if not api_key:
        st.warning("⚠️ **请先配置 API Key！**\n\n在左侧侧边栏输入你的 TikHub API Key")
        st.stop()
    
    # 侧边栏配置
    with st.sidebar:
        st.header("⚙️ 配置")
        username = st.text_input("TikTok 用户名", placeholder="photorevive.ai", value="photorevive.ai")
        count = st.slider("抓取数量", min_value=1, max_value=30, value=10)
        
        st.divider()
        
        if st.button("🚀 获取数据", type="primary", use_container_width=True):
            st.session_state['fetch_data'] = True
    
    # 抓取数据
    if st.session_state.get('fetch_data', False):
        st.session_state['fetch_data'] = False
        
        if not username:
            st.error("❌ 请输入用户名")
            st.stop()
        
        with st.spinner(f'正在抓取 @{username} 的数据...'):
            result = fetch_tiktok_data(api_key, username, count)
            
            if not result['success']:
                st.error(f"❌ {result['error']}")
                if 'details' in result:
                    with st.expander("🔍 查看详细错误"):
                        st.text(result['details'])
                
                st.info("""
                **💡 排查建议：**
                1. 检查 API Key 是否正确（在 TikHub 后台验证）
                2. 检查账户余额是否充足
                3. 检查是否已开通 TikTok API 权限
                4. 联系 TikHub 客服：https://discord.gg/aMEAS8Xsvz
                """)
            else:
                st.success("✅ 数据获取成功！")
                
                # 解析数据
                rows, total_stats, account_info = parse_tiktok_data(result['data'], username)
                
                if not rows:
                    st.warning("⚠️ 未找到视频数据，请检查账号是否正确")
                else:
                    # 账号信息
                    if account_info:
                        st.subheader(f"👤 @{account_info.get('unique_id')}")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("粉丝数", f"{account_info.get('follower_count', 0):,}")
                        with col2:
                            st.metric("总获赞", f"{account_info.get('total_favorited', 0):,}")
                        with col3:
                            st.metric("视频数", len(rows))
                    
                    st.divider()
                    
                    # 核心指标
                    st.subheader(f"📈 核心数据概览 (最近 {len(rows)} 条视频)")
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
                    
                    # 数据表格
                    df = pd.DataFrame(rows)
                    st.dataframe(df, use_container_width=True, hide_index=True)
                    
                    # 图表
                    st.subheader("📊 视频表现趋势")
                    st.bar_chart(df.set_index('发布时间')['播放量'], use_container_width=True)
                    
                    # 下载按钮
                    st.divider()
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
