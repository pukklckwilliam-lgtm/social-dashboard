# 🎯 TikTok账号数据监控看板 - Post Bridge版
import streamlit as st
import requests
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="🎵 TikTok数据监控", layout="wide", page_icon="🎵")

# ============================================
# 🔑 API Key 管理
# ============================================
def get_api_keys():
    """获取API Keys"""
    keys = {}
    
    # TikHub API Key（用于抓取公开数据）
    if "tikhub_api_key" in st.secrets:
        keys['tikhub'] = st.secrets["tikhub_api_key"]
        st.sidebar.success("✅ TikHub API Key 已加载")
    else:
        with st.sidebar:
            keys['tikhub'] = st.text_input("🎵 TikHub API Key", type="password", 
                                          help="用于抓取任意TikTok账号数据")
    
    # Post Bridge API Key（用于管理已连接账号）
    if "postbridge_api_key" in st.secrets:
        keys['postbridge'] = st.secrets["postbridge_api_key"]
        st.sidebar.success("🌉 Post Bridge API Key 已加载")
    else:
        with st.sidebar:
            keys['postbridge'] = st.text_input("🌉 Post Bridge API Key", type="password",
                                              help="用于管理已连接的自有账号")
    
    return keys

# ============================================
# 📡 TikHub 数据抓取函数
# ============================================
def fetch_tiktok_videos(api_key, username, count=10):
    """从TikHub获取TikTok视频数据"""
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
            if result.get('code') == 200:
                return {"success": True, "data": result}
            else:
                return {"success": False, "error": result.get('message', 'API返回错误')}
        else:
            return {"success": False, "error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ============================================
# 📊 数据解析函数
# ============================================
def parse_tiktok_data(result, username):
    """解析TikTok视频数据"""
    if 'data' not in result or 'aweme_list' not in result['data']:
        return [], {}
    
    video_list = result['data']['aweme_list']
    rows = []
    
    # 统计总数
    total_stats = {'play': 0, 'like': 0, 'comment': 0, 'share': 0}
    
    # 获取账号信息（从第一个视频）
    account_info = {}
    if video_list and 'author' in video_list[0]:
        author = video_list[0]['author']
        account_info = {
            'nickname': author.get('nickname', username),
            'unique_id': author.get('unique_id', username),
            'avatar': author.get('avatar_thumb', {}).get('url_list', [''])[0] if author.get('avatar_thumb') else '',
            'signature': author.get('signature', ''),
            'total_favorited': author.get('total_favorited', 0)
        }
    
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
    
    return rows, total_stats, account_info

# ============================================
# 🎨 主界面
# ============================================
def main():
    st.title("🎵 TikTok账号数据监控看板")
    st.markdown("*专门用于监控TikTok账号数据*")
    
    # 获取API Keys
    api_keys = get_api_keys()
    
    if not api_keys.get('tikhub') and not api_keys.get('postbridge'):
        st.warning("⚠️ **请先配置至少一个API Key！**\n\n在左侧侧边栏输入TikHub或Post Bridge的API Key")
        st.stop()
    
    # 侧边栏配置
    with st.sidebar:
        st.header("⚙️ 配置")
        
        # 数据源选择
        data_source = st.radio(
            "选择数据源",
            ["TikHub（任意账号）", "Post Bridge（自有账号）"],
            help="TikHub: 可抓取任意公开账号 | Post Bridge: 仅限已连接的自有账号"
        )
        
        st.divider()
        
        # 刷新按钮
        if st.button("🔄 刷新数据", use_container_width=True):
            st.session_state['refresh'] = True
    
    # ========================================
    # 方式1: TikHub - 抓取任意账号
    # ========================================
    if data_source == "TikHub（任意账号）":
        if not api_keys.get('tikhub'):
            st.error("❌ 请先在侧边栏输入TikHub API Key")
            st.stop()
        
        # 账号输入
        st.subheader("📝 输入TikTok账号")
        col1, col2 = st.columns([3, 1])
        with col1:
            username = st.text_input("TikTok用户名", placeholder="例如：photorevive.ai", value="photorevive.ai")
        with col2:
            count = st.number_input("抓取数量", min_value=1, max_value=30, value=10)
        
        # 获取数据按钮
        if st.button("🚀 获取数据", type="primary", use_container_width=True):
            if not username:
                st.error("❌ 请输入用户名")
                st.stop()
            
            with st.spinner(f'正在抓取 @{username} 的数据...'):
                result = fetch_tiktok_videos(api_keys['tikhub'], username, count)
                
                if not result['success']:
                    st.error(f"❌ {result['error']}")
                    if 'details' in result:
                        st.text(result['details'])
                else:
                    st.success("✅ 数据获取成功！")
                    
                    # 解析数据
                    rows, total_stats, account_info = parse_tiktok_data(result['data'], username)
                    
                    if not rows:
                        st.warning("⚠️ 未找到视频数据，请检查账号是否正确")
                    else:
                        # 显示账号信息
                        if account_info:
                            st.subheader(f"👤 @{account_info.get('unique_id', username)}")
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.write(f"**昵称:** {account_info.get('nickname', 'N/A')}")
                            with col2:
                                st.write(f"**总获赞:** {account_info.get('total_favorited', 0):,}")
                            with col3:
                                st.write(f"**视频数:** {len(rows)}")
                            
                            if account_info.get('signature'):
                                st.caption(f"📝 {account_info['signature']}")
                        
                        st.divider()
                        
                        # === 核心数据概览 ===
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
                        
                        # === 数据表格 ===
                        st.subheader("📋 视频详细列表")
                        df = pd.DataFrame(rows)
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
                                label="📥 下载CSV数据",
                                data=csv,
                                file_name=f'tiktok_{username}_{datetime.now().strftime("%Y%m%d")}.csv',
                                mime='text/csv',
                                use_container_width=True
                            )
                        with col2:
                            import json
                            json_str = json.dumps(result['data'], indent=2, ensure_ascii=False)
                            st.download_button(
                                label="📥 下载完整JSON",
                                data=json_str,
                                file_name=f'tiktok_{username}_{datetime.now().strftime("%Y%m%d")}.json',
                                mime='application/json',
                                use_container_width=True
                            )
    
    # ========================================
    # 方式2: Post Bridge - 已连接账号
    # ========================================
    else:
        if not api_keys.get('postbridge'):
            st.error("❌ 请先在侧边栏输入Post Bridge API Key")
            st.stop()
        
        st.subheader("🔌 已连接的TikTok账号")
        
        # 获取已连接账号
        with st.spinner("正在获取已连接账号..."):
            accounts_url = "https://api.post-bridge.com/v1/social-accounts"
            headers = {"Authorization": f"Bearer {api_keys['postbridge']}"}
            
            try:
                response = requests.get(accounts_url, headers=headers, timeout=30)
                if response.status_code == 200:
                    accounts_data = response.json()
                    accounts = accounts_data.get("data", [])
                    
                    # 筛选TikTok账号
                    tiktok_accounts = [acc for acc in accounts if acc.get("platform", "").lower() == "tiktok"]
                    
                    if not tiktok_accounts:
                        st.warning("⚠️ 未找到已连接的TikTok账号")
                        st.markdown("""
                        ### 📌 如何连接账号：
                        1. 登录 [Post Bridge Dashboard](https://post-bridge.com)
                        2. 点击 **Connect Account**
                        3. 选择 **TikTok** 并完成授权
                        4. 刷新此页面
                        """)
                        st.stop()
                    
                    # 账号选择器
                    account_options = {f"@{acc.get('username', 'Unknown')}": acc for acc in tiktok_accounts}
                    selected_name = st.selectbox("选择TikTok账号", list(account_options.keys()))
                    selected_account = account_options[selected_name]
                    account_id = selected_account.get("id")
                    
                    st.info(f"**当前账号：** {selected_name} | **ID:** `{account_id}`")
                    
                    # 获取分析数据
                    if st.button("📊 获取分析数据", type="primary", use_container_width=True):
                        analytics_url = "https://api.post-bridge.com/v1/analytics"
                        params = {"account_id": account_id}
                        
                        with st.spinner("正在获取分析数据..."):
                            response = requests.get(analytics_url, headers=headers, params=params, timeout=30)
                            if response.status_code == 200:
                                analytics_data = response.json()
                                st.success("✅ 数据获取成功！")
                                
                                # 显示数据
                                data = analytics_data.get("data", {})
                                if isinstance(data, dict):
                                    cols = st.columns(4)
                                    metrics = [
                                        ("粉丝数", data.get("followers", "N/A")),
                                        ("关注数", data.get("following", "N/A")),
                                        ("点赞数", data.get("likes", "N/A")),
                                        ("视频数", data.get("videos", "N/A"))
                                    ]
                                    for i, (label, value) in enumerate(metrics):
                                        with cols[i % 4]:
                                            st.metric(label, f"{value:,}" if isinstance(value, int) else value)
                                else:
                                    st.json(data)
                            else:
                                st.error(f"❌ HTTP {response.status_code}")
            except Exception as e:
                st.error(f"❌ 请求失败：{str(e)}")

# ============================================
# 页脚
# ============================================
st.markdown("---")
st.caption("🛠️ powered by TikHub & Post Bridge | 仅显示TikTok账号数据")

if __name__ == "__main__":
    import json
    main()
