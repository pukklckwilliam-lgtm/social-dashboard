# 🎯 多平台社媒数据监控看板 - 完整版
# 支持：TikTok • Instagram • YouTube • X(Twitter)
import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import json

# 页面配置
st.set_page_config(page_title="📊 多平台社媒监控看板", layout="wide", page_icon="📈")

# ============================================
# 🔑 API Key 管理（支持 Streamlit Secrets）
# ============================================
def get_api_key():
    if "tikhub_api_key" in st.secrets:
        st.sidebar.success("✅ API Key 已自动加载")
        return st.secrets["tikhub_api_key"]
    
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
# 🌐 平台与接口配置
# ============================================
PLATFORM_CONFIG = {
    "TikTok": {
        "视频列表": {
            "endpoint": "/api/v1/tiktok/app/v3/fetch_user_post_videos_v3",
            "method": "GET",
            "param_name": "unique_id",
            "data_path": ["data", "aweme_list"]
        },
        "用户信息": {
            "endpoint": "/api/v1/tiktok/web/fetch_user_profile",
            "method": "GET",
            "param_name": "unique_id",
            "data_path": ["data"]
        }
    },
    "Instagram": {
        "Reels 视频": {
            "endpoint": "/api/v1/instagram/v3/get_user_reels",
            "method": "GET",
            "param_name": "user_id",
            "data_path": ["data", "items"]
        },
        "Posts 帖子": {
            "endpoint": "/api/v1/instagram/v3/get_user_posts",
            "method": "GET",
            "param_name": "user_id",
            "data_path": ["data", "items"]
        },
        "主页信息": {
            "endpoint": "/api/v1/instagram/v3/get_user_profile",
            "method": "GET",
            "param_name": "user_id",
            "data_path": ["data"]
        }
    },
    "YouTube": {
        "频道视频": {
            "endpoint": "/api/v1/youtube/web/get_channel_videos_v2",
            "method": "GET",
            "param_name": "channel_id",
            "data_path": ["data", "items"]
        }
    },
    "X (Twitter)": {
        "用户资料": {
            "endpoint": "/api/v1/twitter/web/fetch_user_profile",
            "method": "GET",
            "param_name": "username",
            "data_path": ["data"]
        }
    }
}

# ============================================
# 📡 API 请求函数
# ============================================
def fetch_data(api_key, platform, data_type, username):
    """通用数据获取函数"""
    config = PLATFORM_CONFIG.get(platform, {}).get(data_type)
    if not config:
        return {"error": f"暂不支持 {platform} 的 {data_type}"}
    
    url = f"https://api.tikhub.io{config['endpoint']}"
    headers = {"Authorization": f"Bearer {api_key}"}
    
    # 构建参数
    param_name = config['param_name']
    params = {param_name: username}
    
    # 添加默认参数
    if data_type in ["视频列表", "Reels 视频", "Posts 帖子", "频道视频"]:
        params["count"] = 10
    
    try:
        if config['method'] == "GET":
            response = requests.get(url, params=params, headers=headers, timeout=30)
        else:
            response = requests.post(url, json=params, headers=headers, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"HTTP {response.status_code}", "details": response.text[:300]}
    except Exception as e:
        return {"error": f"请求失败：{str(e)}"}

# ============================================
# 🔍 数据解析函数
# ============================================
def parse_data(result, platform, data_type):
    """根据平台和数据类型解析数据"""
    config = PLATFORM_CONFIG.get(platform, {}).get(data_type)
    if not config:
        return []
    
    data_path = config['data_path']
    data = result
    
    # 按路径提取数据
    for key in data_path:
        if isinstance(data, dict) and key in data:
            data = data[key]
        else:
            return []
    
    if isinstance(data, list):
        return data
    elif isinstance(data, dict):
        return [data]
    return []

# ============================================
# 📊 数据展示函数
# ============================================
def display_data(data, platform, data_type, username):
    """根据数据类型展示数据"""
    
    if not data:
        st.warning("⚠️ 未找到数据")
        return
    
    # TikTok 视频列表
    if platform == "TikTok" and data_type == "视频列表":
        rows = []
        total_stats = {'play': 0, 'like': 0, 'comment': 0, 'share': 0}
        
        for video in data[:10]:  # 只显示前 10 条
            stats = video.get('statistics', {})
            create_time = video.get('create_time', 0)
            date_str = datetime.fromtimestamp(create_time).strftime('%Y-%m-%d') if create_time else 'N/A'
            
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
                '视频描述': (video.get('desc', '')[:40] + '...') if video.get('desc') else '无描述',
                '播放量': play_count,
                '点赞数': digg_count,
                '评论数': comment_count,
                '分享数': share_count,
            })
        
        # 核心指标
        st.subheader(f"📈 @{username} 的核心数据概览")
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
        st.dataframe(pd.DataFrame(rows), use_container_width=True)
        
        # 图表
        df = pd.DataFrame(rows)
        if not df.empty:
            st.subheader("📊 视频表现趋势")
            col1, col2 = st.columns(2)
            with col1:
                st.bar_chart(df.set_index('发布时间')['播放量'])
            with col2:
                st.bar_chart(df.set_index('发布时间')['点赞数'])
    
    # Instagram Reels/Posts
    elif platform == "Instagram":
        rows = []
        for item in data[:10]:
            rows.append({
                'ID': item.get('id', 'N/A'),
                '类型': item.get('media_type', 'N/A'),
                '时间戳': item.get('timestamp', 'N/A'),
                '点赞数': item.get('like_count', 0),
                '评论数': item.get('comments_count', 0),
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True)
    
    # YouTube 视频
    elif platform == "YouTube":
        rows = []
        for video in data[:10]:
            snippet = video.get('snippet', {})
            stats = video.get('statistics', {})
            rows.append({
                '标题': snippet.get('title', 'N/A')[:50],
                '发布时间': snippet.get('publishedAt', 'N/A')[:10],
                '观看数': stats.get('viewCount', 0),
                '点赞数': stats.get('likeCount', 0),
                '评论数': stats.get('commentCount', 0),
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True)
    
    # X (Twitter) 用户资料
    elif platform == "X (Twitter)":
        if data:
            user = data[0]
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("用户名", user.get('username', 'N/A'))
            with col2:
                st.metric("昵称", user.get('name', 'N/A'))
            with col3:
                st.metric("已认证", "✅" if user.get('verified', False) else "❌")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("粉丝数", f"{user.get('followers_count', 0):,}")
            with col2:
                st.metric("关注数", f"{user.get('following_count', 0):,}")
            with col3:
                st.metric("推文数", f"{user.get('tweet_count', 0):,}")
    
    # 其他数据类型 - 显示原始 JSON
    else:
        st.json(data[:5] if isinstance(data, list) else data)

# ============================================
# 🎨 主界面
# ============================================
def main():
    st.title("📊 多平台社媒数据监控看板")
    st.markdown("*支持 TikTok • Instagram • YouTube • X(Twitter)*")
    
    # 获取 API Key
    api_key = get_api_key()
    
    if not api_key:
        st.warning("⚠️ **请先配置 API Key！**\n\n在左侧侧边栏输入你的 TikHub API Key")
        st.stop()
    
    # 侧边栏配置
    with st.sidebar:
        st.header("⚙️ 配置")
        platform = st.selectbox("选择平台", list(PLATFORM_CONFIG.keys()))
        data_type = st.selectbox("数据类型", list(PLATFORM_CONFIG[platform].keys()))
        
        # 根据平台显示不同的输入提示
        param_name = PLATFORM_CONFIG[platform][data_type]['param_name']
        if param_name == "user_id":
            username = st.text_input("Instagram User ID", placeholder="数字 ID（如：123456789）")
        elif param_name == "channel_id":
            username = st.text_input("YouTube Channel", placeholder="@LinusTechTips 或频道 ID")
        else:
            username = st.text_input("用户名", placeholder="例如：photorevive.ai")
    
    # 主输入区域
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write(f"**当前查询：** {platform} / {data_type} / @{username}")
    with col2:
        if st.button("🚀 获取数据", type="primary", use_container_width=True):
            st.session_state['fetch_data'] = True
    
    # 获取并展示数据
    if st.session_state.get('fetch_data', False):
        st.session_state['fetch_data'] = False
        
        if not username:
            st.error("❌ 请输入用户名/ID")
            st.stop()
        
        with st.spinner(f'正在获取 {platform} 数据...'):
            result = fetch_data(api_key, platform, data_type, username)
            
            if 'error' in result:
                st.error(f"❌ {result['error']}")
                if 'details' in result:
                    st.text(result['details'])
            else:
                st.success("✅ 数据获取成功！")
                
                # 显示原始数据（可折叠）
                with st.expander("📄 查看原始 JSON", expanded=False):
                    st.json(result)
                
                # 解析并展示数据
                data = parse_data(result, platform, data_type)
                display_data(data, platform, data_type, username)
                
                # 下载按钮
                if data:
                    json_str = json.dumps(result, indent=2, ensure_ascii=False)
                    st.download_button(
                        label="📥 下载完整 JSON",
                        data=json_str,
                        file_name=f'{platform}_{username}_{datetime.now().strftime("%Y%m%d")}.json',
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
