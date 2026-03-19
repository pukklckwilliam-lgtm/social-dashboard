# 🎯 多产品社媒监控系统 - 最终生产版
# API Key: vpA5E99O82r1tnSpPrLOwkiJKgm9arlJ1AH7g2ulb9jmm12uGiejcCi/aA==
import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import json

st.set_page_config(page_title="📊 PhotoRevive.AI 社媒监控", layout="wide", page_icon="🎵")

# ============================================
# 🔑 API Key 配置（已内置）
# ============================================
DEFAULT_API_KEY = "vpA5E99O82r1tnSpPrLOwkiJKgm9arlJ1AH7g2ulb9jmm12uGiejcCi/aA=="

def get_api_key():
    """获取 API Key - 优先级：Secrets > 侧边栏 > 默认值"""
    
    # 1. 优先从 Secrets 读取
    try:
        if hasattr(st, 'secrets') and "tikhub_api_key" in st.secrets:
            key = st.secrets["tikhub_api_key"]
            if key and isinstance(key, str) and key.strip():
                return key.strip()
    except:
        pass
    
    # 2. 从侧边栏读取
    with st.sidebar:
        st.header("🔑 API 配置")
        api_key = st.text_input("TikHub API Key", type="password", 
                               value=DEFAULT_API_KEY,
                               help="已预填，可直接使用")
        
        if api_key and api_key.strip():
            api_key = api_key.strip()
            st.session_state["api_key"] = api_key
            st.sidebar.success("✅ API Key 已加载")
            return api_key
        elif "api_key" in st.session_state:
            return st.session_state["api_key"]
    
    # 3. 返回默认值（调试用）
    return DEFAULT_API_KEY

# ============================================
# 📦 产品配置
# ============================================
PRODUCTS_CONFIG = {
    "PhotoRevive.AI": {
        "image": "https://p16-common-sign.tiktokcdn-us.com/tos-useast8-avt-0068-tx2/a62a32b54c026de51797e4862fd4ecd2~tplv-tiktokx-cropcenter:300:300.webp",
        "description": "AI 照片修复工具",
        "accounts": {
            "TikTok": {
                "username": "photorevive.ai",
                "api_endpoint": "/api/v1/tiktok/app/v3/fetch_user_post_videos_v3",
                "param_name": "unique_id",
                "method": "GET"
            },
            "Instagram": {
                "username": "photorevive.ai",
                "api_endpoint": "/api/v1/instagram/v3/get_user_profile",
                "param_name": "user_id",
                "method": "GET",
                "note": "⚠️ 需要数字用户 ID"
            },
            "YouTube": {
                "username": "@PhotoReviveAI",
                "api_endpoint": "/api/v1/youtube/web/get_channel_videos_v2",
                "param_name": "channel_id",
                "method": "GET"
            },
            "X (Twitter)": {
                "username": "photorevive_ai",
                "api_endpoint": "/api/v1/twitter/web/fetch_user_profile",
                "param_name": "username",
                "method": "GET"
            }
        }
    }
}

# ============================================
# 📡 数据获取函数（智能重试 + 多方式）
# ============================================
def fetch_account_data(api_key, platform, username, endpoint, param_name, method="GET"):
    """智能获取账号数据 - 支持多方式自动重试"""
    
    if not api_key or api_key in ["None", "null", ""]:
        return {"success": False, "error": "API Key 无效"}
    
    # 清理用户名
    clean_username = str(username).strip().lstrip('@')
    
    # 基础配置
    base_url = f"https://api.tikhub.io{endpoint}"
    base_headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0"
    }
    
    # 尝试的请求配置列表
    request_configs = [
        # 方式1: GET + Query Params（最常用）
        {
            "name": "GET+Params",
            "method": "GET",
            "url": base_url,
            "params": {param_name: clean_username, "count": 10},
            "json": None,
            "headers": base_headers
        },
        # 方式2: POST + JSON Body
        {
            "name": "POST+JSON",
            "method": "POST",
            "url": base_url,
            "params": None,
            "json": {param_name: clean_username, "count": 10},
            "headers": base_headers
        },
        # 方式3: POST + 额外参数（某些接口需要）
        {
            "name": "POST+Extra",
            "method": "POST",
            "url": base_url,
            "params": None,
            "json": {
                param_name: clean_username,
                "count": 10,
                "cursor": 0,
                "region": "US"
            },
            "headers": base_headers
        }
    ]
    
    last_error = None
    
    for config in request_configs:
        try:
            if config["method"] == "GET":
                response = requests.get(
                    config["url"],
                    params=config["params"],
                    headers=config["headers"],
                    timeout=30
                )
            else:
                response = requests.post(
                    config["url"],
                    json=config["json"],
                    headers=config["headers"],
                    timeout=30
                )
            
            if response.status_code == 200:
                result = response.json()
                # 检查 TikHub 响应格式
                if result.get('code') == 200 or 'data' in result or 'aweme_list' in str(result):
                    return {
                        "success": True, 
                        "data": result,
                        "method_used": config["name"]
                    }
            
            last_error = f"{config['name']}: HTTP {response.status_code}"
            
        except Exception as e:
            last_error = f"{config['name']}: {str(e)}"
            continue
    
    return {"success": False, "error": f"所有请求方式失败: {last_error}"}

# ============================================
# 📊 TikTok 数据解析与展示
# ============================================
def display_tiktok_data(result, username):
    """展示 TikTok 数据"""
    data_content = result.get('data', {})
    video_list = data_content.get('aweme_list', [])
    
    if not video_list:
        st.warning("⚠️ 未找到视频数据")
        with st.expander("🔍 查看原始响应"):
            st.json(result)
        return
    
    st.success(f"✅ 成功获取 {len(video_list)} 个视频！")
    
    # 账号信息
    if video_list and 'author' in video_list[0]:
        author = video_list[0]['author']
        st.subheader(f"👤 @{author.get('unique_id', username)}")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("昵称", author.get('nickname', 'N/A'))
        with col2:
            st.metric("粉丝数", f"{author.get('follower_count', 0):,}")
        with col3:
            st.metric("总获赞", f"{author.get('total_favorited', 0):,}")
        if author.get('signature'):
            st.caption(f"📝 {author['signature']}")
    
    st.divider()
    
    # 核心统计
    total_stats = {'play': 0, 'like': 0, 'comment': 0, 'share': 0}
    rows = []
    
    for video in video_list:
        stats = video.get('statistics', {})
        create_time = video.get('create_time', 0)
        date_str = datetime.fromtimestamp(create_time).strftime('%Y-%m-%d') if create_time else 'N/A'
        
        play = stats.get('play_count', 0)
        like = stats.get('digg_count', 0)
        comment = stats.get('comment_count', 0)
        share = stats.get('share_count', 0)
        
        total_stats['play'] += play
        total_stats['like'] += like
        total_stats['comment'] += comment
        total_stats['share'] += share
        
        rows.append({
            '发布时间': date_str,
            '描述': (video.get('desc', '')[:40] + '...') if video.get('desc') else '无',
            '播放': play,
            '点赞': like,
            '评论': comment,
            '分享': share,
            '链接': video.get('share_url', '')
        })
    
    # 指标卡片
    st.subheader("📈 核心数据概览")
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
    
    # 数据表格
    st.subheader("📋 视频列表")
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # 图表
    if not df.empty:
        st.subheader("📊 播放量趋势")
        st.bar_chart(df.set_index('发布时间')['播放'])
    
    # 下载
    st.divider()
    csv = df.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        "📥 下载 CSV",
        csv,
        f"tiktok_{username}_{datetime.now().strftime('%Y%m%d')}.csv",
        "text/csv",
        use_container_width=True
    )

# ============================================
# 🎨 页面状态管理
# ============================================
if "current_page" not in st.session_state:
    st.session_state.current_page = "home"
if "selected_product" not in st.session_state:
    st.session_state.selected_product = None

# ============================================
# 🏠 首页：产品总览
# ============================================
def render_home_page():
    st.title("📊 社媒产品监控系统")
    st.markdown("*监控多平台社媒数据 • 支持 TikTok/Instagram/YouTube/X*")
    
    # API Key 状态
    api_key = get_api_key()
    if api_key:
        st.sidebar.success(f"✅ API Key: `{api_key[:20]}...`")
    
    # 产品卡片
    cols = st.columns(min(3, len(PRODUCTS_CONFIG)))
    
    for idx, (product_name, config) in enumerate(PRODUCTS_CONFIG.items()):
        with cols[idx % 3]:
            with st.container(border=True):
                # 产品图片
                if config.get("image"):
                    try:
                        st.image(config["image"], use_container_width=True)
                    except:
                        st.write("🖼️ [图片]")
                
                # 产品信息
                st.subheader(product_name)
                st.caption(config.get("description", ""))
                st.metric("支持平台", len(config["accounts"]))
                
                # 进入按钮
                if st.button("🔍 查看详情", key=f"view_{product_name}", use_container_width=True):
                    st.session_state.selected_product = product_name
                    st.session_state.current_page = "product"
                    st.rerun()

# ============================================
# 📱 产品详情页
# ============================================
def render_product_page():
    product_name = st.session_state.selected_product
    config = PRODUCTS_CONFIG.get(product_name, {})
    
    # 返回按钮
    if st.button("← 返回首页"):
        st.session_state.current_page = "home"
        st.session_state.selected_product = None
        st.rerun()
    
    st.title(f"📱 {product_name}")
    st.markdown(f"*{config.get('description', '')}*")
    
    # 平台选择
    platforms = list(config.get("accounts", {}).keys())
    if not platforms:
        st.warning("⚠️ 该产品未配置任何平台")
        return
    
    selected_platform = st.selectbox("选择平台", platforms)
    account_config = config["accounts"][selected_platform]
    
    # 账号输入
    st.subheader(f"⚙️ {selected_platform} 配置")
    col1, col2 = st.columns(2)
    with col1:
        username = st.text_input(
            "用户名/ID", 
            value=account_config.get("username", ""),
            help=account_config.get("note", "")
        )
    with col2:
        count = st.slider("抓取数量", 1, 30, 10)
    
    # 获取数据按钮
    if st.button("🚀 获取数据", type="primary", use_container_width=True):
        if not username:
            st.error("❌ 请输入用户名/ID")
            st.stop()
        
        api_key = get_api_key()
        if not api_key:
            st.error("❌ API Key 无效")
            st.stop()
        
        with st.spinner(f"正在获取 {selected_platform} @{username} 的数据..."):
            result = fetch_account_data(
                api_key,
                selected_platform,
                username,
                account_config["api_endpoint"],
                account_config["param_name"],
                account_config.get("method", "GET")
            )
            
            if result.get("success"):
                st.success(f"✅ 获取成功！使用方式: {result.get('method_used', 'unknown')}")
                
                # 显示原始数据（可折叠）
                with st.expander("📄 查看原始 JSON"):
                    st.json(result["data"])
                
                # 根据平台展示
                if selected_platform == "TikTok":
                    display_tiktok_data(result["data"], username)
                else:
                    st.info(f"ℹ️ {selected_platform} 数据展示功能开发中，请先查看上方原始数据")
                    st.json(result["data"])
                
                # 主页链接
                platform_lower = selected_platform.lower().replace(' ', '').replace('(twitter)', 'twitter')
                st.markdown(f"""
                **🔗 访问主页：**
                [{selected_platform} @{username}](https://{platform_lower}.com/{username.lstrip('@')})
                """)
            else:
                st.error(f"❌ {result.get('error', '未知错误')}")
                
                # Instagram 特殊提示
                if selected_platform == "Instagram" and "403" in result.get("error", ""):
                    st.info("""
                    **Instagram 403 解决方案：**
                    1. 登录 TikHub 后台 → API Management
                    2. 确保已开通 **Instagram** 权限
                    3. `user_id` 需要是**数字**，不是用户名
                    4. 可用查询接口先获取数字 ID
                    """)

# ============================================
# 🚀 主程序
# ============================================
def main():
    api_key = get_api_key()
    
    # 页面路由
    if st.session_state.current_page == "home":
        render_home_page()
    elif st.session_state.current_page == "product":
        render_product_page()

if __name__ == "__main__":
    main()

# ============================================
# 页脚
# ============================================
st.markdown("---")
st.caption(f"🛠️ powered by TikHub API & Streamlit | API Key: `{DEFAULT_API_KEY[:20]}...`")
