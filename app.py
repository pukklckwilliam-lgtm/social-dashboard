# 🎵 TikTok数据监控看板 - TikHub 专业版
import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import json

st.set_page_config(page_title="🎵 TikTok数据监控", layout="wide", page_icon="🎵")

# ============================================
# 🔑 API Key 配置
# ============================================
def get_api_key():
    # 优先从 Secrets 读取
    if "tikhub_api_key" in st.secrets:
        return st.secrets["tikhub_api_key"]
    
    # 从侧边栏读取
    with st.sidebar:
        api_key = st.text_input("🔑 TikHub API Key", type="password", 
                               value="vpA5E99O82r1tnSpPrLOwkiJKgm9arlJ1AH7g2ulb9jmm12uGiejcCi/aA==",
                               help="在 TikHub 后台获取")
        if api_key:
            st.session_state["api_key"] = api_key
            st.success("✅ API Key 已保存")
        elif "api_key" in st.session_state:
            api_key = st.session_state["api_key"]
            st.success("✅ API Key 已加载")
    
    return api_key if 'api_key' in locals() else None

# ============================================
# 📡 API 请求函数（多端点尝试）
# ============================================
def fetch_tiktok_data(api_key, username, count=10):
    """尝试多个端点获取数据"""
    
    # 可能的端点列表
    endpoints = [
        {
            "name": "v3 GET",
            "url": "https://api.tikhub.io/api/v1/tiktok/app/v3/fetch_user_post_videos_v3",
            "method": "GET",
            "params": {"unique_id": username, "count": count},
            "json": None
        },
        {
            "name": "v3 POST",
            "url": "https://api.tikhub.io/api/v1/tiktok/app/v3/fetch_user_post_videos_v3",
            "method": "POST",
            "params": None,
            "json": {"unique_id": username, "count": count}
        },
        {
            "name": "web 端点",
            "url": "https://api.tikhub.io/api/v1/tiktok/web/fetch_user_profile",
            "method": "GET",
            "params": {"unique_id": username},
            "json": None
        }
    ]
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    errors = []
    
    # 尝试每个端点
    for endpoint in endpoints:
        try:
            if endpoint["method"] == "GET":
                response = requests.get(
                    endpoint["url"],
                    params=endpoint["params"],
                    headers=headers,
                    timeout=30
                )
            else:
                response = requests.post(
                    endpoint["url"],
                    json=endpoint["json"],
                    headers=headers,
                    timeout=30
                )
            
            if response.status_code == 200:
                result = response.json()
                # 检查响应码
                if result.get('code') == 200 or 'data' in result:
                    return {
                        "success": True, 
                        "data": result,
                        "endpoint": endpoint["name"]
                    }
            
            errors.append(f"{endpoint['name']}: HTTP {response.status_code}")
            
        except Exception as e:
            errors.append(f"{endpoint['name']}: {str(e)}")
    
    # 所有端点都失败
    return {
        "success": False, 
        "error": "所有端点都失败",
        "details": "\n".join(errors)
    }

# ============================================
# 📊 数据解析
# ============================================
def parse_data(result):
    """解析 TikHub 返回的数据"""
    data = result.get('data', {})
    
    # 尝试不同的数据结构
    video_list = data.get('aweme_list', data.get('videos', data.get('items', [])))
    
    if isinstance(video_list, dict):
        video_list = list(video_list.values())
    
    rows = []
    total_stats = {'play': 0, 'like': 0, 'comment': 0, 'share': 0}
    
    account_info = {}
    
    for video in video_list[:10]:  # 最多10条
        # 提取统计数据（尝试多种字段名）
        stats = video.get('statistics', video.get('stats', {}))
        
        play_count = stats.get('play_count', stats.get('view_count', stats.get('views', 0)))
        digg_count = stats.get('digg_count', stats.get('like_count', stats.get('likes', 0)))
        comment_count = stats.get('comment_count', stats.get('comments', 0))
        share_count = stats.get('share_count', stats.get('shares', 0))
        
        total_stats['play'] += int(play_count) if play_count else 0
        total_stats['like'] += int(digg_count) if digg_count else 0
        total_stats['comment'] += int(comment_count) if comment_count else 0
        total_stats['share'] += int(share_count) if share_count else 0
        
        # 时间
        create_time = video.get('create_time', video.get('created_time', 0))
        if create_time:
            date_str = datetime.fromtimestamp(int(create_time)).strftime('%Y-%m-%d %H:%M')
        else:
            date_str = video.get('create_time_str', 'N/A')
        
        # 描述
        desc = video.get('desc', video.get('description', video.get('caption', '无描述')))
        
        rows.append({
            '发布时间': date_str,
            '视频描述': (desc[:50] + '...') if desc else '无描述',
            '播放量': int(play_count) if play_count else 0,
            '点赞数': int(digg_count) if digg_count else 0,
            '评论数': int(comment_count) if comment_count else 0,
            '分享数': int(share_count) if share_count else 0,
        })
    
    return rows, total_stats, account_info

# ============================================
# 🎨 主界面
# ============================================
def main():
    st.title("🎵 TikTok数据监控看板")
    st.markdown("*powered by TikHub API*")
    
    api_key = get_api_key()
    
    if not api_key:
        st.warning("⚠️ 请先在侧边栏输入 API Key")
        st.stop()
    
    # 侧边栏配置
    with st.sidebar:
        st.header("⚙️ 配置")
        username = st.text_input("TikTok用户名", placeholder="photorevive.ai", value="photorevive.ai")
        count = st.slider("抓取数量", 1, 30, 10)
        
        st.divider()
        
        if st.button("🚀 获取数据", type="primary", use_container_width=True):
            st.session_state['fetch'] = True
        
        if st.button("🔍 调试模式", use_container_width=True):
            st.session_state['debug'] = True
    
    # 调试模式
    if st.session_state.get('debug', False):
        st.session_state['debug'] = False
        st.subheader("🔍 调试信息")
        st.write(f"**API Key:** {api_key[:20]}...{api_key[-10:]}")
        st.write(f"**Key 长度:** {len(api_key)} 字符")
        st.write(f"**用户名:** {username}")
        
        # 测试连接
        st.write("**测试连接...**")
        test_url = "https://api.tikhub.io/api/v1/user/credits"
        headers = {"Authorization": f"Bearer {api_key}"}
        try:
            response = requests.get(test_url, headers=headers, timeout=10)
            st.write(f"状态码：{response.status_code}")
            st.write(response.text[:500])
        except Exception as e:
            st.error(f"错误：{e}")
    
    # 获取数据
    if st.session_state.get('fetch', False):
        st.session_state['fetch'] = False
        
        if not username:
            st.error("请输入用户名")
            st.stop()
        
        with st.spinner(f'正在抓取 @{username} ...'):
            result = fetch_tiktok_data(api_key, username, count)
        
        if result['success']:
            st.success(f"✅ 成功！使用端点：{result.get('endpoint', 'unknown')}")
            
            # 显示原始数据（可折叠）
            with st.expander("📄 查看原始数据"):
                st.json(result['data'])
            
            # 解析数据
            rows, total_stats, account_info = parse_data(result['data'])
            
            if not rows:
                st.warning("⚠️ 未找到视频数据")
                st.write("数据结构：")
                st.json(result['data'])
            else:
                # 核心指标
                st.subheader("📊 数据概览")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("总播放量", f"{total_stats['play']:,}")
                with col2:
                    st.metric("总点赞数", f"{total_stats['like']:,}")
                with col3:
                    st.metric("总评论数", f"{total_stats['comment']:,}")
                with col4:
                    st.metric("视频数", len(rows))
                
                st.divider()
                
                # 表格
                df = pd.DataFrame(rows)
                st.dataframe(df, use_container_width=True)
                
                # 图表
                if not df.empty:
                    st.bar_chart(df.set_index('发布时间')['播放量'])
                
                # 下载
                csv = df.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 下载CSV", csv, f"{username}.csv", "text/csv")
        else:
            st.error(f"❌ {result['error']}")
            st.write(result.get('details', ''))
            
            with st.expander("💡 排查建议"):
                st.write("""
                1. **检查 API Key**：确保在 TikHub 后台有效
                2. **检查余额**：登录 https://tikhub.io 查看余额
                3. **检查权限**：确认已开通 TikTok API 权限
                4. **联系客服**：https://discord.gg/aMEAS8Xsvz
                """)

if __name__ == "__main__":
    main()
