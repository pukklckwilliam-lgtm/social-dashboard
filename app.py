# 🎯 多产品社媒监控系统 - TikTok 完整版（无 plotly 依赖）
import streamlit as st
import requests
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="📊 社媒监控系统", layout="wide", page_icon="📱")

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
                "api_endpoint": "/api/v1/tiktok/app/v3/fetch_user_post_videos_v2",
                "param_name": "unique_id"
            }
        }
    },
    "LingoAI": {
        "image": "https://via.placeholder.com/300/4A90E2/FFFFFF?text=LingoAI",
        "description": "语言学习工具",
        "accounts": {
            "TikTok": {
                "username": "charlidamelio",
                "api_endpoint": "/api/v1/tiktok/app/v3/fetch_user_post_videos_v2",
                "param_name": "unique_id"
            }
        }
    }
}

# ============================================
# 🔑 API Key
# ============================================
API_KEY = "vpA5E99O82r1tnSpPrLOwkiJKgm9arlJ1AH7g2ulb9jmm12uGiejcCi/aA=="

def get_api_key():
    try:
        if hasattr(st, 'secrets') and "tikhub_api_key" in st.secrets:
            return st.secrets["tikhub_api_key"].strip()
    except:
        pass
    
    with st.sidebar:
        api_key = st.text_input("🔑 API Key", type="password", value=API_KEY)
        if api_key:
            st.session_state["api_key"] = api_key.strip()
    
    return st.session_state.get("api_key", API_KEY)

# ============================================
# 📡 数据抓取
# ============================================
def fetch_tiktok_data(username):
    """抓取 TikTok 数据"""
    url = "https://api.tikhub.io/api/v1/tiktok/app/v3/fetch_user_post_videos_v2"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    params = {"unique_id": username, "count": 20}
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)
        if response.status_code == 200:
            result = response.json()
            if result.get('code') == 200:
                return result
        return None
    except:
        return None

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
    st.markdown("*监控多产品社媒数据*")
    
    # 产品卡片网格
    cols = st.columns(min(3, len(PRODUCTS_CONFIG)))
    
    for idx, (product_name, config) in enumerate(PRODUCTS_CONFIG.items()):
        with cols[idx % 3]:
            with st.container(border=True):
                # 产品图片
                try:
                    st.image(config["image"], use_container_width=True)
                except:
                    st.write("🖼️")
                
                # 产品名称
                st.subheader(product_name)
                st.caption(config["description"])
                
                # 账号数量
                st.metric("平台数", len(config["accounts"]))
                
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
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("← 返回"):
            st.session_state.current_page = "home"
            st.session_state.selected_product = None
            st.rerun()
    
    st.title(f"📱 {product_name}")
    st.markdown(f"*{config['description']}*")
    
    # 获取所有平台数据
    st.subheader("📊 各平台数据总览")
    
    # 存储各平台数据
    platform_data = {}
    
    # 获取 TikTok 数据
    if "TikTok" in config["accounts"]:
        tiktok_config = config["accounts"]["TikTok"]
        username = tiktok_config["username"]
        
        with st.spinner(f"正在获取 TikTok @{username} ..."):
            result = fetch_tiktok_data(username)
            
            if result:
                data_content = result.get("data", {})
                video_list = data_content.get("aweme_list", [])
                
                if video_list:
                    # 账号信息
                    author = video_list[0].get("author", {})
                    platform_data["TikTok"] = {
                        "username": author.get("unique_id", username),
                        "nickname": author.get("nickname", ""),
                        "followers": author.get("follower_count", 0),
                        "following": author.get("following_count", 0),
                        "total_likes": author.get("total_favorited", 0),
                        "videos": video_list
                    }
                    
                    # 显示账号卡片
                    st.success(f"✅ TikTok: @{platform_data['TikTok']['username']}")
                    
                    # 核心指标
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("粉丝数", f"{platform_data['TikTok']['followers']:,}")
                    with col2:
                        st.metric("关注数", f"{platform_data['TikTok']['following']:,}")
                    with col3:
                        st.metric("总获赞", f"{platform_data['TikTok']['total_likes']:,}")
                    
                    # 主页链接
                    st.markdown(f"**🔗 [访问 TikTok 主页](https://tiktok.com/@{username})**")
                    
                    # 粉丝分布饼图（用 Streamlit 内置）
                    st.divider()
                    st.subheader("📈 粉丝分布")
                    
                    # 创建饼图数据
                    pie_data = pd.DataFrame({
                        "平台": ["TikTok", "其他平台"],
                        "粉丝数": [platform_data['TikTok']['followers'], 0]
                    })
                    st.write("💡 待补充其他平台数据后显示完整分布")
                    st.dataframe(pie_data, use_container_width=True, hide_index=True)
                    
                    # 视频数据柱状图（用 Streamlit 内置）
                    st.divider()
                    st.subheader("📊 视频表现")
                    
                    # 统计每个视频的播放量
                    video_stats = []
                    for i, video in enumerate(video_list[:10]):
                        stats = video.get("statistics", {})
                        video_stats.append({
                            "视频": f"视频{i+1}",
                            "播放量": stats.get("play_count", 0),
                            "点赞数": stats.get("digg_count", 0)
                        })
                    
                    df = pd.DataFrame(video_stats)
                    st.bar_chart(df.set_index('视频')['播放量'], use_container_width=True)
                    
                    # 点赞数图表
                    st.bar_chart(df.set_index('视频')['点赞数'], use_container_width=True)
                    
                    # 视频封面墙
                    st.divider()
                    st.subheader("🎬 视频列表")
                    
                    video_cols = st.columns(3)
                    for idx, video in enumerate(video_list[:9]):  # 显示前 9 个
                        with video_cols[idx % 3]:
                            # 视频封面
                            cover_url = video.get("video", {}).get("cover", {}).get("url_list", [""])[0]
                            if cover_url:
                                st.image(cover_url, use_container_width=True)
                            
                            # 视频描述
                            desc = video.get("desc", "无描述")[:50] + "..."
                            st.caption(desc)
                            
                            # 统计数据
                            stats = video.get("statistics", {})
                            st.write(f"👁 {stats.get('play_count', 0):,} | ❤ {stats.get('digg_count', 0):,}")
                            
                            # 跳转链接
                            share_url = video.get("share_url", "")
                            if share_url:
                                st.markdown(f"[观看视频]({share_url})")
                    
                    # 加载更多按钮
                    if len(video_list) > 9:
                        if st.button(f"查看更多（共{len(video_list)}个视频）"):
                            st.info("显示全部视频功能开发中...")
                else:
                    st.warning("⚠️ 未找到视频数据")
            else:
                st.error("❌ 获取 TikTok 数据失败")
    
    # 其他平台（预留）
    st.divider()
    st.subheader("🚧 其他平台")
    st.info("Instagram、YouTube、X 平台功能开发中...")

# ============================================
# 🚀 主程序
# ============================================
def main():
    api_key = get_api_key()
    
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
st.caption("🛠️ powered by TikHub API & Streamlit")
