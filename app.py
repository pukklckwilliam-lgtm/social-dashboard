import streamlit as st
import req# 🎯 社媒数据监控看板 - 多接口支持版
import streamlit as st
import requests
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="📊 TikHub 社媒监控看板", layout="wide", page_icon="📈")

# 侧边栏配置
with st.sidebar:
    st.header("⚙️ 设置")
    
    # API Key（支持 Secrets）
    if "tikhub_api_key" in st.secrets:
        api_key = st.secrets["tikhub_api_key"]
        st.success("✅ API Key 已自动加载")
    else:
        api_key = st.text_input("TikHub API Key", type="password")
    
    # 平台选择
    platform = st.selectbox("平台", ["tiktok", "instagram", "facebook", "youtube", "twitter"])
    
    # 🔥 新增：数据类型选择
    data_type = st.selectbox(
        "数据类型",
        [
            "视频列表",           # fetch_user_post_videos_v3
            "用户信息",           # fetch_user_profile / user/info
            "评论数据",           # fetch_video_comments
            "粉丝列表",           # fetch_user_followers
        ]
    )
    
    # 账号输入
    username = st.text_input("账号用户名", placeholder="例如：photorevive.ai")

# 主界面
st.title("📊 TikHub 社媒数据监控看板")
st.markdown(f"*当前：**{platform}** / **@{username}** / **{data_type}** *")

# 接口映射配置
INTERFACE_CONFIG = {
    "tiktok": {
        "视频列表": {
            "endpoint": "/api/v1/tiktok/app/v3/fetch_user_post_videos_v3",
            "params": {"unique_id": None, "count": 10},
            "method": "GET"
        },
        "用户信息": {
            "endpoint": "/api/v1/tiktok/web/fetch_user_profile",
            "params": {"unique_id": None},
            "method": "GET"
        },
        "评论数据": {
            "endpoint": "/api/v1/tiktok/app/v3/fetch_video_comments",
            "params": {"aweme_id": None, "count": 20},
            "method": "GET",
            "note": "⚠️ 需要先获取视频 ID"
        },
        "粉丝列表": {
            "endpoint": "/api/v1/tiktok/app/v3/fetch_user_followers",
            "params": {"unique_id": None, "count": 20},
            "method": "GET"
        }
    },
    # 其他平台可类似扩展...
}

# 获取数据函数
def fetch_data(api_key, platform, data_type, username, extra_params=None):
    config = INTERFACE_CONFIG.get(platform, {}).get(data_type)
    if not config:
        return {"error": f"暂不支持 {platform} 的 {data_type}"}
    
    url = f"https://api.tikhub.io{config['endpoint']}"
    headers = {"Authorization": f"Bearer {api_key}"}
    
    # 构建参数
    params = config['params'].copy()
    for k, v in params.items():
        if v is None and username:
            params[k] = username
    if extra_params:
        params.update(extra_params)
    
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
        return {"error": f"请求失败: {str(e)}"}

# 主逻辑
if st.button("🚀 获取数据", type="primary", use_container_width=True):
    if not api_key:
        st.error("❌ 请先输入 API Key")
        st.stop()
    if not username:
        st.error("❌ 请输入账号用户名")
        st.stop()
    
    with st.spinner(f'正在获取 {data_type}...'):
        result = fetch_data(api_key, platform, data_type, username)
        
        if 'error' in result:
            st.error(f"❌ {result['error']}")
            if 'details' in result:
                st.text(result['details'])
        else:
            st.success("✅ 获取成功！")
            
            # 🔍 调试：显示原始数据（可折叠）
            with st.expander("📄 查看原始 JSON", expanded=False):
                st.json(result)
            
            # 📊 智能解析并展示
            display_data(result, data_type)

# 数据展示函数
def display_data(result, data_type):
    if data_type == "视频列表":
        videos = result.get('data', {}).get('aweme_list', [])
        if videos:
            st.subheader(f"📹 找到 {len(videos)} 个视频")
            
            # 提取核心字段
            rows = []
            for v in videos:
                stats = v.get('statistics', {})
                rows.append({
                    '发布时间': datetime.fromtimestamp(v.get('create_time', 0)).strftime('%Y-%m-%d'),
                    '描述': (v.get('desc', '')[:40] + '...') if v.get('desc') else '无描述',
                    '播放量': stats.get('play_count', 0),
                    '点赞数': stats.get('digg_count', 0),
                    '评论数': stats.get('comment_count', 0),
                    '分享数': stats.get('share_count', 0),
                })
            
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True)
            
            # 简单图表
            col1, col2 = st.columns(2)
            with col1:
                st.bar_chart(df.set_index('发布时间')['播放量'])
            with col2:
                st.bar_chart(df.set_index('发布时间')['点赞数'])
    
    elif data_type == "用户信息":
        user = result.get('data', {})
        if user:
            st.subheader("👤 用户信息")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("用户名", user.get('unique_id', user.get('username', 'N/A')))
            with col2:
                st.metric("昵称", user.get('nickname', user.get('display_name', 'N/A')))
            with col3:
                st.metric("已认证", "✅" if user.get('verified', False) else "❌")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("粉丝数", f"{user.get('follower_count', user.get('followers', 0)):,}")
            with col2:
                st.metric("关注数", f"{user.get('following_count', user.get('following', 0)):,}")
            with col3:
                st.metric("总获赞", f"{user.get('total_favorited', user.get('heart_count', 0)):,}")
    
    elif data_type == "评论数据":
        comments = result.get('data', {}).get('comments', [])
        if comments:
            st.subheader(f"💬 找到 {len(comments)} 条评论")
            for c in comments[:10]:  # 只显示前 10 条
                st.write(f"**@{c.get('user', {}).get('unique_id', 'unknown')}**: {c.get('text', '')[:100]}")
    
    else:
        st.info("ℹ️ 该数据类型暂不支持详细展示，请查看上方原始 JSON")

# 页脚
st.markdown("---")
st.caption("🛠️ powered by TikHub API | 支持多接口 • 多平台")
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
    
    params = {
        "unique_id": username,
        "count": 10
    }
    
    try:
        # 使用 GET 请求
        response = requests.get(url, params=params, headers=headers, timeout=30)
        
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
