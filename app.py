# 🎯 社媒数据监控看板 - 修复版
import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import json

st.set_page_config(page_title="📊 TikHub 社媒监控看板", layout="wide", page_icon="📈")

# 侧边栏配置
st.sidebar.title("⚙️ 设置")

# API Key 管理
if "tikhub_api_key" in st.secrets:
    api_key = st.secrets["tikhub_api_key"]
    st.sidebar.success("✅ API Key 已自动加载")
else:
    api_key = st.sidebar.text_input("TikHub API Key", type="password")
    if api_key:
        st.session_state["api_key"] = api_key

if not api_key and "api_key" in st.session_state:
    api_key = st.session_state["api_key"]

platform = st.sidebar.selectbox("平台", ["tiktok", "instagram", "facebook", "youtube", "twitter"])
data_type = st.sidebar.selectbox(
    "数据类型",
    ["视频列表", "用户信息", "评论数据", "粉丝列表"]
)
username = st.sidebar.text_input("账号用户名", placeholder="例如：photorevive.ai")

# 主界面
st.title("📊 TikHub 社媒数据监控看板")
st.markdown(f"*当前：**{platform} / @{username} / {data_type}*")

# 数据获取函数
def fetch_data(api_key, platform, data_type, username):
    """获取数据 - 支持多种接口"""
    
    # 接口映射配置
    interface_config = {
        "tiktok": {
            "视频列表": {
                "endpoint": "/api/v1/tiktok/app/v3/fetch_user_post_videos_v3",
                "params": {"unique_id": username, "count": 10}
            },
            "用户信息": {
                "endpoint": "/api/v1/tiktok/web/fetch_user_profile",
                "params": {"unique_id": username}
            }
        }
    }
    
    config = interface_config.get(platform, {}).get(data_type)
    if not config:
        return {"error": f"暂不支持 {platform} 的 {data_type}"}
    
    url = f"https://api.tikhub.io{config['endpoint']}"
    headers = {"Authorization": f"Bearer {api_key}"}
    params = config['params']
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"HTTP {response.status_code}", "details": response.text[:300]}
    except Exception as e:
        return {"error": f"请求失败: {str(e)}"}

# 数据清洗函数 - 处理 JSON 键名中的空格
def clean_keys(obj):
    """递归清理 JSON 键名中的空格"""
    if isinstance(obj, dict):
        return {k.strip(): clean_keys(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_keys(item) for item in obj]
    return obj

# 数据显示函数
def display_data(result, data_type):
    """根据数据类型显示数据"""
    
    # 清理 JSON 键名
    clean_result = clean_keys(result)
    
    if data_type == "视频列表":
        # 修复：正确处理数据路径
        data_content = clean_result.get('data', {})
        video_list = data_content.get('aweme_list', [])
        
        if not video_list:
            st.warning("⚠️ 未找到视频数据")
            return
        
        st.success(f"✅ 找到 {len(video_list)} 个视频")
        
        # 提取核心数据
        rows = []
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
                '作者': author.get('nickname', author.get('unique_id', 'N/A'))
            })
        
        # 显示核心指标
        st.subheader(f"📈 核心数据概览")
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
        
        # 显示数据表格
        st.subheader("📋 视频详细列表")
        df = pd.DataFrame(rows)
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
            file_name=f'{platform}_{username}_{datetime.now().strftime("%Y%m%d")}.csv',
            mime='text/csv',
            use_container_width=True
        )
    
    elif data_type == "用户信息":
        user = clean_result.get('data', {})
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
        else:
            st.warning("⚠️ 未找到用户信息")
    
    else:
        st.info("ℹ️ 该数据类型暂不支持详细展示，请查看上方原始 JSON")

# 主逻辑
if st.button("🚀 获取数据", type="primary", use_container_width=True):
    if not api_key:
        st.error("❌ 请先在侧边栏输入 API Key")
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
            
            # 显示原始 JSON（可折叠）
            with st.expander("📄 查看原始 JSON", expanded=False):
                st.json(result)
            
            # 显示数据
            try:
                display_data(result, data_type)
            except Exception as e:
                st.error(f"❌ 数据显示错误：{str(e)}")
                st.info("💡 请查看上方原始 JSON，确认数据结构是否正确")

# 页脚
st.markdown("---")
st.caption("🛠️ powered by TikHub API & Streamlit | 数据仅供参考")
