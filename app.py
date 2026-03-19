# 🎯 多产品社媒监控系统 - 最终修复版（v2 接口）
import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import json

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
                "api_endpoint": "/api/v1/tiktok/app/v3/fetch_user_post_videos_v2",  # ✅ v2 接口
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
    },
    "产品 2（示例）": {
        "image": "https://via.placeholder.com/300",
        "description": "第二个产品",
        "accounts": {
            "TikTok": {
                "username": "charlidamelio",
                "api_endpoint": "/api/v1/tiktok/app/v3/fetch_user_post_videos_v2",
                "param_name": "unique_id",
                "method": "GET"
            }
        }
    }
}

# ============================================
# 🔑 API Key 管理
# ============================================
API_KEY = "vpA5E99O82r1tnSpPrLOwkiJKgm9arlJ1AH7g2ulb9jmm12uGiejcCi/aA=="

def get_api_key():
    """获取 API Key"""
    try:
        if hasattr(st, 'secrets') and "tikhub_api_key" in st.secrets:
            key = st.secrets["tikhub_api_key"]
            if key and isinstance(key, str) and key.strip():
                return key.strip()
    except:
        pass
    
    with st.sidebar:
        api_key = st.text_input("🔑 TikHub API Key", type="password", 
                               value=API_KEY,
                               help="已预填默认 Key")
        if api_key and api_key.strip():
            api_key = api_key.strip()
            st.session_state["api_key"] = api_key
            st.sidebar.success("✅ 已保存")
            return api_key
        elif "api_key" in st.session_state:
            return st.session_state["api_key"]
    
    return API_KEY

# ============================================
# 📡 数据获取函数
# ============================================
def fetch_account_data(api_key, platform, username, endpoint, param_name, method="GET"):
    """获取账号数据"""
    
    if not api_key or api_key in ["None", "null", ""]:
        return {"success": False, "error": "API Key 无效"}
    
    # ✅ 修复：URL 拼接无空格
    url = f"https://api.tikhub.io{endpoint}"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    params = {param_name: username.strip().lstrip('@'), "count": 10}
    
    try:
        if method.upper() == "POST":
            response = requests.post(url, json=params, headers=headers, timeout=30)
        else:
            response = requests.get(url, params=params, headers=headers, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('code') == 200 or 'data' in result:
                return {"success": True, "data": result}
            else:
                return {"success": False, "error": result.get('message', 'API错误')}
        else:
            return {"success": False, "error": f"HTTP {response.status_code}", 
                    "details": response.text[:300]}
    except Exception as e:
        return {"success": False, "error": f"请求异常：{str(e)}"}

# ============================================
# 🎨 页面状态管理
# ============================================
if "current_page" not in st.session_state:
    st.session_state.current_page = "home"
if "selected_product" not in st.session_state:
    st.session_state.selected_product = None
if "selected_platform" not in st.session_state:
    st.session_state.selected_platform = None

# ============================================
# 🏠 首页：产品总览
# ============================================
def render_home_page():
    st.title("📊 社媒产品监控系统")
    st.markdown("*查看所有产品的社媒数据概览*")
    
    # 产品卡片网格
    cols = st.columns(min(3, len(PRODUCTS_CONFIG)))
    
    for idx, (product_name, config) in enumerate(PRODUCTS_CONFIG.items()):
        with cols[idx % 3]:
            with st.container(border=True):
                # 产品图片
                try:
                    st.image(config["image"], use_container_width=True)
                except:
                    st.write("🖼️ [图片]")
                
                # 产品名称
                st.subheader(product_name)
                
                # 产品描述
                st.caption(config["description"])
                
                # 账号数量
                st.metric("平台数量", len(config["accounts"]))
                
                # 进入按钮
                if st.button("查看详情", key=f"view_{product_name}", use_container_width=True):
                    st.session_state.selected_product = product_name
                    st.session_state.current_page = "product"
                    st.rerun()

# ============================================
# 📱 产品详情页
# ============================================
def render_product_page():
    product_name = st.session_state.selected_product
    config = PRODUCTS_CONFIG[product_name]
    
    # 返回按钮
    if st.button("← 返回首页"):
        st.session_state.current_page = "home"
        st.session_state.selected_product = None
        st.rerun()
    
    st.title(f"📱 {product_name}")
    st.markdown(f"*{config['description']}*")
    
    # 平台选择器
    platforms = list(config["accounts"].keys())
    selected_platform = st.selectbox("选择平台", platforms)
    
    if selected_platform:
        st.session_state.selected_platform = selected_platform
        account_config = config["accounts"][selected_platform]
        
        # 获取数据
        api_key = get_api_key()
        if api_key:
            # 账号输入
            st.subheader(f"⚙️ {selected_platform} 配置")
            col1, col2 = st.columns([3, 1])
            with col1:
                username = st.text_input(
                    "用户名/ID", 
                    value=account_config["username"],
                    help=account_config.get("note", "")
                )
            with col2:
                count = st.slider("抓取数量", 1, 30, 10)
            
            if st.button("🚀 获取数据", type="primary", use_container_width=True):
                with st.spinner(f'正在获取 {selected_platform} 数据...'):
                    data = fetch_account_data(
                        api_key,
                        selected_platform,
                        username,
                        account_config["api_endpoint"],
                        account_config["param_name"],
                        account_config.get("method", "GET")
                    )
                    
                    if "error" in data or not data.get("success"):
                        st.error(f"❌ {data.get('error', '未知错误')}")
                        if 'details' in data:
                            with st.expander("🔍 查看详细错误"):
                                st.code(data['details'])
                        
                        # Instagram 特殊提示
                        if selected_platform == "Instagram" and "403" in data.get("error", ""):
                            st.info("""
                            **Instagram 403 解决方案：**
                            1. 在 TikHub 后台开通 Instagram API 权限
                            2. user_id 需要是数字 ID，不是用户名
                            3. 可用查询接口先获取数字 ID
                            """)
                    else:
                        st.success("✅ 数据获取成功！")
                        st.subheader(f"@{username}")
                        
                        # 解析数据（根据不同平台调整）
                        if selected_platform == "TikTok":
                            display_tiktok_data(data["data"], username)
                        else:
                            with st.expander("📄 查看原始数据"):
                                st.json(data["data"])
                            st.info(f"ℹ️ {selected_platform} 数据展示功能开发中")
                        
                        # 主页链接
                        platform_lower = selected_platform.lower().replace(' ', '').replace('(twitter)', 'twitter')
                        st.markdown(f"**[访问 {selected_platform} 主页](https://{platform_lower}.com/{username.lstrip('@')})**")
        else:
            st.warning("请先在侧边栏输入 API Key")

# ============================================
# 📊 TikTok 数据展示
# ============================================
def display_tiktok_data(data, username):
    """展示 TikTok 账号数据"""
    data_content = data.get("data", {})
    
    # 兼容 v2/v3 接口
    aweme_list = data_content.get('aweme_list', 
                   data_content.get('videos', 
                   data_content.get('items', [])))
    
    if not aweme_list:
        st.warning("⚠️ 未找到视频数据")
        with st.expander("🔍 查看原始响应"):
            st.json(data)
        return
    
    st.success(f"✅ 成功获取 {len(aweme_list)} 个视频！")
    
    # 账号信息
    if aweme_list and 'author' in aweme_list[0]:
        author = aweme_list[0]['author']
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
    
    # 核心指标
    total_stats = {"play": 0, "like": 0, "comment": 0, "share": 0}
    rows = []
    
    for video in aweme_list:
        stats = video.get('statistics', video.get('stats', {}))
        create_time = video.get('create_time', video.get('created_time', 0))
        date_str = datetime.fromtimestamp(create_time).strftime('%Y-%m-%d') if create_time else 'N/A'
        
        play = stats.get('play_count', stats.get('view_count', 0))
        like = stats.get('digg_count', stats.get('like_count', 0))
        comment = stats.get('comment_count', stats.get('comments', 0))
        share = stats.get('share_count', stats.get('shares', 0))
        
        total_stats["play"] += play
        total_stats["like"] += like
        total_stats["comment"] += comment
        total_stats["share"] += share
        
        rows.append({
            '发布时间': date_str,
            '描述': (video.get('desc', video.get('description', ''))[:50] + '...') if video.get('desc') or video.get('description') else '无描述',
            '播放量': play,
            '点赞数': like,
            '评论数': comment,
            '分享数': share,
            '链接': video.get('share_url', '')
        })
    
    # 指标卡片
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
    st.subheader("📋 视频列表")
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # 图表
    if not df.empty:
        st.subheader("📊 播放量趋势")
        st.bar_chart(df.set_index('发布时间')['播放量'], use_container_width=True)
    
    # 下载按钮
    st.divider()
    csv = df.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="📥 下载 CSV",
        data=csv,
        file_name=f"tiktok_{username}_{datetime.now().strftime('%Y%m%d')}.csv",
        mime='text/csv',
        use_container_width=True
    )

# ============================================
# 🚀 主程序
# ============================================
def main():
    api_key = get_api_key()
    
    if not api_key and st.session_state.current_page != "home":
        st.warning("⚠️ 请先在侧边栏输入 API Key")
    
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
st.caption("🛠️ powered by TikHub API & Streamlit | 接口版本：v2")
